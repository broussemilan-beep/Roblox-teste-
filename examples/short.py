"""A ~11 s monochrome combat short at the level of a hand-animated Roblox reel.

Original choreography, built with the method in docs/analysis/method-comparison.md:

* **pose-to-pose with solved contacts** - every strike is keyed on its extreme pose and the striking limb is *solved*
  onto the victim (``solver.reach_root``) instead of guessed, then shaped by anticipation, a kinetic chain (torso first,
  head and arms late), a dislocation at the hit and a moving hold;
* **camera that frames the fight** - ``autoframe`` keeps both bodies large in shot, 3/4 angles, plus macro whip-ins;
* **the reference's graphic punctuation** - ink smears, speed streaks, comic stars, b/w impact frames, black frames;
* **secondary motion** - coat, hair and hat never stop.

Authored at 60 fps and shown on a 30 fps clock (``Scene.hold = 2``). World: the hero starts at the origin facing -Z, the
dummy stands at z = -9 facing him. Body positions are world torso centres: ``hroot(x, h, z)`` / ``droot(x, h, z)``.
"""

from __future__ import annotations

import math
import random

from tsb_engine.authoring import K, P, char_points, keep_above_ground, tp, tremble
from tsb_engine.cinematic import Cinematic, autoframe, dolly, tracking
from tsb_engine.footwork import bake_footwork
from tsb_engine.kinematics import apply
from tsb_engine.model import ROOT, Animation, Pose
from tsb_engine.scene import Character, Scene
from tsb_engine.secondary import coat_and_hair
from tsb_engine.solver import dislocate, moving_hold, reach_root

N_FRAMES = 660
DUMMY_Z = -9.0
INK = "#0b0b0f"
HERO_COLORS = {"Torso": "#2b2b34", "Head": "#e9eef2", "Right Arm": "#1d1d25", "Left Arm": "#1d1d25", "Right Leg": "#16161c", "Left Leg": "#16161c"}
DUMMY_COLORS = {k: "#ececf0" for k in HERO_COLORS}
CYAN = "#7ff0ff"
SHORT = {"Right Arm": "RA", "Left Arm": "LA", "Right Leg": "RL", "Left Leg": "LL"}


def hroot(x: float, h: float, z: float):
    """Hero Root offset that puts the torso centre at world (x, h, z)."""
    return (x, h - 3.0, z)


def droot(x: float, h: float, z: float):
    """Dummy Root offset (local frame, base yaw 180) that puts its torso centre at world (x, h, z)."""
    return (-x, h - 3.0, DUMMY_Z - z)


# ------------------------------------------------------------------ dummy
def fly(a: Animation, f0: int, f1: int, p0, p1, apex: float, r0, r1, step: int = 2) -> None:
    """Rigid flight of the dummy between two world points (x, h, z) with a parabolic arc and a steady tumble."""
    for f in range(f0, f1 + 1, step):
        u = (f - f0) / (f1 - f0)
        pos = tuple(p0[i] + (p1[i] - p0[i]) * u for i in range(3))
        h = pos[1] + 4.0 * apex * u * (1.0 - u)
        rot = tuple(r0[i] + (r1[i] - r0[i]) * u for i in range(3))
        K(a, f, "linear", R=P(rot, droot(pos[0], h, pos[2])))


def board(a: Animation, f: int, arms=(30, 30), legs=(0, 0), tilt=8) -> None:
    """The reference's reaction: a stiff board, arms slightly out."""
    K(a, f, "linear", T=tp(0.0, tilt), H=P((0, 0, 0)), RA=P((arms[0], 0, 10)), LA=P((arms[1], 0, -10)), RL=P((legs[0], 0, 3)), LL=P((legs[1], 0, -3)))


def react(a: Animation, t: int, fold: float = -26.0, side: float = 0.0) -> None:
    """Struck at ``t``: the hit region folds first (C shape), the head snaps late, then the body stiffens into a board."""
    K(a, t, "quad_out", T=tp(0.0, fold, side), H=P((10, 0, 0)), RA=P((-30, 0, 24)), LA=P((-40, 0, -24)), RL=P((-14, 0, 3)), LL=P((24, 0, -3)))
    K(a, t + 2, "quad_out", H=P((-34, 0, 0)))  # head lags behind the fold
    K(a, t + 5, "linear", T=tp(0.0, fold * 0.2, side * 0.2), RA=P((40, 0, 18)), LA=P((30, 0, -18)), RL=P((6, 0, 3)), LL=P((10, 0, -3)))
    K(a, t + 8, "sine_inout", H=P((8, 0, 0)))


