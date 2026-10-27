"""Minimal 3D math (pure Python, no dependencies).

Conventions follow Roblox: Y up, the character faces -Z, +X is the character's right.
Rotations are in degrees and composed like ``CFrame.Angles(rx, ry, rz)``,
i.e. matrix = Rx * Ry * Rz.
"""

from __future__ import annotations

import math

Vec = tuple[float, float, float]
Mat = tuple[Vec, Vec, Vec]
Transform = tuple[Mat, Vec]  # (rotation, translation)

IDENTITY: Mat = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def vadd(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vneg(a: Vec) -> Vec:
    return (-a[0], -a[1], -a[2])


def vlen(a: Vec) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def mat_mul(a: Mat, b: Mat) -> Mat:
    return tuple(  # type: ignore[return-value]
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def mat_vec(m: Mat, v: Vec) -> Vec:
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))  # type: ignore[return-value]


def transpose(m: Mat) -> Mat:
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def rot_x(deg: float) -> Mat:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def rot_y(deg: float) -> Mat:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))


def rot_z(deg: float) -> Mat:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def euler(rot: Vec) -> Mat:
    """Rotation matrix equivalent to Roblox ``CFrame.Angles`` (degrees)."""
    return mat_mul(mat_mul(rot_x(rot[0]), rot_y(rot[1])), rot_z(rot[2]))


def compose(a: Transform, b: Transform) -> Transform:
    """``a * b`` (apply b in a's frame)."""
    ra, pa = a
    rb, pb = b
    return (mat_mul(ra, rb), vadd(mat_vec(ra, pb), pa))


def translate(p: Vec) -> Transform:
    return (IDENTITY, p)


def apply(t: Transform, v: Vec) -> Vec:
    return vadd(mat_vec(t[0], v), t[1])
