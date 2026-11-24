"""Small, strict, deterministic PNG RGB8/gray8 encoder (no Pillow/Blender dependency).

Our own reader is for smoke tests only; independent Pillow validation belongs in CI.
"""
from __future__ import annotations

from pathlib import Path
import struct
import zlib


_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def encode_png(width: int, height: int, rgb_or_gray: bytes | bytearray, *, channels: int = 3) -> bytes:
    if not isinstance(width, int) or not isinstance(height, int) or not (1 <= width <= 8192 and 1 <= height <= 8192):
        raise ValueError("Invalid PNG dimensions")
    if channels not in (1, 3):
        raise ValueError("Only grayscale8 or RGB8 are supported")
    if len(rgb_or_gray) != width * height * channels:
        raise ValueError("Pixel buffer length does not match image dimensions")
    stride = width * channels
    data = b"".join(b"\x00" + bytes(rgb_or_gray[row * stride:(row + 1) * stride]) for row in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 0 if channels == 1 else 2, 0, 0, 0)
    return (
        _SIG
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(data, level=6))
        + _chunk(b"IEND", b"")
    )


def write_png(path: str | Path, width: int, height: int, pixels: bytes | bytearray, *, channels: int = 3) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(encode_png(width, height, pixels, channels=channels))


def decode_our_png(blob: bytes) -> tuple[int, int, int, bytes]:
    """Strictly reads the unfiltered grayscale/RGB PNGs produced by encode_png."""
    if not blob.startswith(_SIG):
        raise ValueError("Invalid PNG signature")
    p = len(_SIG)
    chunks: dict[bytes, list[bytes]] = {}
    ended = False
    while p < len(blob):
        if p + 12 > len(blob):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", blob, p)[0]
        start = p + 8
        end = start + size
        if end + 4 > len(blob):
            raise ValueError("PNG chunk exceeds buffer")
        kind = blob[p + 4:p + 8]
        payload = blob[start:end]
        crc = struct.unpack_from(">I", blob, end)[0]
        if crc != zlib.crc32(kind + payload) & 0xFFFFFFFF:
            raise ValueError("PNG chunk CRC mismatch")
        chunks.setdefault(kind, []).append(payload)
        p = end + 4
        if kind == b"IEND":
            ended = True
            break
    if not ended or p != len(blob):
        raise ValueError("PNG must end with one IEND chunk")
    if len(chunks.get(b"IHDR", [])) != 1 or len(chunks.get(b"IEND", [])) != 1:
        raise ValueError("Missing PNG IHDR/IEND")
    width, height, bits, color, comp, filt, interlace = struct.unpack(">IIBBBBB", chunks[b"IHDR"][0])
    if not 1 <= width <= 8192 or not 1 <= height <= 8192 or bits != 8 or color not in (0, 2) or (comp, filt, interlace) != (0, 0, 0):
        raise ValueError("Unsupported PNG image type")
    channels = 1 if color == 0 else 3
    rows = zlib.decompress(b"".join(chunks.get(b"IDAT", [])))
    expected = (width * channels + 1) * height
    if len(rows) != expected:
        raise ValueError("Decompressed PNG length mismatch")
    stride = width * channels
    pixels = bytearray(width * height * channels)
    for row in range(height):
        if rows[row * (stride + 1)] != 0:
            raise ValueError("Unexpected PNG filter")
        lo = row * (stride + 1) + 1
        pixels[row * stride:(row + 1) * stride] = rows[lo:lo + stride]
    return width, height, channels, bytes(pixels)
