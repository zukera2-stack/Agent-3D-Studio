"""Command-line entry: build an internal fixture or inspect our own GLB subset."""
import argparse
import json
from pathlib import Path
import sys

from .glb import read_glb, write_glb
from .project import SurfaceProject, demo_project


def _print_report(mesh, *, require_closed=True, require_outward=True) -> bool:
    report = mesh.validate(require_closed=require_closed, require_outward=require_outward)
    print(json.dumps({"mesh": mesh.name, **report.to_dict()}, ensure_ascii=False, indent=2))
    return report.ok


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="a3ds", description="Agent 3D Studio Stage 01")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Generate asymmetric test body and independent GLB")
    demo.add_argument("--out", required=True, help="Output .glb")
    demo.add_argument("--project", help="Optional JSON parametric project path")
    build = sub.add_parser("build", help="Build a saved parametric project")
    build.add_argument("--project", required=True)
    build.add_argument("--out", required=True)
    inspect = sub.add_parser("inspect", help="Read and validate A3DS Stage 01 GLB")
    inspect.add_argument("--file", required=True)
    args = parser.parse_args(argv)

    if args.command == "demo":
        project = demo_project()
        if args.project:
            project.save(args.project)
        mesh = project.build()
    elif args.command == "build":
        project = SurfaceProject.load(args.project)
        mesh = project.build()
    else:
        mesh = read_glb(args.file)
        return 0 if _print_report(mesh) else 1

    if not _print_report(mesh):
        return 1
    write_glb(mesh, args.out)
    reread = read_glb(args.out)
    original = mesh.validate(require_closed=True, require_outward=True)
    restored = reread.validate(require_closed=True, require_outward=True)
    if not restored.ok or restored.triangles != original.triangles or restored.vertices != original.vertices:
        raise ValueError("GLB roundtrip lost geometry counts")
    print(f"GLB export/import verified: {Path(args.out)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"A3DS error: {exc}", file=sys.stderr)
        sys.exit(2)
