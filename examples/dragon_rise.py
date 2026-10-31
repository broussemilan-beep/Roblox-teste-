"""« Dragon montant » - an ORIGINAL 5-second combat animation (not a copy of any reference), 30 images per second.

Story: a standoff, a dash, an UPPERCUT that launches the dummy, a jump after it, an AXE KICK from the top that smashes it into the ground, a crouched landing, a slow walk away.

What is mine here, and what is borrowed
  * mine: the story, the timing, the two impacts (long anticipation, 2-3 image strike, 3 image hit-stop, flash, shock rings), the whole aerial fight (jump, cocked leg, axe kick,
    landing: written pose by pose), the dummy's flight (ballistic, solved so that it passes exactly through the fist and then the foot), the camera and the effects;
  * borrowed: the ground mechanics (guard, crouch, run, punch base, landing, walk) come from free CMU motion capture, retargeted to R6 with piston-disjointed limbs
    (``tsb_engine/mocap.py``, clips in ``docs/research/mocap-r6``).

Time: ``tau`` is the animation clock, ``f`` the film image.  Both bodies are frozen for 3 images at each hit (hit-stop) while the camera and the effects keep going.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np

from tsb_engine import mocap
from tsb_engine.authoring import K, P, root_pose
from tsb_engine.cinematic import Cinematic, autoframe, dolly, tracking
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from . import practice as PR

FPS = 30
N = 150
STOP = 3                        # hit-stop, in images
HIT1, HIT2 = 48, 78             # animation clock of the uppercut and of the axe kick
G_AIR = 0.055                   # gravity of the anime world, studs per image^2
LIB = Path(__file__).resolve().parent.parent / "docs" / "research" / "mocap-r6" / "clips.npz"

HERO_Z = -1.5                   # the hero walks on this line; his near arm (+z) reaches the dummy's centre line
HERO_COLORS = {"Torso": "#e2582a", "Head": "#f2c48a", "Right Arm": "#f2c48a", "Left Arm": "#f2c48a", "Right Leg": "#1c1f27", "Left Leg": "#1c1f27"}
DUMMY_COLORS = {p: "#f3eee2" for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}
DUMMY_COLORS.update({"Torso": "#fbf7ee", "Head": "#e4dcc6", "Right Leg": "#d9d1bb", "Left Leg": "#d9d1bb"})

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the two clocks

def film_of(tau: float) -> int:
    f = int(tau)
    if tau > HIT1:
        f += STOP
    if tau > HIT2:
        f += STOP
    return f


def tau_table() -> np.ndarray:
    t = np.zeros(N)
    for f in range(N):
        if f <= HIT1:
            t[f] = f
        elif f < HIT1 + STOP:
            t[f] = HIT1
        elif f <= HIT2 + STOP:
            t[f] = f - STOP
        elif f < HIT2 + 2 * STOP:
            t[f] = HIT2
        else:
            t[f] = f - 2 * STOP
    return t


TAU = tau_table()
M = int(TAU[-1]) + 1            # animation frames


def smooth(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_fn(style: str, u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    if style == "in":
        return u ** 2.4
    if style == "out":
        return 1 - (1 - u) ** 2.4
    if style == "lin":
        return u
    if style == "hold":
        return 0.0
    if style == "back":
        c1 = 1.70158
        return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
    return smooth(u)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the hero

PLAN_X = [(0, -8.0), (24, -8.0), (30, -8.1), (44, 2.6), (48, 3.0), (60, 4.6), (78, 6.2), (87, 6.6), (100, 6.6), (143, 10.8)]   # where the hero is, by animation clock


def plan_x(tau: float) -> float:
    return float(np.interp(tau, [p[0] for p in PLAN_X], [p[1] for p in PLAN_X]))


BASE = dict(ry=-90, rx=0, rz=0, T_rx=0, T_ry=0, T_rz=0, H_rx=0, H_ry=0, RA_rx=0, RA_rz=8, LA_rx=0, LA_rz=-8, RL_rx=0, RL_rz=4, LL_rx=0, LL_rz=-4,
            RA_slide=0, LA_slide=0, RL_slide=0, LL_slide=0)
NAMES20 = mocap.NAMES20

# Everything is written for a SIDE view (the lens is on the +z side, the hero runs to +x): what reads there is the forward / back swing of limbs and the lean of the body.
# The near arm (right, +z) is the striking arm; it is kept low and back until it swings, so it never hides his face and chest.
GROUND_KEYS = {
    0: dict(ry=-84, T_ry=-8, T_rz=-3, H_ry=10, rx=-6, T_rx=-4, H_rx=2, RA_rx=-68, RA_rz=6, LA_rx=78, LA_rz=-10, RA_slide=0.4, LA_slide=0.9, RL_rx=-28, RL_rz=4, LL_rx=26, LL_rz=-4, RL_slide=0.35, LL_slide=0.45),     # guard: the far fist up by the chin, the near arm cocked back, feet apart
    12: dict(ry=-86, T_ry=-10, T_rz=-4, H_ry=12, rx=-10, T_rx=-6, H_rx=3, RA_rx=-72, RA_rz=6, LA_rx=84, LA_rz=-10, RA_slide=0.4, LA_slide=0.9, RL_rx=-30, RL_rz=4, LL_rx=28, LL_rz=-4, RL_slide=0.55, LL_slide=0.65),  # breathing in: a little lower
    22: dict(ry=-93, T_ry=-14, T_rz=-5, H_ry=18, rx=-8, T_rx=-5, H_rx=2, RA_rx=-70, RA_rz=6, LA_rx=80, LA_rz=-10, RA_slide=0.4, LA_slide=0.9, RL_rx=-29, RL_rz=4, LL_rx=27, LL_rz=-4, RL_slide=0.45, LL_slide=0.55),
    29: dict(ry=-106, T_ry=-26, T_rz=-8, H_ry=30, rx=-26, T_rx=-14, H_rx=8, RA_rx=-92, RA_rz=8, LA_rx=36, LA_rz=-12, RA_slide=0.1, LA_slide=0.7, RL_rx=-55, RL_rz=4, LL_rx=48, LL_rz=-4, RL_slide=1.3, LL_slide=1.3),       # the load: a deep sink, the arms thrown back
}
GROUND_EASE = {0: "io", 12: "io", 22: "in", 29: "hold"}
STRIKE_KEYS = {
    44: dict(ry=-110, T_ry=-32, T_rz=-8, H_ry=34, rx=-16, T_rx=-8, H_rx=6, RA_rx=-96, RA_rz=8, LA_rx=58, LA_rz=-12, RA_slide=0.0, LA_slide=0.9, RL_rx=-42, RL_rz=4, LL_rx=44, LL_rz=-4, RL_slide=0.7, LL_slide=0.8),        # wind-up: the arm hauled back and low, the hips dropped
    46: dict(ry=-98, T_ry=-34, T_rz=-6, H_ry=26, rx=-20, T_rx=-10, H_rx=4, RA_rx=-18, RA_rz=8, LA_rx=40, LA_rz=-12, RA_slide=0.1, LA_slide=0.9, RL_rx=-46, RL_rz=4, LL_rx=48, LL_rz=-4, RL_slide=1.2, LL_slide=1.2),       # the arm sweeps through low
    47: dict(ry=-80, T_ry=-10, T_rz=2, H_ry=6, rx=-6, T_rx=0, H_rx=0, RA_rx=84, RA_rz=8, LA_rx=-10, LA_rz=-12, RA_slide=0.2, LA_slide=0.5, RL_rx=-38, RL_rz=4, LL_rx=52, LL_rz=-4, RL_slide=0.7, LL_slide=1.0),
    48: dict(ry=-70, T_ry=22, T_rz=9, H_ry=-22, rx=4, T_rx=8, H_rx=-6, RA_rx=128, RA_rz=8, LA_rx=-46, LA_rz=-12, RA_slide=0.0, LA_slide=0.2, RL_rx=-32, RL_rz=4, LL_rx=54, LL_rz=-4, RL_slide=0.3, LL_slide=0.8),           # CONTACT: the fist is up and forward, the body is stretched, the back foot driving
    51: dict(ry=-78, T_ry=10, T_rz=6, H_ry=-8, rx=8, T_rx=10, H_rx=-6, RA_rx=172, RA_rz=8, LA_rx=-60, LA_rz=-14, RA_slide=0.0, LA_slide=0.0, RL_rx=-24, RL_rz=4, LL_rx=40, LL_rz=-4, RL_slide=0.2, LL_slide=0.5),       # follow-through, held
}
STRIKE_EASE = {44: "in", 46: "in", 47: "in", 48: "out", 51: "io"}
LAND_KEYS = {
    88: dict(rx=-30, T_rx=-20, RA_rx=70, RA_rz=18, LA_rx=60, LA_rz=-18, RL_rx=30, RL_rz=8, LL_rx=26, LL_rz=-8, RL_slide=1.5, LL_slide=1.4),        # the touchdown squat
    92: dict(rx=-38, T_rx=-24, RA_rx=42, RA_rz=22, LA_rx=30, LA_rz=-22, RL_rx=34, RL_rz=8, LL_rx=30, LL_rz=-8, RL_slide=1.65, LL_slide=1.55),      # absorbing
    98: dict(rx=-16, T_rx=-8, RA_rx=14, RA_rz=14, LA_rx=6, LA_rz=-14, RL_rx=12, RL_rz=6, LL_rx=10, LL_rz=-6, RL_slide=0.8, LL_slide=0.8),            # rising
    105: dict(rx=0, T_rx=0, RA_rx=-6, RA_rz=8, LA_rx=6, LA_rz=-8, RL_rx=0, RL_rz=4, LL_rx=0, LL_rz=-4),                                              # upright, the arms hang
}
LAND_EASE = {88: "out", 92: "io", 98: "io"}


def authored_from(keys: dict, ease: dict, t0: int, t1: int) -> np.ndarray:
    """Interpolate the 20 angles between keys (a key only has to say what changes: the rest is carried forward from the previous key)."""
    ks = sorted(keys)
    full, prev = {}, dict(BASE)
    for k in ks:
        d = dict(prev)
        d.update(keys[k])
        full[k] = d
        prev = d
    out = np.zeros((t1 - t0 + 1, 20))
    for i, t in enumerate(range(t0, t1 + 1)):
        j = max(0, min(len(ks) - 2, int(np.searchsorted(ks, t, side="right")) - 1))
        a, b = ks[j], ks[j + 1]
        u = ease_fn(ease.get(a, "io"), (t - a) / (b - a)) if b > a else 0.0
        for c, n in enumerate(NAMES20):
            out[i, c] = full[a][n] + (full[b][n] - full[a][n]) * u
    return out


def hero_track():
    """Mocap only where a human does the work better than I can draw it: the run (dash) and the walk away."""
    lib = mocap.load_library(LIB)
    dash, dxz, dair = mocap.assemble([dict(clip="49_04", t0=0.3, t1=1.0, n=14, yaw=-90)], lib, follow=np.array([[plan_x(30 + t), HERO_Z] for t in range(14)]),
                                      start_xz=(plan_x(30), HERO_Z))
    walk, wxz, wair = mocap.assemble([dict(clip="07_01", t0=0.3, t1=1.9, n=38, yaw=-90)], lib, follow=np.array([[plan_x(106 + t), HERO_Z] for t in range(38)]),
                                      start_xz=(plan_x(106), HERO_Z))
    return dash, dxz, dair, walk, wxz, wair


def author_keys():
    """The aerial fight, pose by pose (animation clock 52..87)."""
    keys = {
        51: dict(ry=-78, T_ry=10, T_rz=6, H_ry=-8, rx=8, T_rx=10, RA_rx=172, RA_rz=8, LA_rx=-60, LA_rz=-14, RL_rx=-24, RL_rz=4, LL_rx=40, LL_rz=-4, RL_slide=0.2, LL_slide=0.5),                        # the uppercut's follow-through
        56: dict(ry=-66, T_ry=0, T_rz=4, H_ry=0, rx=12, T_rx=8, H_rx=-4, RA_rx=140, RA_rz=10, LA_rx=-20, LA_rz=-14, RL_rx=14, RL_rz=6, LL_rx=34, LL_rz=-6, RL_slide=0.3, LL_slide=0.4),                       # rising on the strike: the arm drifts down behind the fist, legs trail
        62: dict(ry=-46, T_ry=-10, T_rz=0, H_ry=14, rx=6, T_rx=0, RA_rx=125, RA_rz=22, LA_rx=110, LA_rz=-22, RL_rx=70, RL_rz=6, LL_rx=-28, LL_rz=-8, RL_slide=0.9, LL_slide=0.5),                      # rising, the right knee comes up
        68: dict(ry=-72, T_ry=-14, T_rz=-4, H_ry=18, rx=18, T_rx=6, RA_rx=-55, RA_rz=14, LA_rx=140, LA_rz=-14, RL_rx=118, RL_rz=6, LL_rx=-26, LL_rz=-6, RL_slide=0.4, LL_slide=0.2),                    # leaning back, the leg is cocked, the arms opposed
        72: dict(ry=-92, T_ry=-8, T_rz=-6, H_ry=8, rx=32, T_rx=10, H_rx=10, RA_rx=-62, RA_rz=14, LA_rx=146, LA_rz=-14, RL_rx=172, RL_rz=4, LL_rx=-20, LL_rz=-5, RL_slide=0.0, LL_slide=0.0),          # the apex: the leg straight up, held
        75: dict(ry=-94, T_ry=-6, T_rz=-6, H_ry=6, rx=34, T_rx=10, H_rx=12, RA_rx=-66, RA_rz=14, LA_rx=150, LA_rz=-14, RL_rx=176, RL_rz=4, LL_rx=-22, LL_rz=-5),                                       # a breath at the top
        77: dict(ry=-84, T_ry=8, T_rz=2, H_ry=-4, rx=6, T_rx=-6, RA_rx=-20, RA_rz=14, LA_rx=40, LA_rz=-14, RL_rx=100, RL_rz=4, LL_rx=-12, LL_rz=-6),                                                 # the leg drops
        78: dict(ry=-74, T_ry=18, T_rz=6, H_ry=-14, rx=-6, T_rx=-6, H_rx=-6, RA_rx=70, RA_rz=14, LA_rx=-30, LA_rz=-14, RL_rx=44, RL_rz=3, LL_rx=-16, LL_rz=-6),                                      # CONTACT: the heel lands, the body folds over it
        81: dict(ry=-80, T_ry=10, T_rz=4, H_ry=-8, rx=-14, T_rx=-10, RA_rx=84, RA_rz=18, LA_rx=-40, LA_rz=-18, RL_rx=20, RL_rz=3, LL_rx=-10, LL_rz=-6),                                                # through
        85: dict(ry=-86, T_ry=0, T_rz=0, H_ry=0, rx=-20, T_rx=-10, RA_rx=30, RA_rz=44, LA_rx=40, LA_rz=-44, RL_rx=14, RL_rz=6, LL_rx=22, LL_rz=-6),                                                 # falling, arms out for balance
    }
    ease = {51: "io", 56: "io", 62: "io", 68: "io", 72: "hold", 75: "in", 77: "in", 78: "back", 81: "io", 85: "in"}
    return BASE, keys, ease


def authored(tau0: int, tau1: int) -> np.ndarray:
    _, keys, ease = author_keys()
    # the landing key 88 closes the aerial span so that the last frames fall into the squat
    keys = {**keys, 88: LAND_KEYS[88]}
    return authored_from(keys, {**ease, 85: "in"}, tau0, tau1)


def hero_angles():
    """The hero's 20 angles, his planar path and his height over the whole animation clock."""
    dash, dxz, dair, walk, wxz, wair = hero_track()
    # 0-29 the guard and the load (written), 30-43 the dash (capture), 44-51 the uppercut (written), 52-87 the aerial fight (written), 88-105 landing and rising (written), 106-143 the walk (capture)
    g = authored_from(GROUND_KEYS, GROUND_EASE, 0, 29)
    st = authored_from(STRIKE_KEYS, STRIKE_EASE, 44, 51)
    mid = authored(52, 87)
    ld = authored_from(LAND_KEYS, LAND_EASE, 88, 105)
    seg = {"g": g, "dash": dash, "st": st, "mid": mid, "ld": ld, "walk": walk}
    parts = [g, dash, st, mid, ld, walk]
    # breathing in the guard
    for i in range(len(g)):
        g[i, 1] += 1.2 * math.sin(i * 0.5)
    for k in range(1, len(parts)):
        for c in range(0, 16):
            parts[k][:, c] += 360.0 * np.round((parts[k - 1][-1, c] - parts[k][0, c]) / 360.0)
    ang = np.vstack(parts)
    assert len(ang) == M, (len(ang), M)
    xz = np.array([[plan_x(t), HERO_Z] for t in range(M)])
    xz[30:44] = dxz
    xz[106:] = wxz
    air = np.zeros(M)
    air[30:44] = dair
    air[106:] = wair
    for t in range(47, 88):          # the flight starts with the strike (47): up to the apex at 72, then pulled down by the kick
        if t < 47:
            air[t] = 0.0
        elif t <= 72:
            u = (t - 47) / 25.0
            air[t] = 8.6 * (1 - (1 - u) ** 2)
        elif t <= 78:
            air[t] = 8.6 - 0.9 * ((t - 72) / 6.0) ** 2
        else:
            u = (t - 78) / 9.0
            air[t] = (8.6 - 0.9) * (1 - u ** 1.8)
    # cross-fade 3 images over each join so that nothing pops
    for j in (30, 44, 52, 88, 106):
        prev = ang[j - 1].copy()
        for i in range(3):
            w = (i + 1) / 4.0
            ang[j + i] = prev * (1 - w) + ang[j + i] * w
    return ang, xz, air


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the dummy: a ballistic flight solved to pass through the fist and then the heel

