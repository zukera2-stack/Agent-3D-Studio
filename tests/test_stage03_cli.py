"""End-to-end Stage 03 CLI fixture and mask adapter tests."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from a3ds.maskprep import prepare
from a3ds.optimizer import SilhouetteReference
from a3ds.silhouette import BinaryMask
from a3ds.stage03_cli import main


class Stage03CLITests(unittest.TestCase):
    def test_fixture_outputs_calibrated_not_empty_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertEqual(main([
                "fixture", "--out-dir", str(out), "--width", "64", "--height", "48"
            ]), 0)
            for name in ("side", "top", "front", "rear"):
                mask = BinaryMask.read_png(out / f"{name}_reference.png")
                self.assertGreater(mask.area, 10)
                self.assertLess(mask.area, 64 * 48)
            self.assertIn("SYNTHETIC", (out / "fixture.json").read_text())

    def test_external_mask_adapter_with_real_png_if_pillow_installed(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow only required for external-image adapter")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sketch.png"
            im = Image.new("RGB", (40, 30), (255, 255, 255))
            for x in range(10, 30):
                for y in range(8, 23):
                    im.putpixel((x, y), (0, 0, 0))
            im.save(source)
            mask = prepare(source, crop=(0, 0, 40, 30), width=40, height=30,
                           foreground="dark", threshold=128)
            self.assertEqual(mask.area, 20 * 15)
            with self.assertRaisesRegex(ValueError, "aspect ratios differ"):
                prepare(source, crop=(0, 0, 30, 30), width=40, height=30,
                        foreground="dark", threshold=128)
            with self.assertRaises(ValueError):
                prepare(source, crop=(0, 0, 99, 30), width=40, height=30,
                        foreground="dark", threshold=128)


if __name__ == "__main__":
    unittest.main()
