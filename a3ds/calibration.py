"""Stage 02: explicit 2D landmark calibration, no sketch-content invention.

Fits translation + one positive uniform scale for orthographic U-right/V-up axes.
No rotations, nonlinear distortion, perspective inference or image recognition.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Sequence


@dataclass(frozen=True)
class Landmark:
    world_u: float
    world_v: float
    pixel_x: float
    pixel_y: float


@dataclass(frozen=True)
class Registration:
    pixels_per_bu: float
    origin_x: float
    origin_y: float
    rms_pixels: float
    anchors: int

    def world_to_pixel(self, u: float, v: float) -> tuple[float, float]:
        return (self.origin_x + self.pixels_per_bu * u,
                self.origin_y - self.pixels_per_bu * v)

    def pixel_to_world(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.origin_x) / self.pixels_per_bu,
                (self.origin_y - y) / self.pixels_per_bu)


def fit_landmarks(
    landmarks: Sequence[Landmark], *, max_rms_pixels: float | None = None
) -> Registration:
    if len(landmarks) < 2:
        raise ValueError("At least two distinct calibration anchors are required")
    for a in landmarks:
        if not all(isfinite(value) for value in
                   (a.world_u, a.world_v, a.pixel_x, a.pixel_y)):
            raise ValueError("Calibration coordinates must be finite")
    n = len(landmarks)
    um = sum(a.world_u for a in landmarks) / n
    vm = sum(a.world_v for a in landmarks) / n
    xm = sum(a.pixel_x for a in landmarks) / n
    ym = sum(a.pixel_y for a in landmarks) / n
    den = sum((a.world_u - um) ** 2 + (a.world_v - vm) ** 2 for a in landmarks)
    if den <= 1e-12:
        raise ValueError("Calibration anchors must occupy distinct world coordinates")
    num = sum(
        (a.world_u - um) * (a.pixel_x - xm)
        - (a.world_v - vm) * (a.pixel_y - ym)
        for a in landmarks
    )
    scale = num / den
    if not isfinite(scale) or scale <= 0:
        raise ValueError("Calibration axes inverted or degenerate")
    origin_x = xm - scale * um
    origin_y = ym + scale * vm
    residual = sum(
        (origin_x + scale * a.world_u - a.pixel_x) ** 2
        + (origin_y - scale * a.world_v - a.pixel_y) ** 2
        for a in landmarks
    )
    rms = sqrt(residual / n)
    if max_rms_pixels is not None:
        if not isfinite(max_rms_pixels) or max_rms_pixels < 0:
            raise ValueError("max_rms_pixels must be nonnegative and finite")
        if rms > max_rms_pixels:
            raise ValueError(
                f"Calibration inconsistent: RMS {rms:.3f}px exceeds {max_rms_pixels:.3f}px"
            )
    return Registration(scale, origin_x, origin_y, rms, n)
