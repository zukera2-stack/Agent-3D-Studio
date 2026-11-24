"""Optional adapter for preparing an explicitly selected drawing crop.

The Stage 03 runtime needs only stdlib. THIS optional adapter uses Pillow
to read third-party formats (JPEG, palette PNG, alpha PNG, etc.). It is NOT
an automatic sketch segmenter or a scale/perspective calibration engine.

Usage:
python -m a3ds.maskprep --input sketch.png --crop 10,40,800,600 \
  --width 160 --height 120 --foreground dark --threshold 125 --out ref.png
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .silhouette import BinaryMask


def prepare(
    input_path: str | Path, *,
    crop: tuple[int, int, int, int],
    width: int,
    height: int,
    foreground: str,
    threshold: int,
) -> BinaryMask:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "This optional external-image adapter needs Pillow: python -m pip install Pillow"
        ) from exc
    if foreground not in ("dark", "light", "alpha"):
        raise ValueError("foreground must be dark/light/alpha")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")
    if not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise ValueError("Mask output size outside 1..4096")
    x, y, w, h = crop
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        raise ValueError("Crop requires nonnegative origin and positive size")
    ratio = w / h
    target_ratio = width / height
    if abs(ratio / target_ratio - 1) > 0.01:
        raise ValueError(
            "Crop and output aspect ratios differ >1%. "
            "Choose matching crop: never stretch source art silently."
        )
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if x + w > img.width or y + h > img.height:
            raise ValueError("Crop rectangle is outside source image")
        rgba = img.crop((x, y, x + w, y + h)).convert("RGBA")
        rgba = rgba.resize((width, height), Image.Resampling.NEAREST)
        pix = rgba.tobytes()
    result = bytearray(width * height)
    for i in range(0, len(pix), 4):
        red, green, blue, alpha = pix[i:i+4]
        # Alpha mode operates ONLY on true transparency, not drawn white.
        if foreground == "alpha":
            selected = alpha > threshold
        else:
            gray = (299 * red + 587 * green + 114 * blue + 500) // 1000
            selected = gray < threshold if foreground == "dark" else gray > threshold
        result[i // 4] = 1 if selected else 0
    mask = BinaryMask(width, height, bytes(result))
    if not 0 < mask.area < width * height:
        raise ValueError(
            "Empty/full silhouette after threshold. Check crop/background/mode."
        )
    return mask


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Manually crop and threshold sketch to a silhouette mask")
    parser.add_argument("--input", required=True, help="User-selected source image")
    parser.add_argument("--crop", required=True, help="X,Y,WIDTH,HEIGHT integer crop")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--foreground", choices=["dark", "light", "alpha"], required=True)
    parser.add_argument("--threshold", type=int, default=128)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        parts = tuple(int(p.strip()) for p in args.crop.split(","))
        if len(parts) != 4:
            raise ValueError("Crop must be X,Y,WIDTH,HEIGHT")
        mask = prepare(args.input, crop=parts, width=args.width, height=args.height,
                       foreground=args.foreground, threshold=args.threshold)
        mask.save_png(args.out)
        print(f"Mask saved: {args.out}, foreground={mask.area}/{mask.width*mask.height} pixels")
        print("CAUTION: crop/resize is NOT a calibrated model-space registration.")
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Image preparation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
