# Stage 01 acceptance gates

1. Python 3.11+ stdlib; no Blender or GUI runtime dependency.
2. Matrix/vector operations and normals tested.
3. Invalid sizes, unsorted sections and invalid sampling rejected.
4. Asymmetric body loft is closed, outward, oriented and has no degenerate triangles.
5. Negative tests exercise bad indices, missing faces, edge conflicts and nonmanifold geometry.
6. glTF2 GLB JSON+BIN chunks with POSITION, NORMAL and uint32 indices are emitted reproducibly.
7. Readback restores vertices in A3DS coordinates within float32 tolerance and preserves face indices.
8. Versioned text project loads and produces byte-identical GLB.
9. GitHub Actions 3.11/3.12 execute tests and produce downloadable test fixture artifacts.
10. Record actual CI results with exact commit. Do not equate CI success with appearance or in-game correctness.

NOT verified: general third-party GLB import, mesh self-intersections, UV, textures, drawing/rendering, image comparison or Factorio behavior.
Owner's locomotive sketch is a later integration fixture. Test body is not finished asset.
