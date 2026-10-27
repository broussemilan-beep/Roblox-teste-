"""Berserker ultimate: a ~13 s cinematic (rage awakening -> flurry -> grab and drag -> comet finish).

Everything is authored with tsb_engine; numbers are creative starting values, not TSB data.
World: Y up, attacker starts at the origin facing -Z, victim 6 studs ahead facing it,
pillars at z = -22 / -38, wall at z = -90.
"""

from __future__ import annotations

import math
import random

from tsb_engine.authoring import K, P, attach, keep_above_ground, lying_root_rot, point_world, tp, tremble
from tsb_engine.cinematic import Cinematic, dolly, orbit, tracking
from tsb_engine.footwork import Step, bake_footwork, gait_steps
from tsb_engine.model import ROOT, Animation
from tsb_engine.scene import Character, Scene

N_FRAMES = 780

ATK_COLORS = {
    "Torso": "#b3392b", "Head": "#e8b88a", "Right Arm": "#e8b88a", "Left Arm": "#e8b88a",
    "Right Leg": "#2b2f3a", "Left Leg": "#2b2f3a",
}
VIC_COLORS = {
    "Torso": "#2f6fdd", "Head": "#f2c94c", "Right Arm": "#f2c94c", "Left Arm": "#f2c94c",
    "Right Leg": "#4a9b5b", "Left Leg": "#4a9b5b",
}
ROCK = ["#4a4540", "#5a534c", "#3a3633"]
FIRE = ("#ffd27a", "#ff3a00")


def act1(atk: Character, vic: Character, cine: Cinematic) -> None:
    a, v = atk.anim, vic.anim

    # ---- attacker: sprinter's crouch, eyes on the enemy -> deep compressed breath -> ROAR (chest out, head back, arms in a V) -> lock-on
    K(a, 0, T=tp(0.7, -34), H=P((34, 0, 0)), RA=P((34, 0, 12)), LA=P((30, 0, -12)))
    K(a, 60, T=tp(0.78, -38), H=P((38, 0, 0)), RA=P((38, 0, 14)), LA=P((34, 0, -14)))
    K(a, 100, "quad_in", T=tp(0.9, -42, 4), H=P((30, 0, 0)), RA=P((-10, 0, 10)), LA=P((-12, 0, -10)))
    K(a, 118, "sine_inout", T=tp(1.02, -48, 0), H=P((14, 0, 0)), RA=P((-34, 0, 8)), LA=P((-36, 0, -8)))
    K(a, 122, "cubic_out", T=tp(0.0, 24, 0), H=P((30, 0, 0)), RA=P((-6, 0, 128)), LA=P((-6, 0, -128)))
    K(a, 134, "sine_inout", T=tp(0.0, 28, 0), H=P((34, 0, 0)), RA=P((-10, 0, 138)), LA=P((-10, 0, -138)))
    K(a, 146, "sine_inout", T=tp(0.1, 18, 0), H=P((24, 0, 0)), RA=P((-6, 0, 120)), LA=P((-6, 0, -120)))
    K(a, 156, "cubic_out", T=tp(0.55, -30), H=P((18, 0, 0)), RA=P((30, 0, 12)), LA=P((30, 0, -12)))
    K(a, 166, "linear", T=tp(0.5, -28), H=P((14, 0, 0)), RA=P((34, 0, 12)), LA=P((34, 0, -12)))
    tremble(a, "RA", 0, 58, 2.0, 0.02)
    tremble(a, "LA", 1, 59, 2.0, 0.02)
    tremble(a, "RA", 60, 98, 3.5, 0.03)
    tremble(a, "LA", 61, 99, 3.5, 0.03)
    tremble(a, "RA", 100, 117, 6.0, 0.05)
    tremble(a, "LA", 101, 117, 6.0, 0.05)
    tremble(a, "RA", 124, 146, 3.5, 0.04)
    tremble(a, "LA", 125, 146, 3.5, 0.04)
    tremble(a, "T", 0, 117, 0.9, 0.0, 3)
    tremble(a, "H", 124, 146, 2.5, 0.0, 2)
    K(a, 120, "cubic_out", R=P(pos=(0, 0, 0)))
    K(a, 124, "cubic_out", R=P(pos=(0, 0.3, 0)))  # the roar lifts him onto his toes
    K(a, 144, "sine_inout", R=P(pos=(0, 0.1, 0)))
    K(a, 156, "sine_inout", R=P(pos=(0, 0, 0)))

    # ---- victim: braced guard, flung backwards and skidding when the roar hits
    K(v, 0, T=tp(0.12, -4), H=P((0, 4, 0)), RA=P((62, 0, 12)), LA=P((50, 0, -16)))
    K(v, 112, T=tp(0.14, -4), H=P((0, 4, 0)), RA=P((62, 0, 12)), LA=P((50, 0, -16)))
    K(v, 122, "cubic_out", T=tp(0.1, 20), H=P((26, 0, 0)), RA=P((20, 0, 40)), LA=P((16, 0, -40)))
    K(v, 134, "quad_out", T=tp(0.2, 12), H=P((14, 0, 0)), RA=P((60, 0, 24)), LA=P((50, 0, -24)))
    K(v, 150, "sine_inout", T=tp(0.3, -6), H=P((0, 0, 0)), RA=P((78, 0, 14)), LA=P((68, 0, -14)))
    K(v, 170, T=tp(0.32, -8), H=P((0, 0, 0)), RA=P((72, 0, 14)), LA=P((62, 0, -14)))
    K(v, 122, "cubic_out", R=P(pos=(0, 0, 0)))
    K(v, 150, "quad_out", R=P(pos=(0, 0, 4.4)))
    K(v, 170, R=P(pos=(0, 0, 4.4)))

    # ---- footwork
    bake_footwork(a, {"Right Leg": (2.0, 0.2), "Left Leg": (-2.0, 0.2)}, [], 0, 166)
    bake_footwork(
        v, {"Right Leg": (1.2, 1.2), "Left Leg": (-0.8, -0.5)},
        [Step("Left Leg", 124, 131, (-0.8, 1.6), 0.5), Step("Right Leg", 127, 135, (1.2, 2.6), 0.5),
         Step("Left Leg", 135, 143, (-0.8, 3.6), 0.4), Step("Right Leg", 139, 148, (1.2, 4.6), 0.4)],
        0, 170,
    )

    # ---- set: flame aura, crackling lightning, floating rocks, lava cracks, shockwaves
    TORSO = {"char": 0, "part": "Torso", "off": [0, -0.6, 0]}
    cine.emit(30, 121, origin=(0, 0.9, 0), rate=1.0, vel=(0.03, 0.1), dir=(0, 1, 0), spread=0.4, grav=-0.003, life=(26, 46),
              size=(0.4, 0.06), color=FIRE, alpha=(0.7, 0.0), radius=1.9, shape="flame", seed=1)
    cine.emit(122, 170, origin=(0, 0.9, 0), rate=1.6, vel=(0.05, 0.16), dir=(0, 1, 0), spread=0.5, grav=-0.004, life=(26, 50),
              size=(0.6, 0.08), color=FIRE, alpha=(0.75, 0.0), radius=2.4, shape="flame", seed=2)
    cine.emit(30, 170, origin=(0, 0.2, 0), rate=1.3, vel=(0.01, 0.07), dir=(0, 1, 0), spread=0.6, grav=-0.0015, life=(60, 110),
              size=(0.09, 0.02), color=("#ffd27a", "#ff6a1a"), alpha=(1.0, 0.0), radius=3.6, shape="spark", stretch=2.0, seed=6)
    cine.glow(70, 170, attach={"char": 0, "part": "Torso", "off": [0, 0, 0]}, r0=0.8, r1=2.6, color="#ff6a1f", a0=0.1, a1=0.55, pulse=0.18)
    rb = random.Random(5)
    t = 52
    while t < 170:  # red lightning arcs from the body to the ground, faster and more frequent as the roar approaches
        for k in range(1 if t < 100 else 2 if t < 122 else 3):
            ang = rb.random() * math.tau
            rad = 1.8 + rb.random() * 3.2
            cine.bolt(t, t + 5, attach_a={"char": 0, "part": "Torso", "off": [0, rb.random() * 0.8, 0]},
                      b=(math.cos(ang) * rad, 0.05, math.sin(ang) * rad), width=0.07, color="#ff5a1f", core="#fff0c8",
                      segs=8, jitter=0.5, branch=0.2, seed=int(t * 7 + k))
        t += max(5, int(18 - (t - 52) * 0.15))
    rnd = random.Random(11)
    for i in range(18):
        ang = rnd.random() * math.tau
        rad = 2.4 + rnd.random() * 3.8
        s_ = 0.45 + rnd.random() * 0.8
        cine.debris_piece(46 + int(rnd.random() * 56), (math.cos(ang) * rad, 0.3, math.sin(ang) * rad),
                          (0, 0.015 + rnd.random() * 0.02, 0), (s_, s_ * 0.7, s_ * 0.9), rnd.choice(ROCK),
                          (rnd.random() * 2, rnd.random() * 2, rnd.random() * 2), g=-0.0012, bounce=0.3, g2=0.014, tg=124)
    cine.cracks(80, 24, (0, 0, 0), 5.5, 9, "#15110f", "#ff5a1f", 0.1, seed=3, fade=(300, 340))
    cine.cracks(122, 20, (0, 0, 0), 12, 14, "#15110f", "#ff5a1f", 0.16, seed=4, fade=(300, 340))
    for t, r1 in ((112, 6), (122, 16), (131, 22)):
        cine.ring(t, 24, (0, 0.08, 0), 0.6, r1, 0.9, 0.15, "#ff8a3d", 0.7, 0.0)
    head = point_world(atk, "Head", (0, 0, -0.5), 122)
    cine.burst(122, 12, head, 0.6, 4.2, "#ff6a1f", "#ffe2a0", spikes=16, streaks=14, rot=8, seed=7)
    cine.glow(122, 134, c=head, r0=1.6, r1=0.8, color="#ff8a3d", a0=0.5, a1=0.0, flare=1.4)
    cine.dome(122, 20, (0, 3.0, 0), 1.0, 7.0, "#ff9a4a", 0.12, 0.0)
    cine.line(122, 40, (0, 0, 0), (0, 34, 0), 2.0, 0.0, "#ff7a2a", 0.5, 0.0, easing="quad_out")
    cine.emit(122, 124, origin=(0, 0.3, 0), rate=0, burst=90, vel=(0.25, 0.65), dir=(1, 0.15, 0), spread=1.0, grav=0.004,
              drag=0.04, life=(30, 70), size=(1.0, 2.2), color=("#8a7e72", "#4b4540"), alpha=(0.55, 0.0), add=False, radius=1.2, shape="smoke", seed=5)
    cine.emit(122, 123, origin=(0, 0.3, 0), rate=0, burst=60, vel=(0.3, 0.9), dir=(0, 0.6, 0), spread=1.0, grav=0.012, life=(20, 46),
              size=(0.12, 0.03), color=("#ffe9a8", "#ff5a1f"), alpha=(1.0, 0.0), shape="spark", stretch=3.5, seed=8)
    cine.flash(122, 6, "#ffd9a8", 0.25)

    # ---- camera
    cine.shot(0, 45, dolly((14.0, 1.8, -3.0), (12.0, 1.7, -3.0), (0, 2.4, -3.0), (0, 2.4, -3.0), fov=(38, 36), easing="sine_inout"))
    cine.shot(46, 99, dolly((11.0, 1.4, -4.5), (5.2, 1.0, -5.4), (0, 2.6, -3.0), (0, 2.8, -0.8), fov=(42, 38), easing="sine_inout"))
    cine.shot(100, 121, dolly((3.8, 1.6, -6.6), (2.8, 2.2, -5.0), (0, 2.8, 0), (0, 2.8, 0), fov=(40, 34), easing="quad_in"))
    cine.shot(122, 149, dolly((4.2, 1.6, -10.4), (3.2, 1.9, -8.6), (0, 3.9, 0), (0, 4.3, 0), fov=(54, 46), easing="quad_out"))
    cine.shot(150, 169, dolly((5.0, 1.6, 4.6), (3.8, 1.9, 3.0), (-0.5, 2.6, -6.5), (-0.5, 2.8, -7.0), fov=(50, 46), easing="sine_inout"))
    cine.shake(122, 28, 0.45)
    cine.shake(110, 12, 0.08)
    cine.bars.key(0, 0.115)
    cine.vignette.key(0, 0.15).key(90, 0.32, "quad_in").key(122, 0.5, "cubic_out").key(150, 0.22, "sine_inout")
    cine.bright.key(0, 1.0).key(60, 0.9, "sine_inout").key(120, 0.8, "quad_in").key(124, 1.0, "cubic_out").key(150, 0.92, "sine_inout")
    cine.tint.key(0, 0.0).key(110, 0.0).key(122, 0.08, "cubic_out").key(150, 0.0, "sine_inout")
    cine.speed.key(118, 0.0).key(124, 0.45, "cubic_out").key(136, 0.0, "linear")
    cine.flash(122, 8, "#ffd9a8", 0.3)


