"""Model-derived SVG grid validation; coordinate consistency is measurable."""
from base64 import b64decode
import unittest
from xml.etree import ElementTree as ET

from a3ds.blueprint import svg_grid_sheet
from a3ds.camera import standard_views
from a3ds.png import decode_our_png
from a3ds.project import demo_project
from a3ds.raster import render_mesh


class LinkedSheetTests(unittest.TestCase):
    def setUp(self):
        self.mesh = demo_project().build()
        self.cameras = standard_views(160, 120)

    def test_four_orthographic_sheets_are_standalone_and_axis_calibrated(self):
        for name in ("side", "top", "front", "rear"):
            with self.subTest(name=name):
                camera = self.cameras[name]
                result = render_mesh(self.mesh, camera)
                svg = svg_grid_sheet(result, camera, name, grid_step=0.1)
                root = ET.fromstring(svg)
                self.assertTrue(root.tag.endswith("svg"))
                image = root.find("{http://www.w3.org/2000/svg}image")
                self.assertIsNotNone(image)
                encoded = image.attrib["href"].split(",", 1)[1]
                w, h, channels, pixels = decode_our_png(b64decode(encoded))
                self.assertEqual((w, h, channels), (160, 120, 3))
                self.assertEqual(pixels, bytes(result.pixels))
                lines = root.findall(".//{http://www.w3.org/2000/svg}line")
                self.assertGreater(len(lines), 10)
                self.assertIn("0.1 BU", svg)
                self.assertIn("major 1 BU", svg)

    def test_sheet_determinism(self):
        cam = self.cameras["side"]
        image = render_mesh(self.mesh, cam)
        self.assertEqual(
            svg_grid_sheet(image, cam, "side"),
            svg_grid_sheet(image, cam, "side")
        )

    def test_wrong_axis_and_perspective_rejected(self):
        image = render_mesh(self.mesh, self.cameras["side"])
        with self.assertRaises(ValueError):
            svg_grid_sheet(image, self.cameras["side"], "hero")
        with self.assertRaises(ValueError):
            svg_grid_sheet(image, self.cameras["hero"], "side")

    def test_invalid_grid_rejected(self):
        cam = self.cameras["side"]
        image = render_mesh(self.mesh, cam)
        for step in (0, -0.1, 0.3):
            with self.subTest(step=step), self.assertRaises(ValueError):
                svg_grid_sheet(image, cam, "side", grid_step=step)


if __name__ == "__main__":
    unittest.main()