def dummy_motion(fist: np.ndarray, heel: np.ndarray, hero_x48: float):
    """Positions (x, torso height, z) and the 16 angles of the dummy over the animation clock."""
    pos = np.zeros((M, 3))
    ang = np.zeros((M, 16))
    x0 = hero_x48 + 1.95
    base = np.array([x0, 3.0, HERO_Z + 0.5])      # same depth plane as the hero (side view): the fist lands on its near flank, it never flies in front of him
    pos[:] = base
    p0 = np.array([x0, max(fist[1], 3.0), base[2]])
    T1 = HIT2 - HIT1
    a = np.array([0.0, -G_AIR, 0.0])
    tgt = np.array([heel[0] + 0.15, heel[1] + 0.1, heel[2] - 0.1])
    v0 = (tgt - p0 - 0.5 * a * T1 * T1) / T1
    TG = HIT2 + 6                                    # the heel drives it into the floor
    ground = 0.55
    vs = np.array([0.18, -0.42, 0.0])
    aS = np.array([0.0, -0.085, 0.0])
    tg = TG - HIT2
    p_k = tgt
    # solve the smash velocity so that it reaches the floor exactly at TG
    vs[1] = (ground - p_k[1] - 0.5 * aS[1] * tg * tg) / tg
    p_g = p_k + vs * tg + 0.5 * aS * tg * tg
    v_g = vs + aS * tg
    for t in range(M):
        if t <= HIT1:
            pos[t] = base + np.array([0.0, 0.0, 0.0])
        elif t <= HIT2:
            s = t - HIT1
            pos[t] = p0 + v0 * s + 0.5 * a * s * s
        elif t <= TG:
            s = t - HIT2
            pos[t] = p_k + vs * s + 0.5 * aS * s * s
        else:
            s = t - TG
            # one small bounce, then a slide that dies out
            vy = -v_g[1] * 0.30
            pos[t] = np.array([p_g[0] + 0.18 * (1 - 0.82 ** s) / (1 - 0.82), max(ground, ground + vy * s - 0.5 * 0.085 * s * s), p_g[2]])
    # orientation: a backward tumble that eases out, then it lies flat on its back
    r_hit2 = 2.2 / 0.04 * (1 - math.exp(-0.04 * (HIT2 - HIT1)))      # it stays nearly upright until the heel: lying flat it would cut through the hero
    for t in range(M):
        if t <= HIT1:
            rx = 2.0 * math.sin(0.18 * t)
        elif t <= HIT2:
            rx = 2.2 / 0.04 * (1 - math.exp(-0.04 * (t - HIT1)))
        elif t <= TG:
            rx = r_hit2 + (92.0 - r_hit2) * ease_fn("in", (t - HIT2) / (TG - HIT2))
        else:
            rx = 92.0 + 4.0 * math.exp(-0.5 * (t - TG)) * math.sin(1.2 * (t - TG))
        s_eff = max(0, min(t, TG) - HIT1)
        ry = 90.0 + 3.5 * (1 - math.exp(-0.05 * s_eff)) / 0.05
        fl = 0.0 if t <= HIT1 else math.exp(-0.06 * (t - HIT1)) * math.sin(0.5 * (t - HIT1))
        sprawl = 0.0 if t <= TG else min(1.0, (t - TG) / 3.0)
        launched = 0.0 if t <= HIT1 else min(1.0, (t - HIT1) / 3.0)
        crash = 0.0 if t <= HIT2 else min(1.0, (t - HIT2) / 2.0)
        row = np.zeros(16)
        row[0], row[1] = ry, rx
        row[2] = 3.0 * fl if t > HIT1 else 0.0
        row[8] = -20 * launched * (1 - crash) + 25 * fl * launched + 15 * crash                      # right arm swings back, then folds over
        row[9] = 8 + 62 * launched * (1 - 0.5 * crash) + 14 * fl + 12 * sprawl                       # arms fling out
        row[10] = -15 * launched * (1 - crash) - 22 * fl * launched + 10 * crash
        row[11] = -8 - 62 * launched * (1 - 0.5 * crash) - 14 * fl - 12 * sprawl
        row[12] = -18 * launched + 20 * fl * launched * (1 - crash) + 30 * crash                     # legs trail, then fold
        row[13] = 4 + 18 * launched + 8 * sprawl
        row[14] = 24 * launched - 20 * fl * launched * (1 - crash) + 20 * crash
        row[15] = -4 - 18 * launched - 8 * sprawl
        row[6] = 22 * launched - 16 * crash + 8 * fl                                                 # the head lolls
        ang[t] = row
    return pos, ang, v0, (p_g, TG)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the scene

