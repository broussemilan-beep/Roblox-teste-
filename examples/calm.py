"""« calm » - a 12.9 s solo speed reel, 386 images at 30 fps, after docs/research/reference-analysis-2.md.

The picture index equals the reference's index (the reference clip is 386 images at 30 fps), so frame N here is meant to be compared with frame N there
(``tools/eyes.py compare``). Structure of the reference: calm hold -> forward roll -> crouch macro -> negative flash -> speed bubble and a sprint made of a
different pose on (almost) every image -> a mannequin appears far away -> impact in negative -> red sparks -> silhouette frames -> macro on the blade ->
the mannequin bursts into blocks -> a last run -> the same hold as the opening, seen from behind.

World: the hero starts at the origin; the sprint runs along +X; the mannequin stands at X = 178. Original character (examples/ronin_model.py): nothing is
copied from the reference's assets. Not done / approximations are listed in docs/research/calm-film.md.
"""

from __future__ import annotations

import random

from tsb_engine.authoring import K, P, char_points, keep_above_ground, tp
from tsb_engine.cinematic import Cinematic, autoframe, dolly, tracking
from tsb_engine.kinematics import apply
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from .ronin_model import RONIN_COLORS, dummy_outfit, ronin_outfit

N = 386
FPS = 30
DX = 178.0  # the mannequin
INK = "#0b0b0f"
PALE = {"Head": "#f1ead8", "Torso": "#e6dfcc", "Left Arm": "#f1ead8", "Right Arm": "#f1ead8", "Left Leg": "#cfc8b6", "Right Leg": "#cfc8b6"}
FACE, RUN_X, RUN_Z = 180.0, 270.0, 3.5  # yaw: faces the camera (+Z) / runs along +X


def root(x, h, z, rx=0.0, ry=0.0, rz=0.0):
    """Root pose with an *intrinsic* attitude: ``ry`` yaw (heading), then ``rx`` pitch (negative = dives forward) about the body's own X,
    then ``rz`` roll about its own Z. The engine's Euler order (X, Y, Z about the parent axes) would pitch about the *world* X after the
    heading, i.e. sideways for a body running along +X: the sprint tilted toward the camera instead of diving."""
    import math

    from tsb_engine.mathutil import euler, mat_mul

    m = mat_mul(mat_mul(euler((0.0, ry, 0.0)), euler((rx, 0.0, 0.0))), euler((0.0, 0.0, rz)))
    b = math.asin(max(-1.0, min(1.0, m[0][2])))
    if abs(m[0][2]) < 0.99999:
        a = math.atan2(-m[1][2], m[2][2])
        c = math.atan2(-m[0][1], m[0][0])
    else:  # gimbal: fold the roll into the first angle
        a = math.atan2(m[2][1], m[1][1])
        c = 0.0
    return P((math.degrees(a), math.degrees(b), math.degrees(c)), (x, h - 3.0, z))


# The sprint is a low horizontal dive (as in the reference: body parallel to the floor, head forward, blade across the back). The silhouette changes
# every 2 images through an *ordered* cycle of designed dive poses - limbs, roll and twist change, the line of travel never does:
# (root pitch, root roll, height, torso, head, RA, LA, RL, LL)
SPRINT_POSES = [
    (-85, 0, 1.7, tp(0, -5), (15, 0, 0), (170, 0, 8), (170, 0, -8), (-5, 0, 3), (-5, 0, -3)),        # superman, arms ahead
    (-82, 20, 1.7, tp(0, -10), (10, 0, 0), (-10, 0, 15), (-10, 0, -15), (40, 0, 4), (-30, 0, -4)),    # arms trailing, scissor legs
    (-80, -25, 1.8, tp(0, -10, 25), (20, 0, 0), (140, 0, 40), (30, 0, -25), (60, 0, 4), (0, 0, -4)),  # hand on the blade
    (-78, 40, 1.9, tp(0.2, -20), (10, 0, 0), (-60, 0, 20), (150, 0, -20), (80, 0, 4), (-40, 0, -4)),  # lunge, rolled
    (-85, 0, 1.6, tp(0, -5), (10, 0, 0), (-80, 0, 30), (-80, 0, -30), (20, 0, 4), (20, 0, -4)),       # hands swept back
    (-80, 80, 1.9, tp(0, 0), (0, 0, 0), (100, 0, 60), (-60, 0, -60), (40, 0, 10), (-10, 0, -10)),     # on its side
    (-85, 180, 1.7, tp(0, 10), (-10, 0, 0), (60, 0, 50), (60, 0, -50), (30, 0, 4), (50, 0, -4)),     # belly up
    (-62, 0, 2.2, tp(0.8, -35), (30, 0, 0), (70, 0, 15), (70, 0, -15), (100, 0, 4), (90, 0, -4)),     # tucked crouch-dive
    (-80, 40, 1.8, tp(0, 0, 30), (0, 0, 0), (90, 0, 90), (90, 0, -90), (10, 0, 4), (-10, 0, -4)),     # arms wide, twisting
    (-80, -30, 1.9, tp(0, -10), (15, 0, 0), (150, 0, 20), (-40, 0, -20), (120, 0, 5), (-30, 0, -4)),  # kick
]


