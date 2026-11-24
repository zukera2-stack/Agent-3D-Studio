"""Deterministic, bounded silhouette fitter for a deliberately limited loft family.

This optimizes SHAPE PARAMETERS, not thousands of vertices. References must be
already aligned monochrome silhouette masks from known orthographic cameras.
A good IoU is evidence of 2D overlap, NOT unique 3D reconstruction or
mathematically proven compatibility of all artist sketches.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from .camera import Camera
from .fit_geometry import (
    DEFAULT_STEPS, PARAM_BOUNDS, ShapeParams, alter_project
)
from .project import SurfaceProject
from .raster import render_silhouette
from .silhouette import BinaryMask, MaskMetrics, compare_masks


class ReferenceConflictError(ValueError):
    """Two different targets claim to depict the EXACT SAME calibrated camera."""


@dataclass(frozen=True)
class SilhouetteReference:
    name: str
    camera: Camera
    target: BinaryMask
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Reference name required")
        if self.camera.projection != "orthographic":
            raise ValueError("Stage 03 supports only calibrated orthographic references")
        if (self.target.width, self.target.height) != (self.camera.width, self.camera.height):
            raise ValueError("Reference mask dimensions must match camera pixels exactly")
        if self.target.area == 0:
            raise ValueError("Empty reference silhouette")
        if not isfinite(self.weight) or self.weight <= 0:
            raise ValueError("Reference weight must be finite and positive")


@dataclass(frozen=True)
class FitResult:
    initial: ShapeParams
    parameters: ShapeParams
    initial_loss: float
    final_loss: float
    initial_metrics: dict[str, MaskMetrics]
    final_metrics: dict[str, MaskMetrics]
    evaluations: int
    accepted_moves: int
    accepted_history: tuple[dict, ...]
    unobservable_at_step: tuple[str, ...]
    minimum_view_iou: float
    status: str

    def to_dict(self) -> dict:
        return {
            "format": "a3ds.silhouette-fit/1",
            "initial": self.initial.to_dict(),
            "optimized": self.parameters.to_dict(),
            "initial_loss": self.initial_loss,
            "final_loss": self.final_loss,
            "improvement": self.initial_loss - self.final_loss,
            "initial_per_view": {name: m.to_dict() for name, m in self.initial_metrics.items()},
            "final_per_view": {name: m.to_dict() for name, m in self.final_metrics.items()},
            "evaluations": self.evaluations,
            "accepted_moves": self.accepted_moves,
            "accepted_history": list(self.accepted_history),
            "unobservable_at_step": list(self.unobservable_at_step),
            "minimum_view_iou": self.minimum_view_iou,
            "status": self.status,
            "warnings": [
                "IoU measures calibrated 2D overlap, not unique 3D recovery.",
                "High residual can mean conflicting views, bad camera alignment, insufficient shape family or local optimum.",
                "Unobservable-at-step is a sampled pixel sensitivity check, NOT a proof of parameter identifiability.",
                "No automatic sketch segmentation or perspective inference is performed.",
            ],
        }


def _check_references(references: Sequence[SilhouetteReference]) -> None:
    if not references:
        raise ValueError("At least one calibrated silhouette reference required")
    if len(references) > 8:
        raise ValueError("Stage 03 limits fitting to eight reference masks")
    seen_names: set[str] = set()
    seen_cameras: dict[Camera, BinaryMask] = {}
    for ref in references:
        if ref.name in seen_names:
            raise ValueError("Reference names must be unique")
        seen_names.add(ref.name)
        if ref.camera in seen_cameras:
            if seen_cameras[ref.camera] != ref.target:
                raise ReferenceConflictError(
                    f"Incompatible reference masks for same camera: {ref.name}"
                )
            raise ValueError("Duplicate calibrated camera contributes no new 3D information")
        seen_cameras[ref.camera] = ref.target


def _masks(project: SurfaceProject, params: ShapeParams,
           references: Sequence[SilhouetteReference]) -> list[BinaryMask]:
    mesh = alter_project(project, params).build()
    report = mesh.validate(require_closed=True, require_outward=True)
    if not report.ok:
        raise ValueError("Candidate mesh failed topology QA: " + repr(report.errors))
    return [
        BinaryMask.from_render(render_silhouette(mesh, reference.camera))
        for reference in references
    ]


def measure(project: SurfaceProject, params: ShapeParams,
            references: Sequence[SilhouetteReference]) -> tuple[float, dict[str, MaskMetrics]]:
    _check_references(references)
    rendered = _masks(project, params, references)
    result = {
        ref.name: compare_masks(predicted, ref.target)
        for ref, predicted in zip(references, rendered)
    }
    weight_sum = sum(ref.weight for ref in references)
    loss = sum(
        (1.0 - result[ref.name].iou) * ref.weight
        for ref in references
    ) / weight_sum
    return loss, result


def fit(
    project: SurfaceProject,
    references: Sequence[SilhouetteReference],
    *,
    active: Sequence[str] = ("width_scale", "height_scale", "nose_extension"),
    initial: ShapeParams | None = None,
    max_passes: int = 12,
    min_step_ratio: float = 1 / 32,
    min_iou_per_view: float = 0.90,
    max_evaluations: int = 300,
) -> FitResult:
    """Bounded coordinate search, always retaining the best *measured* score.

    It is intentionally derivative-free: the pixel raster produces staircase
    losses and numerical gradients are unstable at coverage transitions.
    """
    _check_references(references)
    if not active or len(active) != len(set(active)):
        raise ValueError("At least one unique active parameter required")
    if any(name not in PARAM_BOUNDS for name in active):
        raise ValueError("Unknown parameter in active list")
    if not isinstance(max_passes, int) or not 1 <= max_passes <= 60:
        raise ValueError("max_passes must be in [1,60]")
    if not isinstance(max_evaluations, int) or not 2 <= max_evaluations <= 3000:
        raise ValueError("Invalid evaluation budget")
    if not 0 < min_step_ratio < 1:
        raise ValueError("min_step_ratio must lie strictly inside (0,1)")
    if not 0 < min_iou_per_view <= 1:
        raise ValueError("min_iou_per_view must be in (0,1]")

    current = initial if initial is not None else ShapeParams()
    steps = {name: DEFAULT_STEPS[name] for name in active}
    cache: dict[ShapeParams, tuple[float, dict[str, MaskMetrics]]] = {}
    evaluations = 0

    def evaluate(candidate: ShapeParams) -> tuple[float, dict[str, MaskMetrics]]:
        nonlocal evaluations
        if candidate not in cache:
            if evaluations >= max_evaluations:
                raise RuntimeError("Fitting evaluation budget exhausted")
            cache[candidate] = measure(project, candidate, references)
            evaluations += 1
        return cache[candidate]

    baseline_loss, baseline_metrics = evaluate(current)
    best_loss = baseline_loss
    accepted = 0
    history: list[dict] = []
    for pass_index in range(max_passes):
        improved = False
        for name in active:
            local_best = current
            local_loss = best_loss
            low, high = PARAM_BOUNDS[name]
            for sign in (-1, 1):
                value = getattr(current, name) + sign * steps[name]
                if not low <= value <= high:
                    continue
                candidate = current.modified(name, value)
                loss, _ = evaluate(candidate)
                if loss < local_loss - 1e-10:
                    local_best, local_loss = candidate, loss
            if local_best != current:
                current, best_loss = local_best, local_loss
                accepted += 1
                improved = True
                history.append({
                    "pass": pass_index + 1, "parameter": name,
                    "value": getattr(current, name), "loss": best_loss
                })
        if not improved:
            steps = {name: 0.5 * step for name, step in steps.items()}
        if all(steps[name] < DEFAULT_STEPS[name] * min_step_ratio for name in active):
            break

    final_loss, final_metrics = evaluate(current)
    # Discrete finite-difference sensitivity is a *warning* about unobservable
    # knobs at this resolution, NOT a singular-value/unique-solution test.
    current_masks = _masks(project, current, references)
    unobservable: list[str] = []
    for name in active:
        low, high = PARAM_BOUNDS[name]
        step = DEFAULT_STEPS[name]
        test_value = getattr(current, name) + step
        if test_value > high:
            test_value = getattr(current, name) - step
        if test_value < low:
            continue
        probe = current.modified(name, test_value)
        probe_masks = _masks(project, probe, references)
        difference = sum(
            sum(a != b for a, b in zip(reference.pixels, predicted.pixels))
            for reference, predicted in zip(current_masks, probe_masks)
        )
        if difference == 0:
            unobservable.append(name)

    success = all(m.iou >= min_iou_per_view for m in final_metrics.values())
    status = "WITHIN_TOLERANCE" if success else "RESIDUAL_TOO_HIGH_OR_CONFLICT"
    return FitResult(
        initial if initial is not None else ShapeParams(),
        current, baseline_loss, final_loss, baseline_metrics, final_metrics,
        evaluations, accepted, tuple(history), tuple(unobservable),
        min_iou_per_view, status
    )