def key_hero(hero: Character, ang: np.ndarray, xz: np.ndarray, air: np.ndarray):
    for f in range(N):
        t = int(TAU[f])
        a = ang[t]
        K(hero.anim, f, "linear", R=root_pose(float(xz[t, 0]), 3.0 + PR.lowest(a) + float(air[t]), float(xz[t, 1]), a[1], a[0], a[2]),
          T=P((a[3], a[4], a[5])), H=P((a[6], a[7], 0)), RA=P((a[8], 0, a[9]), PR.limb_pos(a, 0)), LA=P((a[10], 0, a[11]), PR.limb_pos(a, 1)),
          RL=P((a[12], 0, a[13]), PR.limb_pos(a, 2)), LL=P((a[14], 0, a[15]), PR.limb_pos(a, 3)))


def key_dummy(dummy: Character, pos: np.ndarray, ang: np.ndarray):
    for f in range(N):
        t = int(TAU[f])
        a = ang[t]
        h = max(float(pos[t, 1]), 3.0 + PR.lowest(a)) if t > HIT2 else float(pos[t, 1])
        K(dummy.anim, f, "linear", R=root_pose(float(pos[t, 0]), h, float(pos[t, 2]), a[1], a[0], a[2]), T=P((0, 0, 0)), H=P((a[6], 0, 0)),
          RA=P((a[8], 0, a[9])), LA=P((a[10], 0, a[11])), RL=P((a[12], 0, a[13])), LL=P((a[14], 0, a[15])))


