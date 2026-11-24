# Agent 3D Studio — Stage 03 status, 2026-11-24

Repo: zukera2-stack/Agent-3D-Studio. Owner accepted independent Agent 3D Studio architecture.
- main bootstrap README HEAD acdeccc322e9db705bdde3edbbf507ca2b25f845 — do not modify.
- Stage 01 PR #1 DRAFT unmerged, branch feature/stage-01-geometry-kernel HEAD f5abc2d55c635d5d30277215f7337b5055530d7f.
- Stage 02 PR #2 DRAFT unmerged, branch feature/stage-02-own-camera-raster HEAD 378901c9cc8bb78958f8b25302fefd95cc836f2a. Verified 54 tests, native PNG/SVG and real five-view artifacts via GitHub Actions. No Blender runtime.
- Stage 03 PR #3 DRAFT unmerged, branch feature/stage-03-silhouette-fitting, stacked on Stage 02 branch and not main.
- Stage 03 source modules: fit_geometry.py, silhouette.py, optimizer.py, stage03_cli.py and optional maskprep.py; tests/test_stage03_fit.py and tests/test_stage03_cli.py.
- Tests are set up for controlled synthetic mask recovery and a held-out fourth rear view, plus conflict/invalid-input cases, stable output and native GLB.
- Optional external crop preprocessing with Pillow is not automatic detection or geometric calibration.
- Attempts to call local container.exec, python.exec, python_user_visible.exec returned ClientError; no in-chat local Python results are claimed.
- CI workflow runs Python 3.11/3.12 and uses Pillow for independent PNG decoding. Inspect and cite real run logs when completed. Do not claim a pass before reading logs.
- The synthetic fixture is NOT finished locomotive art, and no owner sketch has yet been calibrated and fitted. The Factorio repository and art are untouched.

Next: assess actual CI on the exact Stage 03 code SHA, fix any failures in Stage 03 branch, and update this document with exact evidence. Then attempt real-source multi-view masks with explicit calibration; do not mark visual reconstruction success without comparison.