def char_point(char: Character, part: str, off=(0.0, 0.0, 0.0)):
    """Callable frame -> world point of a body part (for tracking cameras)."""
    from tsb_engine.kinematics import apply

    return lambda f: apply(char.world_parts(int(f))[part], off)


VZ0 = 4.4  # victim's local z (studs backwards) when the roar has thrown him back: world z = -6 - VZ0
UP_Z = 8.2  # same, at the end of the uppercut
Z0 = -6.0 - UP_Z  # world z where the victim hangs and is slammed
HIT_GAP = 4.2  # attacker world z minus victim world z when a punch lands
PUNCH_T = [186 + 8 * i for i in range(9)]  # impact frames of the flurry
UPPERCUT = 262


def vzl(i: int) -> float:
    """Victim local z after punch i (every hit knocks him back a little)."""
    return VZ0 + 0.35 * (i + 1)


def azw(i: int) -> float:
    """Attacker world z when punch i lands."""
    return -6.0 - vzl(i) + HIT_GAP


def act2(atk: Character, vic: Character, cine: Cinematic) -> None:
    a, v = atk.anim, vic.anim

    # ---- attacker: explosive sprint -> arrival -> 9 punches that drive the victim back -> wind-down -> uppercut
    K(a, 166, R=P(pos=(0, 0, 0)))
    for k, f in enumerate(range(168, 185, 4)):
        s_ = 1.0 if k % 2 == 0 else -1.0
        K(a, f, "linear", T=tp(0.62 + 0.04 * s_, -46, 8 * s_), H=P((26, 0, 0)), RA=P((-62 * s_ + 6, 0, 10)), LA=P((62 * s_ + 6, 0, -10)))
    for f, z in ((170, -0.9), (174, -2.8), (178, -4.8), (182, azw(0) - 0.5), (185, azw(0) + 0.0)):
        K(a, f, "linear", R=P(pos=(0, 0, z)))
    K(a, 184, "cubic_out", T=tp(0.5, -30, 20), RA=P((-30, 0, 10)), LA=P((60, 0, -10)))
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        hit, other = ("RA", "LA") if side > 0 else ("LA", "RA")
        reach = -(0.55 + 0.04 * i)
        K(a, t - 5, "linear", **{hit: P((-44, 0, side * 10)), other: P((74, 0, -side * 12))}, T=tp(0.36, -20, -side * 26), H=P((8, side * 14, 0)))
        K(a, t - 2, "quad_in", T=tp(0.4, -22, -side * 34), **{hit: P((-50, 0, side * 12))})
        K(a, t, "linear", T=tp(0.5, -26, side * 40), H=P((-8, -side * 22, 0)),
          **{hit: P((110, 0, side * 3), (0, 0, reach)), other: P((-36, 0, -side * 14))})
        K(a, t + 2, "linear", **{hit: P((114, 0, side * 3), (0, 0, reach - 0.15))})
        K(a, t + 4, "cubic_out", T=tp(0.4, -20, side * 14), **{hit: P((74, 0, side * 14)), other: P((64, 0, -side * 14))})
        K(a, t - 2, "linear", R=P(pos=(0, 0, azw(i) + 0.2)))
        K(a, t, "linear", R=P(pos=(0, 0, azw(i) - 0.25)))
        K(a, t + 4, "cubic_out", R=P(pos=(0, 0, azw(i))))
    # wind-down: sink low, fist back by the knee, then the uppercut
    zu = azw(8) - 0.2
    K(a, 252, "quad_in", T=tp(0.95, -36, 14), H=P((24, 0, 0)), RA=P((-62, 0, 16)), LA=P((30, 0, -16)), R=P(pos=(0, 0, azw(8))))
    K(a, 258, "quad_in", T=tp(1.0, -34, 24), H=P((28, 0, 0)), RA=P((-80, 0, 20)), LA=P((22, 0, -18)), R=P(pos=(0, 0, zu + 0.2)))
    K(a, UPPERCUT, "cubic_out", T=tp(0.1, 8, 20), H=P((10, 0, 0)), RA=P((128, 0, 8), (0, 0, -0.7)), LA=P((-44, 0, -22)), R=P(pos=(0, 0.3, zu)))
    K(a, 268, "cubic_out", T=tp(0.0, 14, 28), H=P((6, 0, 0)), RA=P((172, 0, 6)), LA=P((-52, 0, -22)), R=P(pos=(0, 1.2, zu - 0.2)))
    K(a, 280, "sine_inout", T=tp(0.0, 10, 20), H=P((-4, 0, 0)), RA=P((176, 0, 6)), LA=P((-30, 0, -16)), R=P(pos=(0, 2.3, zu - 0.4)))
    K(a, 299, "linear", R=P(pos=(0, 2.4, zu - 0.5)))
    steps = gait_steps(a, 166, 184, first_leg="Left Leg", interval=4, swing=4, lateral=0.7, lift=1.0)
    steps += gait_steps(a, 186, 250, first_leg="Right Leg", interval=16, swing=7, lateral=0.7, lift=0.35)
    bake_footwork(a, {"Right Leg": (2.0, 0.2), "Left Leg": (-2.0, 0.2)}, steps, 166, UPPERCUT - 1)
    K(a, UPPERCUT, "linear", RL=P((24, 0, 4)), LL=P((-36, 0, -4)))
    K(a, 270, "linear", RL=P((10, 0, 6)), LL=P((-20, 0, -6)))
    K(a, 282, "linear", RL=P((32, 0, 6)), LL=P((-12, 0, -6)))
    K(a, 299, "linear", RL=P((30, 0, 6)), LL=P((-10, 0, -6)))

    # ---- victim: face hits snap the head back, body hits fold him over; every hit shoves him back
    K(v, 166, R=P(pos=(0, 0, VZ0)))
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        face = i % 2 == 0
        K(v, t - 1, "linear", T=tp(0.3, -6), H=P((0, 0, 0)), RA=P((74, 0, 14)), LA=P((64, 0, -14)), R=P((0, 0, 0), (0, 0, vzl(i - 1) if i else VZ0)))
        if face:
            K(v, t, "cubic_out", T=tp(0.1, 18, side * 16), H=P((36, -side * 14, 0)), RA=P((128, 0, 44)), LA=P((112, 0, -36)),
              R=P((0, side * 12, 0), (0, 0.0, vzl(i))))
        else:
            K(v, t, "cubic_out", T=tp(0.5, -42, side * 12), H=P((-34, 0, 0)), RA=P((46, 0, 46)), LA=P((52, 0, -46)),
              R=P((0, side * 10, 0), (0, 0.25, vzl(i))))
        K(v, t + 3, "quad_out", R=P((0, side * 4, 0), (0, 0.0, vzl(i))))
        K(v, t + 6, "sine_inout", T=tp(0.3, -6), H=P((0, 0, 0)), RA=P((74, 0, 14)), LA=P((64, 0, -14)), R=P((0, 0, 0), (0, 0, vzl(i))))
    vs = gait_steps(v, 184, 252, first_leg="Left Leg", interval=14, swing=7, lateral=0.8, lift=0.3)
    zv = vzl(8) + 0.3
    K(v, 256, "linear", T=tp(0.3, -10), RA=P((70, 0, 14)), LA=P((60, 0, -14)), R=P((0, 0, 0), (0, 0, zv - 0.2)))
    K(v, UPPERCUT, "cubic_out", T=tp(0.1, 22), H=P((22, 0, 0)), RA=P((150, 0, 34)), LA=P((158, 0, -34)), R=P((0, 0, 0), (0, 0.1, zv)))
    K(v, 272, "quad_out", T=tp(0.0, 30), H=P((30, 0, 0)), RA=P((160, 0, 40)), LA=P((165, 0, -40)), R=P((34, 0, 0), (0, 3.4, zv + 0.4)))
    K(v, 284, "sine_inout", T=tp(0.0, 34), RA=P((120, 0, 30)), LA=P((130, 0, -30)), R=P((64, 0, 0), (0, 3.8, UP_Z)))
    K(v, 299, "linear", R=P((66, 0, 0), (0, 3.7, UP_Z)))
    vf = vzl(0) + 0.0
    bake_footwork(v, {"Right Leg": (1.2, 4.6), "Left Leg": (-0.8, 3.6)}, vs, 166, UPPERCUT - 1)
    K(v, UPPERCUT, "linear", RL=P((-26, 0, 6)), LL=P((-38, 0, -8)))
    K(v, 276, "linear", RL=P((-10, 0, 10)), LL=P((-24, 0, -12)))
    K(v, 299, "linear", RL=P((-18, 0, 10)), LL=P((-30, 0, -12)))

    # ---- fx: sprint
    cine.trail(166, 186, 0, "Torso", (0, 0, 0), 10, 1.4, 0.1, "#ffe9c4", 0.4)
    for leg in ("Right Leg", "Left Leg"):
        cine.emit(166, 186, attach={"char": 0, "part": leg, "off": [0, -1, 0]}, rate=1.1, vel=(0.02, 0.09), dir=(0, 1, 0.5), spread=0.8,
                  life=(24, 40), size=(0.9, 2.0), color=("#8a7e72", "#4b4540"), alpha=(0.5, 0.0), add=False, shape="smoke", seed=21 + len(leg))
    cine.strip(166, 20, (0, 0.03, 0), (0, 0.03, azw(0)), [(1.0, "#ffd9a0", 0.25), (0.35, "#ffffff", 0.35)], "quad_out", fade=(190, 230))
    cine.speed.key(166, 0.0).key(172, 0.5, "cubic_out").key(184, 0.5, "linear").key(188, 0.18, "linear").key(250, 0.18, "linear").key(257, 0.0, "linear")

    # ---- fx: each punch = hit star + sparks + smear + ring + glow + camera kick
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        arm = "Right Arm" if side > 0 else "Left Arm"
        p = point_world(atk, arm, (0, -1.0, 0), t)
        face = i % 2 == 0
        tgt = (p[0], p[1] + (0.2 if face else -0.1), p[2] - 0.3)
        cine.burst(t + 1, 9, tgt, 0.3, 1.7 + 0.12 * i, "#ffb43a" if face else "#ff8a3d", "#ffffff", spikes=11, streaks=8, rot=37 * i, seed=30 + i)
        cine.emit(t + 2, t + 2, origin=tgt, rate=0, burst=22, vel=(0.2, 0.62), dir=(side * 0.25, 0.25, -1), spread=1.0, grav=0.012, life=(10, 22),
                  size=(0.15, 0.03), color=("#ffffff", "#ff8a1a"), alpha=(1, 0), shape="spark", stretch=3.5, seed=40 + i)
        cine.ring(t + 2, 9, tgt, 0.3, 2.3, 0.4, 0.04, "#ffe9c4", 0.8, 0.0, n=(0, 0, 1))
        cine.glow(t - 2, t + 3, attach={"char": 0, "part": arm, "off": [0, -1.0, 0]}, r0=0.5, r1=0.9, color="#ffb43a", a0=0.6, a1=0.0, flare=0.6)
        cine.trail(t - 5, t + 3, 0, arm, (0, -1.0, 0), 7, 0.8, 0.05, "#ffc766", 0.9)
        cine.emit(t + 2, t + 2, origin=(0, 0.15, p[2] - 3.2), rate=0, burst=7, vel=(0.05, 0.14), dir=(0, 1, 0.3), spread=0.9, life=(18, 30), size=(0.8, 1.6),
                  color=("#8a7e72", "#4b4540"), alpha=(0.45, 0.0), add=False, shape="smoke", radius=0.7, seed=60 + i)
        cine.punch_in(t, 0.06, 7)
        cine.shake(t, 6, 0.09 if i % 2 else 0.13)
        cine.flash(t, 3, "#ffe9c4", 0.1)

    # ---- fx: uppercut
    up = point_world(atk, "Right Arm", (0, -1.0, 0), UPPERCUT)
    cine.slash(UPPERCUT - 3, 10, (up[0] + 0.2, up[1] + 0.5, up[2] + 1.2), (1, 0, 0), 3.4, -100, 40, 1.1, "#ffb43a")
    cine.burst(UPPERCUT, 12, (up[0], up[1] + 0.4, up[2] - 0.4), 0.5, 5.2, "#ffd27a", "#ffffff", spikes=14, streaks=12, rot=12, seed=70)
    cine.bolt(UPPERCUT, UPPERCUT + 12, a=(up[0], 0.1, up[2] - 1.0), b=(up[0], 24, up[2] - 1.0), width=0.2, color="#ffd27a", core="#ffffff", segs=14, jitter=1.2, branch=0.3, seed=71)
    cine.bolt(UPPERCUT, UPPERCUT + 10, a=(up[0], 0.1, up[2] - 1.0), b=(up[0] + 3, 18, up[2] - 3), width=0.12, color="#ffd27a", core="#ffffff", segs=10, jitter=1.0, branch=0.2, seed=72)
    cine.ring(UPPERCUT, 26, (up[0], 0.08, up[2] - 1.0), 0.6, 15, 1.2, 0.15, "#ffd9a0", 0.85, 0.0)
    cine.ring(UPPERCUT + 3, 26, (up[0], 0.08, up[2] - 1.0), 0.6, 10, 0.8, 0.1, "#ffffff", 0.6, 0.0)
    cine.line(UPPERCUT, 28, (up[0], 0.0, up[2] - 1.0), (up[0], 28, up[2] - 1.0), 1.4, 0.0, "#fff1d6", 0.5, 0.0, easing="quad_out")
    cine.burst_debris(UPPERCUT, (up[0], 0.2, up[2] - 1.0), 26, 0.3, 0.38, (0.25, 0.7), ROCK, seed=40)
    cine.emit(UPPERCUT, UPPERCUT + 1, origin=(up[0], 0.3, up[2] - 1.0), rate=0, burst=60, vel=(0.3, 0.9), dir=(0, 0.7, 0), spread=1.0, grav=0.012, life=(24, 56),
              size=(0.14, 0.03), color=("#ffe9a8", "#ff6a1a"), alpha=(1, 0), shape="spark", stretch=3.5, seed=73)
    cine.emit(UPPERCUT, UPPERCUT + 2, origin=(up[0], 0.3, up[2] - 1.0), rate=0, burst=70, vel=(0.2, 0.55), dir=(1, 0.2, 0), spread=1.0, grav=0.004, drag=0.04,
              life=(30, 70), size=(1.2, 2.6), color=("#8a7e72", "#4b4540"), alpha=(0.55, 0.0), add=False, shape="smoke", radius=1.2, seed=74)
    cine.flash(UPPERCUT, 4, "#ffffff", 0.25)
    cine.shake(UPPERCUT, 22, 0.55)
    cine.punch_in(UPPERCUT, 0.12, 10)
    cine.vignette.key(168, 0.2, "linear").key(262, 0.3, "cubic_out").key(290, 0.15, "sine_inout")
    cine.bright.key(166, 0.92, "linear").key(180, 1.0, "sine_inout").key(262, 1.0, "linear")

    # ---- camera
    cine.shot(166, 173, dolly((8.0, 1.0, -0.4), (8.0, 1.0, -2.0), (0, 1.9, -0.4), (0, 2.0, -2.4), fov=(52, 50), easing="linear"))
    cine.shot(174, 185, dolly((8.0, 1.2, -3.0), (7.2, 1.4, -6.4), (0, 2.1, -3.2), (0, 2.5, -7.4), fov=(50, 44), easing="quad_out"))
    mid = lambda i: (azw(i) - 6.0 - vzl(i)) / 2
    cine.shot(186, 209, dolly((7.6, 2.0, mid(0)), (6.4, 2.1, mid(2)), (0, 2.8, mid(0)), (0, 2.8, mid(2)), fov=(40, 36), easing="sine_inout"))
    cine.shot(210, 233, tracking(char_point(vic, "Head"), (3.4, 0.1, 6.6), look_dy=0.0, fov=(42, 38), offset_end=(3.0, 0.2, 5.8)))
    cine.shot(234, 255, dolly((-7.6, 1.8, mid(6)), (-6.4, 2.0, mid(8)), (0, 2.8, mid(6)), (0, 2.8, mid(8)), fov=(40, 36), easing="sine_inout"))
    cine.shot(256, 270, dolly((9.0, 0.9, zu + 0.5), (8.4, 1.0, zu - 0.6), (0, 2.0, zu - 2.0), (0, 3.4, zu - 2.6), fov=(52, 48), easing="quad_in"))
    cine.shot(271, 275, dolly((8.4, 1.0, zu - 1.0), (8.0, 1.4, zu - 1.4), (0, 4.4, zu - 2.8), (0, 5.4, zu - 3.0), fov=(50, 50), easing="linear"))
    cine.shot(276, 321, tracking(char_point(vic, "Head"), (4.6, -1.4, 4.2), look_dy=0.2, fov=(56, 46), offset_end=(6.2, 0.6, 5.4)))


