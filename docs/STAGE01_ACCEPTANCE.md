# Stage 01 acceptance gates

1. Python 3.11+ stdlib; no Blender or GUI runtime dependency.
2. Matrix/vector operations and normals tested.
3. Invalid sizes, unsorted sections and invalid sampling rejected.
4. Asymmetric body loft is closed, outward, oriented and has no degenerate triangles.
5. Negative tests exercise bad indices, missing faces, edge conflicts and nonmanifold geometry.
6. glTF2 GLB JSON+BIN chunks with POSITION, NORMAL and uint32 indices are emitted reproducibly.
7. Readback restores vertices in A3DS coordinates within float32 tolerance and preserves face indices.
8. Versioned text project loads and produces byte-identical GLB.
9. GitHub Actions 3.11/3.12 execute tests and produce downloadable test fixture artifacts.
10. Record actual CI results with exact commit. Do not equate CI success with appearance or in-game correctness.

NOT verified: general third-party GLB import, mesh self-intersections, UV, textures, drawing/rendering, image comparison or Factorio behavior.
Owner's locomotive sketch is a later integration fixture. Test body is not finished asset.

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
