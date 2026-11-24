# A3DS agent guardrails

Mission: original Python-controlled 3D model and image optimization tooling. Keep core inspectable, do not wrap Blender or copy unknown external CAD code.

Repository rules:
- main is bootstrap only; do not modify, merge PR or publish release without explicit owner permission.
- Active work uses STACKED Draft PRs: Stage 01 PR #1, Stage 02 PR #2 based on Stage 01, Stage 03 PR #3 based on Stage 02. Preserve parent order.
- Factorio repo and user-approved game models are separate and untouched unless owner approves.
- World coordinates: right-handed X across, +Y front, Z up; model units BU, no assumed real scale. GLB standard Y-up conversion is handled at export.
- JSON parameters are source of truth, GLB and PNG outputs are derived.
- Stage 03 core Python stdlib only; optional Pillow is for external image import and independent CI QA, not a mandatory rendering engine.
- Read docs/STAGE03_ACCEPTANCE.md, docs/CURRENT_WORK.md and docs/CAMERA_COORDINATES.md before changes.
- Only compare explicit calibrated reference silhouettes; an unprocessed perspective concept drawing is not a calibrated orthographic blueprint.
- Parameter search is bounded, logs all accepted moves and per-view loss, checks independent held-out views. No claim of unique physical 3D reconstruction from IoU.
- Distinguish local Python execution, GitHub Actions pass, independent GLB/PNG checks, human visual inspection and Factorio in-game behavior.
- Update docs with exact tested commit and logs. Do not claim success from source code alone.