def orbit_pos(tgt, yaw: float, el: float, dist: float):
    """Lens position ``dist`` studs from ``tgt``: yaw 0 = on the +z side, positive yaw swings it toward +x (in front of the hero), elevation in degrees."""
    y, e = math.radians(yaw), math.radians(el)
    return (tgt[0] + dist * math.sin(y) * math.cos(e), tgt[1] + dist * math.sin(e), tgt[2] + dist * math.cos(y) * math.cos(e))


def dress(cine: Cinematic):
    """The arena: a back wall with pillars and steps, far towers in the haze, broken blocks near the ring for scale (static boxes)."""
    stone, dark, warm = "#98a3b7", "#626e86", "#aab5c8"
    cine.prop((0, 3.0, -24), (70, 6.0, 2.4), stone)
    cine.prop((0, 6.5, -24), (70, 0.9, 3.0), dark)
    for x in (-27, -18, -9, 0, 9, 18, 27):
        cine.prop((x, 7.0, -21.5), (2.6, 14.0, 2.6), warm)
        cine.prop((x, 14.4, -21.5), (3.6, 0.9, 3.6), dark)
        cine.prop((x, 0.5, -21.5), (3.6, 1.0, 3.6), dark)
    for i in range(4):
        cine.prop((0, 0.35 + 0.7 * i, -17.0 + 1.1 * i), (16.0 - 2.0 * i, 0.7, 2.2), stone)
    for k, (x, h, c) in enumerate([(-46, 26, "#8e9cba"), (-34, 38, "#8392b2"), (-18, 22, "#93a1be"), (12, 30, "#8796b6"), (30, 42, "#7a89ab"), (48, 24, "#8e9cb9")]):
        cine.prop((x, h / 2, -70 - 6 * (k % 3)), (9 + (k % 3) * 3, h, 9), c)
    for x, z, s_, yaw in [(-12.0, -8.5, (2.2, 1.4, 1.8), 20), (-4.0, -11.0, (1.6, 2.6, 1.6), -12), (9.5, -9.0, (2.6, 1.0, 2.0), 35), (16.0, -6.0, (1.4, 1.8, 1.4), 8), (-17.0, -3.0, (1.8, 0.9, 1.5), -25)]:
        cine.prop((x, s_[1] / 2, z), s_, "#8995ab", yaw)