ROOT_Y = 3.0
WALL_Z = -90.0
PILLARS = [(-0.3, -27.0), (-0.3, -41.0)]
GRAB, SLAM, DRAG0, DRAG1, THROW1 = 318, 334, 340, 450, 478
HAND_X = -1.0  # attacker x while dragging: his right hand (1.5 to his right) holds the head near x = 0.5
CHARGE0, COMET0, HIT = 521, 557, 564
VIC_WALL = (0.0, 5.8, WALL_Z + 2.55)  # victim torso centre when pinned on the wall (back 0.05 off its face)
SPOT = (0.5, 0.0)  # (x, ground) of the drag line


def world_to_local(vic: Character, p) -> tuple[float, float, float]:
    """World point -> victim base frame (Root keys live there)."""
    from tsb_engine.mathutil import mat_vec, transpose

    r, o = vic.base_transform()
    return mat_vec(transpose(r), (p[0] - o[0], p[1] - o[1], p[2] - o[2]))


def root_world(vic: Character, f: int):
    """World position of the victim's torso centre at frame f."""
    return point_world(vic, "Torso", (0.0, 0.0, 0.0), f)


def set_root_world(vic: Character, f: int, wp, rot) -> None:
    lp = world_to_local(vic, (wp[0], wp[1] - ROOT_Y, wp[2]))
    vic.anim.set_key(ROOT, f, P(rot, lp), "linear")


