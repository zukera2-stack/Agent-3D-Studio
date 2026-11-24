"""Stage 03 binary silhouette metrics, file I/O and error overlays.

Masks have one byte per pixel, 0 or 1; no inferred alpha/transparent artwork.
Native PNG input accepts Stage 02's self-produced PNG subset. Other PNGs must
be converted to the stated binary mask format by an explicitly separate step.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .png import decode_our_png, write_png
from .raster import Render


@dataclass(frozen=True)
class BinaryMask:
    width: int
    height: int
    pixels: bytes

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 8192 or not 1 <= self.height <= 8192:
            raise ValueError("Bad mask dimensions")
        if len(self.pixels) != self.width * self.height:
            raise ValueError("Mask length differs from WxH")
        if any(value not in (0, 1) for value in self.pixels):
            raise ValueError("Mask must contain only binary 0/1 values")

    @property
    def area(self) -> int:
        return sum(self.pixels)

    @classmethod
    def from_render(cls, render: Render) -> "BinaryMask":
        return cls(render.width, render.height, bytes(render.coverage))

    @classmethod
    def from_png_bytes(cls, blob: bytes, *, threshold: int = 128) -> "BinaryMask":
        width, height, channels, raw = decode_our_png(blob)
        if not 1 <= threshold <= 255:
            raise ValueError("Threshold must be in [1,255]")
        if channels == 1:
            data = bytes(1 if v >= threshold else 0 for v in raw)
        else:
            data = bytes(
                1 if max(raw[i:i+3]) >= threshold else 0
                for i in range(0, len(raw), 3)
            )
        return cls(width, height, data)

    def save_png(self, path: str | Path) -> None:
        write_png(path, self.width, self.height,
                  bytes(255 if a else 0 for a in self.pixels), channels=1)

    @classmethod
    def read_png(cls, path: str | Path) -> "BinaryMask":
        return cls.from_png_bytes(Path(path).read_bytes())


@dataclass(frozen=True)
class MaskMetrics:
    intersection: int
    union: int
    target_area: int
    predicted_area: int
    false_positive: int
    false_negative: int
    iou: float

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


def compare_masks(predicted: BinaryMask, target: BinaryMask) -> MaskMetrics:
    if (predicted.width, predicted.height) != (target.width, target.height):
        raise ValueError("Reference and prediction resolution disagree")
    if target.area == 0:
        raise ValueError("Empty target mask: cannot optimize unknown object")
    intersection = sum(1 for p, t in zip(predicted.pixels, target.pixels) if p and t)
    fp = sum(1 for p, t in zip(predicted.pixels, target.pixels) if p and not t)
    fn = sum(1 for p, t in zip(predicted.pixels, target.pixels) if t and not p)
    union = intersection + fp + fn
    return MaskMetrics(
        intersection, union, target.area, predicted.area, fp, fn,
        intersection / union if union else 0.0
    )


def difference_rgb(predicted: BinaryMask, target: BinaryMask) -> bytes:
    """Dark = background; light gray = agreement; red = extra; blue = missing."""
    compare_masks(predicted, target)
    palette = {
        (0, 0): (23, 32, 44),
        (1, 1): (204, 213, 218),
        (1, 0): (236, 66, 77),
        (0, 1): (65, 133, 237),
    }
    return bytes(
        channel
        for p, t in zip(predicted.pixels, target.pixels)
        for channel in palette[(p, t)]
    )


def write_difference_png(path: str | Path, predicted: BinaryMask, target: BinaryMask) -> None:
    compare_masks(predicted, target)
    write_png(path, target.width, target.height, difference_rgb(predicted, target))