def run_pose(a: Animation, f: int, x: float, z: float, ry: float, idx: int, rng: random.Random) -> None:
    rx, rz, h, t, hd, ra, la, rl, ll = SPRINT_POSES[idx]
    j = lambda v: tuple(c + rng.uniform(-8, 8) for c in v)
    K(a, f, "linear", R=root(x, h, z, rx + rng.uniform(-6, 6), ry + rng.uniform(-8, 8), rz), T=t, H=P(j(hd)), RA=P(j(ra)), LA=P(j(la)), RL=P(j(rl)), LL=P(j(ll)))


def cycle(a: Animation, f0: int, f1: int, xf, zf, ry: float, seed: int, every: int = 2) -> None:
    rng = random.Random(seed)
    idx = rng.randrange(len(SPRINT_POSES))
    for f in range(f0, f1 + 1):
        if (f - f0) % every == 0:
            idx = (idx + 1 + rng.randrange(2)) % len(SPRINT_POSES)
        run_pose(a, f, xf(f), zf(f), ry, idx, rng)


def hero_anim(a: Animation) -> None:
    stand = dict(T=tp(0, 0), H=P((0, 0, 0)), RA=P((4, 0, 6)), LA=P((4, 0, -6)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    crouch = dict(T=tp(1.0, -26, 0), H=P((40, 0, 0)), RA=P((60, 0, 12)), LA=P((64, 0, -14)), RL=P((78, 0, 5)), LL=P((70, 0, -5)))
    # 0-14 calm hold (breathing), 15-21 leans forward
    K(a, 0, "sine_inout", R=root(0, 3.0, 0, 0, FACE), **stand)
    K(a, 14, "sine_inout", R=root(0, 2.97, 0, 0, FACE), T=tp(0.03, 1), H=P((2, 0, 0)), RA=P((4, 0, 6)), LA=P((4, 0, -6)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 21, "quad_out", R=root(0, 2.7, 0.6, -8, FACE), T=tp(0.3, -28), H=P((28, 0, 0)), RA=P((10, 0, 6)), LA=P((60, 0, -16)), RL=P((18, 0, 3)), LL=P((10, 0, -3)))
    # 22-36 forward roll toward the camera (+Z)
    K(a, 25, "linear", R=root(0, 2.4, 1.6, -120, FACE), T=tp(0.6, -40), H=P((40, 0, 0)), RA=P((-80, 0, 12)), LA=P((-80, 0, -12)), RL=P((110, 0, 4)), LL=P((110, 0, -4)))
    K(a, 29, "linear", R=root(0, 1.7, 2.6, -220, FACE), T=tp(1.0, -50), H=P((50, 0, 0)), RA=P((-90, 0, 12)), LA=P((-90, 0, -12)), RL=P((120, 0, 4)), LL=P((120, 0, -4)))
    K(a, 33, "linear", R=root(0, 1.9, 3.4, -320, FACE), T=tp(0.8, -40), H=P((40, 0, 0)), RA=P((-60, 0, 12)), LA=P((-60, 0, -12)), RL=P((100, 0, 4)), LL=P((100, 0, -4)))
    K(a, 36, "quad_out", R=root(0, 2.9, 3.7, -360, FACE), T=tp(0.3, -20), H=P((15, 0, 0)), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((20, 0, -4)))
    # 37-47 lands in a crouch, 48-62 holds it (a small settle), blade across the back stays
    K(a, 38, "quad_out", R=root(0, 2.2, 3.7, -4, FACE), **crouch)
    K(a, 47, "sine_inout", R=root(0, 2.15, 3.7, -4, FACE), T=tp(1.03, -28), H=P((44, 0, 0)), RA=P((64, 0, 14)), LA=P((66, 0, -14)), RL=P((80, 0, 5)), LL=P((72, 0, -5)))
    K(a, 62, "sine_inout", R=root(0, 2.1, 3.7, -4, FACE), T=tp(1.06, -32), H=P((46, 0, 0)), RA=P((66, 0, 16)), LA=P((68, 0, -16)), RL=P((82, 0, 5)), LL=P((74, 0, -5)))
    K(a, 65, "linear", R=root(0, 2.1, 3.7, -4, FACE), T=tp(1.06, -32), H=P((46, 0, 0)), RA=P((66, 0, 16)), LA=P((68, 0, -16)))
    # 66-71 jump and turn toward +X
    K(a, 68, "quad_out", R=root(0.5, 6.5, 3.6, -20, 225), T=tp(0.0, -10), H=P((10, 0, 0)), RA=P((120, 0, 30)), LA=P((-30, 0, -30)), RL=P((50, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 71, "quad_in", R=root(2.5, 4.5, 3.6, -50, RUN_X), T=tp(0.2, -25), H=P((20, 0, 0)), RA=P((-60, 0, 20)), LA=P((120, 0, -20)), RL=P((70, 0, 4)), LL=P((-50, 0, -4)))
    # 72-239 the sprint: a new silhouette on every image
    zf = lambda f: RUN_Z - 0.0 * f
    xf = lambda f: 3.0 + 0.95 * (f - 72)
    cycle(a, 72, 239, xf, zf, RUN_X, 5)
    # 240-256 he slows, aims at the far mannequin and dives at it
    for f in range(240, 257):
        u = (f - 240) / 16
        x = xf(239) + (DX - 5.5 - xf(239)) * u
        z = RUN_Z + (0.7 - RUN_Z) * u
        K(a, f, "linear", R=root(x, 3.0 - 0.8 * u, z, -50 - 30 * u, RUN_X), T=tp(0.4 * u, -25 - 15 * u), H=P((10, 0, 0)), RA=P((160, 0, 10)), LA=P((-50, 0, -20)), RL=P((60 + 20 * u, 0, 4)), LL=P((-40, 0, -4)))
    # 257-264 the slam: a low horizontal slide through the mannequin
    K(a, 260, "linear", R=root(DX - 2.0, 2.2, 0.7, -85, RUN_X), T=tp(0.3, -10), H=P((10, 0, 0)), RA=P((170, 0, 8)), LA=P((20, 0, -20)), RL=P((20, 0, 4)), LL=P((10, 0, -4)))
    K(a, 264, "quad_out", R=root(DX + 4.0, 1.4, 0.9, -90, RUN_X), T=tp(0.3, -10), H=P((10, 0, 0)), RA=P((170, 0, 8)), LA=P((20, 0, -20)), RL=P((10, 0, 4)), LL=P((0, 0, -4)))
    # 265-273 curled up and rolling back in a bubble, 274-281 crouched near the mannequin
    for f in range(265, 274):
        u = (f - 265) / 8
        K(a, f, "linear", R=root(DX + 4.0 - 8.0 * u, 2.0, 1.2, -90 - 400 * u, RUN_X), T=tp(0.9, -40), H=P((40, 0, 0)), RA=P((-90, 0, 12)), LA=P((-90, 0, -12)), RL=P((115, 0, 4)), LL=P((115, 0, -4)))
    K(a, 275, "quad_out", R=root(DX - 6.0, 2.2, 1.6, -4, RUN_X), **crouch)
    K(a, 281, "sine_inout", R=root(DX - 6.0, 2.15, 1.6, -4, RUN_X), T=tp(1.03, -28), H=P((44, 0, 0)), RA=P((64, 0, 14)), LA=P((66, 0, -14)), RL=P((80, 0, 5)), LL=P((72, 0, -5)))
    # 282-305 he gets up and runs away along -X (toward the start), slowed down at the end
    xr = lambda f: DX - 6.0 - 2.4 * (f - 282) if f < 300 else DX - 6.0 - 2.4 * 18 - 0.5 * (f - 300)
    cycle(a, 282, 305, xr, lambda f: 1.6, 90.0, 11)
    # 306-309 a frozen silhouette, then the cut to the blade macro (310-341): crouched behind it
    for f in range(306, 310):
        run_pose(a, f, xr(305), 1.6, 90.0, 3, random.Random(1))
    K(a, 310, "linear", R=root(DX - 6.0, 2.3, -1.2, -4, RUN_X), T=tp(1.03, -28), H=P((44, 0, 0)), RA=P((64, 0, 14)), LA=P((66, 0, -14)), RL=P((80, 0, 5)), LL=P((72, 0, -5)))
    K(a, 341, "sine_inout", R=root(DX - 6.0, 2.25, -1.2, -6, RUN_X), T=tp(1.06, -34), H=P((48, 0, 0)), RA=P((66, 0, 16)), LA=P((68, 0, -16)), RL=P((82, 0, 5)), LL=P((74, 0, -5)))
    # 342-349 stands and cuts (the blocks fly), then runs: 350-359 along -X, 360-369 rolling away
    K(a, 342, "linear", R=root(DX - 6.0, 1.8, -1.2, -6, 270.0), T=tp(1.0, -30), H=P((40, 0, 0)), RA=P((66, 0, 16)), LA=P((68, 0, -16)), RL=P((82, 0, 5)), LL=P((74, 0, -5)))
    K(a, 346, "cubic_out", R=root(DX - 4.5, 3.0, 0.0, -30, 90.0), T=tp(0.2, -20, 30), H=P((10, 0, 0)), RA=P((-80, 0, 20)), LA=P((60, 0, -30)), RL=P((60, 0, 4)), LL=P((-30, 0, -4)))
    cycle(a, 350, 359, lambda f: DX - 6.0 - 2.2 * (f - 350), lambda f: 1.0, 90.0, 17)
    for f in range(360, 370):
        u = (f - 360) / 9
        K(a, f, "linear", R=root(DX - 27.0 - 2.5 * (f - 360), 2.2 + 0.6 * u, 1.0, 40 + 340 * u, 90.0), T=tp(0.8, -30), H=P((30, 0, 0)), RA=P((-80, 0, 12)), LA=P((-80, 0, -12)), RL=P((110, 0, 4)), LL=P((110, 0, -4)))
    # 370-385 the opening hold again, seen from behind (he faces -Z, the camera is on +Z)
    K(a, 370, "linear", R=root(0, 3.0, 0, 0, 0), **stand)
    K(a, 385, "sine_inout", R=root(0, 2.97, 0, 0, 0), T=tp(0.03, 1), H=P((2, 0, 0)), RA=P((4, 0, 6)), LA=P((4, 0, -6)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))


BLOCKS = {  # the mannequin's blocks fly apart (offset in the part's parent frame, spin)
    "Head": ((0.6, 2.4, 1.6), (30, 40, 70)), "Right Arm": ((-2.8, 1.6, -1.2), (-20, 10, 80)), "Left Arm": ((2.4, 1.4, 2.2), (30, -20, -70)),
    "Right Leg": ((-1.4, 0.6, -2.8), (50, 10, -30)), "Left Leg": ((1.8, 0.9, -2.6), (-40, 30, 20)),
}
SHORT = {"Head": "H", "Right Arm": "RA", "Left Arm": "LA", "Right Leg": "RL", "Left Leg": "LL"}


def dummy_anim(a: Animation) -> None:
    K(a, 0, "linear", R=root(DX, 3.0, 0, 0, 90.0), T=tp(0, 0), H=P((0, 0, 0)), RA=P((8, 0, 4)), LA=P((8, 0, -4)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 258, "linear", R=root(DX, 3.0, 0, 0, 90.0), T=tp(0, 0))
    # struck at 259: folds and is thrown back (+X), staggers, stands again
    K(a, 260, "quad_out", R=root(DX + 1.5, 3.0, 0, -15, 90.0), T=tp(0.0, -40), H=P((-30, 0, 0)), RA=P((-50, 0, 30)), LA=P((-60, 0, -30)), RL=P((-20, 0, 3)), LL=P((30, 0, -3)))
    K(a, 266, "quad_out", R=root(DX + 4.0, 2.9, 0, 10, 90.0), T=tp(0.0, -15), H=P((10, 0, 0)), RA=P((40, 0, 18)), LA=P((30, 0, -18)), RL=P((6, 0, 3)), LL=P((10, 0, -3)))
    K(a, 280, "sine_inout", R=root(DX + 3.0, 3.0, 0, 0, 90.0), T=tp(0.0, 4), H=P((0, 0, 0)), RA=P((8, 0, 4)), LA=P((8, 0, -4)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 300, "linear", R=root(DX + 3.0, 3.0, 0, 0, 90.0), T=tp(0.0, 0))
    # falls back and lies on the floor in the foreground of the blade macro (310-341)
    K(a, 309, "quad_in", R=root(DX - 3.0, 0.5, 0.8, 0, 0, -90), T=tp(0, 0), RA=P((0, 0, 20)), LA=P((0, 0, -20)))
    K(a, 341, "linear", R=root(DX - 3.0, 0.5, 0.8, 0, 0, -90))
    K(a, 343, "quad_out", R=root(DX - 3.0, 0.65, 0.8, 0, 0, -90))
    for part, (off, spin) in BLOCKS.items():
        base = a.sample_part(part, 341)
        K(a, 342, "linear", **{SHORT[part]: base})
        K(a, 349, "quad_out", **{SHORT[part]: P(tuple(base.rot[i] + spin[i] for i in range(3)), off)})
        K(a, 385, "linear", **{SHORT[part]: P(tuple(base.rot[i] + spin[i] for i in range(3)), off)})


def build() -> Scene:
    hero = Character("hero", Animation("hero", fps=FPS, archetype="cinematic"), colors=RONIN_COLORS, outfit=ronin_outfit(), face="std")
    dummy = Character("dummy", Animation("dummy", fps=FPS, archetype="cinematic"), colors=PALE, outfit=dummy_outfit(), hide=("Head",))
    hero_anim(hero.anim)
    dummy_anim(dummy.anim)
    keep_above_ground(hero, range(N))
    cine = Cinematic(N, fps=FPS)
    cine.sky_color, cine.floor_color = "#3d3b41", "#66646a"
    cine.aspect = 737 / 384
    cine.vignette.key(0, 0.35)
    hp = lambda f: apply(hero.world_parts(int(f))["Torso"], (0, 0, 0))
    hd = lambda f: apply(hero.world_parts(int(f))["Head"], (0, 0, 0))
    dp = lambda f: apply(dummy.world_parts(int(f))["Torso"], (0, 0, 0))
    both = lambda f: char_points(f, hero, dummy)

    # ---- camera: the reference's shot list (frame indices of the reference)
    cine.shot(0, N - 1, dolly((0, 3.7, 12), (0, 3.7, 12), (0, 3.4, 0), (0, 3.4, 0), fov=32))
    cine.shot(0, 14, dolly((3.0, 2.4, 20), (3.0, 2.4, 20), (-2.6, 3.3, 0), (-2.6, 3.3, 0), fov=30))
    cine.shot(15, 36, dolly((3.5, 2.4, 20), (6.0, 3.0, 23), (-0.4, 3.3, 0), (-0.4, 2.2, 2.5), fov=(30, 34)))
    cine.shot(37, 47, tracking(hp, (7.0, 1.6, 14.0), look_dy=-0.4, fov=34))
    cine.shot(48, 52, tracking(hp, (3.6, 0.4, 8.5), look_dy=0.0, fov=32))
    cine.shot(53, 71, tracking(hp, (7.0, 1.6, 15.0), look_dy=0.2, fov=36, roll=(0, 6)))
    cine.shot(72, 110, tracking(hp, (-2.5, 1.5, -13.5), look_dy=0.2, fov=30, roll=(-6, 6)))
    cine.shot(111, 148, tracking(hp, (-2.0, 2.4, -13.0), look_dy=0.2, fov=30, roll=(8, -8)))
    cine.shot(149, 183, tracking(hp, (3.0, 1.6, -12.5), look_dy=0.2, fov=32, roll=(-10, 10)))
    cine.shot(184, 239, tracking(hp, (4.0, 0.7, -13.0), look_dy=0.6, fov=34, roll=(0, 5)))
    cine.shot(240, 256, autoframe(both, 240, 256, azimuth=15, elevation=5, fov=36, fill=1.0, follow=0.25, min_radius=3.5))
    cine.shot(257, 264, autoframe(both, 257, 264, azimuth=40, elevation=8, fov=34, fill=0.95, follow=0.4, min_radius=2.6))
    cine.shot(265, 273, autoframe(both, 265, 273, azimuth=65, elevation=12, fov=38, fill=0.6, follow=0.2, min_radius=3.5))
    cine.shot(274, 281, autoframe(both, 274, 281, azimuth=30, elevation=8, fov=32, fill=0.8, follow=0.3, min_radius=2.6))
    cine.shot(282, 299, tracking(hp, (2.5, 1.5, 13.0), look_dy=0.2, fov=30, roll=(6, -6)))
    cine.shot(300, 305, autoframe(both, 300, 305, azimuth=20, elevation=6, fov=34, fill=0.55, follow=0.2, min_radius=4))
    cine.shot(306, 309, tracking(hd, (2.6, 0.2, 5.0), look_dy=0.2, fov=30))
    bx = DX - 5.5
    cine.shot(310, 341, dolly((bx - 1.0, 2.6, 7.0), (bx - 0.2, 2.7, 6.6), (bx + 1.2, 2.2, 0.0), (bx + 1.5, 2.3, 0.0), fov=30))
    cine.shot(342, 349, autoframe(both, 342, 349, azimuth=30, elevation=10, fov=36, fill=0.9, follow=0.3, min_radius=3.0))
    cine.shot(350, 359, tracking(hp, (-2.0, 1.5, 12.5), look_dy=0.2, fov=30, roll=(0, -8)))
    cine.shot(360, 369, tracking(hp, (9.0, 14.0, 10.0), fov=40))
    cine.shot(370, N - 1, dolly((4.5, 2.2, 27), (4.5, 2.2, 27), (-0.6, 3.0, 0), (-0.6, 3.0, 0), fov=30))

    # ---- speed bubble that follows him, ground speed lines, long diagonals
    gp = lambda f: (hp(f)[0] + 0.8 * (1 if (f < 282 or 265 <= f <= 273) else -1), 0.0, hp(f)[2])
    cine.bubble(66, 256, gp, 2.4, "#b9d2e4", 0.4, half=True)
    cine.bubble(265, 273, gp, 2.4, "#b9d2e4", 0.4, half=True)
    cine.bubble(282, 305, gp, 2.4, "#b9d2e4", 0.4, half=True)
    cine.bubble(350, 369, gp, 2.4, "#b9d2e4", 0.4, half=True)
    for f0, f1 in ((72, 239), (282, 305), (350, 369)):
        for f in range(f0, f1, 6):
            x = hp(f)[0]
            sgn = 1 if f < 282 else -1
            cine.streaks(f, 6, (x - sgn * 16, 0.06, hp(f)[2]), (x, 0.06, hp(f)[2]), n=16, r0=0.15, r1=2.8, w=0.05, color="#ffffff", seed=f)
    for f0, f1 in ((72, 140), (150, 180), (184, 239), (282, 305), (350, 369)):
        for f in range(f0, f1, 5):
            cine.screen_fx("diag", f, 3, n=7, angle=-22, seed=f)
    for f0, f1 in ((72, 239), (282, 305), (350, 369)):
        cine.ink_trail(f0, f1, 0, "Torso", (0, 0, 0), 12, 2.2, 0.0, "#cfcfd4", rag=0.5, seed=21, alpha=0.45)
    # ---- the roll: thin white arcs; the landing dust; the dark smear before the first negative
    for k in range(3):
        cine.ring(22 + 4 * k, 12, (0, 2.0 + 0.2 * k, 2.0 + 0.5 * k), 1.2, 2.6, 0.06, 0.02, "#ffffff", 0.6, 0.0, n=(1, 0, 0), add=True, easing="quad_out")
    cine.emit(37, 47, origin=(0, 0.2, 3.7), rate=3.0, vel=(0.04, 0.18), dir=(0, 1, 0), spread=1.2, life=(14, 26), size=(0.7, 1.7), color=("#8e8c93", "#5a585e"), alpha=(0.5, 0.0), add=False, seed=2, radius=1.2, shape="smoke")
    cine.emit(53, 62, origin=(0, 2.2, 3.7), rate=4.0, vel=(0.02, 0.1), dir=(0, 1, 0), spread=1.5, life=(10, 20), size=(1.6, 2.6), color=("#050507", "#1c1c20"), alpha=(0.7, 0.0), add=False, seed=3, radius=1.2, shape="smoke")
    cine.slices(141, 8, hp(145), n=6, h=6.0, w=1.5, color="#08080a", spread=2.0, seed=4)
    # ---- the ring pulses behind him in the low wide shot, the aim line, the mini dome
    for f in range(186, 238, 6):
        x = hp(f)[0]
        cine.ring(f, 12, (x - 3, 3.0, hp(f)[2]), 0.5, 5.0, 0.12, 0.03, "#ffffff", 0.7, 0.0, n=(1, 0, 0), add=True, easing="quad_out")
    cine.line(241, 15, (hp(241)[0], 3.0, hp(241)[2]), (DX, 3.0, 0.0), 0.06, 0.03, "#ffffff", 0.85, 0.2)
    # ---- negative impact frames, then the silhouette frames (black on white x3, black on red x1)
    for t0, d in ((63, 3), (149, 2), (181, 3), (257, 3), (274, 2)):
        cine.screen_fx("negative", t0, d, hue=150 + (t0 % 3) * 20)
    cine.screen_fx("bw", 306, 3, contrast=24, bright=2.6, bfirst=True, shards=0)
    cine.screen_fx("bw", 309, 1, contrast=24, bright=2.6, bfirst=True, shards=0, multiply="#d4221c")
    # ---- red sparks (the only warm colour), blade glints, the blocks
    cine.emit(258, 281, origin=(DX - 1.0, 2.0, 0.6), rate=3.0, burst=30, vel=(0.12, 0.45), dir=(0, 1, 0.2), spread=1.6, grav=0.02, life=(10, 26), size=(0.22, 0.06), color=("#ff3b2a", "#a01212"), alpha=(1.0, 0.0), add=True, seed=6, shape="spark", stretch=3.0)
    bz = 0.2
    cine.prop((bx + 1.2, 1.7, bz + 0.6), (4.4, 0.12, 0.34), "#cfd6de", yaw=-6.0, vis=(310, 349))
    cine.prop((bx - 1.5, 1.7, bz + 0.5), (1.0, 0.22, 0.3), "#3a2a22", yaw=-6.0, vis=(310, 349))
    for t in range(319, 324):
        cine.flash(t, 1, "#ffffff", 0.9)
    cine.emit(325, 341, origin=(bx + 2.6, 1.7, bz + 0.6), rate=1.5, vel=(0.03, 0.2), dir=(0, 1, 0.3), spread=1.4, grav=0.015, life=(8, 20), size=(0.15, 0.04), color=("#ff3b2a", "#7a0c0c"), alpha=(1.0, 0.0), add=True, seed=7, shape="spark", stretch=2.5)
    cine.emit(343, 349, origin=(DX - 3.0, 1.0, 0.0), burst=26, rate=0.0, vel=(0.1, 0.4), dir=(0, 1, 0), spread=1.8, grav=0.02, life=(10, 24), size=(0.25, 0.08), color=("#d9d9de", "#6a6a70"), alpha=(0.9, 0.0), add=False, seed=8, shape="shard")
    return Scene("calm — reproduction de la 2e référence", [hero, dummy], fps=FPS, cine=cine)
