"""Original, deterministic camera mathematics for Stage 02.

World: right-handed X=width, +Y=front, Z=up (BU). Camera forward is
target-position; screen origin is upper-left; pixel centers are x+.5,y+.5.
Depth is POSITIVE along the viewing direction. Only view-Z is clipped.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, pi, radians, sin, tan

from .math3d import Vec3


@dataclass(frozen=True)
class ScreenPoint:
    x: float
    y: float
    depth: float


@dataclass(frozen=True)
class ViewPoint:
    x: float
    y: float
    depth: float


@dataclass(frozen=True)
class Camera:
    width: int
    height: int
    position: Vec3
    target: Vec3
    up_hint: Vec3
    projection: str = "orthographic"
    vertical_span: float = 8.0
    fov_y_degrees: float = 50.0
    near: float = 0.01
    far: float = 1000.0

    def __post_init__(self) -> None:
        if not isinstance(self.width, int) or not isinstance(self.height, int):
            raise ValueError("Camera dimensions must be integers")
        if self.width < 1 or self.height < 1 or self.width > 8192 or self.height > 8192:
            raise ValueError("Invalid camera resolution")
        if self.projection not in ("orthographic", "perspective"):
            raise ValueError("Unsupported camera projection")
        vals = (self.vertical_span, self.fov_y_degrees, self.near, self.far)
        if not all(isfinite(v) for v in vals) or self.vertical_span <= 0:
            raise ValueError("Camera scale must be finite and positive")
        if not 0.5 < self.fov_y_degrees < 179.5:
            raise ValueError("Perspective FOV must be between 0.5 and 179.5 degrees")
        if not 0 < self.near < self.far:
            raise ValueError("Require 0 < near < far")
        self.basis()

    def basis(self) -> tuple[Vec3, Vec3, Vec3]:
        """Return camera-right, screen-up, camera-forward (orthonormal)."""
        if not self.position.finite() or not self.target.finite() or not self.up_hint.finite():
            raise ValueError("Camera vectors must be finite")
        forward = (self.target - self.position).normalized()
        right = forward.cross(self.up_hint).normalized()
        up = right.cross(forward).normalized()
        return right, up, forward

    def view(self, point: Vec3) -> ViewPoint:
        right, up, forward = self.basis()
        d = point - self.position
        return ViewPoint(d.dot(right), d.dot(up), d.dot(forward))

    @property
    def pixels_per_unit(self) -> float:
        """Orthographic BU to pixels scale; not a perspective metric."""
        return self.height / self.vertical_span

    def screen(self, point: ViewPoint) -> ScreenPoint:
        if point.depth <= 0:
            raise ValueError("Projected view depth must be positive")
        if self.projection == "orthographic":
            factor = self.pixels_per_unit
        else:
            focal = self.height / (2.0 * tan(radians(self.fov_y_degrees) / 2.0))
            factor = focal / point.depth
        return ScreenPoint(
            self.width / 2.0 + point.x * factor,
            self.height / 2.0 - point.y * factor,
            point.depth
        )

    def project(self, world: Vec3) -> ScreenPoint | None:
        view = self.view(world)
        if not self.near <= view.depth <= self.far:
            return None
        return self.screen(view)

    def clip_triangle(self, a: Vec3, b: Vec3, c: Vec3) -> list[tuple[ScreenPoint, ScreenPoint, ScreenPoint]]:
        """Clip triangle against near/far planes in camera space.

        Returns zero, one or more screen-space triangles preserving winding.
        This prevents a vertex behind the camera from flipping its projection.
        """
        poly = [self.view(v) for v in (a, b, c)]

        def clip(poly: list[ViewPoint], z: float, keep_above: bool) -> list[ViewPoint]:
            if not poly:
                return []
            result: list[ViewPoint] = []
            previous = poly[-1]
            prev_inside = previous.depth >= z if keep_above else previous.depth <= z
            for current in poly:
                inside = current.depth >= z if keep_above else current.depth <= z
                if prev_inside != inside:
                    denom = current.depth - previous.depth
                    if denom == 0:
                        raise ValueError("Clipping plane crossing has zero depth delta")
                    t = (z - previous.depth) / denom
                    result.append(ViewPoint(
                        previous.x + (current.x - previous.x) * t,
                        previous.y + (current.y - previous.y) * t,
                        z
                    ))
                if inside:
                    result.append(current)
                previous, prev_inside = current, inside
            return result

        poly = clip(poly, self.near, True)
        poly = clip(poly, self.far, False)
        if len(poly) < 3:
            return []
        screen_poly = [self.screen(v) for v in poly]
        return [
            (screen_poly[0], screen_poly[i], screen_poly[i + 1])
            for i in range(1, len(screen_poly) - 1)
        ]


def standard_views(width: int = 640, height: int = 480) -> dict[str, Camera]:
    """Repeatable calibrated cameras for one A3DS fixture, never guessed from photos.

    Orthographic vertical_span fixes the Blender-unit scale. Side horizontal axis
    is +Y, top horizontal +X, front horizontal -X, matching camera viewpoint.
    Perspective hero is provided as an illustrative view only.
    """
    center = Vec3(0.0, 0.0, 1.15)
    up = Vec3(0, 0, 1)
    common = {"width": width, "height": height, "near": 0.01, "far": 100.0}
    return {
        "side": Camera(position=Vec3(14, 0, 1.15), target=center, up_hint=up,
                       vertical_span=6.2, **common),
        "top": Camera(position=Vec3(0, 0, 14), target=Vec3(0, 0, 0),
                      up_hint=Vec3(0, 1, 0), vertical_span=8.2, **common),
        "front": Camera(position=Vec3(0, 14, 1.15), target=center, up_hint=up,
                        vertical_span=3.2, **common),
        "rear": Camera(position=Vec3(0, -14, 1.15), target=center, up_hint=up,
                       vertical_span=3.2, **common),
        "hero": Camera(position=Vec3(8.5, 9.0, 6.5), target=center, up_hint=up,
                       projection="perspective", fov_y_degrees=52.0, **common),
    }
