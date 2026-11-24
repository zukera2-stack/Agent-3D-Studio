"""Render native A3DS meshes in standard views using ONLY Python stdlib.

Example:
 python -m a3ds.stage02_cli --glb stage01.glb --out-dir out --width 480 --height 360
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .blueprint import save_grid_sheet
from .camera import standard_views
from .glb import read_glb
from .project import SurfaceProject, demo_project
from .raster import render_mesh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A3DS Stage 02 native projection/raster QA")
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--project", help="Saved Stage 01 .a3ds.json")
    sources.add_argument("--glb", help="A3DS Stage 01 GLB")
    parser.add_argument("--out-dir", required=True, help="Directory for deterministic PNG/SVG/JSON outputs")
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--grid", type=float, default=0.1)
    args = parser.parse_args(argv)

    if args.project:
        mesh = SurfaceProject.load(args.project).build()
        source = args.project
    elif args.glb:
        mesh = read_glb(args.glb)
        source = args.glb
    else:
        mesh = demo_project().build()
        source = "a3ds.demo_project"
    report = mesh.validate(require_closed=True, require_outward=True)
    if not report.ok:
        raise ValueError(f"Mesh rejected: {report.errors}")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    views = standard_views(args.width, args.height)
    stats = {
        "format": "a3ds.stage02-projection-report/1",
        "source": Path(source).name,
        "mesh": report.to_dict(),
        "units": "BU",
        "grid_step": args.grid,
        "views": {},
    }
    for name, camera in views.items():
        render = render_mesh(mesh, camera)
        if render.covered == 0:
            raise ValueError(f"{name} camera rendered no pixels")
        render.save(out / f"{name}.png")
        render.save_mask(out / f"{name}_mask.png")
        if name != "hero":
            save_grid_sheet(out / f"{name}_grid.svg", render, camera, name, grid_step=args.grid)
        stats["views"][name] = {
            "projection": camera.projection,
            "width": camera.width,
            "height": camera.height,
            "covered_pixels": render.covered,
            "silhouette_bounds_px": render.silhouette_bounds(),
            "vertical_span_bu": camera.vertical_span if camera.projection == "orthographic" else None,
            "camera_position": camera.position.as_tuple(),
            "camera_target": camera.target.as_tuple(),
            "camera_up_hint": camera.up_hint.as_tuple(),
        }
    (out / "report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"A3DS Stage02 error: {exc}", file=sys.stderr)
        sys.exit(2)
