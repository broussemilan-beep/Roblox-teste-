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
SOLE_REACH = 0.5  # fraction of the sole (per axis) that must clear the floor
SOLE_TOL = 0.03  # studs a planted foot may sink before the leg tilts


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
    """Leg pose that leans towards the (x, z) of ``target`` until the inner sole sits at the
    target height (0 when planted; the swing height otherwise).

    A hip higher than the leg can reach leaves the leg straight (foot slightly above the ground).
    """
    root = root_transform(anim.sample_root(frame))
    base_sample = anim.sample(frame)
    tf = part_transforms(base_sample, root=root)
    hip = joint_world_position(leg, tf)
    torso_rot_t = transpose(tf["Torso"][0])
    want = target[1]

    hx, hz = target[0] - hip[0], target[2] - hip[2]
    norm = math.hypot(hx, hz)
    if norm < 1e-9:
        hx, hz, norm = SIDE[leg], 0.0, 1.0
    hx, hz = hx / norm, hz / norm

    def pose_for(theta_deg: float) -> Pose:
        th = math.radians(theta_deg)
        rx, rz = _angles((math.sin(th) * hx, -math.cos(th), math.sin(th) * hz), torso_rot_t)
        return Pose(rot=(rx, 0.0, rz))

    def sole_y(theta_deg: float) -> float:
        """Height (above the wanted one) of the lowest point of the inner half of the sole."""
        sample = dict(base_sample)
        sample[leg] = pose_for(theta_deg)
        tfl = part_transforms(sample, root=root)[leg]
        sy = -SIZES[leg][1] / 2
        hx_, hz_ = SIZES[leg][0] * SOLE_REACH / 2, SIZES[leg][2] * SOLE_REACH / 2
        return min(apply(tfl, (sx, sy, sz))[1] for sx in (-hx_, hx_) for sz in (-hz_, hz_)) - want

    # The foot is a rigid box: tilting the leg digs the sole edge into the floor. Contact is taken
    # on the inner half of the sole (0.25 stud from its centre), so the outer edge dips by at most
    # 0.25*sin(tilt) while the leg does not pop when the hip crosses 2 studs.
    if sole_y(0.0) >= -SOLE_TOL:
        return pose_for(0.0)
    t, prev = 0.0, 0.0
    while t < 88.0:
        prev, t = t, t + 1.0
        if sole_y(t) >= -SOLE_TOL:
            lo, hi = prev, t
            for _ in range(14):
                mid = (lo + hi) / 2
                if sole_y(mid) >= -SOLE_TOL:
                    hi = mid
                else:
                    lo = mid
            return pose_for(hi)
    return pose_for(88.0)


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
