# Agent 3D Studio (A3DS)

Stage 01: an original agent-oriented geometry kernel. Python 3.11+ standard library only. No dependency on Blender, external CAD frameworks, shader engines, image-to-3D weights or remote APIs.

**Experimental geometry core, NOT a finished locomotive, universal CAD editor or production renderer.**

## Features
- Explicit right-handed coordinates: X = width, +Y = front, Z = up, 1 workspace unit = 1 BU.
- Vector arithmetic, transforms, normals and triangle-topology reports.
- Smooth sampled superellipse loft from editable cross-sections; asymmetrical nose and rear.
- Versioned parameter source in .a3ds.json.
- Native glTF 2.0 GLB export with PBR base color and correct Y-up conversion.
- A3DS Stage 01 subset GLB reader for roundtrip QA (not a general glTF importer).
- Automated regression and negative tests in GitHub Actions.

## Run
No dependencies to install. From repository root:

    python -m unittest discover -s tests -v
    python -m a3ds demo --out demo.glb --project demo.a3ds.json
    python -m a3ds inspect --file demo.glb
    python -m a3ds build --project demo.a3ds.json --out rebuilt.glb

Demo GLB can be opened in compatible 3D viewers. It is a geometry test fixture, NOT an accepted game model.

## Scope and safety
Stage 01 does not implement silhouette fitting, UV/texturing, mesh self-intersection tests, rendering, Factorio sprites or game testing. See docs/ARCHITECTURE.md and docs/STAGE01_ACCEPTANCE.md.

All development on feature/stage-01-geometry-kernel via Draft PR. The new repository main was initialized with ONLY the initial README; no merge without owner permission. Factorio and user art remain untouched.

## Stage 02: native camera and image generator (experimental)
The Stage 02 branch adds a pure-Python orthographic/perspective camera, near/far clipping, CPU Z-buffer renderer, deterministic PNG encoder, real-source silhouette masks, four one-way SVG grid sheets and explicit manual-landmark 2D registration.

Run in repository root:

    python -m unittest discover -s tests -v
    python -m a3ds demo --out stage01.glb --project stage01.a3ds.json
    python -m a3ds.stage02_cli --glb stage01.glb --out-dir out/stage02 --width 480 --height 360

The output folder contains four orthographic color PNG and 0.1 BU SVG grid sheets, a perspective hero PNG, five silhouette masks and report.json. All raster pixels come from the real 3D mesh. The Stage 01 original demo is a technical shape test; it is not approved game art.

See docs/CAMERA_COORDINATES.md and docs/STAGE02_ACCEPTANCE.md. Stage 02 is a stacked Draft PR, not yet merged into main.
