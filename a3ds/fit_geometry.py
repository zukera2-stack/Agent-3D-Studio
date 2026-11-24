"""Stage 03: bounded, named adjustments to the existing parametric loft.

This is a deliberately small, inspectable shape family, NOT an unrestricted
vertex optimizer. It keeps section order, outward winding and the JSON source.
X=width, +Y=nose, Z=up in BU.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from .project import SurfaceProject
from .surfaces import CrossSection


PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "width_scale": (0.65, 1.50),
    "height_scale": (0.70, 1.50),
    "nose_extension": (-0.55, 0.85),  # BU along +Y
    "nose_tip_scale": (0.55, 1.60),
    "rear_tip_scale": (0.55, 1.60),
}
DEFAULT_STEPS = {
    "width_scale": 0.14,
    "height_scale": 0.12,
    "nose_extension": 0.20,
    "nose_tip_scale": 0.15,
    "rear_tip_scale": 0.15,
}


def _smoothstep(x: float) -> float:
    t = min(1.0, max(0.0, x))
    return t * t * (3.0 - 2.0 * t)


@dataclass(frozen=True)
class ShapeParams:
    width_scale: float = 1.0
    height_scale: float = 1.0
    nose_extension: float = 0.0
    nose_tip_scale: float = 1.0
    rear_tip_scale: float = 1.0

    def __post_init__(self) -> None:
        for name, (lo, hi) in PARAM_BOUNDS.items():
            value = getattr(self, name)
            if not isfinite(value) or not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    def modified(self, name: str, value: float) -> "ShapeParams":
        if name not in PARAM_BOUNDS:
            raise ValueError(f"Unknown shape parameter: {name}")
        return replace(self, **{name: value})

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in PARAM_BOUNDS}


def alter_project(base: SurfaceProject, parameters: ShapeParams) -> SurfaceProject:
    """Apply smooth, constrained transformations to ORIGINAL sections only.

    z-center remains unchanged so model height is modified around its own
    sectional center, not around world zero. Shared dimensions remain positive.
    Parameter influence is tapered to avoid introducing a nose/rear seam.
    """
    src = base.sections
    if len(src) < 2:
        raise ValueError("Source project needs at least two sections")
    ymin, ymax = src[0].y, src[-1].y
    span = ymax - ymin
    if span <= 0:
        raise ValueError("Source sections must increase in Y")
    updated: list[CrossSection] = []
    for section in src:
        t = (section.y - ymin) / span
        front = _smoothstep((t - 0.69) / 0.31)
        front_tip = _smoothstep((t - 0.82) / 0.18)
        rear_tip = _smoothstep((0.16 - t) / 0.16)
        new_y = section.y + front * parameters.nose_extension
        width = (
            section.half_width * parameters.width_scale
            * (1.0 + (parameters.nose_tip_scale - 1.0) * front_tip)
            * (1.0 + (parameters.rear_tip_scale - 1.0) * rear_tip)
        )
        height = section.half_height * parameters.height_scale
        updated.append(CrossSection(
            new_y, section.center_z, width, height, section.exponent
        ))
    if any(right.y <= left.y for left, right in zip(updated, updated[1:])):
        raise ValueError("Shape parameters inverted longitudinal section order")
    return SurfaceProject(
        base.name + "_fitted", updated, base.sides, base.steps_per_span, base.unit_label
    )
