"""« Dragon Combo » - an ORIGINAL 8-second combat animation, 30 images per second (240 images).

Beat sheet (film images)
   0-29   standoff, breathing guard                 148 - 160 : the leap, a rocket boost up to the dummy
  30-45   dash (capture, retargeted to R6)           90: aerial right straight      95: aerial left hook      100: spinning kick
  50      jab (face)        57: left hook (head)    114: AXE KICK from the top (hit-stop 3)       122: the dummy hits the floor
  64      low kick (gut)    76: UPPERCUT (launch)    124-152: crouched landing, rise, turn        153-192: he walks toward the lens, 193-239: a glance back

Every contact is solved, not tuned by eye: the dummy (or the hero in the air) is placed so that the tip of the striking limb lands exactly on it (``solve``), with a hit-stop of
2-3 images at each hit (the pose is held, a small tremor rides on it).  The R6 rig has no waist, so the "chain" of a punch is made of timing: the body turns first, the arm follows,
the head counter-turns; limbs are stretched / shortened with the piston slide.
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

from . import dragon_rise as DR
from . import practice as PR

FPS = 30
N = 240
HERO_Z = DR.HERO_Z
NAMES20 = DR.NAMES20
LIB = DR.LIB

HERO_COLORS = DR.HERO_COLORS
DUMMY_COLORS = DR.DUMMY_COLORS


def pchip(xk, yk, xq):
    """Monotone cubic interpolation (no overshoot): flat between equal keys, smooth through the others."""
    xk, yk = np.asarray(xk, float), np.asarray(yk, float)
    o = np.argsort(xk)
    xk, yk = xk[o], yk[o]
    h, d = np.diff(xk), np.diff(yk) / np.diff(xk)
    n = len(xk)
    m = np.zeros(n)
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0], m[-1] = d[0], d[-1]
    xq = np.asarray(xq, float)
    idx = np.clip(np.searchsorted(xk, xq, side="right") - 1, 0, n - 2)
    t = (xq - xk[idx]) / h[idx]
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * yk[idx] + (t3 - 2 * t2 + t) * h[idx] * m[idx] + (-2 * t3 + 3 * t2) * yk[idx + 1] + (t3 - t2) * h[idx] * m[idx + 1]


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the hero: key poses on the film clock

NEUTRAL = dict(ry=-86, rx=-6, rz=0, T_rx=-4, T_ry=-8, T_rz=-3, H_rx=2, H_ry=10, RA_rx=-68, RA_rz=6, RA_slide=0.4, LA_rx=78, LA_rz=-10, LA_slide=0.9,
               RL_rx=-28, RL_rz=4, RL_slide=0.35, LL_rx=26, LL_rz=-4, LL_slide=0.45)


def H(**kw):
    d = dict(NEUTRAL)
    d.update(kw)
    return d


JAB = H(ry=-72, T_ry=26, H_ry=-20, rx=-4, T_rx=-5, T_rz=4, RA_rx=112, RA_rz=6, RA_slide=-0.7, LA_rx=64, LA_rz=-20, LA_slide=0.4, RL_rx=-22, RL_slide=0.0, LL_rx=30, LL_slide=0.15)
HOOK = H(ry=-116, T_ry=-38, H_ry=40, rx=-4, T_rx=-5, T_rz=3, RA_rx=22, RA_rz=22, RA_slide=0.3, LA_rx=112, LA_rz=-30, LA_slide=-0.7, RL_rx=-24, RL_slide=0.0, LL_rx=28, LL_slide=0.15)
KICK = H(ry=-74, T_ry=12, H_ry=-14, rx=16, T_rx=8, T_rz=-6, RA_rx=-78, RA_rz=26, RA_slide=0.3, LA_rx=64, LA_rz=-24, LA_slide=0.5, RL_rx=98, RL_rz=-4, RL_slide=-0.5, LL_rx=-4, LL_rz=-3, LL_slide=0.0)
UPPER = H(ry=-70, T_ry=22, H_ry=-22, rx=4, T_rx=8, T_rz=9, H_rx=-6, RA_rx=128, RA_rz=34, RA_slide=0.0, LA_rx=-46, LA_rz=-12, LA_slide=0.2, RL_rx=-32, RL_slide=0.3, LL_rx=54, LL_slide=0.8)
AJAB = H(ry=-72, T_ry=24, H_ry=-18, rx=0, T_rx=-6, T_rz=3, RA_rx=88, RA_rz=6, RA_slide=-0.6, LA_rx=58, LA_rz=-22, LA_slide=0.5, RL_rx=28, RL_rz=4, RL_slide=0.6, LL_rx=-20, LL_slide=0.4)
AHOOK = H(ry=-118, T_ry=-38, H_ry=40, rx=-2, T_rx=-8, T_rz=3, RA_rx=24, RA_rz=22, RA_slide=0.3, LA_rx=94, LA_rz=-36, LA_slide=-0.5, RL_rx=30, RL_slide=0.7, LL_rx=-18, LL_slide=0.3)
SPIN = dict(T_ry=0, H_ry=-10, rx=8, T_rx=0, T_rz=0, RA_rx=-20, RA_rz=62, RA_slide=0.0, LA_rx=20, LA_rz=-62, LA_slide=0.0, RL_rx=92, RL_rz=0, RL_slide=0.0, LL_rx=-14, LL_rz=-5, LL_slide=0.0)
AXE = H(ry=-450, rx=-6, T_ry=0, H_ry=0, T_rx=-6, T_rz=0, H_rx=-6, RA_rx=70, RA_rz=14, RA_slide=0.0, LA_rx=-30, LA_rz=-14, LA_slide=0.0, RL_rx=44, RL_rz=3, RL_slide=0.0, LL_rx=-16, LL_rz=-6, LL_slide=0.0)
STAND = H(ry=-90, rx=0, T_rx=0, T_ry=0, T_rz=0, H_rx=0, H_ry=0, RA_rx=-6, RA_rz=8, RA_slide=0.0, LA_rx=6, LA_rz=-8, LA_slide=0.0, RL_rx=0, RL_rz=4, RL_slide=0.0, LL_rx=0, LL_rz=-4, LL_slide=0.0)

HERO_KEYS = {
    46: H(ry=-102, T_ry=-22, H_ry=24, rx=-8, T_rx=-6, RA_rx=-36, RA_rz=14, RA_slide=0.0, LA_rx=104, LA_rz=-12, LA_slide=0.3, RL_rx=-26, RL_slide=0.1, LL_rx=30, LL_slide=0.2),     # jab: chamber
    48: H(ry=-84, T_ry=8, H_ry=-4, rx=-6, T_rx=-6, T_rz=2, RA_rx=70, RA_rz=8, RA_slide=-0.3, LA_rx=70, LA_rz=-16, LA_slide=0.5, RL_rx=-24, RL_slide=0.05, LL_rx=30, LL_slide=0.15),
    50: JAB, 52: JAB,                                                                                                                                                              # contact + hit-stop
    55: H(ry=-64, T_ry=30, H_ry=-22, rx=-6, T_rx=-5, T_rz=-3, RA_rx=34, RA_rz=18, RA_slide=0.2, LA_rx=84, LA_rz=-80, LA_slide=0.0, RL_rx=-26, RL_slide=0.1, LL_rx=30, LL_slide=0.2),  # hook: the left arm cocked wide
    57: HOOK, 59: HOOK,
    62: H(ry=-96, T_ry=-6, H_ry=8, rx=6, T_rx=0, T_rz=-4, RA_rx=-48, RA_rz=22, RA_slide=0.2, LA_rx=44, LA_rz=-30, LA_slide=0.4, RL_rx=76, RL_rz=2, RL_slide=0.0, LL_rx=-6, LL_rz=-3, LL_slide=0.0),  # kick: the knee up
    64: KICK, 66: KICK,
    69: H(ry=-110, T_ry=-32, H_ry=34, rx=-16, T_rx=-8, T_rz=-8, H_rx=6, RA_rx=-96, RA_rz=14, RA_slide=0.0, LA_rx=58, LA_rz=-12, LA_slide=0.9, RL_rx=-42, RL_slide=0.7, LL_rx=44, LL_slide=0.8),     # uppercut: the long wind-up
    72: H(ry=-98, T_ry=-34, H_ry=26, rx=-20, T_rx=-10, T_rz=-6, H_rx=4, RA_rx=-18, RA_rz=26, RA_slide=0.1, LA_rx=40, LA_rz=-12, LA_slide=0.9, RL_rx=-46, RL_slide=1.2, LL_rx=48, LL_slide=1.2),
    74: H(ry=-80, T_ry=-10, H_ry=6, rx=-6, T_rx=0, T_rz=2, H_rx=0, RA_rx=84, RA_rz=40, RA_slide=0.2, LA_rx=-10, LA_rz=-12, LA_slide=0.5, RL_rx=-38, RL_slide=0.7, LL_rx=52, LL_slide=1.0),
    76: UPPER, 78: UPPER,
    79: H(ry=-76, T_ry=10, H_ry=-8, rx=-8, T_rx=6, T_rz=6, H_rx=-6, RA_rx=150, RA_rz=22, RA_slide=0.0, LA_rx=-40, LA_rz=-14, LA_slide=0.0, RL_rx=-30, RL_slide=0.4, LL_rx=44, LL_slide=0.8),  # the arm carries on
    81: H(ry=-88, T_ry=0, H_ry=4, rx=-30, T_rx=-16, T_rz=0, RA_rx=22, RA_rz=12, RA_slide=0.0, LA_rx=14, LA_rz=-12, LA_slide=0.0, RL_rx=45, RL_rz=8, RL_slide=1.4, LL_rx=45, LL_rz=-8, LL_slide=1.4),   # the deep squat
    83: H(ry=-88, T_ry=0, H_ry=0, rx=-4, T_rx=0, T_rz=0, RA_rx=165, RA_rz=14, RA_slide=0.0, LA_rx=160, LA_rz=-14, LA_slide=0.0, RL_rx=-6, RL_rz=5, RL_slide=0.0, LL_rx=-8, LL_rz=-5, LL_slide=0.0),   # take-off
    85: H(ry=-80, T_ry=8, H_ry=0, rx=8, T_rx=2, T_rz=0, RA_rx=120, RA_rz=22, RA_slide=0.0, LA_rx=100, LA_rz=-22, LA_slide=0.0, RL_rx=68, RL_rz=6, RL_slide=0.8, LL_rx=-26, LL_rz=-8, LL_slide=0.4),
    88: H(ry=-104, T_ry=-24, H_ry=26, rx=6, T_rx=-4, T_rz=0, RA_rx=-40, RA_rz=14, RA_slide=0.0, LA_rx=96, LA_rz=-14, LA_slide=0.3, RL_rx=40, RL_rz=6, RL_slide=0.8, LL_rx=-18, LL_slide=0.3),       # aerial straight: chamber
    90: AJAB, 91: AJAB,
    93: H(ry=-66, T_ry=30, H_ry=-22, rx=2, T_rx=-4, T_rz=-3, RA_rx=30, RA_rz=18, RA_slide=0.2, LA_rx=60, LA_rz=-84, LA_slide=0.0, RL_rx=36, RL_rz=4, RL_slide=0.7, LL_rx=-16, LL_slide=0.3),   # aerial hook: chamber
    95: AHOOK, 96: AHOOK,
    97: H(ry=-150, **SPIN), 98: H(ry=-250, **SPIN), 99: H(ry=-345, **SPIN),                                                                                                       # the spin: 360 degrees in 3 images
    100: H(ry=-430, **{**SPIN, "RL_rx": 96, "RL_slide": -0.4}), 101: H(ry=-430, **{**SPIN, "RL_rx": 96, "RL_slide": -0.4}),
    104: H(ry=-450, rx=10, T_rx=2, T_ry=0, H_ry=0, T_rz=0, RA_rx=140, RA_rz=18, RA_slide=0.0, LA_rx=130, LA_rz=-18, LA_slide=0.0, RL_rx=60, RL_rz=6, RL_slide=0.6, LL_rx=-20, LL_rz=-6, LL_slide=0.3),
    106: H(ry=-450, rx=18, T_rx=6, T_ry=0, H_ry=0, T_rz=0, RA_rx=-55, RA_rz=14, RA_slide=0.0, LA_rx=140, LA_rz=-14, LA_slide=0.0, RL_rx=118, RL_rz=6, RL_slide=0.4, LL_rx=-26, LL_rz=-6, LL_slide=0.2),
    109: H(ry=-450, rx=32, T_rx=10, T_ry=0, H_ry=0, T_rz=0, H_rx=10, RA_rx=-62, RA_rz=14, RA_slide=0.0, LA_rx=146, LA_rz=-14, LA_slide=0.0, RL_rx=172, RL_rz=4, RL_slide=0.0, LL_rx=-20, LL_rz=-5, LL_slide=0.0),  # the apex: the leg straight up
    111: H(ry=-450, rx=34, T_rx=10, T_ry=0, H_ry=0, T_rz=0, H_rx=12, RA_rx=-66, RA_rz=14, RA_slide=0.0, LA_rx=150, LA_rz=-14, LA_slide=0.0, RL_rx=176, RL_rz=4, RL_slide=0.0, LL_rx=-22, LL_rz=-5, LL_slide=0.0),
    113: H(ry=-450, rx=6, T_rx=-6, T_ry=0, H_ry=0, T_rz=0, H_rx=-6, RA_rx=-20, RA_rz=14, RA_slide=0.0, LA_rx=60, LA_rz=-14, LA_slide=0.0, RL_rx=100, RL_rz=4, RL_slide=0.0, LL_rx=-12, LL_rz=-6, LL_slide=0.0),
    114: AXE, 116: AXE,
    118: H(ry=-450, rx=-14, T_rx=-10, T_ry=0, H_ry=0, T_rz=0, H_rx=-6, RA_rx=84, RA_rz=18, RA_slide=0.0, LA_rx=-40, LA_rz=-18, LA_slide=0.0, RL_rx=20, RL_rz=3, RL_slide=0.0, LL_rx=-10, LL_rz=-6, LL_slide=0.0),
    121: H(ry=-450, rx=-20, T_rx=-10, T_ry=0, H_ry=0, T_rz=0, H_rx=0, RA_rx=30, RA_rz=44, RA_slide=0.0, LA_rx=40, LA_rz=-44, LA_slide=0.0, RL_rx=14, RL_rz=6, RL_slide=0.0, LL_rx=22, LL_rz=-6, LL_slide=0.0),
    124: H(ry=-452, rx=-30, T_rx=-20, T_ry=-14, T_rz=-4, H_ry=10, RA_rx=70, RA_rz=18, RA_slide=0.0, LA_rx=60, LA_rz=-18, LA_slide=0.0, RL_rx=30, RL_rz=8, RL_slide=1.5, LL_rx=26, LL_rz=-8, LL_slide=1.4),   # touchdown
    128: H(ry=-454, rx=-38, T_rx=-24, T_ry=-16, T_rz=-5, H_ry=12, RA_rx=42, RA_rz=22, RA_slide=0.0, LA_rx=30, LA_rz=-22, LA_slide=0.0, RL_rx=34, RL_rz=8, RL_slide=1.65, LL_rx=30, LL_rz=-8, LL_slide=1.55),
    134: H(ry=-448, rx=-16, T_rx=-8, T_ry=-6, T_rz=-2, H_ry=4, RA_rx=14, RA_rz=14, RA_slide=0.0, LA_rx=6, LA_rz=-14, LA_slide=0.0, RL_rx=12, RL_rz=6, RL_slide=0.8, LL_rx=10, LL_rz=-6, LL_slide=0.8),
    142: {**STAND, "ry": -450},
}
HERO_EASE = {46: "in", 48: "in", 50: "hold", 52: "out", 55: "in", 57: "hold", 59: "out", 62: "in", 64: "hold", 66: "out", 69: "io", 72: "in", 74: "in", 76: "hold", 78: "out", 79: "in", 81: "in", 83: "out",
             85: "io", 88: "in", 90: "hold", 91: "out", 93: "in", 95: "hold", 96: "out", 97: "lin", 98: "lin", 99: "lin", 100: "hold", 101: "out", 104: "io", 106: "io", 109: "hold", 111: "in",
             113: "in", 114: "hold", 116: "out", 118: "in", 121: "in", 124: "out", 128: "io", 134: "io"}

# the turn (the head first, then the body), keyed on the film clock: -450 degrees of yaw is facing +x, -270 is facing -x
TURN_KEYS = {k + 37: dict(v, ry=v["ry"] - 360) for k, v in DR.TURN_KEYS.items()}
for _k, _v in TURN_KEYS.items():
    for _n in NAMES20:
        _v.setdefault(_n, STAND.get(_n, 0))
HERO_KEYS.update({k: v for k, v in TURN_KEYS.items() if k > 142})
HERO_EASE.update({k: e for k, e in {143: "io", 145: "io", 148: "io", 150: "out", 152: "hold"}.items()})

FINALE_KEYS = {
    193: {**STAND, "ry": 90},
    200: {**STAND, "ry": 90, "rx": -2, "T_rx": -3, "H_ry": 0, "RA_rz": 10, "LA_rz": -10},
    206: {**STAND, "ry": 62, "rx": -2, "T_rx": -3, "T_ry": 10, "H_ry": -56, "H_rx": 2, "RA_rz": 10, "LA_rz": -10, "RA_rx": 8, "LA_rx": -6},
    216: {**STAND, "ry": 58, "rx": -2, "T_rx": -3, "T_ry": 12, "H_ry": -60, "H_rx": 4, "RA_rz": 12, "LA_rz": -12, "RA_rx": 10, "LA_rx": -8},
    232: {**STAND, "ry": 66, "rx": -4, "T_rx": -6, "T_ry": 6, "H_ry": -50, "H_rx": 6, "RA_rz": 9, "LA_rz": -9},
    239: {**STAND, "ry": 66, "rx": -4, "T_rx": -6, "T_ry": 6, "H_ry": -50, "H_rx": 6, "RA_rz": 9, "LA_rz": -9},
}
FINALE_EASE = {193: "io", 200: "io", 206: "io", 216: "io", 232: "io"}


def keyed(keys, ease, t0, t1):
    return DR.authored_from(keys, ease, t0, t1)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the contacts

# frame, striking limb, hold (images), dummy offset from the limb tip (x, y, z), knock (the dummy is pushed this much), mode
#   "g" ground hit: the hero stays on the floor, the dummy goes where the tip is (x set by ``hero_x``); "a" aerial hit: the dummy is where we want it, the hero is solved (x, z, height)
CONTACTS = [
    dict(f=50, part="Right Arm", hold=3, off=(0.62, 0.0, 0.0), knock=(0.7, 0.1, 0.0), mode="g", hero_x=3.95),     # jab: the fist on the face
    dict(f=57, part="Left Arm", hold=3, off=(0.55, 0.0, 0.0), knock=(0.4, 0.0, 0.25), mode="g", hero_x=4.35),    # hook: the head
    dict(f=64, part="Right Leg", hold=3, off=(0.72, 0.12, 0.0), knock=(0.8, 0.5, 0.0), mode="g", hero_x=4.55),      # kick: the ribs
    dict(f=76, part="Right Arm", hold=3, off=(0.6, 0.25, 0.0), knock=(0.5, 2.0, 0.0), mode="g", hero_x=5.35),     # uppercut: under the chin
    dict(f=90, part="Right Arm", hold=2, off=(0.62, -1.3, 0.0), knock=(0.35, 0.5, 0.0), mode="a", dummy=(9.7, 10.4, HERO_Z + 0.2)),
    dict(f=95, part="Left Arm", hold=2, off=(0.55, -0.2, 0.0), knock=(0.4, 0.4, 0.0), mode="a", dummy=(10.2, 10.9, HERO_Z + 0.2)),
    dict(f=100, part="Right Leg", hold=2, off=(0.6, 0.45, 0.0), knock=(0.4, 0.9, 0.0), mode="a", dummy=(10.7, 11.4, HERO_Z + 0.2)),
    dict(f=114, part="Right Leg", hold=3, off=(0.15, -1.75, 0.0), knock=(0.0, 0.0, 0.0), mode="a", dummy=(11.2, 11.9, HERO_Z + 0.15)),
]
GROUND_HIT = 122                       # the dummy reaches the floor
GROUND_POS = (12.0, 0.62, HERO_Z - 0.35)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the time warp (v2): the combo was authored at fighting-game speed (a hit every ~0.25 s) which nobody can read; the middle of the film is slowed down
# (wind-ups longer, a real hit-stop, the spin readable), the dash a little, the opening and the walk stay at the authored speed.  Everything is authored on the
# old clock (frames 0..239) and resampled at the end, so contacts keep landing together.
N_OLD = N
_HOLDS = set()
for _c in CONTACTS:
    _HOLDS.update(range(_c["f"], _c["f"] + _c["hold"]))


def _warp():
    t = [0.0]
    for f in range(1, N_OLD):
        if f < 31:
            s = 1.0
        elif f <= 46:
            s = 1.3
        elif f <= 152:
            if f in _HOLDS and f - 1 in _HOLDS:
                s = 2.6                          # hit-stop: the pose is held (with its tremor)
            elif 97 <= f <= 101:
                s = 2.3                          # the spin must be readable
            elif 46 < f <= 50 or 68 < f <= 76:
                s = 2.1                          # wind-ups (the jab, the long uppercut)
            else:
                s = 1.8
        else:
            s = 1.0
        t.append(t[-1] + s)
    return np.array(t)


TW = _warp()
NN = int(round(TW[-1])) + 1                      # length of the film after the warp


def T(f: int) -> int:
    """Old frame -> frame on the film clock."""
    return int(round(float(TW[f])))


def retime(a: np.ndarray) -> np.ndarray:
    """Resample per-frame data (old clock) on the film clock with a monotone cubic."""
    old = np.interp(np.arange(NN), TW, np.arange(N_OLD))
    a = np.asarray(a, float)
    flat = a.reshape(N_OLD, -1)
    out = np.stack([pchip(np.arange(N_OLD), flat[:, i], old) for i in range(flat.shape[1])], 1)
    return out.reshape((NN,) + a.shape[1:])

DUMMY_NEUTRAL = dict(ry=90, rx=0, rz=0, T_rx=0, T_ry=0, T_rz=0, H_rx=0, H_ry=0, RA_rx=0, RA_rz=8, RA_slide=0.0, LA_rx=0, LA_rz=-8, LA_slide=0.0, RL_rx=0, RL_rz=4, RL_slide=0.0, LL_rx=0, LL_rz=-4, LL_slide=0.0)


def Dm(**kw):
    d = dict(DUMMY_NEUTRAL)
    d.update(kw)
    return d


D_FACE = Dm(rx=14, H_rx=40, H_ry=14, RA_rx=-30, RA_rz=28, LA_rx=-30, LA_rz=-28, RL_rx=-8, LL_rx=10)
D_HOOK = Dm(ry=150, rx=6, rz=-12, H_rx=8, H_ry=52, RA_rx=40, RA_rz=52, LA_rx=-40, LA_rz=-52, RL_rx=8, LL_rx=-8)
D_GUT = Dm(ry=104, rx=-52, H_rx=-30, RA_rx=46, RA_rz=14, LA_rx=46, LA_rz=-14, RL_rx=34, LL_rx=-8)
D_CHIN = Dm(rx=32, H_rx=58, RA_rx=-70, RA_rz=40, LA_rx=-70, LA_rz=-40, RL_rx=-30, LL_rx=20)
D_AFACE = Dm(ry=124, rx=26, H_rx=52, H_ry=-14, RA_rx=-56, RA_rz=40, LA_rx=-20, LA_rz=-30, RL_rx=-14, LL_rx=16)
D_AGUT = Dm(ry=132, rx=-48, H_rx=-34, RA_rx=50, RA_rz=18, LA_rx=50, LA_rz=-18, RL_rx=30, LL_rx=-8)
D_ASIDE = Dm(ry=200, rx=4, rz=48, H_rx=10, H_ry=24, RA_rx=-20, RA_rz=76, LA_rx=-30, LA_rz=-70, RL_rx=20, LL_rx=-20)
D_AXE = Dm(ry=470, rx=-30, H_rx=-34, RA_rx=-150, RA_rz=30, LA_rx=-150, LA_rz=-30, RL_rx=20, LL_rx=-10)
D_FLOOR = Dm(ry=810, rx=90, H_rx=16, RA_rx=0, RA_rz=76, LA_rz=-76, RL_rx=-4, RL_rz=18, LL_rx=-4, LL_rz=-18)

DUMMY_KEYS = {
    0: Dm(), 49: Dm(),
    50: D_FACE, 52: D_FACE,
    56: Dm(ry=100, rx=6, H_rx=16, H_ry=8, RA_rz=18, LA_rz=-18, RL_rx=-3, LL_rx=4),
    57: D_HOOK, 59: D_HOOK,
    62: Dm(ry=118, rx=-8, rz=-4, H_rx=-12, H_ry=-14, RA_rx=10, RA_rz=30, LA_rx=10, LA_rz=-30),
    64: D_GUT, 66: D_GUT,
    70: Dm(ry=96, rx=-34, H_rx=-26, RA_rx=30, RA_rz=16, LA_rx=30, LA_rz=-16, RL_rx=14),
    74: Dm(ry=92, rx=-18, H_rx=-12, RA_rx=18, RA_rz=18, LA_rx=18, LA_rz=-18),
    76: D_CHIN, 78: D_CHIN,
    82: Dm(ry=96, rx=24, rz=4, H_rx=40, RA_rx=-50, RA_rz=66, LA_rx=-50, LA_rz=-66, RL_rx=10, RL_rz=16, LL_rx=-6, LL_rz=-16),
    87: Dm(ry=112, rx=12, H_rx=14, RA_rx=-30, RA_rz=44, LA_rx=-30, LA_rz=-44, RL_rx=8, RL_rz=10, LL_rx=-4, LL_rz=-10),
    90: D_AFACE, 91: D_AFACE,
    94: Dm(ry=126, rx=6, H_rx=10, RA_rx=-20, RA_rz=36, LA_rx=-20, LA_rz=-36),
    95: D_AGUT, 96: D_AGUT,
    99: Dm(ry=160, rx=-10, H_rx=-6, RA_rx=10, RA_rz=40, LA_rx=10, LA_rz=-40),
    100: D_ASIDE, 101: D_ASIDE,
    108: Dm(ry=380, rx=2, rz=44, H_rx=10, H_ry=20, RA_rx=-24, RA_rz=76, LA_rx=-30, LA_rz=-70, RL_rx=18, LL_rx=-18),
    113: Dm(ry=450, rx=-24, rz=10, H_rx=-26, RA_rx=-120, RA_rz=30, LA_rx=-120, LA_rz=-30, RL_rx=16, LL_rx=-8),
    114: D_AXE, 116: D_AXE,
    119: Dm(ry=640, rx=60, H_rx=20, RA_rx=-20, RA_rz=60, LA_rx=-20, LA_rz=-60, RL_rx=8, RL_rz=12, LL_rx=-6, LL_rz=-12),
    122: D_FLOOR,
    126: {**D_FLOOR, "rx": 98, "H_rx": 22, "RA_rz": 70, "LA_rz": -70},
    133: D_FLOOR,
    239: D_FLOOR,
}
DUMMY_EASE = {0: "io", 50: "hold", 52: "out", 56: "io", 57: "hold", 59: "out", 62: "io", 64: "hold", 66: "out", 70: "io", 74: "in", 76: "hold", 78: "out", 82: "io", 87: "in", 90: "hold", 91: "out",
              94: "in", 95: "hold", 96: "out", 99: "in", 100: "hold", 101: "out", 108: "io", 113: "in", 114: "hold", 116: "in", 119: "in", 122: "out", 126: "io", 133: "hold"}


def tremor(ang: np.ndarray, f0: int, f1: int, amp: float, cols=(2, 5)):
    """A small tremor on a held pose (the hit-stop is not a dead freeze): alternating roll on ``cols`` for images f0..f1."""
    for i, f in enumerate(range(f0, f1 + 1)):
        for c in cols:
            ang[f, c] += amp * (-1) ** i * (1.0 - 0.25 * i)


def hero_angles(lib):
    dash, dxz, dair = mocap.assemble([dict(clip="49_04", t0=0.3, t1=1.0, n=16, yaw=-90)], lib, follow=np.array([[-8.1 + 11.7 * (t / 15) ** 1.2, HERO_Z] for t in range(16)]), start_xz=(-8.1, HERO_Z))
    walk, wxz, wair = mocap.assemble([dict(clip="07_01", t0=0.3, t1=1.9, n=40, yaw=90)], lib, follow=np.array([[10.0 - 5.4 * (t / 39) for t in range(40)], [HERO_Z] * 40]).T, start_xz=(10.0, HERO_Z))
    g = keyed(DR.GROUND_KEYS, DR.GROUND_EASE, 0, 29)
    for i in range(len(g)):
        g[i, 1] += 1.2 * math.sin(i * 0.5)                                   # breathing
    mid = keyed(HERO_KEYS, HERO_EASE, 46, 152)
    fin = keyed(FINALE_KEYS, FINALE_EASE, 193, 239)
    parts = [g, dash, mid, walk, fin]
    for k in range(1, len(parts)):                                           # unwrap the yaw/pitch columns across the joins
        for c in range(0, 16):
            parts[k][:, c] += 360.0 * np.round((parts[k - 1][-1, c] - parts[k][0, c]) / 360.0)
    ang = np.vstack(parts)
    assert len(ang) == N, len(ang)
    for j in (30, 46, 153, 193):                                             # three-image cross-fades over the joins
        prev = ang[j - 1].copy()
        for i in range(3):
            w = (i + 1) / 4.0
            ang[j + i] = prev * (1 - w) + ang[j + i] * w
    for c in CONTACTS:
        tremor(ang, c["f"], c["f"] + c["hold"] - 1, 1.6)
    return ang, dxz, dair, wxz, wair


def key_hero(hero: Character, ang, xz, air):
    for f in range(len(ang)):
        a = ang[f]
        K(hero.anim, f, "linear", R=root_pose(float(xz[f, 0]), 3.0 + PR.lowest(a) + float(air[f]), float(xz[f, 1]), a[1], a[0], a[2]),
          T=P((a[3], a[4], a[5])), H=P((a[6], a[7], 0)), RA=P((a[8], 0, a[9]), PR.limb_pos(a, 0)), LA=P((a[10], 0, a[11]), PR.limb_pos(a, 1)),
          RL=P((a[12], 0, a[13]), PR.limb_pos(a, 2)), LL=P((a[14], 0, a[15]), PR.limb_pos(a, 3)))


def key_dummy(dummy: Character, pos, ang):
    for f in range(len(ang)):
        a = ang[f]
        h = max(float(pos[f, 1]), 3.0 + PR.lowest(a)) if f >= T(GROUND_HIT) else float(pos[f, 1])
        K(dummy.anim, f, "linear", R=root_pose(float(pos[f, 0]), h, float(pos[f, 2]), a[1], a[0], a[2]), T=P((0, 0, 0)), H=P((a[6], a[7], 0)),
          RA=P((a[8], 0, a[9]), PR.limb_pos(a, 0)), LA=P((a[10], 0, a[11]), PR.limb_pos(a, 1)), RL=P((a[12], 0, a[13]), PR.limb_pos(a, 2)), LL=P((a[14], 0, a[15]), PR.limb_pos(a, 3)))


def solve(ang, dxz, dair, wxz, wair):
    """Root path + height of the hero and path of the dummy so that every contact lands.  Returns (hero xz, hero air, dummy pos, contact tips)."""
    zero = np.zeros((N, 2))
    zero[:, 1] = HERO_Z
    h0 = Character("h0", Animation("h0", fps=FPS, archetype="cinematic"), colors=HERO_COLORS)
    key_hero(h0, ang, zero, np.zeros(N))
    tip0 = {c["f"]: np.array(h0.limb_tip(c["part"], c["f"])) for c in CONTACTS}           # the tip with the root at x = 0, on the floor
    kx, kz, ka = [(0, -8.0), (29, -8.1)], [(0, HERO_Z)], [(0, 0.0)]
    dpts = []                                                                              # dummy control points (frame, x, y, z)
    tips = {}
    for c in CONTACTS:
        f, t0 = c["f"], tip0[c["f"]]
        if c["mode"] == "g":
            hx = c["hero_x"]
            tip = t0 + np.array([hx, 0.0, 0.0])
            d = np.array([tip[0] + c["off"][0], 3.0 + c["off"][1], 0.5 * (tip[2] + HERO_Z)])
            hz, air = HERO_Z, 0.0
        else:
            d = np.array(c["dummy"], float)
            tip = d - np.array(c["off"])
            hx, hz, air = tip[0] - t0[0], HERO_Z + (tip[2] - t0[2]), tip[1] - t0[1]
        tips[f] = tip
        for ff in (f, f + c["hold"] - 1):
            kx.append((ff, hx)), kz.append((ff, hz)), ka.append((ff, air))
        c["_dummy"] = d
        dpts.append((f, d))
        dpts.append((f + c["hold"] - 1, d))
        c["_air"], c["_hx"] = air, hx
    # the hero between contacts: the dash arrives, the leap, the landing
    kx += [(45, c0 := CONTACTS[0]["_hx"] - 0.5), (66, CONTACTS[2]["_hx"]), (82, CONTACTS[3]["_hx"] + 0.5), (86, CONTACTS[4]["_hx"] - 0.9), (104, CONTACTS[6]["_hx"] + 0.4), (118, CONTACTS[7]["_hx"] + 0.3),
           (124, CONTACTS[7]["_hx"] + 0.3), (152, CONTACTS[7]["_hx"] + 0.3)]
    a8 = CONTACTS[7]["_air"]
    ka += [(79, 0.0), (82, 0.2), (84, 3.0), (86, 6.4), (105, max(CONTACTS[6]["_air"], CONTACTS[7]["_air"]) + 0.8), (109, a8 + 1.5), (112, a8 + 0.6), (118, a8 - 2.8), (121, 2.6), (124, 0.0), (152, 0.0)]
    kz += [(152, HERO_Z)]
    fr = np.arange(N)
    hx = pchip(*zip(*sorted({k: v for k, v in kx}.items())), fr)
    hz = pchip(*zip(*sorted({k: v for k, v in kz}.items())), fr)
    ha = np.clip(pchip(*zip(*sorted({k: v for k, v in ka}.items())), fr), 0.0, None)
    xz = np.stack([hx, hz], 1)
    air = ha
    # frames outside the authored middle: the capture's own path (dash, walk) and the finale
    x45 = float(hx[45])
    dash_x = -8.1 + (x45 + 8.1) * ((np.arange(16) / 15.0) ** 1.2)
    xz[30:46, 0] = dash_x
    xz[30:46, 1] = HERO_Z
    air[30:46] = dair
    xl = float(hx[152])
    wx = xl - 5.4 * (np.arange(40) / 39.0)
    xz[153:193, 0] = wx
    xz[153:193, 1] = HERO_Z
    air[153:193] = wair
    xz[193:, 0] = wx[-1]
    xz[193:, 1] = HERO_Z
    air[193:] = 0.0
    xz[:30, 0] = -8.0
    # the dummy
    gx, gy, gz = GROUND_POS
    last = dpts[-1][1]
    c_ = CONTACTS
    knots = [(0, dpts[0][1])] + dpts
    for i, c in enumerate(c_[:-1]):
        k = np.array(c["knock"])
        knots.append((c["f"] + c["hold"] + 2, c["_dummy"] + k))
    kx_, ky_, kz_ = [], [], []
    p8 = c_[7]["_dummy"]
    tail = [(118, p8 + np.array([0.3, -1.6, -0.1])), (GROUND_HIT, np.array([gx, gy, gz])), (126, np.array([gx + 0.15, gy + 1.5, gz])), (129, np.array([gx + 0.2, gy, gz])), (140, np.array([gx + 0.22, gy, gz])),
            (239, np.array([gx + 0.22, gy, gz]))]
    knots += tail
    knots.sort(key=lambda t: t[0])
    seen, uniq = set(), []
    for f, p in knots:
        if f not in seen:
            seen.add(f)
            uniq.append((f, p))
    fs = [f for f, _ in uniq]
    pos = np.stack([pchip(fs, [p[i] for _, p in uniq], fr) for i in range(3)], 1)
    pos[:50] = dpts[0][1]
    return xz, air, pos, tips


def dummy_angles():
    ang = keyed(DUMMY_KEYS, DUMMY_EASE, 0, N - 1)
    for f in range(0, 49):                                                    # idle sway
        ang[f, 3] += 1.4 * math.sin(f * 0.21)
        ang[f, 6] += 1.0 * math.sin(f * 0.17 + 1.0)
    for c in CONTACTS:
        tremor(ang, c["f"], c["f"] + c["hold"] - 1, 1.4)
    return ang


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

def build_motion():
    lib = mocap.load_library(LIB)
    ang, dxz, dair, wxz, wair = hero_angles(lib)
    xz, air, pos, tips = solve(ang, dxz, dair, wxz, wair)
    dang = dummy_angles()
    return retime(ang), retime(xz), retime(air), retime(pos), retime(dang), tips


def build() -> Scene:
    from . import dragon_combo_stage as ST
    return ST.build_scene()
