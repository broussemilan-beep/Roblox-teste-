"""Berserker ultimate: a ~13 s cinematic (rage awakening -> flurry -> grab and drag -> comet finish).

Everything is authored with tsb_engine; numbers are creative starting values, not TSB data.
World: Y up, attacker starts at the origin facing -Z, victim 6 studs ahead facing it,
pillars at z = -22 / -38, wall at z = -90.
"""

from __future__ import annotations

import math

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

    # ---- attacker: crouched and trembling -> deep breath -> ROAR (arched back, arms out) -> lock-on stare
    K(a, 0, T=tp(0.45, -20), H=P((-14, 0, 0)), RA=P((12, 0, 8)), LA=P((12, 0, -8)))
    K(a, 60, T=tp(0.55, -24), H=P((-18, 0, 0)), RA=P((20, 0, 10)), LA=P((20, 0, -10)))
    K(a, 100, "quad_in", T=tp(0.72, -30, 4), H=P((-24, 0, 0)), RA=P((-25, 0, 6)), LA=P((-25, 0, -6)))
    K(a, 112, "cubic_out", T=tp(0.64, -27, 0), H=P((-22, 0, 0)), RA=P((-28, 0, 6)), LA=P((-28, 0, -6)))
    K(a, 122, "cubic_out", T=tp(0.05, 16), H=P((34, 0, 0)), RA=P((-8, 0, 74)), LA=P((-8, 0, -74)))
    K(a, 136, "sine_inout", T=tp(0.0, 20, 0), H=P((38, 0, 0)), RA=P((-12, 0, 78)), LA=P((-12, 0, -78)))
    K(a, 150, "cubic_out", T=tp(0.46, -26), H=P((0, 0, 0)), RA=P((26, 0, 10)), LA=P((26, 0, -10)))
    K(a, 166, "linear", T=tp(0.42, -24), H=P((0, 0, 0)), RA=P((30, 0, 10)), LA=P((30, 0, -10)))
    tremble(a, "RA", 0, 58, 2.0, 0.02)
    tremble(a, "LA", 1, 59, 2.0, 0.02)
    tremble(a, "RA", 60, 98, 3.5, 0.03)
    tremble(a, "LA", 61, 99, 3.5, 0.03)
    tremble(a, "RA", 100, 121, 6.0, 0.05)
    tremble(a, "LA", 101, 121, 6.0, 0.05)
    tremble(a, "RA", 124, 135, 3.0, 0.03)
    tremble(a, "LA", 125, 135, 3.0, 0.03)
    tremble(a, "T", 0, 110, 0.8, 0.0, 3)
    K(a, 120, "cubic_out", R=P(pos=(0, 0, 0)))
    K(a, 124, "cubic_out", R=P(pos=(0, 0.22, 0)))  # the roar lifts him onto his toes
    K(a, 134, "sine_inout", R=P(pos=(0, 0, 0)))

    # ---- victim: guard, blown back by the roar
    K(v, 0, T=tp(0.12, -4), H=P((0, 4, 0)), RA=P((62, 0, 12)), LA=P((50, 0, -16)))
    K(v, 112, T=tp(0.14, -4), H=P((0, 4, 0)), RA=P((62, 0, 12)), LA=P((50, 0, -16)))
    K(v, 124, "cubic_out", T=tp(0.2, 14), H=P((18, 0, 0)), RA=P((40, 0, 28)), LA=P((36, 0, -28)))
    K(v, 140, "sine_inout", T=tp(0.28, 4), H=P((8, 0, 0)), RA=P((70, 0, 16)), LA=P((60, 0, -16)))
    K(v, 170, T=tp(0.3, -6), H=P((0, 0, 0)), RA=P((72, 0, 14)), LA=P((62, 0, -14)))
    K(v, 122, "cubic_out", R=P(pos=(0, 0, 0)))
    K(v, 134, "cubic_out", R=P(pos=(0, 0, 1.0)))
    K(v, 170, R=P(pos=(0, 0, 1.0)))

    # ---- footwork
    bake_footwork(a, {"Right Leg": (1.5, 0.2), "Left Leg": (-1.5, 0.2)}, [], 0, 166)
    bake_footwork(
        v, {"Right Leg": (1.2, 1.2), "Left Leg": (-0.8, -0.5)},
        [Step("Left Leg", 124, 131, (-0.8, 0.45), 0.4), Step("Right Leg", 128, 136, (1.2, 1.9), 0.4)],
        0, 170,
    )

    # ---- set: aura, floating rocks, cracks, shockwaves
    cine.emit(36, 108, attach={"char": 0, "part": "Torso", "off": [0, -0.6, 0]}, rate=1.0, vel=(0.03, 0.1), dir=(0, 1, 0),
              spread=0.5, grav=-0.003, life=(26, 46), size=(0.38, 0.05), color=FIRE, alpha=(0.35, 0.0), radius=1.1, seed=1)
    cine.emit(108, 170, attach={"char": 0, "part": "Torso", "off": [0, -0.6, 0]}, rate=1.6, vel=(0.05, 0.16), dir=(0, 1, 0),
              spread=0.55, grav=-0.004, life=(26, 50), size=(0.3, 0.05), color=FIRE, alpha=(0.22, 0.0), radius=1.3, seed=2)
    import random
    rnd = random.Random(11)
    for i in range(16):
        ang = rnd.random() * math.tau
        rad = 2.4 + rnd.random() * 3.6
        s = 0.45 + rnd.random() * 0.8
        cine.debris_piece(46 + int(rnd.random() * 56), (math.cos(ang) * rad, 0.3, math.sin(ang) * rad),
                          (0, 0.015 + rnd.random() * 0.02, 0), (s, s * 0.7, s * 0.9), rnd.choice(ROCK),
                          (rnd.random() * 2, rnd.random() * 2, rnd.random() * 2), g=-0.0012, bounce=0.3, g2=0.014, tg=124)
    cine.cracks(80, 24, (0, 0, 0), 5.5, 9, "#2a2420", "#ff5a1f", 0.1, seed=3)
    cine.cracks(122, 20, (0, 0, 0), 12, 14, "#1f1a17", "#ff5a1f", 0.16, seed=4)
    for t, r1 in ((112, 6), (122, 15), (131, 20)):
        cine.ring(t, 22, (0, 0.08, 0), 0.6, r1, 0.9, 0.2, "#ff8a3d", 0.55, 0.0)
    cine.dome(122, 18, (0, 3.0, 0), 1.0, 6.5, "#ff9a4a", 0.3, 0.0)
    cine.line(122, 34, (0, 0, 0), (0, 30, 0), 2.2, 0.0, "#ff7a2a", 0.22, 0.0, easing="quad_out")
    cine.emit(122, 124, origin=(0, 0.3, 0), rate=0, burst=70, vel=(0.25, 0.6), dir=(1, 0.15, 0), spread=1.0, grav=0.004,
              drag=0.04, life=(30, 60), size=(0.9, 1.8), color=("#8a7e72", "#4b4540"), alpha=(0.5, 0.0), add=False, radius=1.2, seed=5)

    # ---- camera
    cine.shot(0, 61, dolly((8.0, 1.0, -2.6), (6.4, 1.3, -1.6), (0, 2.0, -2.8), (0, 2.3, -2.2), fov=(50, 44), easing="sine_inout"))
    cine.shot(62, 109, orbit((0, 2.4, 0), 10.5, 35, 125, 1.4, 3.8, look_dy=0.3, fov=48, easing="sine_inout"))
    cine.shot(110, 137, dolly((1.6, 3.0, -8.6), (0.8, 3.5, -6.0), (0, 3.4, 0), (0, 3.8, 0), fov=(44, 30), easing="quad_out"))
    cine.shot(138, 169, dolly((2.4, 1.4, 6.6), (1.6, 1.6, 5.0), (0, 3.0, -4.8), (0, 2.9, -5.0), fov=(54, 48), easing="sine_inout"))
    cine.shake(122, 28, 0.45)
    cine.shake(110, 12, 0.08)
    cine.bars.key(0, 0.115)
    cine.vignette.key(0, 0.15).key(90, 0.32, "quad_in").key(122, 0.58, "cubic_out").key(150, 0.22, "sine_inout")
    cine.bright.key(0, 1.0).key(60, 0.82, "sine_inout").key(120, 0.66, "quad_in").key(124, 0.9, "cubic_out").key(150, 0.78, "sine_inout")
    cine.tint.key(0, 0.0).key(110, 0.0).key(122, 0.16, "cubic_out").key(150, 0.0, "sine_inout")
    cine.speed.key(118, 0.0).key(124, 0.45, "cubic_out").key(136, 0.0, "linear")
    cine.flash(122, 8, "#ffd9a8", 0.3)


