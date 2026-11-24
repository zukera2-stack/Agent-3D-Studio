"""Measured landmark registration and meaningful conflict detection."""
import unittest

from a3ds.calibration import Landmark, fit_landmarks


class CalibrationTests(unittest.TestCase):
    def test_known_isotropic_transform_exact(self):
        # U pixel-right and V pixel-up, 20 pixels per Blender unit.
        marks = [
            Landmark(-1, -1, 180, 90),
            Landmark(1, -1, 220, 90),
            Landmark(-1, 1, 180, 50),
            Landmark(1, 1, 220, 50),
        ]
        calibration = fit_landmarks(marks, max_rms_pixels=0.000001)
        self.assertAlmostEqual(calibration.pixels_per_bu, 20)
        self.assertAlmostEqual(calibration.origin_x, 200)
        self.assertAlmostEqual(calibration.origin_y, 70)
        self.assertAlmostEqual(calibration.rms_pixels, 0)
        self.assertEqual(calibration.world_to_pixel(0.5, 0.5), (210, 60))
        self.assertEqual(calibration.pixel_to_world(210, 60), (0.5, 0.5))

    def test_bad_source_markers_report_error(self):
        marks = [
            Landmark(-1, 0, 180, 90),
            Landmark(1, 0, 220, 90),
            Landmark(0, 1, 200, 10),  # Last anchor contradicts other two
        ]
        with self.assertRaisesRegex(ValueError, "Calibration inconsistent"):
            fit_landmarks(marks, max_rms_pixels=2.0)
        measurement = fit_landmarks(marks)
        self.assertGreater(measurement.rms_pixels, 2)

    def test_degenerate_registration_fails(self):
        with self.assertRaises(ValueError):
            fit_landmarks([Landmark(0, 0, 1, 2)])
        with self.assertRaises(ValueError):
            fit_landmarks([Landmark(1, 1, 1, 2), Landmark(1, 1, 5, 4)])

    def test_inverted_axis_rejected(self):
        with self.assertRaises(ValueError):
            fit_landmarks([
                Landmark(-1, 0, 120, 20),
                Landmark(1, 0, 80, 20),
            ])

    def test_negative_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            fit_landmarks([
                Landmark(-1, 0, 80, 20),
                Landmark(1, 0, 120, 20),
            ], max_rms_pixels=-1)


if __name__ == "__main__":
    unittest.main()
