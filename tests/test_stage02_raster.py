"""Pure-Python Z-buffer, clipping, silhouettes and PNG binary acceptance."""
import unittest

from a3ds.camera import Camera, standard_views
from a3ds.math3d import Vec3
from a3ds.mesh import Mesh
from a3ds.png import decode_our_png, encode_png
from a3ds.project import demo_project
from a3ds.raster import render_mesh, render_silhouette


class RasterTests(unittest.TestCase):
    def setUp(self):
        self.camera = Camera(
            81, 81, Vec3(0, -4, 0), Vec3(0, 0, 0),
            Vec3(0, 0, 1), near=1, far=20,
            vertical_span=2.0
        )
        near_pts = [
            Vec3(-0.8, 0, -0.8), Vec3(0.8, 0, -0.8), Vec3(0, 0, 0.8)
        ]
        far_pts = [
            Vec3(-0.8, 1, -0.8), Vec3(0.8, 1, -0.8), Vec3(0, 1, 0.8)
        ]
        self.mesh = Mesh(near_pts + far_pts, [(0, 1, 2), (3, 4, 5)])
        self.colors = [(240, 40, 30), (30, 55, 245)]

    def test_real_zbuffer_independent_of_face_order_orthographic(self):
        front_first = render_mesh(self.mesh, self.camera, face_colors=self.colors, shade=False)
        mesh_back_first = Mesh(self.mesh.vertices, list(reversed(self.mesh.triangles)))
        back_first = render_mesh(
            mesh_back_first, self.camera, face_colors=list(reversed(self.colors)), shade=False
        )
        self.assertEqual(front_first.pixel(40, 40), (240, 40, 30))
        self.assertEqual(front_first.pixels, back_first.pixels)
        self.assertGreater(front_first.covered, 200)

    def test_real_zbuffer_perspective(self):
        persp = Camera(
            81, 81, Vec3(0, -4, 0), Vec3(0, 0, 0),
            Vec3(0, 0, 1), projection="perspective",
            fov_y_degrees=60, near=1, far=20
        )
        result = render_mesh(self.mesh, persp, face_colors=self.colors, shade=False)
        self.assertEqual(result.pixel(40, 40), (240, 40, 30))

    def test_silhouette_coverage_matches_mask_bytes(self):
        mesh = demo_project().build()
        for name, camera in standard_views(224, 168).items():
            with self.subTest(view=name):
                result = render_silhouette(mesh, camera)
                self.assertGreater(result.covered, 50)
                self.assertLess(result.covered, result.width * result.height)
                self.assertIsNotNone(result.silhouette_bounds())
                self.assertEqual(sum(result.coverage), result.covered)

    def test_deterministic_raster_buffer(self):
        mesh = demo_project().build()
        camera = standard_views(124, 96)["side"]
        a = render_mesh(mesh, camera)
        b = render_mesh(mesh, camera)
        self.assertEqual(a.pixels, b.pixels)
        self.assertEqual(a.coverage, b.coverage)

    def test_mesh_behind_camera_is_empty(self):
        cam = Camera(51, 51, Vec3(0, 0, 0), Vec3(0, 1, 0),
                     Vec3(0, 0, 1), near=1, far=10)
        mesh = Mesh(
            [Vec3(-1, -2, -1), Vec3(1, -2, -1), Vec3(0, -2, 1)],
            [(0, 1, 2)]
        )
        result = render_mesh(mesh, cam)
        self.assertEqual(result.covered, 0)
        self.assertIsNone(result.silhouette_bounds())

    def test_partial_near_plane_not_discarded(self):
        cam = Camera(91, 91, Vec3(0, 0, 0), Vec3(0, 1, 0),
                     Vec3(0, 0, 1), projection="perspective",
                     fov_y_degrees=70, near=1, far=10)
        mesh = Mesh(
            [Vec3(-0.6, 0.5, -0.5), Vec3(0.6, 2, -0.5), Vec3(0, 2, 0.6)],
            [(0, 1, 2)]
        )
        self.assertGreater(render_mesh(mesh, cam).covered, 1)

    def test_invalid_color_rejected(self):
        with self.assertRaises(ValueError):
            render_mesh(self.mesh, self.camera, base_color=(300, 0, 0))
        with self.assertRaises(ValueError):
            render_mesh(self.mesh, self.camera, face_colors=[(0, 0, 0)])

    def test_png_pixels_and_crc(self):
        rgb = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255])
        png = encode_png(2, 2, rgb)
        w, h, channel, pixels = decode_our_png(png)
        self.assertEqual((w, h, channel, pixels), (2, 2, 3, rgb))
        self.assertEqual(png, encode_png(2, 2, rgb))
        broken = bytearray(png)
        broken[30] ^= 1
        with self.assertRaises(ValueError):
            decode_our_png(bytes(broken))

    def test_png_grayscale(self):
        data = bytes([0, 128, 255])
        self.assertEqual(decode_our_png(encode_png(3, 1, data, channels=1))[-1], data)

    def test_png_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            encode_png(2, 2, b"not an RGB buffer")
        with self.assertRaises(ValueError):
            decode_our_png(b"fake-image")


if __name__ == "__main__":
    unittest.main()