def meet(atk: Character, vic: Character, f: int) -> None:
    """Shift the attacker's Root at frame f so his right hand lands on the victim's head."""
    tgt = point_world(vic, "Head", (0, 0, 0), f)
    cur = point_world(atk, "Right Arm", (0, -1.0, 0), f)
    r = atk.anim.sample_root(f)
    atk.anim.set_key(ROOT, f, P(r.rot, (r.pos[0] + tgt[0] - cur[0], r.pos[1] + tgt[1] - cur[1], r.pos[2] + tgt[2] - cur[2])), "linear")


def act3(atk: Character, vic: Character, cine: Cinematic) -> None:
    a, v = atk.anim, vic.anim
    lay = lying_root_rot(vic, (0.0, -1.0))

    # ---- attacker leaps to the airborne victim, grabs the head, dives and plants the face in the ground
    K(a, 308, "cubic_out", T=tp(0.0, 8, 10), H=P((-8, 0, 0)), RA=P((152, 0, 8)), LA=P((-50, 0, -22)), R=P(pos=(0, 2.9, Z0 + 1.8)),
      RL=P((30, 0, 6)), LL=P((-10, 0, -6)))
    K(a, GRAB, "sine_inout", T=tp(0.0, 4, 0), H=P((-6, 0, 0)), RA=P((158, 0, 6)), LA=P((-40, 0, -18)), R=P(pos=(0, 2.9, Z0 + 1.1)),
      RL=P((24, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 326, "quad_in", T=tp(0.5, -32, 0), H=P((-14, 0, 0)), RA=P((110, 0, 6)), LA=P((-70, 0, -24)), R=P(pos=(HAND_X * 0.5, 1.5, Z0 + 0.6)),
      RL=P((40, 0, 6)), LL=P((-30, 0, -6)))
    K(a, SLAM, "cubic_in", T=tp(1.1, -55, 0), H=P((-24, 0, 0)), RA=P((50, 0, 0)), LA=P((-60, 0, -14)), R=P(pos=(HAND_X, 0, Z0)))

    # ---- victim hangs at the apex, then folds forward and is carried down
    K(v, 308, "sine_inout", T=tp(0.0, 36), RA=P((110, 0, 30)), LA=P((120, 0, -30)), R=P((78, 0, 0), (0, 3.8, UP_Z)), RL=P((-18, 0, 10)), LL=P((-30, 0, -12)))
    K(v, GRAB, "linear", T=tp(0.0, 30), RA=P((100, 0, 30)), LA=P((110, 0, -30)), R=P((88, 0, 0), (0, 3.6, UP_Z)))
    K(v, 326, "quad_in", T=tp(0.0, 10), RA=P((40, 0, 20)), LA=P((50, 0, -20)), R=P((20, 0, 0), (0, 1.8, UP_Z)), RL=P((8, 0, 8)), LL=P((4, 0, -8)))
    K(v, SLAM, "cubic_in", T=tp(0.0, 0), H=P((-10, 0, 0)), RA=P((14, 0, 10)), LA=P((10, 0, -10)), R=P(lay, (0, 0, UP_Z)))

    # ---- the drag: a low sprint, one hand on the head, through two pillars
    K(a, DRAG0, "linear", R=P(pos=(HAND_X, 0, Z0)))
    K(a, 380, "quad_in", R=P(pos=(HAND_X, 0, Z0 - 8.6)))
    K(a, DRAG1, "linear", R=P(pos=(HAND_X, 0, -52.0)))
    for f in range(DRAG0, DRAG1 + 1, 7):  # sprint bob and the free arm pumping
        ph = ((f - DRAG0) // 7) % 2
        K(a, f, "linear", T=tp(1.1 + 0.05 * ph, -55 - 3 * ph, 10 if ph else -10), LA=P((-70 if ph else 30, 0, -16)), H=P((-26, 0, 0)), RA=P((50, 0, 0)))
    # attacker's follow-through and braking skid
    K(a, 454, "cubic_out", T=tp(0.85, -34, -42), H=P((-18, 0, 0)), RA=P((150, 0, 6)), LA=P((-30, 0, -14)), R=P(pos=(HAND_X, 0, -53.2)))
    K(a, 470, "sine_inout", T=tp(0.3, -12, -10), H=P((-4, 0, 0)), RA=P((60, 0, 8)), LA=P((20, 0, -8)), R=P(pos=(HAND_X, 0, -55.0)))
    steps = gait_steps(a, DRAG0, DRAG1 - 2, first_leg="Left Leg", interval=7, swing=6, lateral=0.6, lift=0.8)
    bake_footwork(a, {"Right Leg": (1.2, Z0 + 0.4), "Left Leg": (-1.2, Z0 - 0.4)}, steps, 330, DRAG1)
    for f in range(SLAM, DRAG1 + 1, 6):  # the victim's limbs trail and flap
        ph = (f // 6) % 2
        K(v, f, "linear", T=tp(0.0, 0), H=P((-10 - 6 * ph, 0, 0)), RA=P((14 + 12 * ph, 0, 10)), LA=P((10 + 10 * (1 - ph), 0, -10)),
          RL=P((8 + 6 * ph, 0, 6)), LL=P((4 + 8 * (1 - ph), 0, -6)), R=P(lay))
    v.set_key(ROOT, SLAM, P(lay), "linear")
    for f in range(DRAG0, DRAG1 + 1):
        v.set_key(ROOT, f, P(lay), "linear")
    meet(atk, vic, GRAB)
    attach(vic, atk, range(GRAB, DRAG1 + 1), "Head", (0, 0, 0), "Right Arm", (0, -1.0, 0))
    keep_above_ground(vic, range(326, DRAG1 + 1))

    # ---- throw: let go, victim tumbles back-first into the wall
    p0 = root_world(vic, DRAG1)
    end = VIC_WALL
    for f in range(DRAG1 + 1, THROW1 + 1):
        u = (f - DRAG1) / (THROW1 - DRAG1)
        wp = (p0[0] + (end[0] - p0[0]) * u, p0[1] + (end[1] - p0[1]) * u + 5.5 * 4 * u * (1 - u), p0[2] + (end[2] - p0[2]) * u)
        set_root_world(vic, f, wp, (lay[0] + (360.0 - lay[0]) * u, lay[1] * (1 - u), 0.0))
        K(v, f, "linear", RA=P((120 * u + 14, 0, 40 * u)), LA=P((130 * u + 10, 0, -40 * u)), RL=P((10 - 30 * u, 0, 10 * u)), LL=P((6 - 30 * u, 0, -10 * u)),
          H=P((-10 + 30 * u, 0, 0)))
    anchors = {"Right Leg": (1.2, -53.5), "Left Leg": (-1.2, -51.0)}
    bake_footwork(a, anchors, [], DRAG1 + 1, THROW1 + 12)

    # ---- fx: crater at the slam, burning drag line, pillars bursting, dust
    hx, hz = 0.5, Z0
    cine.cracks(SLAM, 20, (hx, 0.03, hz), 7, 12, "#2a2420", "#ff5a1f", 0.14, seed=11)
    cine.ring(SLAM, 22, (hx, 0.08, hz), 0.5, 13, 1.1, 0.15, "#ffd9a0", 0.85, 0.0)
    cine.dome(SLAM, 12, (hx, 0.4, hz), 0.6, 5.0, "#ffffff", 0.3, 0.0)
    cine.burst(SLAM, 12, (hx, 0.8, hz), 0.4, 3.0, "#ffb43a", "#ffffff", spikes=14, streaks=12, rot=5, seed=80)
    cine.emit(SLAM, SLAM, origin=(hx, 0.4, hz), rate=0, burst=40, vel=(0.2, 0.7), dir=(0, 0.8, 0), spread=1.0, grav=0.014, life=(14, 34),
              size=(0.16, 0.03), color=("#ffffff", "#ff7a1a"), alpha=(1, 0), shape="spark", stretch=3.5, seed=81)
    cine.burst_debris(SLAM, (hx, 0.3, hz), 26, 0.3, 0.32, (0.25, 0.75), ROCK, seed=12)
    cine.emit(SLAM, SLAM + 1, origin=(hx, 0.3, hz), rate=0, burst=40, vel=(0.12, 0.4), dir=(0, 1, 0), spread=1.0, grav=0.004, drag=0.05,
              life=(24, 50), size=(0.8, 1.6), color=("#8a7e72", "#4b4540"), alpha=(0.5, 0.0), add=False, radius=0.8, shape="smoke", seed=13)
    cine.flash(SLAM, 4, "#ffffff", 0.25)
    cine.punch_in(SLAM, 0.12, 9)
    cine.shake(SLAM, 20, 0.5)
    layers = [(1.7, "#ff2a00", 0.5), (0.95, "#ffb000", 0.75), (0.35, "#ffffff", 0.95)]
    cine.strip(DRAG0, 40, (SPOT[0], 0.03, Z0), (SPOT[0], 0.03, Z0 - 8.6), layers, "quad_in", fade=(DRAG1 + 20, DRAG1 + 90))
    cine.strip(380, DRAG1 - 380, (SPOT[0], 0.03, Z0 - 8.6), (SPOT[0], 0.03, -52.0), layers, "linear", fade=(DRAG1 + 20, DRAG1 + 90))
    cine.emit(DRAG0, DRAG1, attach={"char": 1, "part": "Head", "off": [0, -0.45, 0]}, rate=5.0, vel=(0.1, 0.4), dir=(0.1, 1, 0.8),
              spread=0.9, grav=0.012, life=(8, 18), size=(0.16, 0.03), color=("#ffffff", "#ff7a1a"), alpha=(0.95, 0.0), shape="spark", stretch=4.0, seed=14)
    cine.emit(DRAG0, DRAG1, attach={"char": 1, "part": "Head", "off": [0, -0.45, 0]}, rate=1.4, vel=(0.02, 0.1), dir=(0, 1, 0.6),
              spread=0.9, grav=-0.001, life=(24, 46), size=(0.9, 1.9), color=("#8a7e72", "#4b4540"), alpha=(0.4, 0.0), add=False, shape="smoke", seed=15)
    cine.glow(DRAG0, DRAG1, attach={"char": 1, "part": "Head", "off": [0, -0.45, 0]}, r0=0.9, r1=0.9, color="#ff7a1a", a0=0.7, a1=0.7, flare=0.9, pulse=0.2)
    cine.trail(DRAG0, DRAG1, 0, "Torso", (0, 0, 0), 12, 1.1, 0.05, "#ffffff", 0.2)
    cine.trail(451, THROW1, 1, "Torso", (0, 0, 0), 12, 1.6, 0.1, "#ffe9c4", 0.5)
    cine.speed.key(334, 0.0).key(352, 0.5, "cubic_out").key(446, 0.5, "linear").key(452, 0.0, "linear")
    cine.speed.key(458, 0.0).key(462, 0.4, "cubic_out").key(477, 0.0, "linear")
    # decorative columns that give the depth
    for k in range(-1, 6):
        for sx in (-24.0, 24.0):
            cine.prop((sx, 9.0, -14.0 - 15.0 * k), (3.0, 18.0, 3.0), "#aeb6c6")
    for (px, pz) in PILLARS:
        hit = next(f for f in range(DRAG0, DRAG1) if point_world(atk, "Right Arm", (0, -1.0, 0), f)[2] < pz + 2.6)
        cine.prop((px, 10.0, pz), (4.4, 20.0, 4.4), "#8e96a8", vis=(0, hit))
        cine.shatter(hit, (px, 10.0, pz), (4.4, 20.0, 4.4), "#8e96a8", (3, 8, 3), (SPOT[0], 0.5, pz + 3.0), 0.55, up=0.18, spin=5.0, seed=hit,
                     colors=["#8e96a8", "#7a8294", "#5a5f6c"])
        cine.flash(hit, 3, "#ffffff", 0.18)
        cine.shake(hit, 14, 0.4)
        cine.burst(hit, 11, (px + 1.0, 2.2, pz + 2.4), 0.5, 4.2, "#ffd27a", "#ffffff", spikes=12, streaks=10, rot=hit, seed=hit)
        cine.emit(hit, hit, origin=(px, 2.0, pz + 2.2), rate=0, burst=36, vel=(0.2, 0.7), dir=(0, 0.5, -0.6), spread=1.0, grav=0.012, life=(14, 34),
                  size=(0.15, 0.03), color=("#ffffff", "#ffb43a"), alpha=(1, 0), shape="spark", stretch=3.5, seed=hit + 1)
        cine.ring(hit, 14, (px, 0.08, pz + 2.2), 0.6, 9, 1.0, 0.1, "#ffd9a0", 0.6, 0.0)
        cine.emit(hit, hit + 1, origin=(px, 1.0, pz + 1.5), rate=0, burst=44, vel=(0.1, 0.45), dir=(0, 0.6, -0.4), spread=1.0, grav=0.003,
                  drag=0.04, life=(30, 60), size=(1.2, 2.6), color=("#a79c92", "#5d5750"), alpha=(0.55, 0.0), add=False, radius=2.2, shape="smoke", seed=hit)

    # ---- cameras
    cine.shot(322, 333, tracking(char_point(vic, "Head"), (5.5, 0.9, 3.4), look_dy=0.2, fov=(46, 36), offset_end=(3.4, 0.6, 2.2)))
    cine.shot(334, 344, dolly((7.0, 1.5, Z0 + 5.0), (6.4, 1.3, Z0 + 4.4), (0.2, 0.9, Z0), (0.2, 0.8, Z0 - 0.3), fov=(42, 38), easing="linear"))
    cine.shot(345, 379, tracking(char_point(atk, "Torso"), (4.6, -0.5, -7.0), look_dy=-0.2, fov=(58, 64), offset_end=(4.8, -0.4, -6.0)))
    cine.shot(380, 411, tracking(char_point(vic, "Head"), (8.0, 1.2, -1.0), look_dy=0.6, fov=(46, 44), offset_end=(8.0, 1.4, 1.5)))
    cine.shot(412, 436, tracking(char_point(vic, "Head"), (6.5, 0.6, -6.5), look_dy=0.6, fov=(52, 56), offset_end=(6.0, 0.4, -4.5)))
    cine.shot(437, 450, tracking(char_point(atk, "Torso"), (-5.0, 2.5, 5.0), look_dy=0.0, fov=(50, 50), offset_end=(-6.0, 4.0, 6.0)))
    cine.shot(451, 468, tracking(char_point(vic, "Torso"), (7.0, 1.0, 4.0), look_dy=0.0, fov=(46, 40), offset_end=(9.0, 2.0, 6.0)))
    cine.shot(469, 477, dolly((14.0, 5.0, -64.0), (12.5, 5.2, -70.0), (0, 6.0, -84.0), (0, 6.0, -87.0), fov=(42, 38), easing="linear"))


def act4(atk: Character, vic: Character, cine: Cinematic) -> None:
    a, v = atk.anim, vic.anim
    wx, wy, wz = VIC_WALL
    ax, az = HAND_X, -55.0

    # ---- wall impact: victim pinned, slides, trembles
    K(v, THROW1, "linear", RA=P((150, 0, 60)), LA=P((160, 0, -60)), RL=P((-22, 0, 24)), LL=P((-22, 0, -24)), H=P((20, 0, 0)))
    for f in range(THROW1 + 1, HIT):
        u = (f - THROW1) / (HIT - THROW1)
        slide = 0.8 * (1 - math.exp(-u * 4))
        bounce = 0.35 * math.exp(-(f - THROW1) / 4.0) * math.cos((f - THROW1) * 1.2)
        set_root_world(vic, f, (wx, wy - slide, wz + bounce), (360.0, 0.0, 0.0))
    for f in range(THROW1 + 2, HIT, 3):
        K(v, f, "linear", H=P((30 + 6 * math.sin(f), 0, 0)), RA=P((150 + 8 * math.sin(f * 0.7), 0, 60)), LA=P((160 + 8 * math.cos(f * 0.8), 0, -60)),
          RL=P((-22 + 6 * math.sin(f * 0.9), 0, 24)), LL=P((-22 + 6 * math.cos(f), 0, -24)), T=tp(0.0, 0))
    v.set_key(ROOT, THROW1, P((360.0, 0, 0), world_to_local(vic, (wx, wy - ROOT_Y, wz))), "linear")

    # ---- attacker: stands, breathes, charges
    K(a, 485, "sine_inout", T=tp(0.0, 4, 0), H=P((6, 0, 0)), RA=P((10, 0, 8)), LA=P((10, 0, -8)), R=P(pos=(ax, 0, az)))
    K(a, CHARGE0, "sine_inout", T=tp(0.0, 2, -4), H=P((4, 0, 0)), RA=P((8, 0, 8)), LA=P((8, 0, -8)), R=P(pos=(ax, 0, az)))
    K(a, 540, "cubic_out", T=tp(0.55, -22, -30), H=P((-10, 0, 0)), RA=P((-62, 0, 14)), LA=P((92, 0, -20)), R=P(pos=(ax, 0, az)))
    K(a, 556, "quad_in", T=tp(0.95, -30, -42), H=P((-14, 0, 0)), RA=P((-86, 0, 18)), LA=P((100, 0, -24)), R=P(pos=(ax, 0, az + 0.3)))
    tremble(a, "RA", 524, 556, 3.0, 0.03)
    tremble(a, "T", 530, 556, 1.2, 0.02)
    bake_footwork(a, {"Right Leg": (1.3, -53.5), "Left Leg": (-1.3, -51.0)}, [], THROW1 + 13, COMET0 - 1)

    # comet: ~34 studs in 7 frames, body horizontal, fist leading; hits at HIT
    K(a, COMET0, "linear", T=tp(0.9, -30, -44), RA=P((-90, 0, 18)), LA=P((100, 0, -24)), R=P(pos=(ax, 0.0, az + 0.3)),
      RL=a.sample_part("Right Leg", COMET0 - 1), LL=a.sample_part("Left Leg", COMET0 - 1))
    K(a, COMET0 + 3, "linear", T=tp(0.2, -78, -10), H=P((-30, 0, 0)), RA=P((150, 0, 4)), LA=P((-30, 0, -14)), R=P(pos=(ax * 0.4, 1.1, az - 12.0)),
      RL=P((60, 0, 6)), LL=P((70, 0, -6)))
    K(a, HIT, "linear", T=tp(0.1, -52, -4), H=P((-24, 0, 0)), RA=P((112, 0, 3), (0, 0, -0.9)), LA=P((-60, 0, -10)), R=P(pos=(ax * 0.1, 0.9, WALL_Z + 5.0 - 0.0)),
      RL=P((40, 0, 6)), LL=P((54, 0, -6)))
    K(a, HIT + 6, "cubic_out", T=tp(0.0, -14, -6), H=P((-8, 0, 0)), RA=P((118, 0, 3), (0, 0, -0.6)), LA=P((-30, 0, -14)), R=P(pos=(0, 0.2, WALL_Z - 0.6)),
      RL=P((14, 0, 6)), LL=P((-12, 0, -6)))
    K(a, HIT + 30, "sine_inout", T=tp(0.0, 4, -2), H=P((-4, 0, 0)), RA=P((60, 0, 8)), LA=P((18, 0, -8)), R=P(pos=(0, 0, WALL_Z - 0.8)),
      RL=P((4, 0, 4)), LL=P((-4, 0, -4)))
    K(a, 700, "linear", T=tp(0.0, 2, -2), H=P((-2, 0, 0)), RA=P((10, 0, 8)), LA=P((10, 0, -8)), R=P(pos=(0, 0, WALL_Z - 0.8)),
      RL=P((2, 0, 4)), LL=P((-2, 0, -4)))
    K(a, N_FRAMES - 1, "linear", H=P((6, -20, 0)))

    # ---- victim: driven through the wall, tumbles, lands
    pos = [wx, wy - 0.4, wz]
    vel = [0.0, 0.55, -2.2]
    rx = 360.0
    land = None
    for f in range(HIT, N_FRAMES):
        if f > HIT:
            vel[1] -= 0.05
            vel[2] *= 0.965
            pos = [pos[0] + vel[0], pos[1] + vel[1], pos[2] + vel[2]]
            if pos[1] < 0.55:
                pos[1] = 0.55
                if abs(vel[1]) > 0.25:
                    vel[1] = -vel[1] * 0.4
                    vel[2] *= 0.7
                    land = land or f
                else:
                    vel[1] = 0.0
                    vel[2] *= 0.9
                    if abs(vel[2]) < 0.03:
                        vel[2] = 0.0
        spin = 16.0 if land is None else max(0.0, 16.0 - 2.0 * (f - land))
        rx += spin
        set_root_world(vic, f, tuple(pos), (rx, 0.0, 0.0))
    # settle the final rotation onto the nearest "lying on the back" angle
    end_rx = 90.0 + 360.0 * math.ceil((rx - 90.0) / 360.0)
    for f in range(HIT, N_FRAMES):
        r = v.sample_root(f)
        k = min(1.0, max(0.0, (f - (land or HIT) - 2) / 14.0))
        v.set_key(ROOT, f, P((r.rot[0] * (1 - k) + end_rx * k if k > 0 else r.rot[0], 0.0, 0.0), r.pos), "linear")
    K(v, HIT, "linear", H=P((-40, 0, 0)), RA=P((170, 0, 50)), LA=P((170, 0, -50)), RL=P((-40, 0, 20)), LL=P((-40, 0, -20)))
    K(v, HIT + 14, "linear", RA=P((120, 0, 70)), LA=P((100, 0, -70)), RL=P((-10, 0, 20)), LL=P((-30, 0, -20)), H=P((-10, 0, 0)))
    K(v, (land or HIT + 30) + 14, "quad_out", RA=P((12, 0, 70)), LA=P((20, 0, -80)), RL=P((6, 0, 14)), LL=P((2, 0, -20)), H=P((0, 0, 0)))
    K(v, N_FRAMES - 1, "linear", RA=P((12, 0, 70)), LA=P((20, 0, -80)))
    keep_above_ground(vic, range(HIT, N_FRAMES))

    # ---- set: the wall, in three parts so the middle can be blown out
    cine.prop((-21.0, 15.0, WALL_Z), (26.0, 30.0, 4.0), "#5f6679")
    cine.prop((21.0, 15.0, WALL_Z), (26.0, 30.0, 4.0), "#5f6679")
    cine.prop((0.0, 15.0, WALL_Z), (16.0, 30.0, 4.0), "#5f6679", vis=(0, HIT))
    for (px, py, pz, sx, sy) in ((-26, 14, -160, 14, 28), (14, 20, -175, 12, 40), (38, 12, -150, 16, 24), (-44, 18, -190, 20, 36)):
        cine.prop((px, py, pz), (sx, sy, sx), "#b9c0cf")
    cine.shatter(HIT, (0.0, 15.0, WALL_Z), (16.0, 30.0, 4.0), "#5f6679", (6, 7, 2), (0.0, 5.0, WALL_Z + 8.0), 0.62, up=0.25, spin=4.0,
                 seed=77, colors=["#5f6679", "#555c6f", "#474d5e"])

    # ---- fx: wall impact
    ix, iy, iz = 0.0, 6.4, WALL_Z + 2.02
    cine.cracks(THROW1, 28, (ix, iy, iz), 15, 18, "#2a2622", "#ff7a2a", 0.17, n=(0, 0, 1), seed=21, fade=(HIT, HIT + 2))
    cine.ring(THROW1, 20, (ix, iy, iz), 0.8, 13, 1.3, 0.2, "#ffe9c4", 0.85, 0.0, n=(0, 0, 1))
    cine.dome(THROW1, 12, (ix, iy, iz - 0.5), 1.0, 6.0, "#ffffff", 0.3, 0.0)
    cine.burst(THROW1, 12, (ix, iy, iz + 0.8), 0.6, 5.0, "#ffb43a", "#ffffff", spikes=15, streaks=12, rot=14, seed=90)
    for k in range(5):
        a_ = k * 1.26 + 0.4
        cine.bolt(THROW1 + 1, THROW1 + 7, a=(ix, iy, iz + 0.3), b=(ix + math.cos(a_) * 8.0, iy + math.sin(a_) * 8.0, iz + 0.3), width=0.1,
                  color="#ffb43a", core="#ffffff", segs=9, jitter=0.9, branch=0.3, seed=91 + k)
    cine.emit(THROW1, THROW1, origin=(ix, iy, iz + 0.6), rate=0, burst=50, vel=(0.25, 0.8), dir=(0, 0.2, 1), spread=1.0, grav=0.012, life=(14, 36),
              size=(0.15, 0.03), color=("#ffffff", "#ffb43a"), alpha=(1, 0), shape="spark", stretch=3.5, seed=96)
    cine.burst_debris(THROW1, (ix, iy, iz + 0.5), 16, 0.32, 0.25, (0.25, 0.75), ROCK, seed=22, direction=(0, 0, 1))
    cine.emit(THROW1, THROW1 + 1, origin=(ix, iy, iz + 0.5), rate=0, burst=60, vel=(0.1, 0.4), dir=(0, 0.2, 1), spread=1.0, grav=0.003, drag=0.04,
              life=(30, 70), size=(1.2, 2.8), color=("#a79c92", "#5d5750"), alpha=(0.55, 0.0), add=False, radius=1.8, shape="smoke", seed=23)
    cine.flash(THROW1, 4, "#ffffff", 0.35)
    cine.punch_in(THROW1, 0.1, 10)
    cine.shake(THROW1, 32, 0.9)
    cine.vignette.key(THROW1, 0.3, "linear")

    # ---- fx: charge-up
    cine.cracks(CHARGE0, 32, (ax, 0.03, az), 10, 14, "#2a2420", "#ff5a1f", 0.15, seed=31)
    FIST = {"char": 0, "part": "Right Arm", "off": [0, -1.0, 0]}
    cine.emit(CHARGE0 + 4, 556, attach=FIST, rate=3.5, vel=(0.0, 0.0), dir=(0, 1, 0), spread=1.0,
              life=(26, 26), size=(0.12, 0.03), color=("#fff3c4", "#ff4a10"), alpha=(0.0, 1.0), converge=5.5, shape="spark", stretch=5.0, seed=32)
    cine.glow(CHARGE0, 556, attach=FIST, r0=0.3, r1=2.6, color="#ff7a2a", a0=0.2, a1=0.95, flare=1.6, pulse=0.12)
    tb = CHARGE0 + 6
    rg = random.Random(77)
    while tb < 556:  # arcs from the ground to the fist, more and more often
        for k in range(1 + int((tb - CHARGE0) / 14)):
            a_ = rg.random() * math.tau
            r_ = 2.5 + rg.random() * 4.0
            cine.bolt(tb, tb + 4, a=(ax + math.cos(a_) * r_, 0.05, az + math.sin(a_) * r_), attach_b=FIST, width=0.08, color="#ff6a2a", core="#fff0c8",
                      segs=8, jitter=0.7, branch=0.2, seed=int(tb * 11 + k))
        tb += max(3, 9 - int((tb - CHARGE0) / 6))
    cine.emit(CHARGE0, 556, origin=(ax, 0.8, az), rate=1.8, vel=(0.05, 0.18), dir=(0, 1, 0), spread=0.5, grav=-0.004, life=(26, 50),
              size=(0.5, 0.07), color=FIRE, alpha=(0.7, 0.0), radius=2.2, shape="flame", seed=33)
    rnd = __import__("random").Random(51)
    for i in range(14):
        ang = rnd.random() * math.tau
        rad = 2.2 + rnd.random() * 3.4
        sz = 0.4 + rnd.random() * 0.7
        cine.debris_piece(CHARGE0 + int(rnd.random() * 20), (ax + math.cos(ang) * rad, 0.3, az + math.sin(ang) * rad), (0, 0.018 + rnd.random() * 0.02, 0),
                          (sz, sz * 0.7, sz * 0.9), rnd.choice(ROCK), (rnd.random() * 2, rnd.random() * 2, rnd.random() * 2), g=-0.0014, bounce=0.3, g2=0.016, tg=COMET0)
    for t, r1 in ((530, 8), (544, 12), (554, 16)):
        cine.ring(t, 22, (ax, 0.08, az), 0.6, r1, 0.8, 0.15, "#ff8a3d", 0.5, 0.0)
    cine.line(540, 24, (ax, 0.0, az), (ax, 34, az), 1.8, 0.0, "#ff7a2a", 0.22, 0.0, easing="quad_out")

    # ---- fx: comet and breakthrough
    cine.burst(COMET0, 8, (ax, 0.6, az), 0.5, 3.4, "#ffb43a", "#ffffff", spikes=12, streaks=10, rot=0, seed=97)
    cine.punch_in(COMET0, 0.1, 6)
    cine.trail(COMET0, HIT + 1, 0, "Torso", (0, 0, 0), 10, 1.6, 0.2, "#ffe9c4", 0.4)
    cine.trail(COMET0, HIT + 1, 0, "Right Arm", (0, -1.0, 0), 10, 1.0, 0.1, "#ff6a2a", 0.6)
    cine.line(COMET0 + 1, 24, (ax, 2.4, az), (0.0, 5.0, WALL_Z + 2.0), 2.2, 0.0, "#fff3d6", 0.8, 0.0, easing="quad_out")
    cine.ring(COMET0, 18, (ax, 0.08, az), 0.6, 20, 1.2, 0.1, "#ffd9a0", 0.8, 0.0)
    cine.emit(COMET0, COMET0 + 1, origin=(ax, 0.5, az), rate=0, burst=60, vel=(0.2, 0.6), dir=(0, 0.4, 1), spread=1.0, grav=0.004, drag=0.05,
              life=(20, 50), size=(1.2, 2.4), color=("#a79c92", "#5d5750"), alpha=(0.5, 0.0), add=False, radius=1.5, seed=41)
    bx, by, bz = 0.0, 5.0, WALL_Z + 2.0
    cine.dome(HIT, 22, (bx, by, bz), 1.0, 20.0, "#ffffff", 0.18, 0.0)
    cine.burst(HIT, 14, (bx, by, bz + 1.5), 0.8, 5.6, "#ffb43a", "#ffffff", spikes=20, streaks=18, rot=7, seed=98)
    cine.burst(HIT + 3, 12, (bx, by, bz + 1.5), 0.6, 3.6, "#ffe2a0", "#ffffff", spikes=14, streaks=10, rot=22, seed=99)
    cine.glow(HIT, HIT + 40, c=(bx, by, bz + 1.0), r0=2.4, r1=1.2, color="#ff8a3d", a0=0.7, a1=0.0, flare=2.0)
    for k in range(9):
        a_ = k * 0.7 + 0.2
        cine.bolt(HIT + 1, HIT + 9, a=(bx, by, bz + 1.0), b=(bx + math.cos(a_) * 13.0, by + math.sin(a_) * 11.0, bz + 1.0 + (k % 3 - 1) * 4.0), width=0.14,
                  color="#ffb43a", core="#ffffff", segs=11, jitter=1.4, branch=0.3, seed=100 + k)
    cine.slash(HIT - 1, 12, (bx, by, bz + 3.0), (0, 0, 1), 9.0, -30, 150, 1.8, "#ffd27a")
    cine.ring(HIT, 30, (bx, by, bz), 1.0, 30, 1.6, 0.2, "#fff3d6", 0.8, 0.0, n=(0, 0, 1))
    cine.ring(HIT + 3, 30, (bx, 0.1, bz), 1.0, 40, 2.0, 0.2, "#ffd9a0", 0.8, 0.0)
    cine.line(HIT, 30, (bx, by, bz + 40), (bx, by, bz - 60), 2.2, 0.0, "#ffffff", 0.55, 0.0, easing="quad_out")
    cine.burst_debris(HIT, (bx, by, bz - 1.0), 60, 0.6, 0.5, (0.3, 1.0), ROCK, seed=61, direction=(0, 0, -1))
    cine.emit(HIT, HIT + 1, origin=(bx, by, bz - 1), rate=0, burst=70, vel=(0.2, 1.1), dir=(0, 0.1, -1), spread=1.0, grav=0.004, drag=0.035,
              life=(50, 110), size=(1.6, 4.0), color=("#b4aaa0", "#6a635c"), alpha=(0.4, 0.0), add=False, radius=4.0, shape="smoke", seed=62)
    cine.emit(HIT, HIT + 6, origin=(bx, by, bz), rate=0, burst=160, vel=(0.3, 1.3), dir=(0, 0.2, -1), spread=1.0, grav=0.01, life=(14, 44),
              size=(0.2, 0.04), color=("#ffffff", "#ff7a1a"), alpha=(0.95, 0.0), shape="spark", stretch=4.0, seed=63)
    cine.emit(HIT, HIT + 3, origin=(bx, by, bz), rate=0, burst=60, vel=(0.2, 0.9), dir=(0, 0.2, -1), spread=1.0, grav=0.015, life=(30, 70),
              size=(0.2, 0.2), color=("#7a7f90", "#3a3f4c"), alpha=(1, 1), add=False, shape="shard", seed=66)
    cine.emit(HIT + 6, HIT + 50, origin=(0, 6, WALL_Z - 6), rate=0.5, vel=(0.03, 0.12), dir=(0, 1, 0), spread=1.0, grav=0.0, life=(70, 130),
              size=(3.0, 5.0), color=("#b4aaa0", "#6a635c"), alpha=(0.18, 0.0), add=False, radius=12.0, shape="smoke", seed=64)
    cine.emit(HIT + 6, 740, origin=(0, 8, WALL_Z - 4), rate=1.4, vel=(0.01, 0.08), dir=(0, 1, 0), spread=1.0, grav=-0.0005, life=(90, 200),
              size=(0.1, 0.02), color=("#ffd27a", "#ff3a00"), alpha=(1.0, 0.0), radius=15.0, shape="spark", stretch=2.0, seed=65)
    cine.glow(HIT + 20, 700, c=(bx, by, bz + 0.5), r0=3.2, r1=2.6, color="#ff6a2a", a0=0.22, a1=0.12, pulse=0.1)
    rb2 = random.Random(31)
    for k in range(18):  # embers of lightning crawling around the hole
        t_ = HIT + 14 + k * 9 + rb2.randint(0, 5)
        a_ = rb2.random() * math.tau
        cine.bolt(t_, t_ + 3, a=(bx + math.cos(a_) * 5, by + math.sin(a_) * 5, bz + 1), b=(bx + math.cos(a_ + 0.6) * 9, by + math.sin(a_ + 0.6) * 8, bz + 1),
                  width=0.07, color="#ffb43a", core="#ffffff", segs=7, jitter=0.6, branch=0.3, seed=140 + k)
    if land:  # the body skids in: dust wave and a ring where it lands
        lx, lz = point_world(vic, "Torso", (0, 0, 0), land)[0], point_world(vic, "Torso", (0, 0, 0), land)[2]
        cine.ring(land, 26, (lx, 0.08, lz), 0.6, 12, 1.0, 0.1, "#ffd9a0", 0.6, 0.0)
        cine.emit(land, land + 14, origin=(lx, 0.4, lz + 2.0), rate=6, vel=(0.1, 0.35), dir=(0, 0.4, 1), spread=1.0, grav=0.003, drag=0.05, life=(30, 70),
                  size=(1.4, 3.2), color=("#a79c92", "#5d5750"), alpha=(0.5, 0.0), add=False, shape="smoke", radius=1.2, seed=150)
        cine.shake(land, 14, 0.5)
    cine.flash(HIT, 3, "#ffffff", 0.5)
    cine.flash(HIT + 3, 14, "#ffd9a8", 0.22)
    cine.punch_in(HIT, 0.2, 14)
    cine.shake(HIT, 60, 1.6)

    # ---- screen
    cine.bars.key(HIT - 20, 0.115).key(HIT + 20, 0.16, "sine_inout").key(N_FRAMES - 1, 0.2, "sine_inout")
    cine.bright.key(299, 1.0).key(340, 0.92, "sine_inout").key(THROW1, 1.0, "linear").key(THROW1 + 20, 0.88, "sine_inout")
    cine.bright.key(CHARGE0, 0.88, "linear").key(556, 0.5, "quad_in").key(COMET0 + 1, 0.8, "linear").key(HIT - 1, 0.95, "linear")
    cine.bright.key(HIT, 1.05, "linear").key(HIT + 14, 1.0, "cubic_out").key(N_FRAMES - 36, 1.0, "linear").key(N_FRAMES - 1, 0.0, "quad_in")
    cine.vignette.key(300, 0.22, "linear").key(CHARGE0, 0.3, "sine_inout").key(556, 0.62, "quad_in").key(HIT, 0.2, "cubic_out").key(HIT + 60, 0.26, "sine_inout")
    cine.tint.key(THROW1 + 20, 0.0, "linear").key(556, 0.22, "quad_in").key(HIT, 0.0, "cubic_out")
    cine.speed.key(CHARGE0 + 30, 0.0, "linear").key(COMET0, 0.0, "linear").key(COMET0 + 2, 1.0, "cubic_out").key(HIT + 4, 1.0, "linear").key(HIT + 14, 0.0, "linear")

    # ---- cameras
    cine.shot(478, 520, dolly((6.4, 6.0, -79.2), (5.0, 5.8, -80.6), (0.0, 5.8, -87.5), (0.0, 5.6, -87.5), fov=(36, 30), easing="quad_out"))
    cine.shot(CHARGE0, 555, dolly((3.8, 1.1, -64.0), (2.4, 1.4, -60.4), (-1.0, 2.5, -55.0), (-1.0, 2.7, -55.0), fov=(44, 34), easing="sine_inout"))
    cine.shot(556, 563, dolly((3.8, 2.6, -85.0), (3.4, 2.6, -83.5), (-0.6, 2.0, -62.0), (-0.2, 2.4, -70.0), fov=(40, 52), easing="quad_in"))
    cine.shot(HIT, HIT + 26, dolly((17.0, 4.6, -83.0), (13.5, 5.6, -80.0), (0.0, 5.0, -89.0), (0.0, 5.0, -89.5), fov=(40, 46), easing="quad_out"))
    cine.shot(HIT + 27, 650, dolly((4.0, 6.0, -76.0), (9.0, 9.0, -84.0), (0.0, 2.0, -100.0), (0.0, 1.5, -118.0), fov=(46, 48), easing="sine_inout"))
    cine.shot(651, N_FRAMES - 1, dolly((9.0, 9.0, -84.0), (20.0, 16.0, -96.0), (0.0, 1.5, -118.0), (0.0, 2.5, -112.0), fov=(50, 56), easing="sine_inout"))


def build(n_frames: int = N_FRAMES) -> Scene:
    atk = Character("Barbare", Animation("berserker", fps=60, archetype="cinematic"), base_pos=(0, 0, 0), colors=ATK_COLORS)
    vic = Character("Victime", Animation("victim", fps=60, archetype="cinematic"), base_pos=(0, 0, -6), base_yaw=180.0, colors=VIC_COLORS)
    cine = Cinematic(n_frames)
    for name, (grid, frames) in {"impact_star": (4, 8), "smoke": (8, 64)}.items():  # baked by `python -m tsb_engine.textures`
        cine.use_sheet(name, f"assets/flipbooks/{name}_{grid}x{grid}_{'24' if name != 'smoke' else '15'}fps.png", grid, frames)
    cine.sky_color, cine.floor_color = "#39406a", "#4a4a5e"  # dusk: glows need a dark ground to read
    cine.shot(0, n_frames, dolly((6, 3, 6), (6, 3, 6), (0, 2, -4), (0, 2, -4)))  # fallback, overridden by acts
    act1(atk, vic, cine)
    act2(atk, vic, cine)
    act3(atk, vic, cine)
    act4(atk, vic, cine)
    scene = Scene("Ultime du Berserker", [atk, vic], cine=cine)
    scene.markers = [
        {"f": 0, "label": "acte I · éveil", "act": True}, {"f": 122, "label": "rugissement"},
        {"f": 166, "label": "acte II · rafale", "act": True}, {"f": UPPERCUT, "label": "uppercut"},
        {"f": GRAB, "label": "acte III · traînée", "act": True}, {"f": SLAM, "label": "plaqué"}, {"f": THROW1, "label": "mur"},
        {"f": CHARGE0, "label": "acte IV · comète", "act": True}, {"f": HIT, "label": "impact"},
    ]
    return scene


def roblox_markers() -> dict[str, list[tuple[int, str]]]:
    """KeyframeMarkers per character (phases follow motion-tools' taxonomy: anticipation / hit / follow-through / recovery)."""
    atk = [(t - 4, "Windup") for t in PUNCH_T[:1]] + [(t, "Hit") for t in PUNCH_T] + [(UPPERCUT - 6, "Windup"), (UPPERCUT, "Uppercut"), (GRAB, "Grab"),
           (SLAM, "Slam"), (THROW1, "Throw"), (CHARGE0, "ChargeStart"), (COMET0, "CometStart"), (HIT, "FinalHit"), (HIT + 30, "Recovery")]
    vic = [(t, "Hit") for t in PUNCH_T] + [(UPPERCUT, "Launch"), (THROW1, "WallImpact"), (HIT, "BreakThrough")]
    return {"berserker": sorted(atk), "victim": sorted(vic)}


def hit_events(scene) -> list[dict]:
    """Every hit of the ultimate as game data (trauma / FOV punch / optional hit-stop / VFX seed)."""
    from tsb_engine.roblox_cues import hit_event

    atk, vic = scene.characters
    pos = lambda f: point_world(vic, "Torso", (0, 0, 0), f)
    ev = [hit_event(t, "light" if i < 8 else "heavy", f"punch{i + 1}", 100 + i, pos(t), "berserker", "victim") for i, t in enumerate(PUNCH_T)]
    ev.append(hit_event(UPPERCUT, "heavy", "uppercut", 120, pos(UPPERCUT), "berserker", "victim"))
    ev.append(hit_event(SLAM, "slam", "slam", 121, pos(SLAM), "berserker", "victim"))
    for k, (px, pz) in enumerate(PILLARS):
        f = next(f for f in range(DRAG0, DRAG1) if point_world(atk, "Right Arm", (0, -1.0, 0), f)[2] < pz + 2.6)
        ev.append(hit_event(f, "heavy", f"pillar{k + 1}", 130 + k, (px, 2.0, pz), "berserker", "pillar"))
    ev.append(hit_event(THROW1, "slam", "wall_impact", 140, pos(THROW1), "berserker", "wall"))
    ev.append(hit_event(HIT, "ultimate", "final_hit", 150, pos(HIT), "berserker", "victim"))
    return sorted(ev, key=lambda e: e["frame"])
