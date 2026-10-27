"""Footwork: planted feet and real steps for rigid R6 legs.

R6 legs are rigid 2-stud blocks hinged at the hips, so a foot can only touch the ground on a
circle around the hip (radius depends on hip height). Consequences handled here:

* **Planted foot**: stays at a ground anchor; it is pulled to the nearest point of its reachable
  circle, so a hip that moves away makes the foot slide. Avoid that by *stepping*.
* **Step**: a foot leaves the ground, swings along a small arc and lands on a new anchor.
  Use steps for lunges, dashes and runs instead of letting feet skate or teleport.

All coordinates are ground (x, z) in the character's base frame (the frame the Root track uses).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .kinematics import (
    LEG_LENGTH,
    SIZES,
    joint_world_position,
    lowest_point,
    part_transforms,
    root_transform,
)
from .mathutil import Vec, apply, mat_vec, transpose
from .model import Animation, Pose

LEGS = ("Right Leg", "Left Leg")
SIDE = {"Right Leg": 1.0, "Left Leg": -1.0}


@dataclass(frozen=True)
class Step:
    leg: str
    t0: int  # frame the foot leaves the ground
    t1: int  # frame it lands
    to: tuple[float, float]  # landing anchor (x, z)
    lift: float = 0.5  # peak foot height during the swing, in studs


def _smooth(u: float) -> float:
    return u * u * (3 - 2 * u)


def foot_target(
    leg: str, frame: int, initial: dict[str, tuple[float, float]], steps: list[Step]
) -> tuple[Vec, bool]:
    """(world target, planted?) of a foot at ``frame`` (base frame)."""
    pos = initial[leg]
    for s in sorted((s for s in steps if s.leg == leg), key=lambda s: s.t0):
        if frame < s.t0:
            break
        if frame >= s.t1:
            pos = s.to
            continue
        u = (frame - s.t0) / (s.t1 - s.t0)
        e = _smooth(u)
        return (
            (pos[0] + (s.to[0] - pos[0]) * e, s.lift * math.sin(math.pi * u), pos[1] + (s.to[1] - pos[1]) * e),
            False,
        )
    return (pos[0], 0.0, pos[1]), True


def _angles(d_world: Vec, torso_rot_t) -> tuple[float, float]:
    dx, dy, dz = mat_vec(torso_rot_t, d_world)
    n = math.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / n, dy / n, dz / n
    rz = math.degrees(math.asin(max(-1.0, min(1.0, dx))))
    rx = math.degrees(math.atan2(-dz, -dy))
    return rx, rz


def solve_leg(anim: Animation, leg: str, frame: int, target: Vec, planted: bool) -> Pose:
    """Leg pose whose foot sits at ``target`` height (0 when planted) and heads towards its (x, z).

    The leg is rigid, so the foot is always 2 studs from the hip: the target's height fixes how
    far away horizontally it can be (reach); the target's x/z only gives the direction.
    A planted foot is pulled to touch the ground exactly; a swinging foot is only kept from
    going through it.
    """
    root = root_transform(anim.sample_root(frame))
    base_sample = anim.sample(frame)
    tf = part_transforms(base_sample, root=root)
    hip = joint_world_position(leg, tf)
    torso_rot_t = transpose(tf["Torso"][0])

    foot_y = target[1]
    pose = Pose()
    for _ in range(12):
        dy = hip[1] - foot_y
        reach = math.sqrt(max(LEG_LENGTH**2 - dy * dy, 0.0))
        hx, hz = target[0] - hip[0], target[2] - hip[2]
        norm = math.hypot(hx, hz)
        if norm < 1e-9:
            hx, hz, norm = SIDE[leg], 0.0, 1.0
        d_world = (hx / norm * reach, -dy, hz / norm * reach)
        rx, rz = _angles(d_world, torso_rot_t)
        pose = Pose(rot=(rx, 0.0, rz))
        sample = dict(base_sample)
        sample[leg] = pose
        y_min = lowest_point(leg, part_transforms(sample, root=root)[leg])[1]
        err = -y_min  # > 0: a corner is below the ground
        if (planted and abs(err) < 1e-4) or (not planted and err < 1e-4):
            break
        foot_y += err
    return pose


def _sole_xz(anim: Animation, leg: str, frame: int, pose: Pose) -> tuple[float, float]:
    sample = anim.sample(frame)
    sample[leg] = pose
    tf = part_transforms(sample, root=root_transform(anim.sample_root(frame)))
    p = apply(tf[leg], (0.0, -SIZES[leg][1] / 2, 0.0))
    return (p[0], p[2])


def bake_footwork(
    anim: Animation,
    initial: dict[str, tuple[float, float]],
    steps: list[Step],
    start: int,
    end: int,
) -> None:
    """Write one key per frame for both legs. Call after Torso and Root are keyed.

    ``initial`` anchors are first snapped onto each foot's reachable circle at ``start`` so the
    feet do not slide in the first frames.
    """
    settled = {}
    for leg in LEGS:
        target = (initial[leg][0], 0.0, initial[leg][1])
        settled[leg] = _sole_xz(anim, leg, start, solve_leg(anim, leg, start, target, True))
    for frame in range(start, end + 1):
        for leg in LEGS:
            target, planted = foot_target(leg, frame, settled, steps)
            anim.set_key(leg, frame, solve_leg(anim, leg, frame, target, planted), "linear")


def sole_positions(anim: Animation, frame: int) -> dict[str, Vec]:
    """Base-frame position of each foot's sole centre (stable, unlike the lowest corner)."""
    tf = part_transforms(anim.sample(frame), root=root_transform(anim.sample_root(frame)))
    return {leg: apply(tf[leg], (0.0, -SIZES[leg][1] / 2, 0.0)) for leg in LEGS}


def gait_steps(
    anim: Animation,
    start: int,
    end: int,
    first_leg: str = "Right Leg",
    interval: int = 7,
    swing: int = 6,
    lateral: float = 0.55,
    lift: float = 0.7,
) -> list[Step]:
    """Alternate steps for a run/dash along the Root track's horizontal path.

    Each foot lands ahead of the hip by about its ground reach, so the hips pass over it before
    the next step. ``interval`` is frames between consecutive steps (either foot).
    """
    steps: list[Step] = []
    leg = first_leg
    f = start
    while f + swing <= end:
        t1 = f + swing
        a = anim.sample_root(t1).pos
        b = anim.sample_root(min(t1 + interval, end)).pos
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = math.hypot(dx, dz) or 1.0
        dx, dz = dx / n, dz / n
        tf = part_transforms(anim.sample(t1), root=root_transform(anim.sample_root(t1)))
        h = joint_world_position(leg, tf)[1]
        reach = math.sqrt(max(LEG_LENGTH**2 - h * h, 0.0))
        side = SIDE[leg]
        px, pz = -dz, dx  # perpendicular (left of travel); sign fixed by side below
        tx = a[0] + dx * reach * 0.9 + (px * -side) * lateral
        tz = a[2] + dz * reach * 0.9 + (pz * -side) * lateral
        steps.append(Step(leg, f, t1, (tx, tz), lift))
        leg = "Left Leg" if leg == "Right Leg" else "Right Leg"
        f += interval
    return steps
