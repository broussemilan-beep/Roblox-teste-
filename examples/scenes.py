"""Scenes shown in the viewer: an attacker and a victim reacting to the hit."""

from __future__ import annotations

from tsb_engine.model import ROOT, Animation, Pose
from tsb_engine.moves import bake_planted_legs, torso_pose
from tsb_engine.scene import Character, Scene

from .builders import heavy_punch

VICTIM_COLORS = {
    "Torso": "#d6453d",
    "Head": "#f2c94c",
    "Right Arm": "#f2c94c",
    "Left Arm": "#f2c94c",
    "Right Leg": "#3b3f4a",
    "Left Leg": "#3b3f4a",
}


def _k(a: Animation, part: str, frame: int, rot=(0, 0, 0), pos=(0, 0, 0), easing="linear"):
    a.set_key(part, frame, Pose(tuple(pos), tuple(rot)), easing)


def gut_fold_victim(impact: int = 16) -> Animation:
    """Victim hit in the stomach: folds around the fist, hangs, is thrown back, skids, recovers.

    The victim faces local -Z like every character; the scene turns it to face the attacker.
    Root +Z = knockback direction (away from the attacker).
    """
    a = Animation("victim_gut_fold", fps=60, archetype="reaction")
    i = impact
    t = a.set_key

    # Torso: guard -> fold at contact -> held (moving) -> flung back -> hunched landing -> recover
    t("Torso", 0, torso_pose(drop=0.25, pitch=-3), "sine_inout")
    t("Torso", i - 5, torso_pose(drop=0.28, pitch=-4), "linear")
    t("Torso", i - 1, torso_pose(drop=0.26, pitch=-3), "linear")
    t("Torso", i, Pose((0, -0.45, 0.35), (-40, 0, 0)), "cubic_out")  # folds forward around the fist
    t("Torso", i + 6, Pose((0, -0.5, 0.45), (-46, 0, 3)), "quad_in")  # hitstop drift
    t("Torso", i + 12, Pose((0, -0.2, 0.0), (22, 0, 4)), "linear")  # flung: body arches back
    t("Torso", i + 22, Pose((0, -0.2, 0.0), (16, 0, 2)), "linear")
    t("Torso", i + 24, torso_pose(drop=0.55, pitch=-22), "cubic_out")  # lands hunched
    t("Torso", i + 30, torso_pose(drop=0.75, pitch=-30, roll=4), "sine_inout")
    t("Torso", i + 56, torso_pose(drop=0.3, pitch=-6), "sine_inout")
    t("Torso", i + 64, torso_pose(drop=0.25, pitch=-3), "linear")

    # Head lags the fold, snaps back when thrown, nods on landing
    _k(a, "Head", 0, rot=(0, 0, 0), easing="linear")
    _k(a, "Head", i, rot=(0, 0, 0), easing="cubic_out")
    _k(a, "Head", i + 3, rot=(-34, 0, 0), easing="linear")  # drops forward onto the fist
    _k(a, "Head", i + 10, rot=(-38, 0, 4), easing="quad_in")
    _k(a, "Head", i + 14, rot=(30, 0, 0), easing="cubic_out")  # whiplash back
    _k(a, "Head", i + 24, rot=(18, 0, -4), easing="sine_inout")
    _k(a, "Head", i + 30, rot=(-24, 0, 0), easing="sine_inout")
    _k(a, "Head", i + 60, rot=(0, 0, 0))

    # Arms: guard -> flinch around the fist -> flung back -> catch -> guard
    _k(a, "Right Arm", 0, rot=(62, 0, 12))
    _k(a, "Right Arm", i, rot=(62, 0, 12), easing="cubic_out")
    _k(a, "Right Arm", i + 4, rot=(92, 0, 20), easing="quad_in")
    _k(a, "Right Arm", i + 12, rot=(-58, 0, 48), easing="linear")
    _k(a, "Right Arm", i + 24, rot=(-30, 0, 30), easing="cubic_out")
    _k(a, "Right Arm", i + 36, rot=(40, 0, 16), easing="sine_inout")
    _k(a, "Right Arm", i + 64, rot=(62, 0, 12))
    _k(a, "Left Arm", 0, rot=(50, 0, -16))
    _k(a, "Left Arm", i, rot=(50, 0, -16), easing="cubic_out")
    _k(a, "Left Arm", i + 5, rot=(80, 0, -8), easing="quad_in")
    _k(a, "Left Arm", i + 13, rot=(-80, 0, -34), easing="linear")
    _k(a, "Left Arm", i + 26, rot=(-12, 0, -40), easing="cubic_out")
    _k(a, "Left Arm", i + 40, rot=(30, 0, -22), easing="sine_inout")
    _k(a, "Left Arm", i + 64, rot=(50, 0, -16))

    # Root: shake during hitstop, thrown back on an arc, bounce, skid
    _k(a, ROOT, 0, easing="linear")
    shake = [(i + 1, 0.05), (i + 2, -0.05), (i + 3, 0.04), (i + 4, -0.04), (i + 5, 0.03), (i + 6, 0.0)]
    for f, x in shake:
        _k(a, ROOT, f, pos=(x, 0, 0.0))
    _k(a, ROOT, i + 7, pos=(0, 0, 0), easing="expo_out")
    _k(a, ROOT, i + 14, pos=(0, 1.25, 2.6), rot=(14, 0, 0), easing="sine_inout")
    _k(a, ROOT, i + 22, pos=(0, 0.0, 5.0), rot=(0, 0, 0), easing="linear")
    _k(a, ROOT, i + 26, pos=(0, 0.38, 5.5), easing="quad_in")  # ground bounce
    _k(a, ROOT, i + 30, pos=(0, 0.0, 5.9), easing="quad_out")
    _k(a, ROOT, i + 46, pos=(0, 0.0, 6.6))
    _k(a, ROOT, i + 64, pos=(0, 0.0, 6.6))

    # Legs: planted until launch, trail while airborne, planted from the landing on
    bake_planted_legs(a, 0, i + 10, lateral=0.55, front_leg="Right Leg")
    for part, early, mid in (("Right Leg", (38, 0, 8), (-28, 0, 12)), ("Left Leg", (55, 0, -6), (-46, 0, -14))):
        _k(a, part, i + 12, rot=early)
        _k(a, part, i + 17, rot=mid)
    bake_planted_legs(a, i + 19, i + 64, lateral=0.7, front_leg="Left Leg")
    return a


def heavy_punch_hit() -> Scene:
    attacker = Character("Attaquant", heavy_punch())
    impact = attacker.anim.event_frame("impact")
    tip = attacker.limb_tip("Right Arm", impact)
    # victim stands so that its stomach touches the fist at impact, facing the attacker
    victim = Character(
        "Victime",
        gut_fold_victim(impact),
        base_pos=(tip[0], 0.0, tip[2] - 0.5),
        base_yaw=180.0,
        colors=VICTIM_COLORS,
    )
    return Scene(
        "Coup lourd — réaction de la victime",
        [attacker, victim],
        events={"windup": attacker.anim.event_frame("windup"), "impact": impact, "hitstop": attacker.anim.events["hitstop"]},
    )


def _ultimate() -> Scene:
    from .ultimate import build

    return build()


SCENES = {"heavy_punch_hit": heavy_punch_hit, "berserker_ultimate": _ultimate}
