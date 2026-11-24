# A3DS owner-accepted roadmap

- Stage 01: original geometry kernel, smooth asymmetric parametric loft, standards-based GLB and binary roundtrip QA.
- Stage 02: original cameras, normalized orthographic/raster projections and calibrated sketch alignment.
- Stage 03: constrained parameter optimization from several reference silhouettes, explicit inconsistency/uncertainty reporting.
- Stage 04: technical detail construction, UV/PBR materials, assemblies, game-oriented export validation.

Blender may be an independent inspector, never an A3DS core requirement. Never present intermediate blockout models as finished game art. Never modify Factorio main or its graphics as part of this project.

## Verified Stage 02 development milestone (2026-11-24)
Pure-Python five-view camera, near/far clipping, CPU Z-buffer and PNG/linked SVG grid are implemented on an isolated branch. Verified 54 tests on Python 3.11 and 3.12, independent Pillow decoding and 15 repeatable output files at GitHub Actions run 45438225604, commit c9523add915d2037a3932d0a48b0642380981caa. No Blender dependency, no Factorio game testing and no acceptance of test body as finished art.
The next Stage 03 must introduce measurable silhouette error, constrained optimization and explicit treatment of conflicting views.
