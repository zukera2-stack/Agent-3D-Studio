"""Validate actual GLB binary roundtrip, corruption rejection and project files."""
from pathlib import Path
import json
import struct
import tempfile
import unittest

from a3ds.glb import decode_glb, encode_glb, read_glb, write_glb
from a3ds.project import SurfaceProject, demo_project


class GLBTests(unittest.TestCase):
    def setUp(self):
        self.model = demo_project().build()

    def test_binary_header_and_roundtrip(self):
        blob = encode_glb(self.model)
        magic, version, total = struct.unpack_from("<4sII", blob, 0)
        self.assertEqual((magic, version, total), (b"glTF", 2, len(blob)))
        reimported = decode_glb(blob)
        self.assertEqual(reimported.name, self.model.name)
        self.assertEqual(reimported.triangles, self.model.triangles)
        self.assertEqual(len(reimported.vertices), len(self.model.vertices))
        for a, b in zip(reimported.vertices, self.model.vertices):
            self.assertLess((a - b).length(), 1e-6)
        self.assertTrue(reimported.validate(require_closed=True, require_outward=True).ok)

    def test_deterministic_bytes(self):
        self.assertEqual(encode_glb(self.model), encode_glb(self.model))

    def test_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "body.glb"
            write_glb(self.model, output)
            self.assertEqual(len(read_glb(output).triangles), len(self.model.triangles))

    def test_bad_magic_rejected(self):
        with self.assertRaises(ValueError):
            decode_glb(b"invalid")

    def test_bad_length_rejected(self):
        blob = encode_glb(self.model)
        with self.assertRaises(ValueError):
            decode_glb(blob[:-1])

    def test_project_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "test.a3ds.json"
            initial = demo_project()
            initial.save(target)
            loaded = SurfaceProject.load(target)
            self.assertEqual(initial.as_dict(), loaded.as_dict())
            self.assertEqual(initial.build(), loaded.build())

    def test_wrong_project_version_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "invalid.json"
            target.write_text(json.dumps({"format": "a3ds.surface-project/99"}))
            with self.assertRaises(ValueError):
                SurfaceProject.load(target)


if __name__ == "__main__":
    unittest.main()
