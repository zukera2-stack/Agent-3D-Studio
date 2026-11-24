---
name: a3ds-reference-to-model
description: Build and validate actual editable 3D game assets from calibrated views or concept art using the verified A3DS experimental workflows, with real renders, iterative correction and honest acceptance.
---

# A3DS reference-to-model

Read root AGENTS.md, docs/CURRENT_WORK.md, docs/REFERENCE_TO_MODEL_METHOD.md and the relevant QA record before execution. Preserve the active branch, owner constraints, original files and accepted assets. Stage 04B is frozen; this skill documents experimental modeling and QA, not authorization to integrate or start Stage 05.

## Execute
1. Identify deliverable, reference class, axes, known scale, source hash, license and target engine. Separate measured values from inferred details. Work in a fresh directory; check runtime/dependencies. Obtain the exact archived source scripts if reusing a historical experiment; verify hashes from the methodology. If missing, explicitly report blocker or implement a new isolated candidate, never claim a historical run.
2. Route: calibrated RGB/silhouette views -> visual hull (A); artistic collage or mechanical assembly -> parametric named components (B); combine only where supported. Never treat an uncalibrated illustration as exact orthographic geometry. For a blind benchmark, keep original mesh/materials out of the reconstruction path; known scale from original must be disclosed.
3. Build real geometry, keep editable parameters; export test GLB, render actual geometry at matching camera settings. For A use multi-angle masks, signed-distance intersection, active voxel pruning, marching cubes and visibility/normal weighted color; preserve real thin or detached parts. For B build a hull and individual functional details; use texture for painted stripes and preserve common pivot for movable layers. See method for exact locomotive art constraints.
4. Compare main and held-out views, classify residuals, correct shape/details/camera/material, rerender. When original 3D is available, compare in original coordinates with two-way closest-triangle distances, 3D overlay, heatmap and sections; no hidden ICP. Use independent final views; do not select on them. Use finite compute budget and report actual best result. Never fake a render or claim exact equivalence from silhouettes.
5. Validate topology/finite vertices/degeneracy, appropriate closure, material/UV presence, dimensions and triangle budget. Reopen exact exported GLB; log hashes and results. Do not claim untested PBR, self-intersection absence, native UI or in-game acceptance. For Factorio keep body/pantograph separate and defer sprite/game modifications until approved.
6. Deliver final inspected candidate only, actual comparison renders, source/parameters, GLB and QA log. Include limitations, measured errors and PASS/FAIL/NOT_RUN. Record results in docs with exact inputs, output hash, method, iterations and commands. Do not ask for routine iteration permission within authorized work; ask only for an essential missing dependency or out-of-scope authorization. No merge/release/game modifications by default.

## Evidence and thresholds
See docs/QA_BARRAMUNDI_RGB_RECONSTRUCTION.md (99.1778% fresh-angle IoU, ~0.69 mm average surface deviation, dense mesh) and docs/QA_LOCOMOTIVE_CONCEPT_MODEL.md (parametric 36640-triangle assembly, owner judged usable). These are benchmark observations, not universal acceptance thresholds. Define tolerances by project and scale. Do not deliver unapproved blockouts as finished work. A qualitative owner approval of the example does not prove exact fidelity or native game readiness.

## Reusable accepted V3 source
For locomotive-style mechanical models, read experiments/locomotive-v3/README.md and baseline/qa.json, inspect the archived build.py and verify.py, and use the separate rebuild wrapper in an isolated directory. Do not change accepted V3 inputs or replace exact original GLBs with differing builds. Preserve roof-mounted components on the actual supporting surface and validate normals, closure where applicable, stable bounds and named moving parts after smoothing. V3 is a visual benchmark, not a general threshold or in-game approval.

## Owner execution preference (2026-11-24)
Bulk 3D and sprite rendering must run in the assistant's local computational environment when available; GitHub Actions is too slow for this workflow. Use GitHub for persistent source and documentation and the Factorio repository's required official install ZIP packaging, not routine rendering. If local execution is unavailable, report the blocker rather than silently switching to CI rendering.
