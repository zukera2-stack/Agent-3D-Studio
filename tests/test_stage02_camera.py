"""Analytical camera tests: coordinate conventions, clipping and known pixel positions."""
from math import isclose
import unittest

from a3ds.camera import Camera, standard_views
from a3ds.math3d import Vec3


class CameraTests(unittest.TestCase):
    def test_orthogonal_orthonormal_basis(self):
        cam = standard_views(400, 300)["hero"]
        right, up, forward = cam.basis()
        for vector in (right, up, forward):
            self.assertAlmostEqual(vector.length(), 1.0, places=10)
        self.assertAlmostEqual(right.dot(up), 0, places=10)
        self.assertAlmostEqual(up.dot(forward), 0, places=10)
        self.assertAlmostEqual(forward.dot(right), 0, places=10)
        self.assertAlmostEqual(right.cross(up).dot(forward), -1.0, places=10)

    def test_top_blender_xy(self):
        cam = standard_views(400, 300)["top"]
        origin = cam.project(Vec3(0, 0, 0))
        assert origin is not None
        self.assertAlmostEqual(origin.x, 200)
        self.assertAlmostEqual(origin.y, 150)
        x = cam.project(Vec3(1, 0, 0))
        y = cam.project(Vec3(0, 1, 0))
        assert x is not None and y is not None
        self.assertAlmostEqual(x.x - origin.x, cam.pixels_per_unit)
        self.assertAlmostEqual(y.y - origin.y, -cam.pixels_per_unit)

    def test_side_blender_yz(self):
        cam = standard_views(400, 300)["side"]
        origin = cam.project(Vec3(0, 0, 0))
        x = cam.project(Vec3(0, 1, 0))
        z = cam.project(Vec3(0, 0, 1))
        assert origin is not None and x is not None and z is not None
        self.assertAlmostEqual(x.x - origin.x, cam.pixels_per_unit)
        self.assertAlmostEqual(z.y - origin.y, -cam.pixels_per_unit)

    def test_front_mirrors_world_x(self):
        cam = standard_views(400, 300)["front"]
        origin = cam.project(Vec3(0, 0, 0))
        positive_x = cam.project(Vec3(1, 0, 0))
        assert origin is not None and positive_x is not None
        self.assertAlmostEqual(positive_x.x - origin.x, -cam.pixels_per_unit)

    def test_real_perspective_half_size_at_twice_depth(self):
        cam = Camera(
            400, 300, Vec3(0, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1),
            projection="perspective", fov_y_degrees=60, near=0.1, far=100
        )
        closer = cam.project(Vec3(1, 2, 0))
        farther = cam.project(Vec3(1, 4, 0))
        assert closer is not None and farther is not None
        self.assertAlmostEqual(closer.x - 200, 2 * (farther.x - 200), places=7)

    def test_near_and_far_clip_projection(self):
        cam = Camera(100, 80, Vec3(0, 0, 0), Vec3(0, 1, 0),
                     Vec3(0, 0, 1), near=1, far=3)
        self.assertIsNone(cam.project(Vec3(0, 0.5, 0)))
        self.assertIsNone(cam.project(Vec3(0, 4, 0)))
        self.assertIsNotNone(cam.project(Vec3(0, 2, 0)))

    def test_clip_partly_near_triangle(self):
        cam = Camera(100, 100, Vec3(0, 0, 0), Vec3(0, 1, 0),
                     Vec3(0, 0, 1), projection="perspective",
                     near=1, far=10)
        clipped = cam.clip_triangle(
            Vec3(-0.8, 0.5, -0.5), Vec3(0.8, 2, -0.5), Vec3(0, 2, 0.8)
        )
        self.assertEqual(len(clipped), 2)
        for triangle in clipped:
            for p in triangle:
                self.assertGreaterEqual(p.depth, cam.near)
                self.assertLessEqual(p.depth, cam.far)

    def test_clip_fully_behind_camera(self):
        cam = Camera(100, 100, Vec3(0, 0, 0), Vec3(0, 1, 0),
                     Vec3(0, 0, 1), near=0.1, far=5)
        self.assertEqual(cam.clip_triangle(
            Vec3(-1, -2, -1), Vec3(1, -2, -1), Vec3(0, -2, 1)), [])

    def test_invalid_camera_orientation_rejected(self):
        with self.assertRaises(ValueError):
            Camera(200, 100, Vec3(0, 0, 0), Vec3(0, 0, 0), Vec3(0, 0, 1))
        with self.assertRaises(ValueError):
            Camera(200, 100, Vec3(0, 0, 0), Vec3(0, 1, 0), Vec3(0, 1, 0))

    def test_invalid_camera_parameters_rejected(self):
        for kwargs in ({"near": 0}, {"near": 10, "far": 3},
                       {"projection": "fisheye"}, {"fov_y_degrees": 180},
                       {"vertical_span": -3}, {"width": 0}):
            args = dict(width=200, height=100,
                        position=Vec3(0, 0, 0), target=Vec3(0, 1, 0),
                        up_hint=Vec3(0, 0, 1))
            args.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Camera(**args)


if __name__ == "__main__":
    unittest.main()
