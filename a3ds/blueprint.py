"""Linked model-derived orthographic grid sheet, not a manually drawn fake blueprint.

Each SVG embeds the ACTUAL Stage 02 raster of the supplied mesh. The grid is
computed from its real camera projection and labels model-space Blender units.
It is a one-way view: editing SVG does not modify the parameter source.
"""
from __future__ import annotations

from base64 import b64encode
from math import ceil, floor, isfinite
from pathlib import Path
from xml.sax.saxutils import escape

from .camera import Camera
from .math3d import Vec3
from .mesh import Mesh
from .png import encode_png
from .raster import Render


_AXES = {
    "side": (Vec3(0, 1, 0), Vec3(0, 0, 1), "+Y", "+Z"),
    "top": (Vec3(1, 0, 0), Vec3(0, 1, 0), "+X", "+Y"),
    "front": (Vec3(-1, 0, 0), Vec3(0, 0, 1), "-X", "+Z"),
    "rear": (Vec3(1, 0, 0), Vec3(0, 0, 1), "+X", "+Z"),
}


def _fmt(value: float) -> str:
    return f"{value:.5f}".rstrip("0").rstrip(".")


def svg_grid_sheet(render: Render, camera: Camera, view: str, *, grid_step: float = 0.10) -> str:
    """Build standalone SVG with a world-aligned, calibrated 0.1BU grid."""
    if view not in _AXES or camera.projection != "orthographic":
        raise ValueError("Grid sheet needs an explicitly supported orthographic view")
    if not isfinite(grid_step) or grid_step <= 0:
        raise ValueError("grid_step must be positive and finite")
    # Major grid ticks are exactly at whole Blender units.
    major_count = round(1.0 / grid_step)
    if major_count < 1 or major_count > 100 or abs(major_count * grid_step - 1.0) > 1e-8:
        raise ValueError("grid_step must divide 1 BU into 1..100 equal parts")
    if (render.width, render.height) != (camera.width, camera.height):
        raise ValueError("Rendered image and camera resolution disagree")
    horizontal, vertical, label_h, label_v = _AXES[view]
    world_zero = Vec3(0, 0, 0)
    origin = camera.project(world_zero)
    axis_h = camera.project(horizontal)
    axis_v = camera.project(vertical)
    if origin is None or axis_h is None or axis_v is None:
        raise ValueError("Grid origin/axes lie behind the camera")
    du = axis_h.x - origin.x
    dv = axis_v.y - origin.y
    scale = camera.pixels_per_unit
    if abs(du - scale) > 1e-6 or abs(dv + scale) > 1e-6:
        raise ValueError("Camera is not axis-aligned for this orthographic sheet")
    W, H = render.width, render.height
    step_px = scale * grid_step
    if W / step_px > 4000 or H / step_px > 4000:
        raise ValueError("Grid density too high to export safely")

    # Fully portable SVG: all image bytes are embedded, no external links.
    png = encode_png(W, H, render.pixels)
    encoded = b64encode(png).decode("ascii")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H + 26}" viewBox="0 0 {W} {H + 26}">',
        f'<rect width="{W}" height="{H + 26}" fill="#ffffff"/>',
        f'<image width="{W}" height="{H}" href="data:image/png;base64,{encoded}"/>',
        f'<g stroke="#23364b" fill="none" shape-rendering="crispEdges">'
    ]

    for axis in ("u", "v"):
        origin_pixel = origin.x if axis == "u" else origin.y
        direction = 1 if axis == "u" else -1
        limit = W if axis == "u" else H
        # Include ticks on both sides of zero with explicit integer coordinates.
        bound = int(ceil((limit + abs(origin_pixel)) / step_px)) + 2
        for k in range(-bound, bound + 1):
            loc = origin_pixel + direction * k * step_px
            if not -0.5 <= loc <= limit + 0.5:
                continue
            major = k % major_count == 0
            stroke = "#e14a55" if k == 0 else ("#506b86" if major else "#a4b6c7")
            opacity = "0.83" if k == 0 else ("0.45" if major else "0.22")
            if axis == "u":
                parts.append(f'<line x1="{_fmt(loc)}" y1="0" x2="{_fmt(loc)}" y2="{H}" stroke="{stroke}" stroke-opacity="{opacity}"/>')
            else:
                parts.append(f'<line x1="0" y1="{_fmt(loc)}" x2="{W}" y2="{_fmt(loc)}" stroke="{stroke}" stroke-opacity="{opacity}"/>')
    parts.append("</g>")
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#69788a"/>')
    parts.append('<g fill="#162d44" font-family="monospace" font-size="11">')
    parts.append(f'<text x="7" y="{H + 17}">{escape(view.upper())}: horizontal {label_h}, vertical {label_v}; step {_fmt(grid_step)} BU, major 1 BU</text>')
    parts.append("</g></svg>")
    return "\n".join(parts) + "\n"


def save_grid_sheet(path: str | Path, render: Render, camera: Camera, view: str, *, grid_step: float = 0.10) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg_grid_sheet(render, camera, view, grid_step=grid_step), encoding="utf-8")
