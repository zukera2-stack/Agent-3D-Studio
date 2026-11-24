"""Real Stage 03 regression tests: measured improvement, topology, masks, conflicts."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from a3ds.camera import standard_views
from a3ds.fit_geometry import PARAM_BOUNDS, ShapeParams, alter_project
from a3ds.optimizer import (
    ReferenceConflictError, SilhouetteReference, fit, measure,
)
from a3ds.png import decode_our_png
from a3ds.project import demo_project, SurfaceProject
from a3ds.raster import render_silhouette
from a3ds.silhouette import (
    BinaryMask, compare_masks, difference_rgb, write_difference_png
)


def _references(width: int = 112, height: int = 84):
    project = demo_project()
    truth = ShapeParams(width_scale=1.21, height_scale=1.13,
                        nose_extension=0.39)
    mesh = alter_project(project, truth).build()
    cams = standard_views(width, height)
    refs = [
        SilhouetteReference(
            name, cams[name],
            BinaryMask.from_render(render_silhouette(mesh, cams[name]))
        )
        for name in ("side", "top", "front")
    ]
    return project, truth, refs


class MaskTests(unittest.TestCase):
    def test_known_iou_and_false_pos_negative(self):
        predicted = BinaryMask(3, 2, bytes([1, 1, 0, 0, 0, 0]))
        target = BinaryMask(3, 2, bytes([1, 0, 1, 0, 0, 0]))
        metric = compare_masks(predicted, target)
        self.assertEqual(metric.intersection, 1)
        self.assertEqual(metric.union, 3)
        self.assertEqual(metric.false_positive, 1)
        self.assertEqual(metric.false_negative, 1)
        self.assertAlmostEqual(metric.iou, 1 / 3)
        self.assertEqual(
            difference_rgb(predicted, target),
            bytes([
                204, 213, 218, 236, 66, 77, 65, 133, 237,
                23, 32, 44, 23, 32, 44, 23, 32, 44
            ])
        )

    def test_empty_target_rejected(self):
        with self.assertRaises(ValueError):
            compare_masks(BinaryMask(2, 2, b"\x00" * 4), BinaryMask(2, 2, b"\x00" * 4))

    def test_bad_target_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            compare_masks(BinaryMask(2, 2, b"\x01" * 4), BinaryMask(3, 2, b"\x01" * 6))

    def test_nonbinary_rejected(self):
        with self.assertRaises(ValueError):
            BinaryMask(2, 2, bytes([0, 1, 255, 0]))

    def test_mask_roundtrip_and_difference_png(self):
        mask = BinaryMask(3, 2, bytes([0, 1, 0, 1, 1, 0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mask.png"
            mask.save_png(path)
            self.assertEqual(BinaryMask.read_png(path), mask)
            difference = Path(tmp) / "diff.png"
            write_difference_png(difference, mask, mask)
            w, h, channels, _ = decode_our_png(difference.read_bytes())
            self.assertEqual((w, h, channels), (3, 2, 3))


class GeometryTransformTests(unittest.TestCase):
    def test_default_is_exact_geometry(self):
        project = demo_project()
        p = alter_project(project, ShapeParams())
        self.assertEqual(p.sections, project.sections)
        self.assertEqual(p.build().vertices, project.build().vertices)

    def test_parameters_keep_mesh_valid(self):
        project = demo_project()
        altered = alter_project(project, ShapeParams(
            width_scale=1.36, height_scale=0.89, nose_extension=0.67,
            nose_tip_scale=1.32, rear_tip_scale=0.72
        ))
        qa = altered.build().validate(require_closed=True, require_outward=True)
        self.assertTrue(qa.ok, qa.errors)
        self.assertGreater(altered.sections[-1].y, project.sections[-1].y)
        self.assertLess(altered.sections[0].half_width, project.sections[0].half_width)

    def test_unknown_parameters_and_bounds_rejected(self):
        with self.assertRaises(ValueError):
            ShapeParams(width_scale=2)
        with self.assertRaises(ValueError):
            ShapeParams(nose_extension=-2)
        with self.assertRaises(ValueError):
            ShapeParams().modified("unknown", 2)


class OptimizerTests(unittest.TestCase):
    def test_true_parameters_have_zero_synthetic_loss(self):
        project, truth, refs = _references(96, 72)
        loss, metrics = measure(project, truth, refs)
        self.assertAlmostEqual(loss, 0, places=10)
        self.assertTrue(all(abs(m.iou - 1.0) < 1e-10 for m in metrics.values()))

    def test_multiview_fitting_reduces_error_and_preserves_mesh(self):
        project, truth, refs = _references(112, 84)
        result = fit(project, refs, max_passes=12, min_iou_per_view=0.82)
        self.assertLess(result.final_loss, result.initial_loss - 0.025)
        self.assertGreater(result.evaluations, 2)
        self.assertGreater(result.accepted_moves, 0)
        self.assertTrue(all(
            metric.iou >= 0.82 for metric in result.final_metrics.values()
        ), result.to_dict())
        self.assertEqual(result.status, "WITHIN_TOLERANCE")
        self.assertLess(abs(result.parameters.width_scale - truth.width_scale), 0.15)
        qa = alter_project(project, result.parameters).build().validate(
            require_closed=True, require_outward=True
        )
        self.assertTrue(qa.ok, qa.errors)

    def test_references_with_same_camera_conflicting_masks_fail(self):
        project, truth, refs = _references(80, 60)
        cam = refs[0].camera
        original = refs[0].target
        different = BinaryMask(original.width, original.height,
                               original.pixels[1:] + original.pixels[:1])
        self.assertNotEqual(different, original)
        with self.assertRaises(ReferenceConflictError):
            fit(project, [
                SilhouetteReference("first", cam, original),
                SilhouetteReference("second", cam, different),
            ], active=("width_scale",))

    def test_duplicate_camera_not_double_counted(self):
        project, truth, refs = _references(80, 60)
        duplicate = SilhouetteReference("copy", refs[0].camera, refs[0].target)
        with self.assertRaisesRegex(ValueError, "Duplicate calibrated"):
            fit(project, [refs[0], duplicate], active=("width_scale",))

    def test_reference_resolution_and_empty_mask_fails(self):
        cameras = standard_views(80, 60)
        target = BinaryMask(8, 6, bytes([1] * 48))
        with self.assertRaises(ValueError):
            SilhouetteReference("bad", cameras["side"], target)
        with self.assertRaises(ValueError):
            SilhouetteReference("bad", cameras["side"], BinaryMask(80, 60, bytes(4800)))
        with self.assertRaises(ValueError):
            SilhouetteReference("bad", cameras["hero"], BinaryMask(80, 60, bytes([1] * 4800)))

    def test_unobserved_front_camera_nose_extension_warning(self):
        project = demo_project()
        cam = standard_views(64, 48)["front"]
        target = BinaryMask.from_render(render_silhouette(project.build(), cam))
        ref = SilhouetteReference("front", cam, target)
        result = fit(project, [ref], active=("nose_extension",),
                     max_passes=3, min_iou_per_view=0.90)
        self.assertIn("nose_extension", result.unobservable_at_step)
        self.assertEqual(result.status, "WITHIN_TOLERANCE")
        self.assertEqual(result.final_loss, 0.0)

    def test_high_residual_gets_no_false_success(self):
        project, truth, refs = _references(80, 60)
        result = fit(project, refs, active=("rear_tip_scale",),
                     max_passes=2, min_iou_per_view=0.999)
        self.assertEqual(result.status, "RESIDUAL_TOO_HIGH_OR_CONFLICT")
        self.assertTrue(any(m.iou < 0.999 for m in result.final_metrics.values()))

    def test_invalid_fitter_configuration_rejected(self):
        project, truth, refs = _references(80, 60)
        for config in ({"active": ("strange",)}, {"active": ()},
                       {"max_passes": 0}, {"max_evaluations": 1},
                       {"min_iou_per_view": 0}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                fit(project, refs, **config)


if __name__ == "__main__":
    unittest.main()
