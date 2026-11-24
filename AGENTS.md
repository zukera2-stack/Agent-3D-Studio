# A3DS: instructions for agents

- Owner-approved target: independent Python geometry kernel, not a Blender wrapper.
- Do not change main, merge PR, publish a release, or change other repositories without explicit owner permission. New empty repo was initialized once with minimal README.
- Stage 01: Python standard library only; no network calls, third-party engine code or generated model weights.
- Read README.md, docs/ARCHITECTURE.md, docs/STAGE01_ACCEPTANCE.md, docs/CURRENT_WORK.md before work.
- Internal world axes: right-handed X across, +Y front, Z up, 1 unit = BU (not assumed metre or Factorio tile).
- Parameter JSON is the editable source; GLB is derived. glTF output rotates (x,y,z) -> (x,z,-y) for glTF standard Y-up and -Z forward.
- A3DS Stage 01 GLB reader supports ONLY its own subset. Reject unsupported data rather than claiming universal compatibility.
- No user-approved locomotive yet. Never deliver a draft/blockout model as a finished asset.
- Separate static/code checks, real CI results, binary roundtrip, independent viewer QA, sketch similarity, and game-native tests. Never infer one from another.
- Test bad faces, degenerates, winding, nonmanifold geometry, corrupted GLB and deterministic regeneration.
- When material work changes, update docs/CURRENT_WORK.md and record the exact checked CI run.

## Stage 02 agent contract (2026-11-24)
- Stage 02 lives on feature/stage-02-own-camera-raster, stacked on the unmerged Stage 01 branch. Do NOT merge either PR without owner authorization.
- The native Camera, raster, png and blueprint files must remain Python standard-library only; external Pillow is permitted in CI for independent decoding, never as mandatory runtime.
- See docs/CAMERA_COORDINATES.md for screen handedness, world-BU scale and near/far clipping.
- SVG output is a one-way reproducible model-derived sheet; editing SVG does NOT modify A3DS geometry.
- Calibration is from explicit owner-provided image landmarks; RMS must be recorded. Do not infer hidden geometry or silently claim the perspective concept art is a calibrated orthographic drawing.
- Distinguish local Python tests, GitHub Actions, independently decoded PNG, human viewer inspection, sketch similarity and Factorio gameplay.
