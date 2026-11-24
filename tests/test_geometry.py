"""Geometry kernel acceptance gates (stdlib unittest, no GUI)."""
import math
import unittest

from a3ds import CrossSection, Mat4, Mesh, Vec3, loft_sections
from a3ds.project import demo_project


class VectorTests(unittest.TestCase):
    def test_cross_product(self):
        self.assertEqual(Vec3(1, 0, 0).cross(Vec3(0, 1, 0)), Vec3(0, 0, 1))

    def test_normal(self):
        self.assertAlmostEqual(Vec3(3, 4, 0).normalized().length(), 1)

    def test_zero_vector_rejected(self):
        with self.assertRaises(ValueError):
            Vec3(0, 0, 0).normalized()

    def test_matrix_composition(self):
        m = Mat4.translation(1, 2, 3) @ Mat4.rotation_z(math.pi / 2)
        p = m.point(Vec3(1, 0, 0))
        self.assertAlmostEqual(p.x, 1, places=7)
        self.assertAlmostEqual(p.y, 3, places=7)
        self.assertAlmostEqual(p.z, 3, places=7)

    def test_negative_scale_preserves_orientation(self):
        mesh = demo_project().build()
        mirrored = mesh.transformed(Mat4.scale(-1, 1, 1))
        report = mirrored.validate(require_closed=True, require_outward=True)
        self.assertTrue(report.ok, report.errors)

    def test_singular_scale_rejected(self):
        with self.assertRaises(ValueError):
            demo_project().build().transformed(Mat4.scale(1, 0, 1))


class SurfaceTests(unittest.TestCase):
    def test_demo_is_closed_outward_and_asymmetric(self):
        mesh = demo_project().build()
        report = mesh.validate(require_closed=True, require_outward=True)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.boundary_edges, 0)
        self.assertEqual(report.nonmanifold_edges, 0)
        self.assertEqual(report.degenerate_triangles, 0)
        self.assertGreater(report.signed_volume, 0)
        self.assertAlmostEqual(report.bounds_min[1], -3.60)
        self.assertAlmostEqual(report.bounds_max[1], 3.60)

    def test_shape_counts(self):
        mesh = loft_sections(
            [CrossSection(0, 1, 1, 1), CrossSection(2, 1, 0.3, 0.4)],
            sides=16, steps_per_span=3
        )
        # 4 longitudinal rings + 2 cap centers.
        self.assertEqual(len(mesh.vertices), 4 * 16 + 2)
        self.assertEqual(len(mesh.triangles), 2 * 16 * 4)
        self.assertTrue(mesh.validate(require_closed=True, require_outward=True).ok)

    def test_unsorted_sections_rejected(self):
        with self.assertRaises(ValueError):
            loft_sections([CrossSection(1, 0, 1, 1), CrossSection(0, 0, 1, 1)])

    def test_bad_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            CrossSection(0, 1, 0, 1)

    def test_too_few_sides_rejected(self):
        with self.assertRaises(ValueError):
            loft_sections([CrossSection(0, 0, 1, 1), CrossSection(1, 0, 1, 1)], sides=5)

    def test_determinism(self):
        self.assertEqual(demo_project().build(), demo_project().build())


class TopologyNegativeTests(unittest.TestCase):
    def setUp(self):
        self.tetra = Mesh(
            [Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1)],
            [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)], "Tetra"
        )

    def test_valid_tetra(self):
        self.assertTrue(self.tetra.validate(require_closed=True, require_outward=True).ok)

    def test_boundary_detected(self):
        m = Mesh(self.tetra.vertices, self.tetra.triangles[:-1])
        report = m.validate(require_closed=True)
        self.assertFalse(report.ok)
        self.assertGreater(report.boundary_edges, 0)

    def test_winding_conflict_detected(self):
        t = list(self.tetra.triangles)
        a, b, c = t[0]
        t[0] = (a, c, b)
        report = Mesh(self.tetra.vertices, t).validate()
        self.assertFalse(report.ok)
        self.assertGreater(report.winding_conflicts, 0)

    def test_nonmanifold_detected(self):
        t = list(self.tetra.triangles) + [(0, 1, 2)]
        report = Mesh(self.tetra.vertices, t).validate()
        self.assertFalse(report.ok)
        self.assertGreater(report.nonmanifold_edges, 0)

    def test_degenerate_detected(self):
        t = list(self.tetra.triangles) + [(0, 0, 1)]
        report = Mesh(self.tetra.vertices, t).validate()
        self.assertFalse(report.ok)
        self.assertEqual(report.degenerate_triangles, 1)

    def test_invalid_index_detected(self):
        m = Mesh(self.tetra.vertices, [(0, 1, 9)])
        self.assertFalse(m.validate().ok)


if __name__ == "__main__":
    unittest.main()