def dummy_act1(a: Animation) -> None:
    K(a, 0, T=tp(0.0, 0), H=P((0, 0, 0)), RA=P((8, 0, 4)), LA=P((8, 0, -4)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 61, "linear", R=P(pos=(0, 0, 0)), T=tp(0.0, 0))
    react(a, 62, -26)
    fly(a, 62, 104, (0, 3.0, -9.0), (0, 4.4, -19.0), 3.4, (0, 0, 0), (-250, 0, 0))
    react(a, 104, -20)
    fly(a, 106, 122, (0, 4.4, -19.4), (0, 3.4, -23.0), 2.6, (-250, 0, 0), (-400, 0, 0))
    react(a, 122, -30)
    fly(a, 124, 138, (0, 3.4, -23.2), (0, 3.1, -23.4), 3.2, (-400, 0, 0), (-480, 0, 0))
    react(a, 138, -16)
    fly(a, 140, 150, (0, 3.1, -23.6), (0, 9.5, -24.6), 0.0, (-480, 0, 0), (-640, 0, 0))


# ------------------------------------------------------------------ hero
def solve(h: Character, f: int, part: str, target, hint, easing: str = "linear", **keys) -> float:
    """Key the pose ``keys`` at ``f``, then solve ``part`` onto ``target`` (sliding the Root if it is out of reach)."""
    K(h.anim, f, easing, **keys)
    pose, res = reach_root(h, f, part, target, hint)
    K(h.anim, f, easing, **{SHORT[part]: pose})
    return res


def dpoint(d: Character, f: int, part: str, off):
    """World point on the dummy's ``part`` at frame ``f`` (``off`` in the part's local frame; front face is -Z)."""
    return apply(d.world_parts(f)[part], off)


def hero_act1(h: Character, d: Character) -> None:
    a = h.anim
    # ---- B1 (0-49): crouched, gathering. Tremble + moving hold: never frozen
    K(a, 0, T=tp(0.75, -32, 0), H=P((26, 0, 0)), RA=P((26, 0, 12)), LA=P((-24, 0, -12)))
    K(a, 22, "sine_inout", T=tp(0.85, -36, 6), H=P((30, 0, 0)), RA=P((30, 0, 14)), LA=P((-28, 0, -14)))
    K(a, 40, "quad_in", T=tp(0.98, -40, 30), H=P((34, 0, 0)), RA=P((-52, 0, 18)), LA=P((74, 0, -16)))
    K(a, 49, "linear", T=tp(0.98, -40, 30), H=P((34, 0, 0)), RA=P((-56, 0, 18)), LA=P((78, 0, -16)))
    tremble(a, "T", 0, 40, 0.9, 0.0, 3)
    tremble(a, "RA", 1, 41, 2.0, 0.02, 3)
    bake_footwork(a, {"Right Leg": (1.5, 0.3), "Left Leg": (-1.5, 0.3)}, [], 0, 49)
    # ---- B2 (50-61): the hero leaves the stage (never show the travel)
    K(a, 50, "linear", R=P(pos=(0, 0, 0)))
    K(a, 51, "linear", R=P(pos=(0, 0, 60)))
    K(a, 61, "linear", R=P(pos=(0, 0, 60)))

    # ---- C1 (62): re-enters ON the contact: body flat, leg driving into the chest, head up, arms thrown
    chest = dpoint(d, 62, "Torso", (0.0, 0.3, -0.5))
    res = solve(h, 62, "Right Leg", chest, (125, 0), R=P((-78, 0, 0), hroot(0, 4.0, -5.8)), T=tp(0, -8, 0), H=P((62, 0, 0)),
                RA=P((-55, 0, 26)), LA=P((70, 0, -22)), LL=P((-40, 0, -8)))
    dislocate(a, "Right Leg", 62, (0.0, -0.5, 0.0), settle=3)  # the leg block slides out of the hip for two frames
    K(a, 70, "cubic_out", R=P((-76, 0, 0), hroot(0, 3.9, -7.0)), RL=P((125, 0, 0)), LL=P((-50, 0, -8)), RA=P((-30, 0, 20)), LA=P((60, 0, -18)), H=P((50, 0, 0)))
    K(a, 82, "quad_in", R=P((-34, 0, 0), hroot(0, 3.6, -12.0)), T=tp(0.25, -14, 0), H=P((8, 0, 0)), RA=P((22, 0, 20)), LA=P((56, 0, -20)), RL=P((60, 0, 4)), LL=P((20, 0, -6)))
    # ---- C2 (104): spin heel kick (the yaw passes 90 deg at contact so the leg points down -Z) onto the head
    head = dpoint(d, 104, "Head", (0.0, 0.0, -0.5))
    K(a, 94, "linear", R=P((-14, -200, 0), hroot(0, 3.4, -14.8)), T=tp(0.5, -24, 0), H=P((14, 0, 0)), RA=P((40, 0, 18)), LA=P((-30, 0, -16)), RL=P((40, 0, 4)), LL=P((-20, 0, -6)))
    for f, ry in ((98, -200), (100, -110), (102, 0)):
        K(a, f, "linear", R=P((0, ry, 0), hroot(0, 3.5, -16.2 - (104 - f) * -0.2)), T=tp(0.2, 0, 0, 14), H=P((10, 0, 0)), RA=P((0, 0, 110)), LA=P((0, 0, -70)), RL=P((10, 0, 60)), LL=P((0, 0, -4)))
    res2 = solve(h, 104, "Right Leg", head, (95, 0), R=P((0, 90, 0), hroot(0, 4.0, -18.4)), T=tp(0.2, 0, 0, 14), H=P((10, 0, 0)), RA=P((0, 0, 110)), LA=P((0, 0, -70)), LL=P((0, 0, -4)))
    for f, ry in ((106, 170), (108, 250)):
        K(a, f, "linear", R=P((0, ry, 0), hroot(0, 3.9, -19.2 - (f - 104) * 0.2)), T=tp(0.2, 0, 0, 14), RA=P((0, 0, 110)), LA=P((0, 0, -70)), RL=P((10, 0, 100)), LL=P((0, 0, -4)))
    K(a, 114, "linear", R=P((0, 270, 0), hroot(0, 3.3, -21.0)), T=tp(0.5, -25, 0), RL=P((30, 0, 4)), LL=P((-10, 0, -6)), RA=P((30, 0, 10)), LA=P((30, 0, -10)))
    print("act1 residuals", round(res, 3), round(res2, 3))


def hero_act1b(h: Character, d: Character) -> None:
    a = h.anim
    # ---- C3 (122): cartwheel along the travel axis, the hand strikes as it passes under the dummy
    for f, rz, z, hh in ((114, 0, -19.6, 3.0), (117, 40, -20.4, 3.9), (120, 80, -21.2, 4.7), (125, 150, -22.2, 4.2), (128, 190, -23.0, 3.3)):
        K(a, f, "linear", R=P((0, 90, rz), hroot(0, hh, z)), T=tp(0.0, 0, 0), H=P((0, 0, 0)), RA=P((0, 0, 170)), LA=P((0, 0, 165)), RL=P((0, 0, 35)), LL=P((0, 0, -35)))
    res = solve(h, 122, "Right Arm", dpoint(d, 122, "Torso", (0.0, -0.2, 0.0)), (0, 170), R=P((0, 90, 100), hroot(0, 4.8, -21.5)), T=tp(0.0, 0, 0), H=P((0, 0, 0)),
                LA=P((0, 0, 165)), RL=P((0, 0, 35)), LL=P((0, 0, -35)))
    dislocate(a, "Right Arm", 122, (0.0, -0.6, 0.0), settle=3)
    # ---- C4 (138): slide kick from the ground, then he rises
    K(a, 132, "linear", R=P((0, 0, 0), hroot(0, 3.0, -23.0)), T=tp(0.9, -30, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    res2 = solve(h, 138, "Right Leg", dpoint(d, 138, "Torso", (0.0, -0.8, -0.5)), (80, 0), "cubic_out", R=P((60, 0, 0), hroot(0, 2.2, -22.4)), T=tp(0.0, -10, 0),
                 H=P((-20, 0, 0)), RA=P((60, 0, 20)), LA=P((100, 0, -30)), LL=P((-10, 0, -3)))
    K(a, 150, "quad_out", R=P((0, 0, 0), hroot(0, 3.0, -25.5)), T=tp(0.8, -30, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    print("act1b residuals", round(res, 3), round(res2, 3))


JUG_Z = -33.0
CYC = [((0, 0, 0), 5.6, JUG_Z), ((-62, 0, 0), 5.0, JUG_Z - 0.8), ((-22, 0, 0), 5.4, JUG_Z - 0.3)]


def dummy_act2(a: Animation) -> None:
    # launched by C4, he is juggled in place: three poses cycle every 4 frames
    fly(a, 150, 172, (0, 9.5, -24.6), (0, 5.6, JUG_Z), 2.0, (-640, 0, 0), (-720, 0, 0))
    for i, f in enumerate(range(174, 256, 4)):
        rot, hh, z = CYC[i % 3]
        K(a, f, "linear", R=P(rot, droot(0, hh + 0.12 * math.sin(i * 0.9), z)))
        board(a, f, arms=(40 + 9 * math.sin(i * 1.3), 40 + 9 * math.cos(i * 1.1)), tilt=6 + 3 * math.sin(i))
    # finisher: he is driven down and slides across the ground
    fly(a, 258, 276, (0, 5.4, JUG_Z - 0.4), (0, 1.0, -46.0), 0.6, (0, 0, 0), (-90, 0, 0))
    fly(a, 278, 296, (0, 1.0, -46.0), (0, 0.8, -52.0), 0.0, (-90, 0, 0), (-90, 0, 0))
    K(a, 300, "linear", R=P((-90, 0, 0), droot(0, 0.8, -52.0)))
    K(a, 380, "linear", R=P((-90, 0, 0), droot(0, 0.8, -52.0)))


def hero_act2(h: Character, d: Character) -> None:
    a = h.anim
    K(a, 156, "linear", R=P((0, 0, 0), hroot(0, 3.0, -30.2)), T=tp(0.8, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    # juggle: right and left kicks alternate every 4 frames, each solved onto the dummy's lower back, torso leaning back
    for i, f in enumerate(range(176, 256, 4)):
        part, other = ("Right Leg", "Left Leg") if i % 2 == 0 else ("Left Leg", "Right Leg")
        side = -1 if i % 2 == 0 else 1
        keys = dict(R=P((0, 0, 0), hroot(0, 3.5, -30.0 - 0.03 * (f - 176))), T=tp(0.3, 14, 0, 8 * side), H=P((-8, 0, 0)), RA=P((-50 * side, 0, 20)), LA=P((-50 * -side + 12, 0, -20)))
        keys[SHORT[other]] = P((-14, 0, 4 * -side))
        solve(h, f, part, dpoint(d, f, "Torso", (0.0, -0.5, -0.5)), (110, 0), **keys)
    # ---- finisher (262): flying kick, body flat, sends him sliding
    K(a, 256, "linear", R=P((-20, 0, 0), hroot(0, 3.4, -31.0)), T=tp(0.6, -28, 0), RL=P((60, 0, 4)), LL=P((-20, 0, -4)), RA=P((-40, 0, 20)), LA=P((60, 0, -20)))
    res = solve(h, 262, "Right Leg", dpoint(d, 262, "Torso", (0.0, 0.2, -0.5)), (150, 0), "cubic_out", R=P((-82, 0, 0), hroot(0, 5.2, -30.5)), T=tp(0.0, -6, 0), H=P((60, 0, 0)),
                RA=P((-60, 0, 24)), LA=P((120, 0, -22)), LL=P((-30, 0, -6)))
    dislocate(a, "Right Leg", 262, (0.0, -0.6, 0.0), settle=4)
    K(a, 272, "quad_out", R=P((-30, 0, 0), hroot(0, 3.4, -36.5)), T=tp(0.4, -20, 0), RL=P((60, 0, 4)), LL=P((10, 0, -6)))
    K(a, 284, "quad_out", R=P((0, 0, 0), hroot(0, 3.0, -39.0)), T=tp(0.9, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    # ---- lull (300-339): coils at the frame edge, the coat settles
    K(a, 300, "linear", R=P((0, 0, 0), hroot(0, 3.0, -39.0)), T=tp(0.9, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)))
    K(a, 318, "sine_inout", R=P((0, 0, 0), hroot(0, 3.0, -37.5)), T=tp(1.05, -38, 18), H=P((34, 0, 0)), RA=P((-30, 0, 16)), LA=P((60, 0, -16)), RL=P((40, 0, 4)), LL=P((-10, 0, -4)))
    K(a, 338, "quad_in", R=P((0, 0, 0), hroot(0, 3.0, -37.0)), T=tp(1.1, -40, 26), H=P((36, 0, 0)), RA=P((-52, 0, 18)), LA=P((78, 0, -16)), RL=P((40, 0, 4)), LL=P((-10, 0, -4)))
    print("act2 res", round(res, 3))


def hero_act3(h: Character, d: Character) -> None:
    a = h.anim
    # ---- turns to the camera (340): impact frame, then the smirk (hand on the hat brim)
    K(a, 340, "linear", R=P((0, -90, 0), hroot(0, 3.0, -37.0)), T=tp(0.1, 4, 0), H=P((-6, 0, 0)), RA=P((150, 0, 22)), LA=P((10, 0, -10)), RL=P((0, 0, 4)), LL=P((0, 0, -4)))
    K(a, 376, "sine_inout", R=P((0, -90, 0), hroot(0, 3.0, -37.0)), T=tp(0.1, 6, 0), H=P((-10, 8, 4)), RA=P((158, 0, 22)), LA=P((10, 0, -10)))
    # ---- he walks onto the fallen dummy (blink-cut) and scoops him up with a rising kick (392)
    K(a, 380, "linear", R=P((0, 0, 0), hroot(0, 3.0, -47.0)), T=tp(0.5, -14, 0), RA=P((30, 0, 10)), LA=P((-20, 0, -10)), RL=P((20, 0, 4)), LL=P((-20, 0, -6)))
    res = solve(h, 392, "Right Leg", dpoint(d, 392, "Torso", (0.0, 0.0, 0.0)), (150, 0), "cubic_out", R=P((-35, 0, 0), hroot(0, 3.6, -50.0)), T=tp(0.3, -22, 0), H=P((20, 0, 0)),
                RA=P((-40, 0, 24)), LA=P((60, 0, -24)), LL=P((-10, 0, -6)))
    dislocate(a, "Right Leg", 392, (0.0, -0.6, 0.0), settle=4)
    # ---- the leap: he shoots up after the dummy and flies beside him
    K(a, 400, "quad_out", R=P((-10, 0, 0), hroot(0, 9.0, -51.0)), T=tp(0.2, -14, 0), RA=P((-30, 0, 20)), LA=P((-30, 0, -20)), RL=P((60, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 420, "linear", R=P((-18, 0, 0), hroot(0, 21.0, -51.0)), T=tp(0.2, -18, 0), H=P((18, 0, 0)), RA=P((120, 0, 30)), LA=P((-40, 0, -30)), RL=P((56, 0, 4)), LL=P((-26, 0, -4)))
    K(a, 444, "sine_inout", R=P((-22, 0, 0), hroot(0, 25.0, -50.6)), T=tp(0.2, -22, 0), H=P((22, 0, 0)), RA=P((140, 0, 26)), LA=P((-52, 0, -24)), RL=P((70, 0, 4)), LL=P((-30, 0, -4)))
    # ---- the slash (456-462): wind back, then one sweep
    K(a, 456, "quad_in", R=P((-24, 0, 0), hroot(0, 25.3, -50.8)), T=tp(0.0, -28, 40), H=P((20, 0, 0)), RA=P((170, 0, 50)), LA=P((-70, 0, -30)), RL=P((80, 0, 4)), LL=P((-36, 0, -4)))
    K(a, 462, "cubic_out", R=P((-10, 0, 0), hroot(0, 25.0, -50.6)), T=tp(0.0, -10, -50), H=P((10, 0, 0)), RA=P((-70, 0, -10)), LA=P((60, 0, -30)), RL=P((40, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 474, "sine_inout", R=P((-6, 0, 0), hroot(0, 22.0, -50.6)), T=tp(0.1, -4, -20), H=P((12, 0, 0)), RA=P((-30, 0, 18)), LA=P((20, 0, -18)), RL=P((30, 0, 4)), LL=P((-10, 0, -4)))
    # slow float, then the drop and a landing crouch
    K(a, 484, "cubic_in", R=P((0, 0, 0), hroot(0, 9.0, -50.6)), T=tp(0.2, 0, 0), RA=P((40, 0, 24)), LA=P((20, 0, -24)), RL=P((20, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 490, "quad_out", R=P((0, 0, 0), hroot(0, 1.7, -50.0)), T=tp(1.1, -30, 0), H=P((30, 0, 0)), RA=P((-20, 0, 24)), LA=P((60, 0, -24)), RL=P((70, 0, 5)), LL=P((70, 0, -5)))
    K(a, 512, "sine_inout", R=P((0, -60, 0), hroot(0, 3.0, -50.0)), T=tp(0.0, 4, 0), H=P((-8, 0, 0)), RA=P((152, 0, 46)), LA=P((6, 0, -8)), RL=P((0, 0, 4)), LL=P((0, 0, -4)))
    K(a, 556, "sine_inout", R=P((0, -64, 0), hroot(0, 3.0, -50.0)), T=tp(0.0, 3, 0), H=P((-10, 4, 2)), RA=P((156, 0, 48)), LA=P((4, 0, -8)), RL=P((0, 0, 4)), LL=P((0, 0, -4)))
    K(a, 590, "quad_out", T=tp(0.0, 2, 0), H=P((-22, 14, 3)), RA=P((132, 0, 40)), LA=P((6, 0, -8)))  # tips the brim up and looks at the lens
    K(a, 659, "sine_inout", H=P((-26, 16, 3)), RA=P((126, 0, 36)), LA=P((8, 0, -10)))
    print("act3 res", round(res, 3))


BLOCKS = {  # final scatter of the dummy's six blocks relative to its torso (parent frame)
    "Head": ((0.6, 0.0, 3.6), (30, 40, 70)),
    "Right Arm": ((-2.8, 0.6, -1.2), (-20, 10, 80)),
    "Left Arm": ((2.4, 0.4, 2.2), (30, -20, -70)),
    "Right Leg": ((-1.4, 0.2, -3.8), (50, 10, -30)),
    "Left Leg": ((1.8, 0.3, -2.6), (-40, 30, 20)),
}


def dummy_act3(a: Animation) -> None:
    # scooped (392): rises fast, tumbling, high into the sky; the slash (462) cuts him into his six blocks
    react(a, 392, -34)
    fly(a, 392, 440, (0, 0.8, -52.0), (0, 24.0, -52.0), 0.0, (-90, 0, 0), (-450, 0, 0))
    fly(a, 442, 462, (0, 24.2, -52.0), (0, 25.0, -51.8), 0.0, (-450, 0, 0), (-500, 0, 0))
    K(a, 462, "linear", T=tp(0.0, 0), H=P((0, 0, 0)))
    # parts burst apart for the fall: each block gets its own offset and spin
    for part, (off, spin) in BLOCKS.items():
        short = {"Head": "H", "Right Arm": "RA", "Left Arm": "LA", "Right Leg": "RL", "Left Leg": "LL"}[part]
        base = a.sample_part(part, 462)
        K(a, 466, "quad_out", **{short: Pose(tuple(off[i] * 0.45 for i in range(3)), tuple(base.rot[i] + spin[i] * 0.5 for i in range(3)))})
        K(a, 486, "quad_in", **{short: Pose(off, tuple(base.rot[i] + spin[i] for i in range(3)))})
        K(a, 659, "linear", **{short: Pose(off, tuple(base.rot[i] + spin[i] for i in range(3)))})
    fly(a, 464, 486, (0, 25.0, -51.8), (0, 0.6, -52.4), 0.0, (-500, 0, 0), (-630, 0, 0))
    K(a, 659, "linear", R=P((-630, 0, 0), droot(0, 0.6, -52.4)))


def char_point(char: Character, part: str, off=(0.0, 0.0, 0.0)):
    return lambda f: apply(char.world_parts(int(f))[part], off)


def build(n_frames: int = N_FRAMES) -> Scene:
    hero = Character("hero", Animation("hero", fps=60, archetype="cinematic"), base_pos=(0, 0, 0), colors=HERO_COLORS, outfit=coat_and_hair(), face="smirk")
    dummy = Character("dummy", Animation("dummy", fps=60, archetype="cinematic"), base_pos=(0, 0, DUMMY_Z), base_yaw=180.0, colors=DUMMY_COLORS)
    dummy_act1(dummy.anim)
    dummy_act2(dummy.anim)
    dummy_act3(dummy.anim)
    hero_act1(hero, dummy)
    hero_act1b(hero, dummy)
    hero_act2(hero, dummy)
    hero_act3(hero, dummy)
    for ch in (hero, dummy):  # no root-level body part below the floor (linter TSB001)
        keep_above_ground(ch, range(n_frames))
    cine = Cinematic(n_frames)
    cine.sky_color, cine.floor_color = "#8f9cab", "#8c9098"
    cine.shot(0, n_frames - 1, dolly((15, 3.4, -3.5), (15, 3.4, -3.5), (0, 1.9, -3.5), (0, 1.9, -3.5), fov=44))  # fallback
    both = lambda f: char_points(f, hero, dummy)
    cine.bars.key(0, 0.05)

    def tip(f, part):
        return apply(hero.world_parts(f)[part], (0, -1.0, 0))

    # one contact = star on the victim, ink smear along the striking limb, speed streaks, thin wind arcs, a shake
    def hit(t, part, star, k, torso=True, ground=False):
        cine.ink_trail(t, t + 14, 0, part, (0, -1.0, 0), 12, 1.5, 0.0, INK, rag=0.4, seed=10 + k, alpha=0.9)
        if torso:
            cine.ink_trail(t, t + 12, 0, "Torso", (0, 0, 0), 10, 1.2, 0.0, INK, rag=0.45, seed=20 + k, alpha=0.5)
        src = (star[0], star[1], star[2] + 4.5)
        cine.streaks(t, 12, src, (star[0], star[1], star[2] + 0.5), n=14, r0=0.4, r1=1.5, w=0.07, seed=30 + k)
        cine.burst(t + 1, 10, star, 0.2, 1.8, "#f2f2f4", "#ffffff", spikes=11, streaks=5, seed=40 + k)
        for j in range(2):
            cine.ink_arc(t + 1 + j, 10, star, (1, 0, 0.05), 2.2 + 1.0 * j, -60 + 70 * j, 130 + 60 * j, 0.13, "#ffffff", rag=0.1, seed=50 + k + j, grow=4, alpha=0.6)
        cine.shake(t, 8, 0.15)
        cine.punch_in(t, 0.06, 8)

    # ---------------- B1/B2 (0-61): crouch, ink slices, empty stage
    cine.shot(0, 61, autoframe(lambda f: char_points(f, hero, tips=False), 0, 61, azimuth=-38, elevation=4, fov=36, fill=0.8, min_radius=2.4, follow=0.2, pad=1.2))
    cine.slices(46, 5, (0, 2.0, 0.0), 3, h=4.0, w=0.2, spread=0.55, seed=1)
    cine.ink_path(50, 8, [(0, 0.2, 0.4), (0, 2.6, 0.4), (0, 5.2, 0.4)], 0.18, INK, rag=0.2, seed=2, grow=2)
    # ---------------- B3/B4 (62-149): four contacts, each on its most extreme pose
    cine.shot(62, 97, autoframe(both, 62, 97, azimuth=42, elevation=6, fill=0.95, follow=0.25))
    cine.shot(98, 149, autoframe(both, 98, 149, azimuth=50, azimuth_end=82, elevation=6, fill=0.95, follow=0.25))
    hit(62, "Right Leg", dpoint(dummy, 62, "Torso", (0, 0.3, -0.5)), 1)
    hit(104, "Right Leg", dpoint(dummy, 104, "Head", (0, 0, -0.5)), 2)
    hit(122, "Right Arm", dpoint(dummy, 122, "Torso", (0, 0, 0)), 3)
    hit(138, "Right Leg", dpoint(dummy, 138, "Torso", (0, -0.8, -0.5)), 4)
    # ---------------- B5 (150-175): whip-in macro on the hero's head and hat, ragged white spikes for two frames
    cine.screen_fx("burst", 150, 3, seed=7)
    cine.shot(150, 175, tracking(char_point(hero, "Torso"), (4.2, 0.6, -1.6), look_dy=0.9, fov=(34, 30), offset_end=(3.6, 0.5, -1.4)))
    cine.hand.key(150, 0.0)
    # ---------------- B6 (176-255): juggle seen from low: stars + persistent ink swirls
    cine.shot(176, 255, autoframe(both, 176, 255, azimuth=58, azimuth_end=88, elevation=-3, fill=0.95, follow=0.25, roll=(-3.0, 3.0)))
    rng = random.Random(9)
    for i, f in enumerate(range(178, 254, 12)):
        c = (0, 5.2, JUG_Z)
        cine.burst(f, 7, c, 0.2, 1.5, "#f2f2f4", "#ffffff", spikes=10, streaks=5, seed=60 + i)
        cine.ink_arc(f, 26, c, (1, 0.15, 0.1), 3.0 + 0.5 * (i % 2), rng.uniform(-90, 0), rng.uniform(150, 230), 0.45, INK, rag=0.5, seed=70 + i, grow=5, alpha=0.4)
        cine.streaks(f, 6, (0, 3.5, JUG_Z + 2.5), c, n=8, r0=0.3, r1=1.0, w=0.06, seed=80 + i)
        cine.shake(f, 6, 0.1)
    # ---------------- B7 (256-299): finisher: contact, a long ink streak along the ground, dust
    cine.shot(256, 283, autoframe(both, 256, 283, azimuth=75, elevation=4, fill=0.95, follow=0.2))
    cine.shot(284, 299, autoframe(both, 284, 299, azimuth=78, elevation=3, fov=40, fill=0.9, min_radius=5.0, follow=0.15))
    hit(262, "Right Leg", dpoint(dummy, 262, "Torso", (0, 0.2, -0.5)), 5, torso=False)
    cine.ink_path(264, 40, [(0, 0.5, -35.0), (0, 0.5, -42.0), (0, 0.5, -52.0)], 1.0, INK, rag=0.5, seed=90, grow=6, alpha=0.95)
    cine.burst(270, 12, (0, 1.4, -46.0), 0.3, 3.2, "#f2f2f4", "#ffffff", spikes=12, streaks=6, seed=91)
    cine.emit(270, 270, origin=(0, 0.5, -46.0), rate=0, burst=26, vel=(0.08, 0.3), dir=(0, 0.5, -1), spread=1.0, grav=0.004, drag=0.05, life=(24, 60),
              size=(1.0, 2.6), color=("#c9ccd2", "#8a8f99"), alpha=(0.7, 0.0), add=False, shape="smoke", radius=0.8, seed=92)
    # ---------------- B8 (300-339): lull, wide, a hint of handheld
    cine.shot(300, 339, autoframe(both, 300, 339, azimuth=70, elevation=3, fov=40, fill=0.9, min_radius=6.0, follow=0.15))
    cine.hand.key(300, 0.02).key(339, 0.02)
    # ---------------- B9 (340-375): manga impact frame, then the smirk with a speech bubble
    cine.shot(340, 347, dolly((8, 3.6, -37) , (7, 3.6, -37), (0, 3.4, -37), (0, 3.4, -37), fov=(42, 38)))
    cine.screen_fx("bw", 340, 8, seed=11, accent=True, focus=(0.5, 0.45), shards=18)
    cine.shot(348, 375, dolly((4.8, 5.0, -37.0), (4.2, 5.0, -37.0), (0, 4.8, -37), (0, 4.8, -37), fov=(34, 30), easing="linear"))
    cine.screen_fx("bubble", 352, 24, focus=(0.7, 0.22))
    # ---------------- B10 (376-407): he cuts to the fallen dummy and scoops him into the sky
    cine.shot(376, 391, autoframe(lambda f: char_points(f, hero) + [(0, 0.8, -52.0)], 376, 391, azimuth=60, elevation=4, fill=0.95, follow=0.25))
    cine.screen_fx("black", 387, 3)
    cine.shot(392, 410, autoframe(both, 392, 410, azimuth=70, elevation=-8, fill=0.95, follow=0.3))
    hit(392, "Right Leg", dpoint(dummy, 392, "Torso", (0, 0, 0)), 6, torso=False)
    cine.streaks(396, 16, (0, 2.0, -50.8), (0, 24.0, -52.0), n=12, r0=0.5, r1=1.4, w=0.07, seed=95)
    # ---------------- B11 (408-483): the slash storm around the two of them, high in the sky
    cine.shot(408, 465, autoframe(both, 408, 465, azimuth=50, azimuth_end=95, elevation=-14, fov=40, fill=0.9, min_radius=3.4, follow=0.3))
    rs = random.Random(21)
    for f in range(412, 458, 2):
        pos, tgt, _fov, _roll = cine.camera_state(f)
        fwd = tuple(tgt[i] - pos[i] for i in range(3))
        fl = math.sqrt(sum(x * x for x in fwd))
        fwd = tuple(x / fl for x in fwd)
        right = (-fwd[2], 0.0, fwd[0])
        rl = math.sqrt(sum(x * x for x in right))
        right = tuple(x / rl for x in right)
        up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
        plane = tuple(pos[i] + fwd[i] * 7.5 for i in range(3))
        amount = 4 if f < 440 else max(0, 4 - (f - 440) // 5)
        for k in range(amount):
            th = rs.uniform(0, math.pi)
            off = rs.uniform(-2.4, 2.4)
            ln = rs.uniform(6.0, 9.0)
            ca, sa = math.cos(th), math.sin(th)
            mids = []
            for j in range(5):
                t = (j / 4 - 0.5) * 2 * ln
                bend = 0.6 * math.sin(j / 4 * math.pi) * rs.uniform(-1, 1)
                x = ca * t - sa * (off + bend)
                y = sa * t + ca * (off + bend)
                mids.append(tuple(plane[i] + right[i] * x + up[i] * y for i in range(3)))
            cine.ink_path(f, 3, mids, rs.uniform(0.14, 0.3), "#ffffff", glow=CYAN, rag=0.3, seed=rs.randint(1, 9999), grow=1, alpha=0.97)
    # ---------------- the cut (456-466): one clean cyan slash through the dummy, then the blocks burst apart
    pos, tgt, _fov, _roll = cine.camera_state(462)
    c0 = char_point(dummy, "Torso")(462)
    cine.screen_fx("black", 458, 2)
    cine.screen_fx("bw", 460, 4, seed=15, accent=True, focus=(0.5, 0.5), shards=16)
    sw = [(c0[0] + 0.3 * k, c0[1] + 4.2 - 1.05 * k, c0[2] - 3.2 + 0.8 * k) for k in range(-4, 5)]
    cine.ink_path(464, 10, [(c0[0], c0[1] + 5.0 - 1.2 * k, c0[2] - 4.0 + 1.0 * k) for k in range(0, 9)], 0.55, "#ffffff", glow=CYAN, rag=0.15, seed=33, grow=2, alpha=1.0)
    cine.slash(464, 10, c0, (1, 0.2, 0.1), 3.6, -70, 70, 0.8, CYAN, core="#ffffff")
    cine.burst(466, 10, c0, 0.4, 3.5, "#ffffff", CYAN, spikes=12, streaks=8, seed=34)
    cine.flash(466, 5, "#ffffff", 0.9)
    cine.shot(466, 480, autoframe(lambda f: char_points(f, hero), 466, 480, azimuth=80, azimuth_end=55, elevation=-14, fov=38, fill=0.9, min_radius=3.0, follow=0.5, pad=0.8))
    cine.shot(481, 489, autoframe(lambda f: char_points(f, hero, tips=False) + [(0, 0.6, -52.4), (0, 2.5, -52.4)], 481, 489, azimuth=62, elevation=3, fov=38, fill=0.9, min_radius=4.5, follow=0.3))
    # ---------------- B12 (484-659): the blocks hit the ground, hat macro, blink rhythm, final hold
    cine.emit(486, 486, origin=(0, 0.5, -52.4), rate=0, burst=30, vel=(0.1, 0.35), dir=(0, 0.5, 1), spread=1.0, grav=0.004, drag=0.05, life=(26, 70),
              size=(1.0, 2.8), color=("#c9ccd2", "#8a8f99"), alpha=(0.7, 0.0), add=False, shape="smoke", radius=0.8, seed=96)
    cine.shake(486, 10, 0.2)
    cine.shot(490, 499, autoframe(lambda f: char_points(f, hero) + [(0, 0.8, -52.4)], 490, 499, azimuth=40, elevation=2, fov=36, fill=0.95, follow=0.4))
    cine.screen_fx("burst", 500, 4, seed=13)
    cine.shot(500, 503, tracking(char_point(hero, "Head"), (3.2, 0.3, 0.9), look_dy=0.0, fov=(30, 27), offset_end=(2.8, 0.35, 0.8)))
    cine.screen_fx("black", 504, 4)
    cine.screen_fx("glint", 508, 2, focus=(0.5, 0.5))
    cine.shot(504, 549, tracking(char_point(hero, "Head"), (3.0, 0.2, 1.0), look_dy=0.0, fov=(30, 26), offset_end=(2.6, 0.25, 0.9)))
    cine.screen_fx("black", 550, 6)
    cine.screen_fx("bw", 556, 6, seed=17, accent=True, focus=(0.55, 0.5), shards=14)
    cine.shot(556, n_frames - 1, autoframe(lambda f: char_points(f, hero), 556, n_frames - 1, azimuth=32, azimuth_end=6, elevation=-7, fov=34, fill=0.95, min_radius=3.2, follow=0.08, pad=0.9, roll=(1.5, -1.0)))
    # the one accent colour comes back: slow cyan embers rise around him while he holds the pose
    cine.emit(556, 650, origin=(0, 0.6, -50.0), rate=0.5, vel=(0.01, 0.04), dir=(0, 1, 0), spread=1.2, grav=-0.0008, drag=0.02, life=(50, 110),
              size=(0.16, 0.02), color=(CYAN, "#ffffff"), alpha=(0.9, 0.0), add=True, shape="spark", radius=2.6, seed=97)
    cine.bright.key(0, 1.0).key(n_frames - 14, 1.0).key(n_frames - 1, 0.0, "quad_in")
    cine.hand.key(484, 0.015).key(n_frames - 1, 0.015)
    sc = Scene("Duel (court métrage)", [hero, dummy], cine=cine, hold=2)
    sc.markers = [{"f": 0, "label": "anticipation", "act": True}, {"f": 50, "label": "blink"}, {"f": 62, "label": "contact"}, {"f": 392, "label": "envol"}, {"f": 462, "label": "taillade"}]
    return sc
