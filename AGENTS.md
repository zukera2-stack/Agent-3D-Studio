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
