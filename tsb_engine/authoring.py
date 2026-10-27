"""Authoring helpers for long choreographies (ultimates): short pose keys, tremble, attach, lying poses.

Still explicit: nothing here moves a body part unless you call it.
"""

from __future__ import annotations

import math

from .kinematics import apply, corners, part_transforms
from .mathutil import mat_vec, transpose
from .model import ROOT, Animation, Pose
from .moves import torso_pose
from .scene import Character

SHORT = {
    "T": "Torso", "H": "Head", "RA": "Right Arm", "LA": "Left Arm",
    "RL": "Right Leg", "LL": "Left Leg", "R": ROOT,
}


def P(rot=(0.0, 0.0, 0.0), pos=(0.0, 0.0, 0.0)) -> Pose:
    return Pose(tuple(pos), tuple(rot))


def K(anim: Animation, frame: int, easing: str = "linear", **parts) -> None:
    """Key several parts at once: ``K(a, 120, T=tp(0.4, -20), H=P((10,0,0)), RA=P((60,0,10)))``.

    Keys: T H RA LA RL LL R(oot). Values: Pose, or a (rot, pos) tuple.
    """
    for short, v in parts.items():
        pose = v if isinstance(v, Pose) else P(*v) if isinstance(v[0], (tuple, list)) else P(v)
        anim.set_key(SHORT[short], frame, pose, easing)


tp = torso_pose


def tremble(anim: Animation, part: str, f0: int, f1: int, rot: float, pos: float = 0.0, period: int = 2) -> None:
    """High-frequency shake around the pose the part already has: alternate +-rot every ``period`` frames."""
    name = SHORT.get(part, part)
    sign = 1.0
    for f in range(f0, f1 + 1, period):
        base = anim.sample_part(name, f)
        anim.set_key(
            name, f,
            Pose(
                (base.pos[0] + sign * pos, base.pos[1], base.pos[2]),
                (base.rot[0] + sign * rot, base.rot[1], base.rot[2] + sign * rot * 0.6),
            ),
            "linear",
        )
        sign = -sign


def point_world(char: Character, part: str, off: tuple[float, float, float], frame: int):
    return apply(char.world_parts(frame)[part], off)


def attach(
    victim: Character, holder: Character, frames, victim_part: str = "Head",
    victim_off=(0.0, 0.0, 0.0), holder_part: str = "Right Arm", holder_off=(0.0, -1.0, 0.0),
    offset_world=(0.0, 0.0, 0.0),
) -> None:
    """Move the victim's Root so ``victim_part`` sits on the holder's hand, frame by frame.

    Orientation (Root rot) is kept as already keyed; only the Root position is solved.
    """
    rb_t = transpose(victim.base_transform()[0])
    for f in frames:
        target = point_world(holder, holder_part, holder_off, f)
        target = (target[0] + offset_world[0], target[1] + offset_world[1], target[2] + offset_world[2])
        cur = point_world(victim, victim_part, victim_off, f)
        d = mat_vec(rb_t, (target[0] - cur[0], target[1] - cur[1], target[2] - cur[2]))
        root = victim.anim.sample_root(f)
        victim.anim.set_key(ROOT, f, Pose((root.pos[0] + d[0], root.pos[1] + d[1], root.pos[2] + d[2]), root.rot), "linear")


def lying_root_rot(char: Character, head_dir_world, face_down: bool = True) -> tuple[float, float, float]:
    """Root rotation that lays the body flat with its head pointing along ``head_dir_world`` = (x, z)."""
    from .mathutil import compose, translate
    from .kinematics import ROOT_REST_Y, pose_transform

    rx = -90.0 if face_down else 90.0
    best, best_err = (rx, 0.0, 0.0), 1e9
    for ry in range(0, 360, 5):
        root = compose(char.base_transform(), compose(translate((0.0, ROOT_REST_Y, 0.0)), pose_transform(Pose((0, 0, 0), (rx, float(ry), 0.0)))))
        tf = part_transforms({}, root=root)
        dx, dz = tf["Head"][1][0] - tf["Torso"][1][0], tf["Head"][1][2] - tf["Torso"][1][2]
        n = math.hypot(dx, dz) or 1.0
        err = math.hypot(dx / n - head_dir_world[0], dz / n - head_dir_world[1])
        if err < best_err:
            best, best_err = (rx, float(ry), 0.0), err
    return best


def rest_on_ground(char: Character, frames, clearance: float = 0.0) -> None:
    """Lower/raise the Root so the lowest body point touches the ground (for lying/kneeling poses)."""
    for f in frames:
        tf = char.world_parts(f)
        low = min(min(c[1] for c in corners(p, t)) for p, t in tf.items())
        root = char.anim.sample_root(f)
        char.anim.set_key(ROOT, f, Pose((root.pos[0], root.pos[1] - low + clearance, root.pos[2]), root.rot), "linear")


def keep_above_ground(char: Character, frames, clearance: float = 0.0) -> None:
    """Raise the Root of frames where a part dips below the ground (never lowers it)."""
    for f in frames:
        tf = char.world_parts(f)
        low = min(min(c[1] for c in corners(p, t)) for p, t in tf.items())
        if low < clearance:
            root = char.anim.sample_root(f)
            char.anim.set_key(ROOT, f, Pose((root.pos[0], root.pos[1] + clearance - low, root.pos[2]), root.rot), "linear")