def screen_report(cine: Cinematic, hero: Character, dummy: Character):
    """Objective check of the shot sizes: how much of the frame height each body takes, and whether it stays in frame."""
    rows = []
    for f in range(0, N, 6):
        pos, tgt, fov, roll = cine.camera_state(f)
        fwd = np.array(tgt) - np.array(pos)
        fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, (0, 1, 0))
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        out = [f]
        for ch in (hero, dummy):
            c = np.array(ch.world_parts(f)["Torso"][1])
            pts = [c + np.array((0, 2.75, 0)), c + np.array((0, -2.75, 0)), c + np.array((1.6, 0, 0)), c + np.array((-1.6, 0, 0))]
            ys, xs = [], []
            for q in pts:
                d = q - np.array(pos)
                z = float(d @ fwd)
                if z <= 0.1:
                    ys.append(9.0); xs.append(9.0)
                    continue
                t = math.tan(math.radians(fov) / 2)
                ys.append(float(d @ up) / (z * t))
                xs.append(float(d @ right) / (z * t * 16 / 9))
            out += [round((max(ys) - min(ys)) / 2.0, 2), round(max(abs(min(xs)), abs(max(xs))), 2), round(max(abs(min(ys)), abs(max(ys))), 2)]
        rows.append(out)
    return rows


