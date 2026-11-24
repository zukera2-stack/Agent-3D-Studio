# Stage 03 — bounded silhouette fitting and acceptance contract

## Required machine checks
1. Every target is an explicitly calibrated orthographic black/white silhouette. Reject wrong resolution, empty masks, invalid camera and perspective substituted for orthographic.
2. Pixel overlap is measured by intersection over union (IoU), false-positive and false-negative counts. Differences in PNG are red (model excess) and blue (target missing).
3. The source is an original versioned parameter JSON. Vary only bounded dimensions: body width, body height, nose longitudinal extension, nose-tip width, rear-tip width.
4. Every candidate rebuilds a new watertight mesh (positive outward volume, valid normals, no observed bad triangle indices or edge conflicts). No free placement of individual vertices.
5. Optimizer records starting and final loss per view, parameter values, evaluation budget, accepted moves and discrete sampled sensitivity.
6. All supplied views individually need IoU >= acceptance threshold. Do not hide an incorrect view behind the weighted mean.
7. Exact-camera conflicting silhouettes throw ReferenceConflictError before any search. High residual among different cameras means RESIDUAL_TOO_HIGH_OR_CONFLICT, NOT proof the drawing is inconsistent (restricted model family or bad calibration is possible).
8. Synthetic fixture uses known source deformation. The fitter receives mask images only, not truth parameters. It must reduce measured loss and produce valid GLB + editable parameter JSON.
9. Hold rear view OUT of the fitting references and test the resulting GLB on this withheld view. Do not claim general reconstruction from this synthetic control experiment.
10. Python 3.11 and 3.12 GitHub Actions verify positive/negative tests, deterministic second fit, independent PNG decoding with Pillow (QA only) and real execution logs at exact SHA. Local Python tests are a separate evidence gate.

## Real sketch limitations
- A single drawing does not determine its hidden 3D details; different bodies can share projections.
- The current adapter requires an explicitly chosen crop and foreground threshold, with optional Pillow for arbitrary PNG/JPEG ingestion. It is NOT an AI vision-based auto segmenter.
- A crop or stretch does not equal a calibrated projection. Confirm image pixel scale, axes, origin and landmarks separately before comparing to any project sketch.
- User's multi-view perspective sketch may have mutually inconsistent outlines. High residuals are warnings; do not modify source artwork or invent missing geometry to force zero error.
- Technical mesh validation is not a guarantee of no self-intersections or faithful finished game art.
- Stage 03 does not include production CAD details, UV/PBR, an external model viewer, Factorio sprite render or game-native QA.

## Completion rule
Stage 03 is technically verified when complete CI logs show successful unit tests, demonstrable fit improvement, held-out-view success, byte-identical repeatability, and independent PNG/GLB checks. Aesthetic acceptance against actual locomotive sketch is a separate later task.
