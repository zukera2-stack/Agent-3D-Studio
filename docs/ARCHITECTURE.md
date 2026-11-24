# A3DS Stage 01 architecture

## Components
- a3ds/math3d.py: frozen Vec3 and row-major affine Mat4.
- a3ds/mesh.py: triangle mesh, vertex normals, topology and signed-volume QA, negative-determinant transform repair.
- a3ds/surfaces.py: parameterized superelliptic X/Z cross-sections along +Y, sampled cubic Hermite interpolation, end caps.
- a3ds/project.py: versioned text-based parameter project; stored project is authoritative.
- a3ds/glb.py: glTF 2.0 single-mesh GLB writer; A3DS-subset GLB reader; no external libraries.
- a3ds/__main__.py: demo/build/inspect CLI with nonzero exit on QA failure.
- tests: positive and negative stdlib unittest checks.

## Geometry rules
X = across, +Y = front, Z = up; units are arbitrary Blender-compatible BU. Sections have y, center_z, half_width, half_height, exponent. Y must be strictly increasing, dimensions positive. Sampling is deterministic. Side facets and end caps wind outward. Closed manifoldness is checked by triangle-edge incidence and winding; signed oriented volume is positive for correctly oriented closed meshes.

A3DS -> glTF coordinates: (x,y,z) to (x,z,-y). Right-handed rotation, preserved triangle winding. A3DS GLB importer reverses this. GLB is a derived artifact; edit JSON source.

## Not in Stage 01
UVs/textures, multiple materials or scene nodes, smooth CAD BRep/NURBS, Boolean operations, distant triangle self-intersections, skeletal mechanisms, sketch fitting, render comparisons, or a finished Factorio model. Stage 02 adds own projections and raster; Stage 03 constrained sketch optimization; Stage 04 materials and assemblies.

## Evidence
Geometry tests and GLB rebuild are machine-checkable. Independent viewer rendering and game-native tests are separate gates. Check exact CI SHA before saying PASS.

## Stage 02: original cameras, raster and sheet export
- a3ds/camera.py: world-to-view basis and orthographic/perspective projection with near/far triangle clipping.
- a3ds/raster.py: filled triangle CPU Z-buffer, flat Lambert shading, separate color and coverage mask.
- a3ds/png.py: deterministic RGB8/grayscale8 PNG export with restricted internal reader.
- a3ds/blueprint.py: SVG grids computed from canonical camera and world origin, embedded real PNG; one-way generated drawing.
- a3ds/calibration.py: measured world-to-pixel scale+translation fit, RMS and inconsistency threshold. This does NOT reconstruct 3D from an artist sketch.
- a3ds/stage02_cli.py: five camera views, ten PNG, four SVG and machine-readable report.
- Stage 02 CI uses only stdlib in the application; Pillow is independently installed for test decoding in Actions.

No production-ready antialiasing, global illumination, textures, UV, contour optimization, editor interactions or Factorio sprite export exists yet.