def char_point(char: Character, part: str, off=(0.0, 0.0, 0.0)):
    """Callable frame -> world point of a body part (for tracking cameras)."""
    from tsb_engine.kinematics import apply

    return lambda f: apply(char.world_parts(int(f))[part], off)


PUNCH_T = [186 + 8 * i for i in range(9)]  # impact frames of the flurry
UPPERCUT = 262


def act2(atk: Character, vic: Character, cine: Cinematic) -> None:
    a, v = atk.anim, vic.anim

    # ---- attacker: sprint in, 9-punch flurry, uppercut
    K(a, 166, R=P(pos=(0, 0, 0)))
    K(a, 172, "linear", R=P(pos=(0, 0, -1.0)), T=tp(0.5, -38, 0), H=P((-16, 0, 0)), RA=P((-45, 0, 8)), LA=P((-45, 0, -8)))
    K(a, 182, "cubic_out", R=P(pos=(0, 0, -3.0)), T=tp(0.38, -24, -26), H=P((-6, 22, 0)), RA=P((20, 0, 10)), LA=P((-35, 0, -12)))
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        hit, other = ("RA", "LA") if side > 0 else ("LA", "RA")
        reach = -(0.5 + 0.06 * i)
        K(a, t - 4, "linear", **{hit: P((-34, 0, side * 8))})
        K(a, t, "linear", T=tp(0.36, -22, side * 34), **{hit: P((112, 0, side * 3), (0, 0, reach)), other: P((-30, 0, -side * 10))})
        K(a, t + 2, "linear", H=P((-6, -side * 14, 0)))
        K(a, t + 4, "linear", **{hit: P((70, 0, side * 14))})
        K(a, t + 5, "linear", **{other: P((68, 0, -side * 14))})
    K(a, 256, "quad_in", T=tp(0.85, -30, 0), H=P((-14, 0, 0)), RA=P((-70, 0, 20)), LA=P((24, 0, -14)), R=P(pos=(0, 0, -3.0)))
    K(a, UPPERCUT, "cubic_out", T=tp(0.12, 6, 24), H=P((10, 0, 0)), RA=P((128, 0, 8), (0, 0, -0.7)), LA=P((-40, 0, -20)), R=P(pos=(0, 0.3, -3.2)))
    K(a, 268, "cubic_out", T=tp(0.0, 14, 30), RA=P((172, 0, 6)), LA=P((-52, 0, -22)), R=P(pos=(0, 1.2, -3.4)))
    K(a, 280, "sine_inout", T=tp(0.0, 10, 20), H=P((-4, 0, 0)), RA=P((176, 0, 6)), LA=P((-30, 0, -16)), R=P(pos=(0, 2.3, -3.6)))
    K(a, 299, "linear", R=P(pos=(0, 2.4, -3.6)))
    steps = gait_steps(a, 166, 184, first_leg="Left Leg", interval=5, swing=4, lateral=0.75, lift=0.9)
    bake_footwork(a, {"Right Leg": (1.5, 0.2), "Left Leg": (-1.5, 0.2)}, steps, 166, UPPERCUT - 1)
    K(a, UPPERCUT, "linear", RL=P((24, 0, 4)), LL=P((-36, 0, -4)))
    K(a, 270, "linear", RL=P((10, 0, 6)), LL=P((-20, 0, -6)))
    K(a, 282, "linear", RL=P((32, 0, 6)), LL=P((-12, 0, -6)))
    K(a, 299, "linear", RL=P((30, 0, 6)), LL=P((-10, 0, -6)))

    # ---- victim: juggled by every hit, launched by the uppercut
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        K(v, t, "cubic_out", T=tp(0.3, -34, side * 16), RA=P((98, 0, 24)), LA=P((92, 0, -24)), R=P(pos=(0, 0, 1.0 + 0.08 * (i + 1))))
        K(v, t + 2, "linear", H=P((-28, 0, side * 8)))
        K(v, t + 5, "quad_out", T=tp(0.28, -8, 0), RA=P((72, 0, 14)), LA=P((62, 0, -14)))
        K(v, t + 7, "linear", H=P((-4, 0, 0)))
    K(v, UPPERCUT, "cubic_out", T=tp(0.1, 22, 0), H=P((22, 0, 0)), RA=P((150, 0, 34)), LA=P((158, 0, -34)), R=P(pos=(0, 0.1, 1.9)))
    K(v, 272, "quad_out", T=tp(0.0, 30, 0), H=P((30, 0, 0)), RA=P((160, 0, 40)), LA=P((165, 0, -40)), R=P((34, 0, 0), (0, 3.4, 2.2)))
    K(v, 284, "sine_inout", T=tp(0.0, 34, 0), RA=P((120, 0, 30)), LA=P((130, 0, -30)), R=P((64, 0, 0), (0, 3.8, 2.4)))
    K(v, 299, "linear", R=P((66, 0, 0), (0, 3.7, 2.4)))
    bake_footwork(v, {"Right Leg": (1.2, 1.9), "Left Leg": (-0.8, 0.45)}, [], 166, UPPERCUT - 1)
    K(v, UPPERCUT, "linear", RL=P((-26, 0, 6)), LL=P((-38, 0, -8)))
    K(v, 276, "linear", RL=P((-10, 0, 10)), LL=P((-24, 0, -12)))
    K(v, 299, "linear", RL=P((-18, 0, 10)), LL=P((-30, 0, -12)))

    # ---- fx
    cine.trail(166, 184, 0, "Torso", (0, 0, 0), 9, 1.5, 0.1, "#ffffff", 0.35)
    cine.emit(166, 184, attach={"char": 0, "part": "Right Leg", "off": [0, -1, 0]}, rate=2.0, vel=(0.02, 0.1), dir=(0, 1, 0.4),
              spread=0.9, grav=0.0, life=(20, 34), size=(0.5, 1.2), color=("#9a8f84", "#5b554f"), alpha=(0.35, 0.0), add=False, seed=21)
    cine.emit(36, 300, attach={"char": 0, "part": "Torso", "off": [0, -0.6, 0]}, rate=1.2, vel=(0.05, 0.14), dir=(0, 1, 0),
              spread=0.55, grav=-0.004, life=(24, 44), size=(0.42, 0.05), color=FIRE, alpha=(0.32, 0.0), radius=1.2, seed=22) if False else None
    for i, t in enumerate(PUNCH_T):
        side = 1.0 if i % 2 == 0 else -1.0
        arm = "Right Arm" if side > 0 else "Left Arm"
        p = point_world(atk, arm, (0, -1, 0), t)
        cine.emit(t, t, attach={"char": 0, "part": arm, "off": [0, -1, 0]}, rate=0, burst=16, vel=(0.3, 0.75), dir=(0, 0.2, 1),
                  spread=1.0, grav=0.012, life=(8, 18), size=(0.16, 0.03), color=("#ffffff", "#ff7a1a"), alpha=(0.9, 0.0), seed=30 + i)
        cine.ring(t, 9, p, 0.3, 2.0, 0.4, 0.05, "#ffe9c4", 0.7, 0.0, n=(0, 0, 1))
        cine.shake(t, 7, 0.08 if i % 2 else 0.12)
    cine.speed.key(180, 0.0).key(188, 0.3, "cubic_out").key(250, 0.3, "linear").key(257, 0.0, "linear")
    up = point_world(atk, "Right Arm", (0, -1, 0), UPPERCUT)
    cine.ring(UPPERCUT, 26, (up[0], 0.08, up[2]), 0.6, 13, 1.4, 0.2, "#ffd9a0", 0.8, 0.0)
    cine.line(UPPERCUT, 30, (up[0], 0.0, up[2]), (up[0], 26, up[2]), 1.8, 0.0, "#fff1d6", 0.55, 0.0, easing="quad_out")
    cine.dome(UPPERCUT, 16, up, 0.8, 6.5, "#ffffff", 0.55, 0.0)
    cine.burst_debris(UPPERCUT, (up[0], 0.2, up[2]), 22, 0.28, 0.35, (0.25, 0.7), ROCK, seed=40)
    cine.flash(UPPERCUT, 7, "#ffffff", 0.55)
    cine.shake(UPPERCUT, 22, 0.55)
    cine.vignette.key(168, 0.2, "linear").key(262, 0.3, "cubic_out").key(290, 0.15, "sine_inout")
    cine.bright.key(166, 0.84, "linear").key(180, 0.95, "sine_inout").key(262, 1.0, "linear")

    # ---- camera
    cine.shot(170, 183, dolly((-4.6, 1.0, -1.0), (-3.6, 1.3, -3.6), (0, 2.0, -0.4), (-0.2, 2.2, -3.4), fov=(56, 50), easing="quad_out"))
    cine.shot(184, 215, orbit((0, 2.7, -4.6), 8.0, 78, 118, 1.7, 2.7, look_dy=0.0, fov=46, easing="sine_inout"))
    cine.shot(216, 233, dolly((-2.0, 1.7, -9.4), (-1.4, 1.9, -8.8), (0.2, 3.0, -3.2), (0.1, 3.1, -3.4), fov=(46, 40), easing="linear"))
    cine.shot(234, 255, dolly((4.4, 2.4, -2.0), (3.6, 2.6, -3.1), (0, 2.8, -4.9), (0, 2.9, -5.0), fov=(44, 38), easing="linear"))
    cine.shot(256, 263, dolly((6.4, 1.2, -1.0), (5.4, 1.0, -2.4), (0, 2.0, -4.4), (0, 2.8, -5.4), fov=(52, 46), easing="quad_in"))
    cine.shot(264, 321, tracking(char_point(vic, "Head"), (4.6, -1.4, 4.2), look_dy=0.2, fov=(56, 46), offset_end=(6.2, 0.6, 5.4)))


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
    K(a, 308, "cubic_out", T=tp(0.0, 8, 10), H=P((-8, 0, 0)), RA=P((152, 0, 8)), LA=P((-50, 0, -22)), R=P(pos=(0, 2.9, -6.6)),
      RL=P((30, 0, 6)), LL=P((-10, 0, -6)))
    K(a, GRAB, "sine_inout", T=tp(0.0, 4, 0), H=P((-6, 0, 0)), RA=P((158, 0, 6)), LA=P((-40, 0, -18)), R=P(pos=(0, 2.9, -7.3)),
      RL=P((24, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 326, "quad_in", T=tp(0.5, -32, 0), H=P((-14, 0, 0)), RA=P((110, 0, 6)), LA=P((-70, 0, -24)), R=P(pos=(HAND_X * 0.5, 1.5, -8.0)),
      RL=P((40, 0, 6)), LL=P((-30, 0, -6)))
    K(a, SLAM, "cubic_in", T=tp(1.1, -55, 0), H=P((-24, 0, 0)), RA=P((50, 0, 0)), LA=P((-60, 0, -14)), R=P(pos=(HAND_X, 0, -8.4)))

    # ---- victim hangs at the apex, then folds forward and is carried down
    K(v, 308, "sine_inout", T=tp(0.0, 36), RA=P((110, 0, 30)), LA=P((120, 0, -30)), R=P((78, 0, 0), (0, 3.8, 2.3)), RL=P((-18, 0, 10)), LL=P((-30, 0, -12)))
    K(v, GRAB, "linear", T=tp(0.0, 30), RA=P((100, 0, 30)), LA=P((110, 0, -30)), R=P((88, 0, 0), (0, 3.6, 2.4)))
    K(v, 326, "quad_in", T=tp(0.0, 10), RA=P((40, 0, 20)), LA=P((50, 0, -20)), R=P((20, 0, 0), (0, 1.8, 2.4)), RL=P((8, 0, 8)), LL=P((4, 0, -8)))
    K(v, SLAM, "cubic_in", T=tp(0.0, 0), H=P((-10, 0, 0)), RA=P((14, 0, 10)), LA=P((10, 0, -10)), R=P(lay, (0, 0, 2.4)))

    # ---- the drag: a low sprint, one hand on the head, through two pillars
    K(a, DRAG0, "linear", R=P(pos=(HAND_X, 0, -8.4)))
    K(a, 380, "quad_in", R=P(pos=(HAND_X, 0, -17.0)))
    K(a, DRAG1, "linear", R=P(pos=(HAND_X, 0, -52.0)))
    for f in range(DRAG0, DRAG1 + 1, 7):  # sprint bob and the free arm pumping
        ph = ((f - DRAG0) // 7) % 2
        K(a, f, "linear", T=tp(1.1 + 0.05 * ph, -55 - 3 * ph, 10 if ph else -10), LA=P((-70 if ph else 30, 0, -16)), H=P((-26, 0, 0)), RA=P((50, 0, 0)))
    # attacker's follow-through and braking skid
    K(a, 454, "cubic_out", T=tp(0.85, -34, -42), H=P((-18, 0, 0)), RA=P((150, 0, 6)), LA=P((-30, 0, -14)), R=P(pos=(HAND_X, 0, -53.2)))
    K(a, 470, "sine_inout", T=tp(0.3, -12, -10), H=P((-4, 0, 0)), RA=P((60, 0, 8)), LA=P((20, 0, -8)), R=P(pos=(HAND_X, 0, -55.0)))
    steps = gait_steps(a, DRAG0, DRAG1 - 2, first_leg="Left Leg", interval=7, swing=6, lateral=0.6, lift=0.8)
    bake_footwork(a, {"Right Leg": (1.2, -8.0), "Left Leg": (-1.2, -8.8)}, steps, 330, DRAG1)
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
        rx = lay[0] + (360.0 - lay[0]) * u
        set_root_world(vic, f, wp, (rx, 0.0, 0.0))
        K(v, f, "linear", RA=P((120 * u + 14, 0, 40 * u)), LA=P((130 * u + 10, 0, -40 * u)), RL=P((10 - 30 * u, 0, 10 * u)), LL=P((6 - 30 * u, 0, -10 * u)),
          H=P((-10 + 30 * u, 0, 0)))
    anchors = {"Right Leg": (1.2, -53.5), "Left Leg": (-1.2, -51.0)}
    bake_footwork(a, anchors, [], DRAG1 + 1, THROW1 + 12)

    # ---- fx: crater at the slam, burning drag line, pillars bursting, dust
    hx, hz = 0.5, -8.4
    cine.cracks(SLAM, 20, (hx, 0.03, hz), 7, 12, "#2a2420", "#ff5a1f", 0.14, seed=11)
    cine.ring(SLAM, 22, (hx, 0.08, hz), 0.5, 13, 1.1, 0.15, "#ffd9a0", 0.85, 0.0)
    cine.dome(SLAM, 12, (hx, 0.4, hz), 0.6, 5.0, "#ffffff", 0.6, 0.0)
    cine.burst_debris(SLAM, (hx, 0.3, hz), 26, 0.3, 0.32, (0.25, 0.75), ROCK, seed=12)
    cine.emit(SLAM, SLAM + 1, origin=(hx, 0.3, hz), rate=0, burst=40, vel=(0.12, 0.4), dir=(0, 1, 0), spread=1.0, grav=0.004, drag=0.05,
              life=(24, 50), size=(0.8, 1.6), color=("#8a7e72", "#4b4540"), alpha=(0.5, 0.0), add=False, radius=0.8, seed=13)
    cine.flash(SLAM, 5, "#ffffff", 0.35)
    cine.shake(SLAM, 20, 0.5)
    layers = [(1.7, "#ff2a00", 0.5), (0.95, "#ffb000", 0.75), (0.35, "#ffffff", 0.95)]
    cine.strip(DRAG0, 40, (SPOT[0], 0.03, -8.4), (SPOT[0], 0.03, -17.0), layers, "quad_in", fade=(DRAG1 + 20, DRAG1 + 90))
    cine.strip(380, DRAG1 - 380, (SPOT[0], 0.03, -17.0), (SPOT[0], 0.03, -52.0), layers, "linear", fade=(DRAG1 + 20, DRAG1 + 90))
    cine.emit(DRAG0, DRAG1, attach={"char": 1, "part": "Head", "off": [0, -0.45, 0]}, rate=3.0, vel=(0.08, 0.34), dir=(0.1, 1, 0.8),
              spread=0.9, grav=0.012, life=(10, 22), size=(0.2, 0.04), color=("#ffffff", "#ff7a1a"), alpha=(0.95, 0.0), seed=14)
    cine.emit(DRAG0, DRAG1, attach={"char": 1, "part": "Head", "off": [0, -0.45, 0]}, rate=1.4, vel=(0.02, 0.1), dir=(0, 1, 0.6),
              spread=0.9, grav=-0.001, life=(24, 46), size=(0.9, 1.9), color=("#8a7e72", "#4b4540"), alpha=(0.4, 0.0), add=False, seed=15)
    cine.trail(DRAG0, DRAG1, 0, "Torso", (0, 0, 0), 12, 1.1, 0.05, "#ffffff", 0.2)
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
        cine.flash(hit, 4, "#ffffff", 0.25)
        cine.shake(hit, 14, 0.4)
        cine.ring(hit, 14, (px, 0.08, pz + 2.2), 0.6, 9, 1.0, 0.1, "#ffd9a0", 0.6, 0.0)
        cine.emit(hit, hit + 1, origin=(px, 1.0, pz + 1.5), rate=0, burst=44, vel=(0.1, 0.45), dir=(0, 0.6, -0.4), spread=1.0, grav=0.003,
                  drag=0.04, life=(30, 60), size=(1.2, 2.6), color=("#a79c92", "#5d5750"), alpha=(0.55, 0.0), add=False, radius=2.2, seed=hit)

    # ---- cameras
    cine.shot(322, 333, tracking(char_point(vic, "Head"), (5.5, 0.9, 3.4), look_dy=0.2, fov=(46, 36), offset_end=(3.4, 0.6, 2.2)))
    cine.shot(334, 344, dolly((4.8, 1.2, -4.4), (4.4, 1.0, -4.9), (0.4, 0.6, -8.4), (0.4, 0.6, -8.6), fov=(40, 36), easing="linear"))
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
    vel = [0.0, 0.55, -2.6]
    rx = 360.0
    land = None
    for f in range(HIT, N_FRAMES):
        if f > HIT:
            vel[1] -= 0.05
            vel[2] *= 0.985
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
    cine.prop((-21.0, 15.0, WALL_Z), (26.0, 30.0, 4.0), "#9ea6b8")
    cine.prop((21.0, 15.0, WALL_Z), (26.0, 30.0, 4.0), "#9ea6b8")
    cine.prop((0.0, 15.0, WALL_Z), (16.0, 30.0, 4.0), "#9ea6b8", vis=(0, HIT))
    for (px, py, pz, sx, sy) in ((-26, 14, -160, 14, 28), (14, 20, -175, 12, 40), (38, 12, -150, 16, 24), (-44, 18, -190, 20, 36)):
        cine.prop((px, py, pz), (sx, sy, sx), "#b9c0cf")
    cine.shatter(HIT, (0.0, 15.0, WALL_Z), (16.0, 30.0, 4.0), "#9ea6b8", (8, 10, 2), (0.0, 5.0, WALL_Z + 8.0), 0.75, up=0.25, spin=4.0,
                 seed=77, colors=["#9ea6b8", "#8a92a5", "#6e7586"])

    # ---- fx: wall impact
    ix, iy, iz = 0.0, 6.4, WALL_Z + 2.02
    cine.cracks(THROW1, 28, (ix, iy, iz), 15, 18, "#2a2622", "#ff7a2a", 0.17, n=(0, 0, 1), seed=21, fade=(HIT, HIT + 2))
    cine.ring(THROW1, 20, (ix, iy, iz), 0.8, 13, 1.3, 0.2, "#ffe9c4", 0.85, 0.0, n=(0, 0, 1))
    cine.dome(THROW1, 12, (ix, iy, iz - 0.5), 1.0, 6.0, "#ffffff", 0.7, 0.0)
    cine.burst_debris(THROW1, (ix, iy, iz + 0.5), 30, 0.32, 0.25, (0.25, 0.75), ROCK, seed=22, direction=(0, 0, 1))
    cine.emit(THROW1, THROW1 + 1, origin=(ix, iy, iz + 0.5), rate=0, burst=60, vel=(0.1, 0.4), dir=(0, 0.2, 1), spread=1.0, grav=0.003, drag=0.04,
              life=(30, 70), size=(1.2, 2.8), color=("#a79c92", "#5d5750"), alpha=(0.55, 0.0), add=False, radius=1.8, seed=23)
    cine.flash(THROW1, 7, "#ffffff", 0.6)
    cine.shake(THROW1, 32, 0.9)
    cine.vignette.key(THROW1, 0.3, "linear")

    # ---- fx: charge-up
    cine.cracks(CHARGE0, 32, (ax, 0.03, az), 10, 14, "#2a2420", "#ff5a1f", 0.15, seed=31)
    cine.emit(CHARGE0 + 4, 556, attach={"char": 0, "part": "Right Arm", "off": [0, -1.0, 0]}, rate=3.0, vel=(0.0, 0.0), dir=(0, 1, 0), spread=1.0,
              life=(26, 26), size=(0.24, 0.06), color=("#fff3c4", "#ff4a10"), alpha=(0.0, 0.9), converge=5.0, seed=32)
    cine.emit(CHARGE0, 556, attach={"char": 0, "part": "Torso", "off": [0, -0.6, 0]}, rate=1.6, vel=(0.05, 0.18), dir=(0, 1, 0), spread=0.55,
              grav=-0.004, life=(26, 50), size=(0.34, 0.05), color=FIRE, alpha=(0.28, 0.0), radius=1.3, seed=33)
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
    cine.trail(COMET0, HIT + 1, 0, "Torso", (0, 0, 0), 10, 1.6, 0.2, "#ffe9c4", 0.4)
    cine.trail(COMET0, HIT + 1, 0, "Right Arm", (0, -1.0, 0), 10, 1.0, 0.1, "#ff6a2a", 0.6)
    cine.line(COMET0 + 1, 24, (ax, 2.4, az), (0.0, 5.0, WALL_Z + 2.0), 2.2, 0.0, "#fff3d6", 0.8, 0.0, easing="quad_out")
    cine.ring(COMET0, 18, (ax, 0.08, az), 0.6, 20, 1.2, 0.1, "#ffd9a0", 0.8, 0.0)
    cine.emit(COMET0, COMET0 + 1, origin=(ax, 0.5, az), rate=0, burst=60, vel=(0.2, 0.6), dir=(0, 0.4, 1), spread=1.0, grav=0.004, drag=0.05,
              life=(20, 50), size=(1.2, 2.4), color=("#a79c92", "#5d5750"), alpha=(0.5, 0.0), add=False, radius=1.5, seed=41)
    bx, by, bz = 0.0, 5.0, WALL_Z + 2.0
    cine.dome(HIT, 22, (bx, by, bz), 1.0, 20.0, "#ffffff", 0.35, 0.0)
    cine.ring(HIT, 30, (bx, by, bz), 1.0, 34, 2.4, 0.2, "#fff3d6", 0.9, 0.0, n=(0, 0, 1))
    cine.ring(HIT + 3, 30, (bx, 0.1, bz), 1.0, 40, 2.0, 0.2, "#ffd9a0", 0.8, 0.0)
    cine.line(HIT, 30, (bx, by, bz + 40), (bx, by, bz - 60), 2.2, 0.0, "#ffffff", 0.55, 0.0, easing="quad_out")
    cine.burst_debris(HIT, (bx, by, bz - 1.0), 60, 0.6, 0.5, (0.3, 1.0), ROCK, seed=61, direction=(0, 0, -1))
    cine.emit(HIT, HIT + 1, origin=(bx, by, bz - 1), rate=0, burst=70, vel=(0.2, 1.1), dir=(0, 0.1, -1), spread=1.0, grav=0.004, drag=0.035,
              life=(50, 110), size=(1.6, 4.0), color=("#b4aaa0", "#6a635c"), alpha=(0.4, 0.0), add=False, radius=4.0, seed=62)
    cine.emit(HIT, HIT + 6, origin=(bx, by, bz), rate=0, burst=120, vel=(0.3, 1.0), dir=(0, 0.2, -1), spread=1.0, grav=0.01, life=(14, 34),
              size=(0.3, 0.05), color=("#ffffff", "#ff7a1a"), alpha=(0.95, 0.0), seed=63)
    cine.emit(HIT + 6, 720, origin=(0, 6, WALL_Z - 6), rate=0.7, vel=(0.03, 0.12), dir=(0, 1, 0), spread=1.0, grav=0.0, life=(60, 120),
              size=(3.0, 6.0), color=("#b4aaa0", "#6a635c"), alpha=(0.2, 0.0), add=False, radius=12.0, seed=64)
    cine.emit(HIT + 6, 700, origin=(0, 8, WALL_Z - 4), rate=0.8, vel=(0.02, 0.1), dir=(0, 1, 0), spread=1.0, grav=-0.0006, life=(80, 160),
              size=(0.22, 0.05), color=("#ffd27a", "#ff3a00"), alpha=(0.8, 0.0), radius=14.0, seed=65)
    cine.flash(HIT, 5, "#ffffff", 0.9)
    cine.flash(HIT + 5, 16, "#ffd9a8", 0.3)
    cine.shake(HIT, 60, 1.6)

    # ---- screen
    cine.bars.key(HIT - 20, 0.115).key(HIT + 20, 0.16, "sine_inout").key(N_FRAMES - 1, 0.2, "sine_inout")
    cine.bright.key(299, 1.0).key(340, 0.92, "sine_inout").key(THROW1, 1.0, "linear").key(THROW1 + 20, 0.88, "sine_inout")
    cine.bright.key(CHARGE0, 0.88, "linear").key(556, 0.5, "quad_in").key(COMET0 + 1, 0.8, "linear").key(HIT - 1, 0.95, "linear")
    cine.bright.key(HIT, 1.15, "linear").key(HIT + 14, 1.0, "cubic_out").key(N_FRAMES - 30, 0.92, "linear").key(N_FRAMES - 1, 0.0, "quad_in")
    cine.vignette.key(300, 0.22, "linear").key(CHARGE0, 0.3, "sine_inout").key(556, 0.62, "quad_in").key(HIT, 0.2, "cubic_out").key(HIT + 60, 0.26, "sine_inout")
    cine.tint.key(THROW1 + 20, 0.0, "linear").key(556, 0.22, "quad_in").key(HIT, 0.0, "cubic_out")
    cine.speed.key(CHARGE0 + 30, 0.0, "linear").key(COMET0, 0.0, "linear").key(COMET0 + 2, 1.0, "cubic_out").key(HIT + 4, 1.0, "linear").key(HIT + 14, 0.0, "linear")

    # ---- cameras
    cine.shot(478, 520, dolly((9.0, 6.2, -75.5), (7.0, 5.8, -77.0), (0.0, 5.8, -87.5), (0.0, 5.6, -87.5), fov=(46, 38), easing="quad_out"))
    cine.shot(CHARGE0, 555, orbit((ax, 2.0, az), 13.0, 70, 160, 3.6, 5.6, look_dy=-0.2, fov=36, easing="sine_inout"))
    cine.shot(556, 563, dolly((3.8, 2.6, -85.0), (3.4, 2.6, -83.5), (-0.6, 2.0, -62.0), (-0.2, 2.4, -70.0), fov=(40, 52), easing="quad_in"))
    cine.shot(HIT, HIT + 26, dolly((15.0, 4.0, -80.0), (12.0, 5.5, -77.0), (0.0, 5.0, -89.0), (0.0, 5.0, -89.5), fov=(38, 48), easing="quad_out"))
    cine.shot(HIT + 27, 650, dolly((7.0, 2.2, -75.0), (11.0, 15.0, -63.0), (-0.5, 3.5, -92.0), (0.0, 3.0, -97.0), fov=(48, 58), easing="sine_inout"))
    cine.shot(651, N_FRAMES - 1, dolly((11.0, 15.0, -63.0), (34.0, 24.0, -42.0), (0.0, 3.0, -97.0), (0.0, 4.0, -100.0), fov=(58, 50), easing="sine_inout"))


def build(n_frames: int = N_FRAMES) -> Scene:
    atk = Character("Barbare", Animation("berserker", fps=60, archetype="cinematic"), base_pos=(0, 0, 0), colors=ATK_COLORS)
    vic = Character("Victime", Animation("victim", fps=60, archetype="cinematic"), base_pos=(0, 0, -6), base_yaw=180.0, colors=VIC_COLORS)
    cine = Cinematic(n_frames)
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
