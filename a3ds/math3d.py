"""Small, explicit 3-D vector and row-major matrix math (right-handed; Z up)."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, sin, sqrt


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        return sqrt(self.dot(self))

    def normalized(self) -> "Vec3":
        length = self.length()
        if length == 0 or not isfinite(length):
            raise ValueError("Cannot normalize zero-length or nonfinite vector")
        return self * (1.0 / length)

    def finite(self) -> bool:
        return isfinite(self.x) and isfinite(self.y) and isfinite(self.z)

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class Mat4:
    """Row-major 4x4 affine matrix; points are column vectors."""

    m: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.m) != 16 or not all(isfinite(v) for v in self.m):
            raise ValueError("Mat4 needs 16 finite numbers")

    @classmethod
    def identity(cls) -> "Mat4":
        return cls((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))

    @classmethod
    def translation(cls, x: float, y: float, z: float) -> "Mat4":
        return cls((1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z, 0, 0, 0, 1))

    @classmethod
    def scale(cls, x: float, y: float, z: float) -> "Mat4":
        return cls((x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1))

    @classmethod
    def rotation_z(cls, angle_radians: float) -> "Mat4":
        c, s = cos(angle_radians), sin(angle_radians)
        return cls((c, -s, 0, 0, s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))

    def __matmul__(self, other: "Mat4") -> "Mat4":
        a, b = self.m, other.m
        return Mat4(tuple(
            sum(a[r * 4 + k] * b[k * 4 + col] for k in range(4))
            for r in range(4) for col in range(4)
        ))

    def point(self, p: Vec3) -> Vec3:
        a = self.m
        w = a[12] * p.x + a[13] * p.y + a[14] * p.z + a[15]
        if w == 0:
            raise ValueError("Point mapped to infinity")
        return Vec3(
            (a[0] * p.x + a[1] * p.y + a[2] * p.z + a[3]) / w,
            (a[4] * p.x + a[5] * p.y + a[6] * p.z + a[7]) / w,
            (a[8] * p.x + a[9] * p.y + a[10] * p.z + a[11]) / w,
        )
