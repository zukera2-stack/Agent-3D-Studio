# Stage 04A — native interactive parameter editor
Run from repository root: `python -m a3ds.editor` (Python 3.11+ with Tk installed; Linux may need python3-tk).

The GUI uses Tk only for controls and display. Native A3DS geometry, camera, CPU raster and GLB export remain authoritative. Select a longitudinal section, enter Y, center Z, half width, half height and superellipse exponent, then Apply section. Invalid edits must leave original geometry unchanged. Orbit the hero view with left drag; wheel zooms. Front/side/top/rear use existing exact-axis cameras. Save editable JSON, export GLB, undo applied changes. Demo geometry is a technical fixture, not approved Factorio art.

Scope: single loft, numeric edits, one viewport. No direct vertex picking, arbitrary mesh import, simultaneous views, live sketch calibration, GPU acceleration or general CAD. Fixed camera center assumes the Stage 01 fixture; imported projects may require different framing. No changes to Factorio or main.

Acceptance: run all unittest cases; independently launch Tk on Windows, orbit and zoom, switch all views, edit and undo, reject invalid Y order, save/reopen project and export/inspect GLB. GUI behavior is NOT_RUN until actual interactive verification. CPU performance is not measured. No merge or release authorized.