def build() -> Scene:
    ang, xz, air = hero_angles()
    hero = Character("hero", Animation("hero", fps=FPS, archetype="cinematic"), colors=HERO_COLORS)
    key_hero(hero, ang, xz, air)
    fist = np.array(hero.limb_tip("Right Arm", HIT1))                 # where the uppercut lands, film image 48
    hero_c_x48 = float(hero.world_parts(HIT1)["Torso"][1][0])
    heel = np.array(hero.limb_tip("Right Leg", film_of(HIT2)))        # where the axe kick lands
    pos, dang, v0, (p_g, TG) = dummy_motion(fist, heel, hero_c_x48)
    dummy = Character("dummy", Animation("dummy", fps=FPS, archetype="cinematic"), colors=DUMMY_COLORS)
    key_dummy(dummy, pos, dang)

    cine = Cinematic(N, fps=FPS)
    cine.look = "arena"
    cine.sky_color, cine.horizon_color, cine.floor_color = "#3d68b6", "#f5d2a8", "#a3a9b6"
    dress(cine)
    f1, f2, fg = film_of(HIT1), film_of(HIT2), film_of(TG)
    hero_c = lambda f: tuple(float(v) for v in hero.world_parts(int(f))["Torso"][1])
    dum_c = lambda f: tuple(float(v) for v in dummy.world_parts(int(f))["Torso"][1])
    mid = lambda a_, b_: tuple((u + v) / 2 for u, v in zip(a_, b_))

    # ---- camera: fixed shot sizes, each one computed from a distance (fov and distance give the frame height: 2 d tan(fov/2)), hard cuts at the impacts
    t0 = (-2.4, 3.0, -0.6)
    cine.shot(0, 26, dolly(orbit_pos(t0, -14, 3, 27), orbit_pos(t0, -9, 3, 23), t0, (-2.0, 3.0, -0.6), fov=30, easing="sine_inout"))               # establishing: both in frame, hero ~45 % high
    cine.shot(26, f1 - 8, tracking(hero_c, (6.0, 1.4, 14.5), look_dy=0.2, fov=(32, 30), offset_end=(4.6, 1.2, 12.5)))                              # the dash seen from the front quarter, he runs toward the lens' right
    tg1 = (3.9, 3.7, -1.0)
    cine.shot(f1 - 8, f1 + 4, dolly(orbit_pos(tg1, -10, 3, 21.0), orbit_pos(tg1, -5, 3, 17.5), tg1, (4.0, 3.9, -1.0), fov=(30, 26), easing="expo_out"))   # the hit, over the hero's shoulder, the whole hero in frame
    cine.shot(f1 + 4, f2 - 8, autoframe(lambda f: [hero_c(f), dum_c(f)], f1 + 4, f2 - 8, azimuth=-10, elevation=6.0, fov=34.0, fill=0.8, min_radius=3.0, follow=0.45, lift=0.6, pad=1.0))
    tg2 = (4.8, 9.0, -1.0)
    cine.shot(f2 - 8, f2 + 6, dolly(orbit_pos(tg2, 30, -5, 21.0), orbit_pos(tg2, 24, -4, 17.5), tg2, (4.8, 8.4, -1.0), fov=(32, 28), easing="expo_out"))  # the kick, from below, hero and dummy both in frame
    tg3 = (5.9, 2.4, -0.2)
    cine.shot(f2 + 6, fg + 8, dolly(orbit_pos(tg3, 30, 3, 21.0), orbit_pos(tg3, 38, 3, 16.0), (5.6, 5.5, -0.2), tg3, fov=(32, 30), roll=(0.0, -2.0), easing="expo_out"))   # down with the dummy, to the floor
    tg4 = (7.0, 2.0, -0.4)
    cine.shot(fg + 8, N + 1, dolly(orbit_pos(tg4, 34, 3, 16.0), orbit_pos((9.5, 2.6, -0.4), 14, 12, 27.0), tg4, (9.5, 2.6, -0.4), fov=(30, 36), roll=(-2.0, 0.0), easing="sine_inout"))  # the pull-back

    # ---- hit 1: the uppercut
    cine.punch_in(f1, 0.13, 9)
    cine.shake(f1, 9, 0.5)
    cine.screen_fx("white", f1, 2, alpha=0.85)
    cine.screen_fx("bw", f1 + 2, 3, seed=5, accent=True, focus=(0.55, 0.5), shards=16, bright=1.6)
    cine.ring(f1, 10, tuple(fist), 0.3, 3.4, 0.35, 0.05, "#ffffff", 0.95, 0.0, n=(0, 0, 1))
    cine.ring(f1, 8, (fist[0], 0.1, fist[2]), 0.6, 3.6, 0.3, 0.04, "#fff2d6", 0.8, 0.0)
    cine.burst(f1, 8, tuple(fist), 0.4, 3.0, "#ffd27a", "#ffffff")
    cine.emit(f1, f1 + 6, origin=(fist[0], 0.3, fist[2]), rate=0, burst=26, vel=(0.2, 0.5), dir=(0, 1, 0), spread=1.1, grav=0.02, life=(14, 26), size=(0.5, 0.15),
              color=("#d8cdb4", "#9a9078"), alpha=(0.7, 0.0), add=False, shape="smoke", seed=3, radius=0.7)
    sh = (hero_c(f1)[0] + 0.3, hero_c(f1)[1] + 0.5, hero_c(f1)[2])
    cine.slash(f1 - 5, 7, sh, (0, 0, 1), 3.0, -140, 20, 0.5, "#fff1c9", "#ffffff")                # the arc of the uppercut: low-back to high-front

    # ---- dash: dust, speed lines
    d0, d1 = film_of(30), film_of(44)
    cine.emit(d0, d1, attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=2.6, vel=(0.02, 0.12), dir=(-1, 0.3, 0), spread=0.7, life=(16, 32), size=(0.9, 2.6),
              color=("#c9b998", "#9d8d6c"), alpha=(0.45, 0.0), add=False, shape="smoke", seed=2, radius=0.4)
    cine.streaks(d0 + 2, d1 - d0, (-10.0, 2.6, HERO_Z + 0.4), (-5.0, 3.0, HERO_Z + 0.4), n=12, r0=0.4, r1=2.2, w=0.05, color="#ffffff", seed=4)

    # ---- the flight: a soft trail on the dummy
    cine.emit(f1 + 2, f2, attach={"char": 1, "part": "Torso", "off": [0, 0, 0]}, rate=1.6, vel=(0.01, 0.05), dir=(0, 1, 0), spread=0.9, life=(14, 24), size=(0.6, 0.15),
              color=("#fff3da", "#d6c39a"), alpha=(0.35, 0.0), add=True, shape="soft", seed=6, radius=0.5)

    # ---- hit 2: the axe kick
    cine.punch_in(f2, 0.16, 10)
    cine.shake(f2, 12, 0.8)
    cine.screen_fx("black", f2, 1)
    cine.screen_fx("bw", f2 + 1, 4, seed=9, accent=True, focus=(0.5, 0.45), shards=18, bright=1.8)
    cine.flash(f2 + 5, 3, "#ffffff", 0.5)
    hp = tuple(float(v) for v in heel)
    cine.ring(f2, 12, hp, 0.4, 4.2, 0.4, 0.05, "#ffe2b0", 0.95, 0.0, n=(0, 0, 1))
    cine.dome(f2, 9, hp, 0.4, 3.0, "#ffd9a0", 0.55, 0.0)
    cine.slash(f2 - 5, 7, (heel[0] - 0.6, heel[1] + 2.2, heel[2]), (0, 0, 1), 2.8, 150, 10, 0.55, "#ffb86b", "#ffffff")

    # ---- the ground: the slam
    gp = (float(p_g[0]), 0.05, float(p_g[2]))
    cine.shake(fg, 20, 1.3)
    cine.punch_in(fg, 0.2, 12)
    cine.flash(fg, 3, "#ffffff", 0.45)
    for k, (r1, col) in enumerate(((5.5, "#ffffff"), (8.0, "#ffe3b0"), (11.0, "#bcd0f0"))):
        cine.ring(fg + 2 * k, 16 + 3 * k, gp, 0.5, r1, 0.5 - 0.1 * k, 0.04, col, 0.9 - 0.15 * k, 0.0)
    cine.cracks(fg, 20, gp, 7.5, 13, "#2b2822", glow=None, width=0.07, seed=2, fade=(70, 40))
    cine.burst_debris(fg, gp, 38, 0.32, 0.55, (0.18, 0.5), ["#7d6f58", "#96876b", "#6a5e49"], seed=3, g=0.03)
    cine.emit(fg, fg + 14, origin=gp, rate=0, burst=44, vel=(0.26, 0.4), dir=(0, 1, 0), spread=1.6, grav=0.01, life=(22, 44), size=(1.0, 2.8), color=("#d9ccb0", "#a39878"),
              alpha=(0.42, 0.0), add=False, shape="smoke", seed=5, radius=1.4)

    # ---- the landing, the walk away
    l0 = film_of(88)
    cine.emit(l0, l0 + 8, attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=0, burst=24, vel=(0.2, 0.2), dir=(0, 1, 0), spread=1.4, life=(16, 30), size=(0.8, 2.0),
              color=("#c9b998", "#9d8d6c"), alpha=(0.4, 0.0), add=False, shape="smoke", seed=8, radius=0.8)
    cine.vignette.key(0, 0.18).key(f1, 0.18).key(f1 + 2, 0.4).key(f1 + 14, 0.18).key(N, 0.28)
    if os.environ.get("DR_POSELAB"):     # pose lab: only the hero, big, in profile, to judge his poses
        cine.shots = []
        cine.shot(0, N + 1, tracking(hero_c, (1.5, 1.2, 15.0), look_dy=0.2, fov=30))
    scene = Scene("Dragon montant", [hero, dummy], fps=FPS, cine=cine)
    scene.report = screen_report(cine, hero, dummy)
    return scene
