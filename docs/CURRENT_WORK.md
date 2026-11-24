# A3DS current work — 2026-11-24

Repository: zukera2-stack/Agent-3D-Studio, created by owner.

- main initialized solely with bootstrap README: acdeccc322e9db705bdde3edbbf507ca2b25f845.
- Active branch: feature/stage-01-geometry-kernel.
- Source: stdlib Python vector math, mesh topology, loft surfaces, JSON parameter project, native GLB encoder and own-subset GLB decoder.
- Tests: stdlib unittest and GitHub Actions matrix Python 3.11/3.12; report actual results and exact run URL.
- Demo is asymmetric geometry fixture, NOT user-accepted locomotive or released asset.
- No merges, releases, modifications of Factorio or of user art authorized.

Next gate: inspect GitHub Actions, fix any code/test failures, then verify against acceptance criteria. No viewer or game tests claimed.

## Verified Stage 01 CI evidence (2026-11-24)
- Tested code-and-workflow HEAD: 5bec5b2c44069a6bd1b628c4a963aed5645d490d.
- PR Actions: https://github.com/zukera2-stack/Agent-3D-Studio/actions/runs/45435315301 — SUCCESS, Python 3.11 and 3.12 jobs both SUCCESS.
- Push Actions: https://github.com/zukera2-stack/Agent-3D-Studio/actions/runs/45435277612 — SUCCESS, Python 3.11 and 3.12 jobs both SUCCESS.
- Real execution logs: 25 unit tests passed (each Python version), CLI generated the asymmetric mesh, inspector decoded exported GLB and the rebuilt bytes matched.
- Reported signed mesh volume: 17.680451953354446 BU^3 before export, 17.680451897979093 BU^3 after float32 GLB roundtrip. Boundary edges: 0; error list: empty.
- Exported deterministic GLB: 58,032 bytes.
- Download test fixtures with parameter JSON, GLB and logs from https://github.com/zukera2-stack/Agent-3D-Studio/actions/runs/45435315301/artifacts/14940846164 (3.11) or https://github.com/zukera2-stack/Agent-3D-Studio/actions/runs/45435315301/artifacts/14941791007 (3.12).
- This verifies **Stage 01 unit/CLI GLB workflow only**. NOT_RUN: independent third-party glTF conformance validator, independent viewer render/visual QA, self-intersection checks, sketch-fitting, UV/PBR texture tests, Factorio engine QA.
- PR #1 remains DRAFT. Owner has not accepted the sample as finished 3D art.
