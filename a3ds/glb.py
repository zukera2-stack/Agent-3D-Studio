"""Minimal self-contained glTF 2.0 binary (.glb) writer and subset reader.

Stage 01 supports one triangle mesh, POSITION + NORMAL + indices and PBR color.
The input coordinate convention is right-handed X=width, +Y=front, Z=up.
glTF is Y-up/-Z-forward: export rotates (x,y,z)->(x,z,-y).
The subset reader restores the original A3DS convention.

This module does NOT promise to import arbitrary third-party glTF/GLB files.
"""
from __future__ import annotations

import json
from pathlib import Path
import struct

from .math3d import Vec3
from .mesh import Mesh

_MAGIC = b"glTF"
_JSON = b"JSON"
_BIN = b"BIN\x00"


def _pad(data: bytes, pad: bytes) -> bytes:
    return data + pad * ((-len(data)) % 4)


def _to_gltf(v: Vec3) -> tuple[float, float, float]:
    return (v.x, v.z, -v.y)


def _from_gltf(x: float, y: float, z: float) -> Vec3:
    return Vec3(x, -z, y)


def encode_glb(mesh: Mesh, *, base_color: tuple[float, float, float, float] = (0.67, 0.71, 0.76, 1.0)) -> bytes:
    report = mesh.validate(require_closed=False)
    if not report.ok:
        raise ValueError(f"Mesh is invalid: {report.errors}")
    if not (len(base_color) == 4 and all(0 <= c <= 1 for c in base_color)):
        raise ValueError("base_color must be four floats between 0 and 1")
    vertices = [_to_gltf(p) for p in mesh.vertices]
    normals = [_to_gltf(p) for p in mesh.vertex_normals()]
    indices = [index for face in mesh.triangles for index in face]
    if len(vertices) > 2**32 - 1 or len(indices) > 2**32 - 1:
        raise ValueError("Mesh exceeds uint32 limits")
    positions_blob = b"".join(struct.pack("<fff", *v) for v in vertices)
    normals_blob = b"".join(struct.pack("<fff", *n) for n in normals)
    indices_blob = b"".join(struct.pack("<I", v) for v in indices)
    binary = positions_blob + normals_blob + indices_blob
    position_length, normals_length = len(positions_blob), len(normals_blob)
    axes = list(zip(*vertices))
    gltf = {
        "asset": {"version": "2.0", "generator": "Agent 3D Studio Stage 01"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": mesh.name}],
        "meshes": [{"name": mesh.name, "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1},
            "indices": 2, "mode": 4, "material": 0
        }]}],
        "materials": [{
            "name": "A3DS_default",
            "doubleSided": False,
            "pbrMetallicRoughness": {
                "baseColorFactor": list(base_color),
                "metallicFactor": 0.15,
                "roughnessFactor": 0.56
            }
        }],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": position_length, "target": 34962},
            {"buffer": 0, "byteOffset": position_length, "byteLength": normals_length, "target": 34962},
            {"buffer": 0, "byteOffset": position_length + normals_length, "byteLength": len(indices_blob), "target": 34963}
        ],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(vertices),
             "type": "VEC3", "min": [min(ax) for ax in axes], "max": [max(ax) for ax in axes]},
            {"bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(vertices), "type": "VEC3"},
            {"bufferView": 2, "byteOffset": 0, "componentType": 5125, "count": len(indices), "type": "SCALAR"},
        ],
        "extras": {"a3ds_axes": "X_right_Y_front_Z_up", "a3ds_stage": 1},
    }
    json_chunk = _pad(json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), b" ")
    binary_chunk = _pad(binary, b"\x00")
    total = 12 + 8 + len(json_chunk) + 8 + len(binary_chunk)
    return (
        struct.pack("<4sII", _MAGIC, 2, total)
        + struct.pack("<I4s", len(json_chunk), _JSON) + json_chunk
        + struct.pack("<I4s", len(binary_chunk), _BIN) + binary_chunk
    )


def write_glb(mesh: Mesh, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_glb(mesh))


def decode_glb(blob: bytes) -> Mesh:
    if len(blob) < 28:
        raise ValueError("GLB too short")
    magic, version, total = struct.unpack_from("<4sII", blob, 0)
    if magic != _MAGIC or version != 2 or total != len(blob):
        raise ValueError("Invalid GLB header or length")
    offset = 12
    chunks: list[tuple[bytes, bytes]] = []
    while offset < len(blob):
        if offset + 8 > len(blob):
            raise ValueError("Truncated GLB chunk header")
        length, kind = struct.unpack_from("<I4s", blob, offset)
        offset += 8
        if length % 4 or offset + length > len(blob):
            raise ValueError("Invalid GLB chunk size")
        chunks.append((kind, blob[offset:offset + length]))
        offset += length
    if len(chunks) != 2 or chunks[0][0] != _JSON or chunks[1][0] != _BIN:
        raise ValueError("Expected JSON and BIN chunks")
    doc = json.loads(chunks[0][1].decode("utf-8"))
    binary = chunks[1][1]
    if doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("Not glTF 2.0")
    if doc.get("extras", {}).get("a3ds_axes") != "X_right_Y_front_Z_up":
        raise ValueError("GLB does not declare the A3DS coordinate contract")
    if len(doc["buffers"]) != 1 or doc["buffers"][0]["byteLength"] > len(binary):
        raise ValueError("Binary buffer length mismatch")
    if len(doc["meshes"]) != 1 or len(doc["meshes"][0]["primitives"]) != 1:
        raise ValueError("Only single-mesh files from A3DS Stage 01 can be loaded")
    primitive = doc["meshes"][0]["primitives"][0]
    if primitive.get("mode") != 4:
        raise ValueError("Expected triangles")

    def accessor(index: int, *, component: int, kind: str) -> tuple[int, bytes]:
        acc = doc["accessors"][index]
        if acc["type"] != kind or acc["componentType"] != component:
            raise ValueError("Unsupported accessor type")
        view = doc["bufferViews"][acc["bufferView"]]
        if view["buffer"] != 0 or "byteStride" in view or acc.get("sparse"):
            raise ValueError("Only tightly-packed A3DS buffers are supported")
        offset = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        count = acc["count"]
        length = count * (12 if component == 5126 else 4)
        if count < 0 or offset < 0 or length > view["byteLength"] - acc.get("byteOffset", 0) or offset + length > len(binary):
            raise ValueError("Accessor range exceeds buffer")
        return count, binary[offset:offset + length]

    vcount, pos_blob = accessor(primitive["attributes"]["POSITION"], component=5126, kind="VEC3")
    ncount, _ = accessor(primitive["attributes"]["NORMAL"], component=5126, kind="VEC3")
    icount, index_blob = accessor(primitive["indices"], component=5125, kind="SCALAR")
    if ncount != vcount or icount % 3 != 0:
        raise ValueError("Normal and triangle count mismatch")
    verts = [_from_gltf(*xyz) for xyz in struct.iter_unpack("<fff", pos_blob)]
    flat = [value[0] for value in struct.iter_unpack("<I", index_blob)]
    faces = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    mesh = Mesh(verts, faces, doc["meshes"][0].get("name", "Mesh"))
    if not mesh.validate().ok:
        raise ValueError("Decoded mesh failed topology validation")
    return mesh


def read_glb(path: str | Path) -> Mesh:
    return decode_glb(Path(path).read_bytes())
