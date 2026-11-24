# Stage 02 acceptance report

Goal: own original cameras and deterministic native 3D projections, independent of Blender.

## Confirmed with actual GitHub Actions
- Test source SHA: c9523add915d2037a3932d0a48b0642380981caa.
- Actions run: https://github.com/zukera2-stack/Agent-3D-Studio/actions/runs/45438225604; Python 3.11 and 3.12 jobs PASS.
- 54 positive/negative unittest cases per version: vector and geometry/GLB regression, camera bases, perspective scaling, near/far clipping, CPU Z-buffer occlusion, PNG CRC, camera-axis SVG sheets, and landmark calibration with inconsistency warnings.
- 360x270 output: four ortho views + one perspective, five masks, four linked SVG with 0.1 BU grids and an encoded source image; 15 generated files byte-for-byte equal across two runs.
- Independent Pillow 11.3 test verified 10 PNG files; 4 SVG embedded PNG images decoded and matched exported rendered pixels; SVG XML parsed.
- Machine report coverage: side 24043, top 12800, front 21142, rear 21142, hero 4485.
- Download artifacts with source GLB, JSON parameters, images, SVG and logs from Actions run link.

## Measured conventions
Right-handed Blender-compatible world coordinates: X width, +Y forward, Z height. The camera view origin is upper-left, world +Z maps screen upward in side/front/rear views. Perspective scales as inverse depth. Actual world 0,0,0 anchors every SVG grid.

## NOT DONE
- In-chat local Python execution (runtime tools returned ClientError). GitHub Actions tests are server-side.
- Independent human visual inspection of PNG drawings, calibrated comparison with owner sketch, shape optimization, texture/UV/PBR, self-intersection checks, real Factorio screenshots or gameplay.
- Editing SVG to drive model parameters; SVG is one-way regenerated output.

This milestone does not certify user-accepted model appearance, only the listed machine-verified projection functionality.
