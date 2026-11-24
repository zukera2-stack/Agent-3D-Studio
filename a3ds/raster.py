"""Original CPU triangle rasterizer with a real Z-buffer and RGB/alpha-free masks.

No OpenGL, Blender, VTK, graphics backends, PIL or NumPy required.
Faces are clipped in camera depth space before perspective division.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, isfinite

from .camera import Camera, ScreenPoint
from .math3d import Vec3
from .mesh import Mesh
from .png import write_png


RGB = tuple[int, int, int]


def _rgb(color: tuple[int, ...]) -> RGB:
    if len(color) != 3 or any(not isinstance(c, int) or c < 0 or c > 255 for c in color):
        raise ValueError("RGB color must contain three integers in [0,255]")
    return color[0], color[1], color[2]


def _edge(a: ScreenPoint, b: ScreenPoint, x: float, y: float) -> float:
    return (x - a.x) * (b.y - a.y) - (y - a.y) * (b.x - a.x)


@dataclass
class Render:
    width: int
    height: int
    pixels: bytearray
    coverage: bytearray
    depth: list[float]

    def pixel(self, x: int, y: int) -> RGB:
        if not 0 <= x < self.width or not 0 <= y < self.height:
            raise IndexError("Pixel out of frame")
        i = (y * self.width + x) * 3
        return self.pixels[i], self.pixels[i + 1], self.pixels[i + 2]

    @property
    def covered(self) -> int:
        return sum(self.coverage)

    def silhouette_bounds(self) -> tuple[int, int, int, int] | None:
        indices = [i for i, v in enumerate(self.coverage) if v]
        if not indices:
            return None
        return (
            min(i % self.width for i in indices),
            min(i // self.width for i in indices),
            max(i % self.width for i in indices),
            max(i // self.width for i in indices),
        )

    def save(self, path: str) -> None:
        write_png(path, self.width, self.height, self.pixels)

    def save_mask(self, path: str) -> None:
        grayscale = bytearray(255 if visible else 0 for visible in self.coverage)
        write_png(path, self.width, self.height, grayscale, channels=1)


def _fill_triangle(
    result: Render,
    p: tuple[ScreenPoint, ScreenPoint, ScreenPoint],
    color: RGB,
    *,
    perspective: bool
) -> None:
    a, b, c = p
    area = _edge(a, b, c.x, c.y)
    if not isfinite(area) or abs(area) <= 1e-12:
        return
    min_x = max(0, floor(min(a.x, b.x, c.x)))
    max_x = min(result.width - 1, ceil(max(a.x, b.x, c.x)) - 1)
    min_y = max(0, floor(min(a.y, b.y, c.y)))
    max_y = min(result.height - 1, ceil(max(a.y, b.y, c.y)) - 1)
    if min_x > max_x or min_y > max_y:
        return
    sign = 1.0 if area > 0 else -1.0
    reciprocal = 1.0 / abs(area)
    invz_a, invz_b, invz_c = 1 / a.depth, 1 / b.depth, 1 / c.depth
    pixels = result.pixels
    coverage, zbuffer = result.coverage, result.depth
    W = result.width
    for y in range(min_y, max_y + 1):
        py = y + 0.5
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            w0 = sign * _edge(b, c, px, py) * reciprocal
            w1 = sign * _edge(c, a, px, py) * reciprocal
            w2 = sign * _edge(a, b, px, py) * reciprocal
            if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                continue
            if perspective:
                inv_depth = w0 * invz_a + w1 * invz_b + w2 * invz_c
                if inv_depth <= 0:
                    continue
                depth = 1 / inv_depth
            else:
                depth = w0 * a.depth + w1 * b.depth + w2 * c.depth
            index = y * W + x
            if depth < zbuffer[index]:
                zbuffer[index] = depth
                coverage[index] = 1
                off = 3 * index
                pixels[off:off + 3] = bytes(color)


def render_mesh(
    mesh: Mesh,
    camera: Camera,
    *,
    base_color: RGB = (171, 186, 204),
    background: RGB = (247, 249, 252),
    light: Vec3 = Vec3(0.65, -0.45, 1.0),
    ambient: float = 0.32,
    shade: bool = True,
    face_colors: list[RGB] | None = None,
) -> Render:
    report = mesh.validate()
    if not report.ok:
        raise ValueError("Cannot render invalid mesh: " + "; ".join(report.errors))
    base_color, background = _rgb(base_color), _rgb(background)
    if not 0.0 <= ambient <= 1.0 or not isfinite(ambient):
        raise ValueError("ambient must be between 0 and 1")
    if face_colors is not None:
        if len(face_colors) != len(mesh.triangles):
            raise ValueError("face_colors length must equal face count")
        face_colors = [_rgb(color) for color in face_colors]
    light = light.normalized() if shade else light
    width, height = camera.width, camera.height
    result = Render(
        width, height,
        bytearray(bytes(background) * (width * height)),
        bytearray(width * height),
        [float("inf")] * (width * height)
    )
    for face_index, face in enumerate(mesh.triangles):
        pts = [mesh.vertices[i] for i in face]
        normal = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized()
        color = face_colors[face_index] if face_colors is not None else base_color
        if shade:
            brightness = ambient + (1.0 - ambient) * max(0.0, normal.dot(light))
            color = tuple(min(255, max(0, round(component * brightness))) for component in color)
        for triangle in camera.clip_triangle(*pts):
            _fill_triangle(result, triangle, color, perspective=camera.projection == "perspective")
    return result


def render_silhouette(mesh: Mesh, camera: Camera) -> Render:
    """Black/white coverage-mask primitive for future sketch matching."""
    return render_mesh(mesh, camera, base_color=(255, 255, 255), background=(0, 0, 0), shade=False)
