"""Smooth elliptical/superelliptic loft through longitudinal cross sections.

Convention: X across body, +Y front, Z up. Cross-section ring winds in X/Z.
Geometry has capped ends; no external modeling package is used.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import copysign, cos, isfinite, pi, sin
from .math3d import Vec3
from .mesh import Mesh


@dataclass(frozen=True)
class CrossSection:
    y: float
    center_z: float
    half_width: float
    half_height: float
    exponent: float = 2.4

    def __post_init__(self) -> None:
        values = (self.y, self.center_z, self.half_width, self.half_height, self.exponent)
        if not all(isfinite(v) for v in values):
            raise ValueError("CrossSection values must be finite")
        if self.half_width <= 0 or self.half_height <= 0 or self.exponent < 1:
            raise ValueError("Invalid cross-section size or exponent")


def _spline_value(stations: list[CrossSection], index: int, alpha: float, field: str) -> float:
    """Piecewise cubic Hermite, derivatives measured against Y coordinates."""
    count = len(stations)
    a, b = stations[index], stations[index + 1]
    left = stations[max(0, index - 1)]
    right = stations[min(count - 1, index + 2)]
    get = lambda station: getattr(station, field)
    m0 = (get(b) - get(left)) / (b.y - left.y)
    m1 = (get(right) - get(a)) / (right.y - a.y)
    span = b.y - a.y
    t = alpha
    return (
        (2 * t**3 - 3 * t**2 + 1) * get(a)
        + (t**3 - 2 * t**2 + t) * span * m0
        + (-2 * t**3 + 3 * t**2) * get(b)
        + (t**3 - t**2) * span * m1
    )


def _interpolate(stations: list[CrossSection], steps_per_span: int) -> list[CrossSection]:
    rings: list[CrossSection] = []
    for i in range(len(stations) - 1):
        a, b = stations[i], stations[i + 1]
        for sub in range(steps_per_span):
            t = sub / steps_per_span
            # Smooth values but clamp overshoot in positive dimensions.
            fields = {
                field: _spline_value(stations, i, t, field)
                for field in ("center_z", "half_width", "half_height", "exponent")
            }
            rings.append(CrossSection(
                a.y + (b.y - a.y) * t,
                fields["center_z"],
                max(1e-5, fields["half_width"]),
                max(1e-5, fields["half_height"]),
                max(1.0, fields["exponent"]),
            ))
    rings.append(stations[-1])
    return rings


def loft_sections(
    sections: list[CrossSection],
    *,
    sides: int = 32,
    steps_per_span: int = 3,
    name: str = "Loft",
) -> Mesh:
    if len(sections) < 2:
        raise ValueError("At least two sections required")
    if sides < 8 or sides > 4096 or steps_per_span < 1 or steps_per_span > 128:
        raise ValueError("Invalid sampling resolution")
    if any(b.y <= a.y for a, b in zip(sections, sections[1:])):
        raise ValueError("Section Y coordinates must be strictly increasing")
    rings = _interpolate(sections, steps_per_span)
    vertices: list[Vec3] = []
    for ring in rings:
        power = 2.0 / ring.exponent
        for j in range(sides):
            angle = 2 * pi * j / sides
            c, s = cos(angle), sin(angle)
            x = ring.half_width * copysign(abs(c) ** power, c)
            z = ring.center_z + ring.half_height * copysign(abs(s) ** power, s)
            vertices.append(Vec3(x, ring.y, z))
    triangles: list[tuple[int, int, int]] = []
    for index in range(len(rings) - 1):
        base = index * sides
        next_base = (index + 1) * sides
        for j in range(sides):
            jp = (j + 1) % sides
            a, b, c, d = base + j, next_base + j, base + jp, next_base + jp
            # Outward normals for right-handed world, +Y front.
            triangles.extend([(a, b, c), (c, b, d)])
    back_center = len(vertices)
    vertices.append(Vec3(0, rings[0].y, rings[0].center_z))
    front_center = len(vertices)
    vertices.append(Vec3(0, rings[-1].y, rings[-1].center_z))
    front_offset = (len(rings) - 1) * sides
    for j in range(sides):
        jp = (j + 1) % sides
        # X/Z angle grows CCW when viewed from -Y: back normal is -Y.
        triangles.append((back_center, j, jp))
        triangles.append((front_center, front_offset + jp, front_offset + j))
    return Mesh(vertices, triangles, name)
