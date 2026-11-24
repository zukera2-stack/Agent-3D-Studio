"""Triangular mesh storage, normals, edge topology and measurable acceptance gates."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from .math3d import Mat4, Vec3


@dataclass(frozen=True)
class MeshReport:
    vertices: int
    triangles: int
    boundary_edges: int
    nonmanifold_edges: int
    winding_conflicts: int
    degenerate_triangles: int
    signed_volume: float
    bounds_min: tuple[float, float, float] | None
    bounds_max: tuple[float, float, float] | None
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        from dataclasses import asdict
        result = asdict(self)
        result["ok"] = self.ok
        return result


@dataclass
class Mesh:
    vertices: list[Vec3]
    triangles: list[tuple[int, int, int]]
    name: str = "Mesh"

    def transformed(self, matrix: Mat4) -> "Mesh":
        if not isinstance(matrix, Mat4):
            raise TypeError("Expected Mat4")
        vertices = [matrix.point(v) for v in self.vertices]
        triangles = list(self.triangles)
        # Negative determinant reverses handedness; keep outward winding.
        a = matrix.m
        det = (
            a[0] * (a[5] * a[10] - a[6] * a[9])
            - a[1] * (a[4] * a[10] - a[6] * a[8])
            + a[2] * (a[4] * a[9] - a[5] * a[8])
        )
        if det == 0:
            raise ValueError("Singular transform produces degenerate faces")
        if det < 0:
            triangles = [(a, c, b) for a, b, c in triangles]
        return Mesh(vertices, triangles, self.name)

    def face_normal(self, tri: tuple[int, int, int]) -> Vec3:
        a, b, c = (self.vertices[i] for i in tri)
        return (b - a).cross(c - a).normalized()

    def vertex_normals(self) -> list[Vec3]:
        accumulator = [Vec3(0, 0, 0) for _ in self.vertices]
        for i, j, k in self.triangles:
            if min(i, j, k) < 0 or max(i, j, k) >= len(self.vertices):
                raise ValueError("Invalid face indices")
            normal = (self.vertices[j] - self.vertices[i]).cross(
                self.vertices[k] - self.vertices[i]
            )
            if normal.length() <= 1e-12:
                raise ValueError("Degenerate triangle has no vertex normal")
            for idx in (i, j, k):
                accumulator[idx] = accumulator[idx] + normal
        # Cap-center vertices can have only cap normals, others are area-weighted.
        return [v.normalized() for v in accumulator]

    def validate(self, *, require_closed: bool = False, require_outward: bool = False) -> MeshReport:
        errors: list[str] = []
        count = len(self.vertices)
        if not count or not self.triangles:
            errors.append("Mesh must contain vertices and triangles")
        if any(not p.finite() for p in self.vertices):
            errors.append("Nonfinite vertex coordinate")
        edges: dict[tuple[int, int], list[int]] = {}
        degenerate = 0
        volume6 = 0.0
        origin = self.vertices[0] if self.vertices else Vec3(0, 0, 0)
        for face in self.triangles:
            if len(face) != 3 or any(not isinstance(i, int) for i in face):
                errors.append("Face must have exactly three integer indices")
                continue
            i, j, k = face
            if min(face) < 0 or max(face) >= count:
                errors.append("Face refers to out-of-range vertex")
                continue
            if len(set(face)) != 3:
                degenerate += 1
                continue
            a, b, c = (self.vertices[idx] for idx in face)
            cross = (b - a).cross(c - a)
            area2 = cross.length()
            if not isfinite(area2) or area2 <= 1e-12:
                degenerate += 1
            if a.finite() and b.finite() and c.finite():
                # Translation-stable oriented volume; closed meshes only.
                volume6 += (a - origin).dot((b - origin).cross(c - origin))
            for u, v in ((i, j), (j, k), (k, i)):
                key = (u, v) if u < v else (v, u)
                edges.setdefault(key, []).append(1 if u < v else -1)
        boundary = sum(len(signs) == 1 for signs in edges.values())
        nonmanifold = sum(len(signs) > 2 for signs in edges.values())
        conflicts = sum(len(signs) == 2 and sum(signs) != 0 for signs in edges.values())
        if degenerate:
            errors.append(f"{degenerate} degenerate triangles")
        if nonmanifold:
            errors.append(f"{nonmanifold} nonmanifold edges")
        if conflicts:
            errors.append(f"{conflicts} winding-conflict edges")
        if require_closed and boundary:
            errors.append(f"{boundary} boundary edges (not watertight)")
        signed_volume = volume6 / 6.0
        if require_outward and (boundary or nonmanifold or conflicts or signed_volume <= 1e-10):
            errors.append("Mesh is not closed with positive outward signed volume")
        if self.vertices and all(v.finite() for v in self.vertices):
            minimum = tuple(min(getattr(v, d) for v in self.vertices) for d in "xyz")
            maximum = tuple(max(getattr(v, d) for v in self.vertices) for d in "xyz")
        else:
            minimum = maximum = None
        return MeshReport(
            count, len(self.triangles), boundary, nonmanifold, conflicts, degenerate,
            signed_volume, minimum, maximum, tuple(errors)
        )
