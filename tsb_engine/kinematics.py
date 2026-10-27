"""Forward kinematics for the standard R6 rig.

Geometry (studs) of the default R6 rig, with the HumanoidRootPart centred on the torso:

    Torso 2x2x1, Head 1x1x1, Arms 1x2x1, Legs 1x2x1.

Each joint is described by (C0, C1) translations; the legacy rotated axes of the real
Motor6D C0/C1 are intentionally ignored here: in this engine all limb rotations are
expressed in the *torso frame* (rx = swing forward/back, rz = swing sideways, ry = twist).
Mapping to real Motor6D axes belongs in an exporter and must be verified on the target rig.

Standing pose: root at y = 3, feet at y = 0. Character faces -Z.
"""

from __future__ import annotations

from itertools import product

from .mathutil import (
    Transform,
    Vec,
    apply,
    compose,
    euler,
    translate,
    vneg,
)
from .model import PARTS, Pose

ROOT_REST_Y = 3.0

SIZES: dict[str, Vec] = {
    "Torso": (2.0, 2.0, 1.0),
    "Head": (1.0, 1.0, 1.0),
    "Right Arm": (1.0, 2.0, 1.0),
    "Left Arm": (1.0, 2.0, 1.0),
    "Right Leg": (1.0, 2.0, 1.0),
    "Left Leg": (1.0, 2.0, 1.0),
}

# part -> (C0 in torso frame, C1 in limb frame)
JOINTS: dict[str, tuple[Vec, Vec]] = {
    "Head": ((0.0, 1.0, 0.0), (0.0, -0.5, 0.0)),
    "Right Arm": ((1.0, 0.5, 0.0), (-0.5, 0.5, 0.0)),
    "Left Arm": ((-1.0, 0.5, 0.0), (0.5, 0.5, 0.0)),
    "Right Leg": ((1.0, -1.0, 0.0), (0.5, 1.0, 0.0)),
    "Left Leg": ((-1.0, -1.0, 0.0), (-0.5, 1.0, 0.0)),
}

LEG_LENGTH = 2.0


def pose_transform(pose: Pose) -> Transform:
    return compose(translate(pose.pos), (euler(pose.rot), (0.0, 0.0, 0.0)))


def part_transforms(
    sample: dict[str, Pose],
    root_pos: Vec = (0.0, ROOT_REST_Y, 0.0),
    root: Transform | None = None,
) -> dict[str, Transform]:
    """World transform of every part for a sampled pose.

    ``root`` (a full transform) overrides ``root_pos``; the scene module uses it to place a
    character in the world and apply its Root track.
    """
    root_tf = root if root is not None else translate(root_pos)
    torso = compose(root_tf, pose_transform(sample.get("Torso", Pose())))
    result: dict[str, Transform] = {"Torso": torso}
    for part in PARTS:
        if part == "Torso":
            continue
        c0, c1 = JOINTS[part]
        t = compose(torso, translate(c0))
        t = compose(t, pose_transform(sample.get(part, Pose())))
        t = compose(t, translate(vneg(c1)))
        result[part] = t
    return result


def joint_world_position(part: str, transforms: dict[str, Transform]) -> Vec:
    """World position of the joint (hip/shoulder/neck) of a limb."""
    c0, _ = JOINTS[part]
    return apply(transforms["Torso"], c0)


def corners(part: str, transform: Transform) -> list[Vec]:
    sx, sy, sz = SIZES[part]
    return [
        apply(transform, (x * sx / 2, y * sy / 2, z * sz / 2))
        for x, y, z in product((-1, 1), repeat=3)
    ]


def lowest_point(part: str, transform: Transform) -> Vec:
    return min(corners(part, transform), key=lambda p: p[1])


def lowest_y(
    sample: dict[str, Pose], parts: tuple[str, ...] = PARTS, root: Transform | None = None
) -> float:
    tf = part_transforms(sample, root=root)
    return min(lowest_point(p, tf[p])[1] for p in parts)


def root_transform(root_pose: Pose) -> Transform:
    """Root transform for a character standing at the origin with a Root-track pose applied."""
    return compose(translate((0.0, ROOT_REST_Y, 0.0)), pose_transform(root_pose))
