"""Explicit pose helpers (no hidden automation).

Each helper returns plain ``Pose`` objects that you place on tracks yourself, so every
animation decision stays visible and editable.
"""

from __future__ import annotations

import math

from .kinematics import (
    LEG_LENGTH,
    joint_world_position,
    lowest_point,
    part_transforms,
)
from .mathutil import Vec, mat_vec, rot_y, transpose
from .model import Animation, Pose


def torso_pose(drop: float = 0.0, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0) -> Pose:
    """Torso relative to the root. ``drop`` lowers the centre of mass (studs, >= 0).

    ``pitch`` is rx: **negative leans the torso forward** (towards -Z), positive leans it back.
    (For hanging limbs such as arms and legs the opposite holds: rx > 0 swings forward.)
    """
    return Pose(pos=(0.0, -drop, 0.0), rot=(pitch, yaw, roll))


def plant_legs(
    torso: Pose,
    lateral: float = 0.0,
    front_leg: str | None = None,
    stance_yaw: float = 0.0,
    ground_y: float = 0.0,
    anchors: dict[str, tuple[float, float]] | None = None,
) -> dict[str, Pose]:
    """Leg poses that keep both feet on the ground for a given torso pose.

    Legs are rigid 2-stud blocks hinged at the hips, so when the torso drops they must
    tilt. This solves the tilt (pure trigonometry, then a short numeric refinement so the
    lowest leg corner touches the ground instead of dipping through it).

    ``lateral``    – sideways spread budget per foot, in studs, measured from each hip.
    ``front_leg``  – "Right Leg" / "Left Leg" puts that foot forward (-Z) and the other
                     back; ``None`` spreads both feet sideways only.
    ``stance_yaw`` – rotates the stance around Y (degrees), e.g. to square up to a target.
    ``anchors``    – optional world (x, z) per leg (see :func:`foot_anchors`). When given, each
                     foot is placed on the reachable circle at the point nearest its anchor,
                     which keeps the feet from sliding while the torso rotates.
    """
    if front_leg not in (None, "Right Leg", "Left Leg"):
        raise ValueError("front_leg must be None, 'Right Leg' or 'Left Leg'")
    base = part_transforms({"Torso": torso})
    torso_rot_t = transpose(base["Torso"][0])
    stance_rot = rot_y(stance_yaw)
    result: dict[str, Pose] = {}

    for leg, side in (("Right Leg", 1.0), ("Left Leg", -1.0)):
        hip = joint_world_position(leg, base)
        target_y = ground_y
        pose = Pose()
        for _ in range(12):
            dy = hip[1] - target_y
            if dy > LEG_LENGTH + 1e-9:
                raise ValueError(
                    f"{leg}: hip is {dy:.2f} studs above the target, longer than the leg "
                    f"({LEG_LENGTH}). Lower the torso (drop) or raise the ground."
                )
            reach = math.sqrt(max(LEG_LENGTH**2 - dy * dy, 0.0))
            if front_leg is None:
                lat, fwd = reach, 0.0
            else:
                lat = min(lateral, reach)
                forward = math.sqrt(max(reach * reach - lat * lat, 0.0))
                fwd = -forward if leg == front_leg else forward
            if anchors is not None and leg in anchors:
                hx, hz = anchors[leg][0] - hip[0], anchors[leg][1] - hip[2]
                norm = math.hypot(hx, hz)
                if norm < 1e-9:
                    hx, hz, norm = side, 0.0, 1.0
                horizontal: Vec = (hx / norm * reach, 0.0, hz / norm * reach)
            else:
                horizontal = mat_vec(stance_rot, (side * lat, 0.0, fwd))
            d_world: Vec = (horizontal[0], -dy, horizontal[2])
            dx, dyl, dz = mat_vec(torso_rot_t, d_world)
            n = math.sqrt(dx * dx + dyl * dyl + dz * dz)
            dx, dyl, dz = dx / n, dyl / n, dz / n
            rz = math.degrees(math.asin(max(-1.0, min(1.0, dx))))
            rx = math.degrees(math.atan2(-dz, -dyl))
            pose = Pose(rot=(rx, 0.0, rz))
            sample = {"Torso": torso, leg: pose}
            y_min = lowest_point(leg, part_transforms(sample)[leg])[1]
            err = ground_y - y_min
            if abs(err) < 1e-4:
                break
            target_y += err
        result[leg] = pose
    return result


def foot_anchors(torso: Pose, legs: dict[str, Pose]) -> dict[str, tuple[float, float]]:
    """World (x, z) of each planted foot for a given torso + leg solution."""
    tf = part_transforms({"Torso": torso, **legs})
    out = {}
    for leg in ("Right Leg", "Left Leg"):
        p = lowest_point(leg, tf[leg])
        out[leg] = (p[0], p[2])
    return out


def bake_planted_legs(
    anim: Animation,
    start: int,
    end: int,
    lateral: float = 0.0,
    front_leg: str | None = None,
    stance_yaw: float = 0.0,
) -> None:
    """Write one leg key per frame in [start, end] that keeps both feet planted.

    The stance (foot positions) is solved once at ``start`` from the torso pose there, then
    held in world space while the torso moves. Call it *after* the torso track is keyed.
    """
    ref = anim.sample_part("Torso", start)
    anchors = foot_anchors(ref, plant_legs(ref, lateral, front_leg, stance_yaw))
    for frame in range(start, end + 1):
        legs = plant_legs(anim.sample_part("Torso", frame), anchors=anchors)
        for leg, pose in legs.items():
            anim.set_key(leg, frame, pose, "linear")
