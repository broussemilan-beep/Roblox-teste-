"""« calm » - a 12.9 s solo speed reel, 386 images at 30 fps, after docs/research/reference-analysis-2.md.

The picture index equals the reference's index (the reference clip is 386 images at 30 fps), so frame N here is meant to be compared with frame N there
(``tools/eyes.py compare``). Structure of the reference: calm hold -> forward roll -> crouch macro -> negative flash -> speed bubble and a sprint made of a
different pose on (almost) every image -> a mannequin appears far away -> impact in negative -> red sparks -> silhouette frames -> macro on the blade ->
the mannequin bursts into blocks -> a last run -> the same hold as the opening, seen from behind.

World: the hero starts at the origin; the sprint runs along +X; the mannequin stands at X = 178. Original character (examples/ronin_model.py): nothing is
copied from the reference's assets. Not done / approximations are listed in docs/research/calm-film.md.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np

from tsb_engine.authoring import K, P, char_points, keep_above_ground, rest_on_ground, root_pose, tp
from tsb_engine.cinematic import Cinematic, autoframe, dolly, tracking
from tsb_engine.gait import add_air, run_keys, stride_speed
from tsb_engine.solver import reach_root
from tsb_engine.kinematics import apply
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from .ronin_model import RONIN_COLORS, dummy_outfit, ronin_outfit

N = 386
FPS = 30
DX = 125.0  # the mannequin for the first exchange (images 257-283)
XD2 = DX + 22.0  # where he stands for the final blow (284-355)
DRAW = (304, 345)  # the katana is drawn on image 304 and put away by 345
POSES72 = Path(__file__).resolve().parent.parent / 'docs' / 'research' / 'reference-poses' / 'hero_72_148.json'
POSES284 = Path(__file__).resolve().parent.parent / 'docs' / 'research' / 'reference-poses' / 'hero_284_299.json'
TRACK72 = Path(__file__).resolve().parent.parent / 'docs' / 'research' / 'reference-tracks' / 'hero_72_148.json'
TRACK284 = Path(__file__).resolve().parent.parent / 'docs' / 'research' / 'reference-tracks' / 'hero_284_299.json'
INK = "#0b0b0f"
PALE = {"Head": "#f1ead8", "Torso": "#e6dfcc", "Left Arm": "#f1ead8", "Right Arm": "#f1ead8", "Left Leg": "#cfc8b6", "Right Leg": "#cfc8b6"}
FACE, RUN_X, RUN_Z = 180.0, 270.0, 3.5  # yaw: faces the camera (+Z) / runs along +X


root = root_pose  # intrinsic attitude (heading, pitch, roll): see tsb_engine/authoring.py


# The sprint (re-read at full size in the reference, images 72-134): the camera sits low and slightly behind him, he runs away along the floor lines in a crouch,
# leaning hard forward, his silhouette changing every couple of images (tilt, tuck, hand to the blade, stride, slide, spin) while the shell stays round around him.
# (root pitch, root roll, height, torso, head, RA, LA, RL, LL)
SPRINT_POSES = [
    (-40, 10, 2.5, tp(0.6, -25), (25, 0, 0), (-70, 0, 18), (-70, 0, -18), (80, 0, 4), (-30, 0, -4)),       # crouch sprint, arms streaming
    (-55, -15, 2.2, tp(0.8, -35), (30, 0, 0), (-90, 0, 20), (-80, 0, -20), (100, 0, 4), (40, 0, -4)),     # deep lean
    (-35, 20, 2.6, tp(0.4, -20, 15), (15, 0, 0), (-160, 0, -15), (30, 0, -20), (60, 0, 4), (-40, 0, -4)),  # hand reaches the blade on his back
    (-45, 0, 3.2, tp(0.2, -20), (20, 0, 0), (-60, 0, 25), (120, 0, -25), (-30, 0, 4), (70, 0, -4)),        # leaping stride
    (-70, 25, 1.7, tp(1.0, -30), (35, 0, 0), (50, 0, 20), (-60, 0, -30), (100, 0, 6), (80, 0, -6)),       # low slide
    (-30, 40, 2.4, tp(0.5, -15, 25), (10, 0, 0), (80, 0, 60), (-40, 0, -60), (60, 0, 12), (-20, 0, -12)),  # banked, arms out
    (-50, -30, 2.4, tp(1.0, -40), (40, 0, 0), (70, 0, 15), (70, 0, -15), (115, 0, 4), (110, 0, -4)),      # tucked ball
    (-35, -25, 2.9, tp(0.2, -15), (15, 0, 0), (-50, 0, 30), (90, 0, -20), (125, 0, 4), (-30, 0, -4)),     # kick extended
    (-25, 55, 2.8, tp(0.3, -10, -25), (0, 0, 0), (100, 0, 80), (-80, 0, -70), (40, 0, 6), (30, 0, -6)),   # spinning
    (-60, 5, 2.0, tp(1.1, -45), (45, 0, 0), (-120, 0, 10), (-100, 0, -10), (95, 0, 4), (85, 0, -4)),      # bundled crouch
    (-15, 0, 3.0, tp(0.1, -10), (10, 0, 0), (60, 0, 12), (-60, 0, -12), (70, 0, 4), (-50, 0, -4)),        # upright stride
]


def run_pose(a: Animation, f: int, x: float, z: float, ry: float, idx: int, rng: random.Random) -> None:
    rx, rz, h, t, hd, ra, la, rl, ll = SPRINT_POSES[idx]
    h = h - 0.5
    j = lambda v: tuple(c + rng.uniform(-8, 8) for c in v)
    K(a, f, "linear", R=root(x, h, z, rx + rng.uniform(-6, 6), ry + rng.uniform(-8, 8), rz), T=t, H=P(j(hd)), RA=P(j(ra)), LA=P(j(la)), RL=P(j(rl)), LL=P(j(ll)))


def zigzag(f0: int = 72, f1: int = 239, seg: int = 10, x0: float = 3.0, z0: float = RUN_Z, x1: float = 111.0):
    """Sprint path of the first run: a sharp change of heading (+-35..45 deg) every ``seg`` images, pairs of equal and opposite turns so the
    lateral drift cancels, the speed scaled so that the hero covers ``x1 - x0`` studs along the grid. Returns (x(f), z(f), heading_deg(f))."""
    rng = random.Random(3)
    mags = [rng.choice([35, 40, 45]) for _ in range(8)]
    heads = [h for m in mags for h in (m, -m)]
    hd = lambda f: heads[(f - f0) // seg] if (f - f0) // seg < len(heads) else 0.0
    cs = sum(math.cos(math.radians(hd(f))) for f in range(f0, f1 + 1))
    spd = (x1 - x0) / cs
    xs, zs = {f0 - 1: x0}, {f0 - 1: z0}
    for f in range(f0, f1 + 1):
        xs[f] = xs[f - 1] + spd * math.cos(math.radians(hd(f)))
        zs[f] = zs[f - 1] + spd * math.sin(math.radians(hd(f)))
    return (lambda f: xs[max(f0, min(f1, f))]), (lambda f: zs[max(f0, min(f1, f))]), hd


def cycle(a: Animation, f0: int, f1: int, xf, zf, ry, seed: int, every: int = 2) -> None:
    rng = random.Random(seed)
    idx = rng.randrange(len(SPRINT_POSES))
    for f in range(f0, f1 + 1):
        if (f - f0) % every == 0:
            idx = (idx + 1 + rng.randrange(2)) % len(SPRINT_POSES)
        run_pose(a, f, xf(f), zf(f), ry(f) if callable(ry) else ry, idx, rng)


def copied_poses(path: Path) -> dict[int, list[float]]:
    """Joint angles copied from the reference (tools/copy_poses.py: the R6 rig fitted to the tracked hero's silhouette), lightly smoothed in time."""
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    frames = [(x["f"], x["angles"]) for x in d["frames"] if x["angles"] is not None]
    if not frames:
        return {}
    fs = [f for f, _ in frames]
    A = np.array([a for _, a in frames], float)
    sm = A.copy()
    for k in range(3, 16):   # not the heading (0, 1, 2 are view-dependent attitude: kept raw for pitch/roll, heading unused)
        pad = np.pad(A[:, k], 1, mode="edge")
        sm[:, k] = 0.25 * pad[:-2] + 0.5 * pad[1:-1] + 0.25 * pad[2:]
    return {f: list(sm[i]) for i, f in enumerate(fs)}


def key_copied(a: Animation, f: int, ang: list[float], x: float, z: float, ry: float) -> None:
    """Key one image from copied angles: the body's own attitude (pitch, roll) and every joint from the fit; the heading and the position are ours (story and path)."""
    K(a, f, "linear", R=root(x, 3.0, z, ang[1], ry, ang[2]), T=P((ang[3], ang[4], ang[5])), H=P((ang[6], ang[7], 0)),
      RA=P((ang[8], 0, ang[9])), LA=P((ang[10], 0, ang[11])), RL=P((ang[12], 0, ang[13])), LL=P((ang[14], 0, ang[15])))


def hero_anim(hero_char: Character) -> None:
    a = hero_char.anim
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
    xf, zf, hdg = zigzag()
    # a real crouched gait (feet planted: the root height comes from the feet), with a stylised accent pose every ninth image pair so the silhouette still jumps
    run_keys(a, 72, 239, lambda f: (xf(f), zf(f), RUN_X - hdg(f)), period=8.0, amp=55.0, lean=32.0, arm=50.0)
    cp72 = copied_poses(POSES72)
    copied = [f for f in range(72, 149) if f in cp72]
    for f in copied:   # 72-148: the reference's own poses
        key_copied(a, f, cp72[f], xf(f), zf(f), RUN_X - hdg(f))
    accents = [f for f in range(149, 240) if (f - 149) % 9 in (7, 8)]
    run_frames = [f for f in range(72, 240) if f not in accents]
    rest_on_ground(hero_char, run_frames)
    add_air(hero_char, [f for f in run_frames if f not in copied], 72, 8.0, 0.5)
    rng = random.Random(5)
    for f in accents:
        run_pose(a, f, xf(f), zf(f), RUN_X - hdg(f), rng.randrange(len(SPRINT_POSES)), rng)
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
    # 274-283 second exchange: he springs onto the felled mannequin and kneels over him, pumping (red spatter), then the picture cuts
    K(a, 275, "quad_out", R=root(DX - 6.0, 2.2, 1.6, -4, RUN_X), **crouch)
    K(a, 277, "quad_out", R=root(DX - 1.4, 2.1, 0.9, -45, RUN_X), T=tp(0.7, -32), H=P((30, 0, 0)), RA=P((110, 0, 10)), LA=P((60, 0, -12)), RL=P((95, 0, 5)), LL=P((70, 0, -5)))
    for f, ra in ((279, 150), (281, 20), (283, 140)):
        K(a, f, "quad_out", R=root(DX - 0.8, 1.8, 0.9, -35, RUN_X), T=tp(0.9, -38), H=P((34, 0, 0)), RA=P((ra, 0, 8)), LA=P((50, 0, -12)), RL=P((100, 0, 5)), LL=P((80, 0, -5)))
    K(a, 283, "constant", R=root(DX - 0.8, 1.8, 0.9, -35, RUN_X), T=tp(0.9, -38), H=P((34, 0, 0)), RA=P((140, 0, 8)), LA=P((50, 0, -12)), RL=P((100, 0, 5)), LL=P((80, 0, -5)))
    # 284-305 the run at the mannequin: a real gait (feet planted, stride tied to speed), the blade drawn on 304
    v = stride_speed(55.0, 8.0)
    x0 = XD2 - 22.5
    xrun = lambda f: x0 + v * (f - 284) if f <= 300 else x0 + v * 16 + 1.15 * v * (f - 300)
    cp = copied_poses(POSES284)
    if cp:   # the reference's own run (the rig fitted to his silhouette), then the gait takes over for the last strides
        for f in range(284, 300):
            key_copied(a, f, cp[f], xrun(f), 0.0, RUN_X)
        run_keys(a, 300, 303, lambda f: (xrun(f), 0.0, RUN_X), period=8.0, amp=55.0, lean=24.0, arm=50.0, sword_arm=True, phase0=2.0)
        rest_on_ground(hero_char, range(284, 304))
    else:
        run_keys(a, 284, 303, lambda f: (xrun(f), 0.0, RUN_X), period=8.0, amp=55.0, lean=24.0, arm=50.0, sword_arm=True)
        rest_on_ground(hero_char, range(284, 304))
        add_air(hero_char, range(284, 304), 284, 8.0, 0.4)
    # 304-309 the strike: wind-up (304-305), the cut (306), held while the impact frames flash (307-309)
    K(a, 304, "quad_out", R=root(xrun(304), 2.7, 0.0, -20, RUN_X), T=tp(0.5, -26, -40), H=P((22, 0, 0)), RA=P((95, 0, 70)), LA=P((-50, 0, -25)), RL=P((70, 0, 4)), LL=P((-45, 0, -4)))
    K(a, 306, "cubic_out", R=root(xrun(305) + 0.5, 2.3, 0.0, -18, RUN_X), T=tp(0.7, -28, 50), H=P((20, 0, 0)), RA=P((95, 0, -25)), LA=P((-40, 0, -30)), RL=P((80, 0, 4)), LL=P((-50, 0, -4)))
    neck = (XD2, 4.5, 0.0)
    pose, res = reach_root(hero_char, 306, "Right Arm", neck, hint=(95, -25), tip=(0.0, -0.95, -2.4))
    K(a, 306, "cubic_out", RA=pose)
    for f in (307, 309):
        K(a, f, "linear", R=root(xrun(305) + 0.5 + 0.12 * (f - 306), 2.3, 0.0, -18, RUN_X), T=tp(0.7, -28, 50), H=P((20, 0, 0)), RA=pose, LA=P((-40, 0, -30)), RL=P((80, 0, 4)), LL=P((-50, 0, -4)))
    # 310-341 the macro: the cut is already made, he holds the lunge (a small drift, never frozen)
    K(a, 341, "sine_inout", R=root(xrun(305) + 0.5 + 0.12 * 5 + 0.15, 2.2, 0.0, -20, RUN_X), T=tp(0.75, -30, 52), H=P((22, 0, 0)), RA=pose, LA=P((-42, 0, -30)), RL=P((82, 0, 4)), LL=P((-52, 0, -4)))
    # 342-355 he rises with the blade up, then crouches (the mannequin bursts into blocks)
    K(a, 346, "cubic_out", R=root(XD2 - 3.2, 2.9, 0.0, -10, RUN_X), T=tp(0.2, -12, 20), H=P((12, 0, 0)), RA=P((170, 0, 12)), LA=P((-30, 0, -30)), RL=P((50, 0, 4)), LL=P((-30, 0, -4)))
    K(a, 352, "sine_inout", R=root(XD2 - 3.0, 2.1, 0.0, -10, RUN_X), T=tp(0.9, -30, 8), H=P((30, 0, 0)), RA=P((172, 0, 8)), LA=P((60, 0, -20)), RL=P((95, 0, 5)), LL=P((75, 0, -5)))
    K(a, 355, "constant", R=root(XD2 - 3.0, 2.1, 0.0, -10, RUN_X), T=tp(0.9, -30, 8), H=P((30, 0, 0)), RA=P((172, 0, 8)), LA=P((60, 0, -20)), RL=P((95, 0, 5)), LL=P((75, 0, -5)))
    # 356-365 he slides and rolls away (the high oblique shot), a white dust trail behind him
    for f in range(356, 366):
        u = (f - 356) / 9
        K(a, f, "linear", R=root(XD2 - 5.0 - 3.0 * (f - 356), 2.0 + 0.7 * u, 1.0, 40 + 340 * u, 90.0), T=tp(0.8, -30), H=P((30, 0, 0)), RA=P((-80, 0, 12)), LA=P((-80, 0, -12)), RL=P((110, 0, 4)), LL=P((110, 0, -4)))
    # 366-374 he skids in from behind, crouched and lopsided, 6 studs, leaning back to brake; 375-385 he stands up into the opening idle
    brake = dict(T=tp(0.9, -25, 12), H=P((25, 0, 0)), RA=P((-40, 0, 50)), LA=P((40, 0, -20)), RL=P((95, 0, 6)), LL=P((-25, 0, -6)))
    for f in range(366, 375):
        u = (f - 366) / 8
        K(a, f, "linear", R=root(0.4, 2.0, 7.0 - 6.0 * (1 - (1 - u) ** 2), 12, 0, 18), **brake)
    K(a, 379, "quad_out", R=root(0.4, 2.6, 0.9, 4, 0, 6), T=tp(0.3, -10, 4), H=P((8, 0, 0)), RA=P((20, 0, 14)), LA=P((10, 0, -10)), RL=P((30, 0, 5)), LL=P((10, 0, -5)))
    K(a, 385, "sine_inout", R=root(0, 2.97, 0.9, 0, 0, 0), **stand)


BLOCKS = {  # the mannequin's blocks fly apart (offset in the part's parent frame, spin)
    "Head": ((0.6, 2.4, 1.6), (30, 40, 70)), "Right Arm": ((-2.8, 1.6, -1.2), (-20, 10, 80)), "Left Arm": ((2.4, 1.4, 2.2), (30, -20, -70)),
    "Right Leg": ((-1.4, 0.6, -2.8), (50, 10, -30)), "Left Leg": ((1.8, 0.9, -2.6), (-40, 30, 20)),
}
SHORT = {"Head": "H", "Right Arm": "RA", "Left Arm": "LA", "Right Leg": "RL", "Left Leg": "LL"}


def dummy_anim(a: Animation) -> None:
    stand = dict(T=tp(0, 0), H=P((0, 0, 0)), RA=P((8, 0, 4)), LA=P((8, 0, -4)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 0, "linear", R=root(DX, 3.0, 0, 0, 90.0), **stand)
    K(a, 258, "linear", R=root(DX, 3.0, 0, 0, 90.0), T=tp(0, 0))
    # struck on 259: folds and is thrown back (+X), staggers, stands again (265-273 the far shot)
    K(a, 260, "quad_out", R=root(DX + 1.5, 3.0, 0, -15, 90.0), T=tp(0.0, -40), H=P((-30, 0, 0)), RA=P((-50, 0, 30)), LA=P((-60, 0, -30)), RL=P((-20, 0, 3)), LL=P((30, 0, -3)))
    K(a, 266, "quad_out", R=root(DX + 4.0, 2.9, 0, 10, 90.0), T=tp(0.0, -15), H=P((10, 0, 0)), RA=P((40, 0, 18)), LA=P((30, 0, -18)), RL=P((6, 0, 3)), LL=P((10, 0, -3)))
    K(a, 272, "sine_inout", R=root(DX + 3.0, 3.0, 0, 0, 90.0), **stand)
    # struck again on 274-276: falls on his back and lies there while the hero kneels over him (278-283)
    K(a, 274, "quad_in", R=root(DX + 3.0, 3.0, 0, 0, 90.0), **stand)
    K(a, 278, "quad_out", R=root(DX + 3.6, 0.55, 0.5, 0, 0, -90), T=tp(0, 0), H=P((0, 0, 0)), RA=P((0, 0, 20)), LA=P((0, 0, -20)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))
    K(a, 283, "constant", R=root(DX + 3.6, 0.55, 0.5, 0, 0, -90), T=tp(0, 0))
    # 284: the picture cuts to the final blow; he stands again, 22 studs further on, facing the runner
    K(a, 284, "linear", R=root(XD2, 3.0, 0, 0, 90.0), **stand)
    K(a, 306, "linear", R=root(XD2, 3.0, 0, 0, 90.0), T=tp(0, 0))
    K(a, 308, "quad_out", R=root(XD2 + 0.4, 3.0, 0, 6, 90.0), T=tp(0.0, 8, 4), H=P((-22, 0, 14)))   # the cut: the head leans, the body does not yet know
    K(a, 341, "sine_inout", R=root(XD2 + 0.6, 2.98, 0, 8, 90.0), T=tp(0.0, 10, 6), H=P((-26, 0, 18)))
    # 342: he bursts into his blocks (offset + spin per part, as in the first short)
    for part, (off, spin) in BLOCKS.items():
        base = a.sample_part(part, 341)
        K(a, 342, "linear", **{SHORT[part]: base})
        K(a, 349, "quad_out", **{SHORT[part]: P(tuple(base.rot[i] + spin[i] for i in range(3)), off)})
        K(a, 385, "linear", **{SHORT[part]: P(tuple(base.rot[i] + spin[i] for i in range(3)), off)})


def chase_cam(hp, hdg, f0: int, f1: int, back=13.0, side: float = 2.4, up: float = 1.3, ahead: float = 5.0, lift: float = 1.6,
              fov: float = 42.0, lag: float = 0.22, roll: float = 25.0, seg: int = 10):
    """Camera low behind and slightly beside the runner, looking along his line of travel. The heading it follows lags behind his sharp turns (so the
    picture swings), and the roll snaps to the other side at every turn."""
    ang, a = {}, math.radians(hdg(f0))
    for f in range(f0, f1 + 1):
        a += (math.radians(hdg(f)) - a) * lag
        ang[f] = a

    def fn(u: float, f: float):
        f = max(f0, min(f1, int(round(f))))
        h = ang[f]
        d = (math.cos(h), 0.0, math.sin(h))
        r = (-d[2], 0.0, d[0])
        c = hp(f)
        bk = back(f) if callable(back) else back
        pos = (c[0] - d[0] * bk + r[0] * side, up, c[2] - d[2] * bk + r[2] * side)
        tgt = (c[0] + d[0] * ahead, lift, c[2] + d[2] * ahead)
        sg = 1 if hdg(f) >= 0 else -1
        return pos, tgt, fov, sg * roll
    return fn


def chase_framed(hp, hdg, f0: int, f1: int, track: dict, yaw_off: float = 28.0, fov: float = 40.0, hero_h: float = 5.0, lag: float = 0.15, aspect: float = 737 / 384):
    """The reference's *chase*: the camera turns with his heading (lagging a little, ``yaw_off`` degrees off his back), and the distance / on-screen position come
    from the tracked reference hero (size ``h`` -> distance, centroid ``cx, cy`` -> where he sits in the frame)."""
    def fill(v):
        a = np.array([np.nan if x is None else x for x in v], float)
        idx = np.arange(len(a))
        ok = ~np.isnan(a)
        return np.interp(idx, idx[ok], a[ok])

    sm = lambda v: np.convolve(np.pad(fill(v), 2, mode="edge"), np.ones(5) / 5, mode="valid")
    cx, cy, hh = sm(track["cx"]), sm(track["cy"]), sm(track["h"])
    ang, a_ = {}, math.radians(hdg(f0))
    for f in range(f0, f1 + 1):
        a_ += (math.radians(hdg(f)) - a_) * lag
        ang[f] = a_
    t = math.tan(math.radians(fov) / 2.0)

    def fn(u: float, f: float):
        f = max(f0, min(f1, int(round(f))))
        i = min(len(cx) - 1, f - f0)
        h = ang[f] + math.radians(yaw_off)
        fwd = (math.cos(h), 0.0, math.sin(h))
        r = (-fwd[2], 0.0, fwd[0])
        D = hero_h / (max(float(hh[i]), 0.08) * 2.0 * t)
        S = 2.0 * D * t
        X, Y = (float(cx[i]) - aspect / 2.0) * S, -(float(cy[i]) - 0.5) * S
        c = hp(f)
        pos = (c[0] - fwd[0] * D - r[0] * X, c[1] - Y, c[2] - fwd[2] * D - r[2] * X)
        return pos, (pos[0] + fwd[0], pos[1], pos[2] + fwd[2]), fov, 0.0
    return fn


def framed_cam(hp, f0: int, track: dict, fov: float = 30.0, aspect: float = 737 / 384, hero_h: float = 5.5):
    """Camera that reproduces the reference's *framing*: the hero lands where the tracked reference hero is in the picture (centroid ``cx, cy`` in picture heights)
    and at the same apparent size ``h`` - so the follow is the reference's follow (it does not lock on him: he drifts across the frame while the camera sweeps).
    The camera looks along -Z from the +Z side (screen right = +X). Gaps in the track are interpolated, the series lightly smoothed."""
    def fill(v):
        a = np.array([np.nan if x is None else x for x in v], float)
        idx = np.arange(len(a))
        ok = ~np.isnan(a)
        return np.interp(idx, idx[ok], a[ok])

    cx, cy, hh = (np.convolve(np.pad(fill(track[k]), 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid") for k in ("cx", "cy", "h"))
    t = math.tan(math.radians(fov) / 2.0)

    def fn(u: float, f: float):
        i = max(0, min(len(cx) - 1, int(round(f)) - f0))
        D = hero_h / (max(float(hh[i]), 0.08) * 2.0 * t)
        S = 2.0 * D * t
        X, Y = (float(cx[i]) - aspect / 2.0) * S, -(float(cy[i]) - 0.5) * S
        c = hp(f)
        pos = (c[0] - X, c[1] - Y, c[2] + D)
        return pos, (pos[0], pos[1], pos[2] - 1.0), fov, 0.0
    return fn


def build() -> Scene:
    hero = Character("hero", Animation("hero", fps=FPS, archetype="cinematic"), colors=RONIN_COLORS, outfit=ronin_outfit(draw=DRAW), face="std")
    dummy = Character("dummy", Animation("dummy", fps=FPS, archetype="cinematic"), colors=PALE, outfit=dummy_outfit(), hide=("Head",))
    hero_anim(hero)
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
    _, _, hdg = zigzag()
    cine.shot(72, 148, chase_framed(hp, hdg, 72, 148, json.loads(TRACK72.read_text()), yaw_off=58.0, fov=40.0))
    cine.shot(149, 183, chase_cam(hp, hdg, 149, 183, back=12.0, side=5.0, up=1.2, ahead=8.0, lift=2.6, fov=42, roll=5.0))
    for f0 in range(184, 240, 10):   # the low side travelling shot (the reference's 184-239): the roll still snaps at every turn
        sg = 1 if hdg(f0) >= 0 else -1
        cine.shot(f0, min(239, f0 + 9), tracking(hp, (6.0, 1.0, -22.0), look_dy=0.8, fov=34, roll=(sg * 3, sg * 6)))
    cine.shot(240, 256, autoframe(both, 240, 256, azimuth=15, elevation=5, fov=36, fill=1.0, follow=0.25, min_radius=3.5))
    cine.shot(257, 264, autoframe(both, 257, 264, azimuth=40, elevation=8, fov=34, fill=0.95, follow=0.4, min_radius=2.6))
    cine.shot(265, 273, autoframe(both, 265, 273, azimuth=65, elevation=12, fov=38, fill=0.6, follow=0.2, min_radius=3.5))
    cine.shot(274, 281, autoframe(both, 274, 281, azimuth=30, elevation=8, fov=32, fill=0.8, follow=0.3, min_radius=2.6))
    cine.shot(278, 283, tracking(hp, (2.5, 4.2, 4.6), look_dy=-1.0, fov=34))
    cine.shot(284, 299, framed_cam(hp, 284, json.loads(TRACK284.read_text()), fov=30.0))
    # the final blow, three angles on the same cut: A (300-309) low side, the runner crosses the left foreground; B (310-341) the macro on the blade; C (342-355) pulled back
    cine.shot(300, 305, dolly((XD2 - 11.0, 1.3, 8.5), (XD2 - 8.5, 1.4, 7.5), (XD2 - 5.0, 2.5, 0.0), (XD2 - 3.8, 2.7, 0.0), fov=34))
    cine.shot(306, 309, dolly((XD2 - 6.0, 2.5, 6.8), (XD2 - 5.6, 2.6, 6.4), (XD2 - 3.4, 3.4, 0.0), (XD2 - 3.2, 3.5, 0.0), fov=28))
    cine.shot(310, 341, dolly((XD2 - 6.6, 3.0, 7.6), (XD2 - 6.0, 3.1, 7.2), (XD2 - 2.6, 3.7, 0.0), (XD2 - 2.2, 3.8, 0.0), fov=26))
    cine.shot(342, 349, autoframe(both, 342, 349, azimuth=30, elevation=10, fov=36, fill=0.9, follow=0.3, min_radius=3.0))
    cine.shot(350, 359, tracking(hp, (5.0, 2.0, 9.0), look_dy=0.4, fov=36))
    cine.shot(360, 369, tracking(hp, (9.0, 14.0, 10.0), fov=40))
    cine.shot(366, 374, dolly((4.0, 2.0, 25.0), (3.4, 1.9, 20.0), (0.4, 1.8, 4.0), (0.4, 1.6, 1.5), fov=34, roll=-22))
    cine.shot(375, N - 1, dolly((3.4, 2.0, 20.0), (4.5, 3.0, 24.0), (0.4, 2.4, 0.6), (-0.6, 3.0, 0.0), fov=(34, 30), roll=(-22, 0)))

    # ---- smooth speed shell around the torso (stretched along the heading), thin ring, needles behind it, thin diagonals that avoid him
    dir_at = lambda f: (math.cos(math.radians(hdg(f))), 0.0, math.sin(math.radians(hdg(f)))) if 72 <= f <= 239 else ((1.0, 0.0, 0.0) if f <= 349 else (-1.0, 0.0, 0.0))
    cine.bubble(66, 256, hp, 2.1, "#c4d8e8", 0.5, dir_at=dir_at, stretch=1.0, hatch=6)
    cine.bubble(78, 239, lambda f: tuple(v + o for v, o in zip(hp(max(72, f - 7)), (0, 1.2, 0))), 4.0, "#c4d8e8", 0.12, dir_at=dir_at, stretch=1.0)   # the ghost of the shell, lagging behind him
    cine.bubble(265, 273, hp, 2.2, "#c4d8e8", 0.5, dir_at=dir_at, stretch=1.1)
    cine.bubble(284, 305, hp, 2.4, "#c4d8e8", 0.5, dir_at=dir_at, stretch=1.0)
    cine.bubble(350, 365, hp, 2.4, "#c4d8e8", 0.5, dir_at=dir_at, stretch=1.0)
    for f0, f1 in ((72, 239), (284, 305), (350, 365)):
        for f in range(f0, f1, 3):
            d, c = dir_at(f), hp(f)
            a_ = (c[0] - d[0] * 22, 0.12, c[2] - d[2] * 22)   # toward the camera: the fan opens
            b_ = (c[0] - d[0] * 1.5, 0.12, c[2] - d[2] * 1.5)  # at his feet: it closes
            cine.streaks(f, 3, a_, b_, n=35, r0=3.0, r1=0.12, w=0.04, color="#f2f2f5", seed=f)
    for f0, f1 in ((72, 140), (150, 180), (184, 239), (284, 305), (350, 365)):
        for f in range(f0, f1, 5):
            cine.screen_fx("diag", f, 3, n=8, angle=-22, seed=f, avoid=0, avoidR=0.22, thick=0.012)
            if f % 10 == 0:
                cine.screen_fx("diag", f, 3, n=2, angle=-26, seed=f + 1, avoid=0, avoidR=0.22)
    # thin curved wakes off the feet, hands and shoulder (not one rigid tube), a faint wide one behind the torso
    for f0, f1 in ((184, 239), (284, 305), (350, 365)):
        for part, w, al in (("Right Leg", 0.3, 0.5), ("Left Leg", 0.3, 0.5)):
            cine.ink_trail(f0, f1, 0, part, (0, -1.0, 0), 9, w, 0.0, "#f2f2f5", rag=0.25, seed=21, alpha=al)
        cine.ink_trail(f0, f1, 0, "Torso", (0, 0, 0), 12, 0.7, 0.0, "#cfcfd4", rag=0.5, seed=22, alpha=0.16)
    # leg smear on the sideways start (66-71): the planted leg is stretched toward where he is going
    for part, col, al in (("Left Leg", "#16161a", 0.95), ("Right Leg", "#e9e9ee", 0.8)):
        cine.ink_trail(66, 72, 0, part, (0, -1.0, 0), 4, 1.5, 0.1, col, rag=0.3, seed=30, alpha=al)
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
    for t0, d in ((63, 3), (149, 2), (181, 3), (274, 2)):
        cine.screen_fx("negative", t0, d, hue=150 + (t0 % 3) * 20)
    cine.screen_fx("bw", 257, 3, contrast=24, bright=2.6, bfirst=True, shards=10, prisms=12, seed=5)   # impact frame: white world, black silhouettes, cyan/yellow shards
    cine.streaks(260, 10, (DX + 1.5, 2.2, 0.7), (DX + 30.0, 2.6, 0.7), n=30, r0=0.2, r1=3.5, w=0.07, color="#ffffff", seed=9)   # the blast cone out of the cut
    cine.screen_fx("edges", 274, 8, n=70, seed=2)
    cine.screen_fx("edges", 310, 32, n=40, seed=3)
    cine.screen_fx("edges", 342, 8, n=70, seed=4)
    cine.debris_piece(369, (0.2, 0.3, 3.6), (0.02, 0.11, -0.08), (1.0, 0.6, 0.8), "#6c6a70", (4, 2, 1), g=0.02)   # the block his foot kicks up in the skid
    cine.emit(366, 376, origin=(0.4, 0.2, 3.4), rate=3.0, vel=(0.04, 0.2), dir=(0, 1, 0), spread=1.3, life=(12, 24), size=(0.8, 1.8), color=("#8e8c93", "#5a585e"), alpha=(0.5, 0.0), add=False, seed=12, radius=1.8, shape="smoke")
    cine.screen_fx("bw", 306, 3, contrast=24, bright=2.6, bfirst=True, shards=0)
    cine.screen_fx("bw", 309, 1, contrast=24, bright=2.6, bfirst=True, shards=0, multiply="#d4221c")
    # ---- red sparks (the only warm colour), blade glints, the blocks
    cine.emit(258, 281, origin=(DX - 1.0, 2.0, 0.6), rate=3.0, burst=30, vel=(0.12, 0.45), dir=(0, 1, 0.2), spread=1.6, grav=0.02, life=(10, 26), size=(0.22, 0.06), color=("#ff3b2a", "#a01212"), alpha=(1.0, 0.0), add=True, seed=6, shape="spark", stretch=3.0)
    cine.emit(278, 283, origin=(DX - 0.4, 1.2, 0.8), rate=3.0, burst=20, vel=(0.1, 0.4), dir=(0, 1, 0.3), spread=1.6, grav=0.02, life=(10, 24), size=(0.2, 0.05), color=("#ff3b2a", "#a01212"), alpha=(1.0, 0.0), add=True, seed=14, shape="spark", stretch=3.0)
    cine.glow(318, 324, c=(XD2 - 2.6, 4.0, 0.3), r0=2.2, r1=5.0, color="#ffffff")   # the glint of the blade in the macro: a local glare, not a white screen
    for t in range(320, 323):
        cine.flash(t, 1, "#ffffff", 0.28)
    cine.emit(322, 341, origin=(XD2 - 1.6, 4.1, 0.2), rate=1.5, vel=(0.03, 0.2), dir=(0, 1, 0.3), spread=1.2, grav=0.015, life=(8, 20), size=(0.15, 0.04), color=("#ff3b2a", "#7a0c0c"), alpha=(1.0, 0.0), add=True, seed=7, shape="spark", stretch=2.5)
    cine.emit(342, 349, origin=(XD2, 2.5, 0.0), burst=26, rate=0.0, vel=(0.1, 0.4), dir=(0, 1, 0), spread=1.8, grav=0.02, life=(10, 24), size=(0.25, 0.08), color=("#d9d9de", "#6a6a70"), alpha=(0.9, 0.0), add=False, seed=8, shape="shard")
    return Scene("calm — reproduction de la 2e référence", [hero, dummy], fps=FPS, cine=cine)
