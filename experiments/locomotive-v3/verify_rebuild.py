"""Run the archived geometry QA without requiring the historical comparison images."""
from pathlib import Path
import json
import hashlib

root = Path(__file__).resolve().parent
script = root / "loco_v3" / "verify.py"
source = script.read_text(encoding="utf-8")
head, marker, _ = source.partition("# before / after sheet")
assert marker, "Unexpected archived verifier"
exec(compile(head, str(script), "exec"), {"__file__": str(script)})
baseline = json.loads((root / "baseline" / "qa.json").read_text())
actual = json.loads((root / "loco_v3" / "qa.json").read_text())
for name in ("Locomotive_v3.glb", "Locomotive_v3_body.glb", "Locomotive_v3_pantograph.glb"):
    for key in ("meshes", "triangles", "degenerate"):
        assert actual[name][key] == baseline[name][key], (name, key)
assert actual["hull_watertight"] and actual["hull_winding_consistent"]
assert actual["texture"] == baseline["texture"]
for name in ("hero_pixels", "side_pixels", "top_pixels", "front_pixels", "rear_pixels"):
    assert actual[name] == baseline[name], name
results = {}
for row in (root / "accepted-assets.sha256").read_text().splitlines():
    expected, name = row.split("  ", 1)
    digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
    results[name] = {"expected": expected, "actual": digest, "identical": expected == digest}
(root / "rebuild_hashes.json").write_text(json.dumps(results, indent=2) + "\n")
print("V3 structural checks PASS; exact bytes:", all(v["identical"] for v in results.values()))
