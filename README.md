# Agent 3D Studio (A3DS)

Original 3D geometry and reconstruction tools for an AI agent, written in Python 3.11+ and designed to run without Blender. Stages are developed in separate nonmerged Draft PRs.

- Stage 01: parametric surface mesh, topology, GLB2 export.
- Stage 02: orthographic/perspective cameras, native CPU raster, Z-buffer, PNG, SVG coordinate grids.
- Stage 03: measured 2D silhouette fitting via bounded modifications to the source project, multiple camera views, IoU loss, residual overlays and warnings.

Important: this is an early experimental geometry tool. Stage 03 does NOT autonomously understand a complex colored sketch or guarantee unique 3D reconstruction.

## Run original kernel/tests

    python -m unittest discover -s tests -v

## Stage 03 self-contained synthetic test

    python -m a3ds.stage03_cli fixture --out-dir refs --width 112 --height 84
    python -m a3ds demo --out base.glb --project base.a3ds.json
    python -m a3ds.stage03_cli fit --project base.a3ds.json --ref side=refs/side_reference.png --ref top=refs/top_reference.png --ref front=refs/front_reference.png --out-dir fitted --width 112 --height 84 --active width_scale height_scale nose_extension --min-iou 0.82

The fitter receives only reference masks (NOT the synthetic truth parameters). The rear mask is withheld for an independent generalization check. Output: fitted.a3ds.json, fitted.glb, shaded PNG, fitted masks, red/blue difference PNG and fit_report.json with IoU per view.

## Real source drawing workflow (MANUAL calibration)
1. Select actual side/top/front orthographic views, calibrate pixel-per-BU, screen direction and registration. A perspective illustration is not automatically recognized as a true orthographic view.
2. Optionally install Pillow ONLY for reading arbitrary external JPEG/PNG files: python -m pip install Pillow
3. Produce a binary silhouette from an explicitly selected crop, e.g.:

    python -m a3ds.maskprep --input sketch.png --crop 10,40,800,600 --width 160 --height 120 --foreground dark --threshold 128 --out side_reference.png

4. Confirm reference image registration separately; cropping and resizing do not establish camera calibration.
5. Run fit with calibrated masks and measure each view's residual. High residual cannot alone establish whether the drawing is inconsistent, the camera is wrong or this simple shape family is inadequate.
6. Inspect GLB and final render against real sketch. Do not approve a model solely from IoU.

See AGENTS.md, docs/STAGE03_ACCEPTANCE.md, docs/CURRENT_WORK.md. No Factorio mod changes and no main merges without owner approval.

## Quick start for another AI agent — Stage 04B

The default `main` branch is deliberately a bootstrap README only. The complete current tool source is in `feature/stage-04b-linked-views`. Clone that branch into a fresh writable directory:

```sh
git clone --branch feature/stage-04b-linked-views --single-branch https://github.com/zukera2-stack/Agent-3D-Studio.git
cd Agent-3D-Studio
python --version
python -m unittest discover -s tests -v
python -m a3ds demo --out smoke.glb --project smoke.a3ds.json
python -m a3ds inspect --file smoke.glb
python -m a3ds.stage02_cli --glb smoke.glb --out-dir smoke_views --width 360 --height 270 --grid 0.1
```

Use Python 3.11+ (historical CI verified 3.11 and 3.12). Optional Pillow enables external image import and additional QA; install with `python -m pip install Pillow==11.3.0` if needed. For the linked-view GUI, verify Tk with `python -m tkinter`, then run `python -m a3ds.linked_editor`. A headless agent can use the CLI and Python modules without the GUI. On Linux Tk and a display or Xvfb must be available for GUI execution. See [Stage 04B](docs/STAGE04B_LINKED_VIEWS.md).

**This is source code, not an installed MCP server or remote execution service.** The agent needs its own working Python execution environment, repository access and permission to write outputs. The core is an experimental parametric loft editor with native rendering and calibrated silhouette fitting, not a general mesh editor. For complex assets consult [the modeling method](docs/REFERENCE_TO_MODEL_METHOD.md), [the agent skill](.agents/skills/a3ds-reference-to-model/SKILL.md), and [the actual archived locomotive V3 generator](experiments/locomotive-v3/README.md), which has separate dependencies and is not integrated into the core.

If execution tools or repository access are absent, identify the exact missing capability; do not claim a successful build from reading the code alone. Perform actual smoke tests locally; no automatic GitHub rendering. Stage 04B remains frozen. No main changes, merges, new stage, or releases without owner approval.
