"""Reference animations built with the engine, used by tests and as usage examples.

``heavy_punch`` is a worked example of the workflow (block -> plant legs -> lint), NOT a
canonical "TSB animation". Its numbers are starting values, not measurements.

Conventions: character faces -Z; rx > 0 swings a limb forward; ry < 0 on the torso winds the
right shoulder back (towards +Z); ``Pose.pos`` z < 0 pushes a limb forward.
"""

from __future__ import annotations

from tsb_engine.model import Animation, Pose
from tsb_engine.moves import bake_planted_legs, torso_pose


def _key(anim: Animation, part: str, frame: int, rot=(0, 0, 0), pos=(0, 0, 0), easing="linear"):
    anim.set_key(part, frame, Pose(tuple(pos), tuple(rot)), easing)


def heavy_punch() -> Animation:
    a = Animation("heavy_punch", fps=60, archetype="heavy", striker="Right Arm")
    a.events = {"windup": 14, "impact": 16, "hitstop": [16, 22]}

    # Torso: guard stance -> coil (keeps compressing: moving hold) -> 2-frame snap -> follow-through
    t = a.set_key
    t("Torso", 0, torso_pose(drop=0.30, pitch=4, yaw=-10), "quad_out")
    t("Torso", 12, torso_pose(drop=0.45, pitch=10, yaw=-55), "linear")
    t("Torso", 14, torso_pose(drop=0.52, pitch=12, yaw=-62), "linear")  # windup (still compressing)
    t("Torso", 15, torso_pose(drop=0.40, pitch=16, yaw=-10), "linear")
    t("Torso", 16, torso_pose(drop=0.35, pitch=18, yaw=42), "linear")  # impact
    t("Torso", 22, torso_pose(drop=0.35, pitch=18, yaw=45), "cubic_out")  # hitstop drift
    t("Torso", 28, torso_pose(drop=0.33, pitch=14, yaw=52), "sine_inout")  # overshoot
    t("Torso", 40, torso_pose(drop=0.30, pitch=6, yaw=18), "sine_inout")
    t("Torso", 55, torso_pose(drop=0.30, pitch=4, yaw=-10), "linear")

    # Striking arm: cocked back, then snaps 90 deg forward with a brief dislocation
    _key(a, "Right Arm", 0, rot=(15, 0, -5), easing="quad_out")
    _key(a, "Right Arm", 12, rot=(-25, 0, -8))
    _key(a, "Right Arm", 14, rot=(-38, 0, -10), pos=(0, 0, 0.2))
    _key(a, "Right Arm", 15, rot=(-36, 0, -10), pos=(0, 0, 0.2))
    _key(a, "Right Arm", 16, rot=(90, 0, 0), pos=(0, 0, -0.9))  # impact
    _key(a, "Right Arm", 18, rot=(91, 0, 0), pos=(0, 0, -0.9))
    _key(a, "Right Arm", 19, rot=(92, 0, 0), pos=(0, 0, -0.15))
    _key(a, "Right Arm", 22, rot=(94, 0, 0), easing="cubic_out")
    _key(a, "Right Arm", 28, rot=(104, 0, 4), easing="sine_inout")
    _key(a, "Right Arm", 45, rot=(25, 0, -5), easing="sine_inout")
    _key(a, "Right Arm", 55, rot=(15, 0, -5))

    # Opposite arm: guard that is thrown back as a counterweight
    _key(a, "Left Arm", 0, rot=(55, 0, 20), easing="quad_out")
    _key(a, "Left Arm", 12, rot=(45, 0, 22))
    _key(a, "Left Arm", 14, rot=(60, 0, 28))
    _key(a, "Left Arm", 16, rot=(-40, 0, -12))
    _key(a, "Left Arm", 22, rot=(-44, 0, -14), easing="cubic_out")
    _key(a, "Left Arm", 40, rot=(30, 0, 14), easing="sine_inout")
    _key(a, "Left Arm", 55, rot=(55, 0, 20))

    # Head: keeps looking at the target while the torso winds back, then lags the snap
    _key(a, "Head", 0, rot=(0, 8, 0), easing="quad_out")
    _key(a, "Head", 14, rot=(0, 58, 0))
    _key(a, "Head", 16, rot=(0, 58, 0))
    _key(a, "Head", 17, rot=(0, -12, 0), easing="cubic_out")
    _key(a, "Head", 24, rot=(-8, -34, 0), easing="sine_inout")
    _key(a, "Head", 40, rot=(0, -14, 0), easing="sine_inout")
    _key(a, "Head", 55, rot=(0, 8, 0))

    # Legs: asymmetric guard stance, feet held in world space for the whole move
    bake_planted_legs(a, 0, 55, lateral=0.5, front_leg="Left Leg", stance_yaw=0)
    return a


def robotic_punch() -> Animation:
    """Everything the linter should complain about: slow, stiff, symmetric, in unison."""
    a = Animation("robotic_punch", fps=60, archetype="heavy", striker="Right Arm")
    a.events = {"windup": 0, "impact": 10}
    for part, start, end in (
        ("Torso", Pose(), Pose(rot=(0, 5, 0))),
        ("Head", Pose(), Pose(rot=(0, 5, 0))),
        ("Right Arm", Pose(rot=(0, 0, 0)), Pose(rot=(90, 0, 0))),
        ("Left Arm", Pose(rot=(0, 0, 0)), Pose(rot=(90, 0, 0))),
    ):
        a.set_key(part, 0, start, "linear")
        a.set_key(part, 10, end, "linear")
    return a


def clipping_crouch() -> Animation:
    """Torso dropped without re-planting the legs: feet go through the floor."""
    a = Animation("clipping_crouch", fps=60, archetype="light")
    a.set_key("Torso", 0, torso_pose(drop=0.0), "linear")
    a.set_key("Torso", 12, torso_pose(drop=0.6), "linear")
    return a
