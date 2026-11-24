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
