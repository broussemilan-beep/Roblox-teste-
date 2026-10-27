"""Limb solving and combat-pose helpers: aim a limb at a world point, make a contact reachable, dislocate, breakdown.

Poses written by guessing joint angles drift: a kick that should land on the dummy's chest ends up a stud short, or the
hand passes through the torso. These helpers solve the *contact* (a limb tip must touch a world point) with the same
forward kinematics the viewer uses, so the key pose is right at the frame that matters, and then the animator shapes
everything around it (anticipation, kinetic chain, overshoot).

Conventions follow ``authoring.py``: limb rotations are in the torso frame (rx > 0 swings a hanging limb forward).
"""

from __future__ import annotations

import math

from .kinematics import JOINTS, SIZES, apply, compose, pose_transform
from .mathutil import Vec, mat_vec, transpose, translate, vneg
from .model import ROOT, Animation, Pose
from .scene import Character

LIMB_NAMES = {"RA": "Right Arm", "LA": "Left Arm", "RL": "Right Leg", "LL": "Left Leg"}


def limb_tip_from_torso(torso_tf, part: str, rot: Vec, pos: Vec = (0.0, 0.0, 0.0), tip: Vec | None = None) -> Vec:
    """World position of a limb's far-face centre (or ``tip`` in the limb frame) for a rotation, given the torso transform."""
    c0, c1 = JOINTS[part]
    t = compose(torso_tf, translate(c0))
    t = compose(t, pose_transform(Pose(pos, rot)))
    t = compose(t, translate(vneg(c1)))
    return apply(t, tip if tip is not None else (0.0, -SIZES[part][1] / 2, 0.0))


def aim_limb(char: Character, frame: int, part: str, target: Vec, hint: tuple[float, float] = (60.0, 0.0), twist: float = 0.0,
             tip: Vec | None = None) -> tuple[Pose, float]:
    """(rx, rz) of ``part`` that put its tip closest to ``target`` at ``frame``; returns (pose, residual in studs).

    Search is a coarse grid, then a shrinking pattern search; ties go to the solution nearest to ``hint`` (rx, rz).
    """
    torso = char.world_parts(frame)["Torso"]

    def cost(rx: float, rz: float) -> float:
        p = limb_tip_from_torso(torso, part, (rx, twist, rz), tip=tip)
        d = math.dist(p, target)
        return d + 0.0008 * (abs(rx - hint[0]) + abs(rz - hint[1]))

    best = (1e9, hint[0], hint[1])
    for rx in range(-180, 181, 12):
        for rz in range(-150, 151, 12):
            c = cost(rx, rz)
            if c < best[0]:
                best = (c, float(rx), float(rz))
    _, rx, rz = best
    step = 6.0
    while step > 0.2:
        improved = False
        for dx, dz in ((step, 0), (-step, 0), (0, step), (0, -step), (step, step), (-step, -step), (step, -step), (-step, step)):
            c = cost(rx + dx, rz + dz)
            if c < cost(rx, rz) - 1e-9:
                rx, rz, improved = rx + dx, rz + dz, True
                break
        if not improved:
            step /= 2
    p = limb_tip_from_torso(torso, part, (rx, twist, rz), tip=tip)
    return Pose((0.0, 0.0, 0.0), (rx, twist, rz)), math.dist(p, target)


def reach_root(char: Character, frame: int, part: str, target: Vec, hint: tuple[float, float] = (60.0, 0.0), twist: float = 0.0,
               tip: Vec | None = None, iters: int = 6, tol: float = 0.06) -> tuple[Pose, float]:
    """Solve ``part`` at ``frame`` to touch ``target``; when it cannot reach, slide the character's Root toward it and retry.

    The torso/root orientation must already be keyed at ``frame``. Returns the limb pose and the final residual.
    """
    rb_t = transpose(char.base_transform()[0])
    pose, res = aim_limb(char, frame, part, target, hint, twist, tip)
    for _ in range(iters):
        if res <= tol:
            break
        cur = limb_tip_from_torso(char.world_parts(frame)["Torso"], part, pose.rot, tip=tip)
        d = mat_vec(rb_t, (target[0] - cur[0], target[1] - cur[1], target[2] - cur[2]))
        root = char.anim.sample_root(frame)
        char.anim.set_key(ROOT, frame, Pose((root.pos[0] + d[0] * 0.8, root.pos[1] + d[1] * 0.8, root.pos[2] + d[2] * 0.8), root.rot), "linear")
        pose, res = aim_limb(char, frame, part, target, hint, twist, tip)
    return pose, res


def tip_world(char: Character, frame: int, part: str, tip: Vec | None = None) -> Vec:
    return apply(char.world_parts(frame)[part], tip if tip is not None else (0.0, -SIZES[part][1] / 2, 0.0))


def dislocate(anim: Animation, part: str, f_hit: int, offset: Vec, settle: int = 3, over: float = 0.2, pre: int = 1) -> None:
    """'Deboitement': the limb block slides out along ``offset`` (parent frame, studs) for ~2 frames at the hit, then re-seats.

    Needs the limb already keyed at ``f_hit``. Keys: ``f_hit - pre`` (rest), ``f_hit`` (offset), ``f_hit + 2`` (offset),
    ``f_hit + 2 + settle`` (re-seated with a small overshoot opposite to the offset). Keep |offset| <= ~1.5 studs.
    """
    base = anim.sample_part(part, f_hit)
    anim.set_key(part, f_hit - pre, Pose(base.pos, anim.sample_part(part, f_hit - pre).rot), "linear")
    anim.set_key(part, f_hit, Pose(tuple(base.pos[i] + offset[i] for i in range(3)), base.rot), "constant")
    anim.set_key(part, f_hit + 2, Pose(tuple(base.pos[i] - offset[i] * over for i in range(3)), base.rot), "quad_out")
    anim.set_key(part, f_hit + 2 + settle, Pose(base.pos, base.rot), "linear")


def moving_hold(anim: Animation, part: str, f0: int, f1: int, drift: Vec = (3.0, 0.0, 1.0)) -> None:
    """Never freeze a held pose: insert a key halfway that drifts the rotation a few degrees (then the end key stays)."""
    a, b = anim.sample_part(part, f0), anim.sample_part(part, f1)
    mid = (f0 + f1) // 2
    anim.set_key(part, mid, Pose(tuple((a.pos[i] + b.pos[i]) / 2 for i in range(3)), tuple((a.rot[i] + b.rot[i]) / 2 + drift[i] for i in range(3))), "sine_inout")


def chain(anim: Animation, f: int, easing: str = "linear", lags: dict[str, int] | None = None, **parts) -> None:
    """Key parts for the pose at ``f`` but let each follow the torso by its own lag: kinetic chain / overlap.

    Default lags (frames at 60 fps): head +2, arms +1, legs 0. ``lags`` overrides. Keys use authoring short names.
    """
    from .authoring import SHORT, P

    base = {"T": 0, "R": 0, "H": 2, "RA": 1, "LA": 2, "RL": 0, "LL": 0}
    if lags:
        base.update(lags)
    for short, v in parts.items():
        pose = v if isinstance(v, Pose) else P(*v) if isinstance(v[0], (tuple, list)) else P(v)
        anim.set_key(SHORT[short], f + base.get(short, 0), pose, easing)
