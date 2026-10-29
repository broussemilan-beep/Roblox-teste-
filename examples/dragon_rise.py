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

HERO_COLORS = {"Torso": "#d9552b", "Head": "#f1c27d", "Right Arm": "#f1c27d", "Left Arm": "#f1c27d", "Right Leg": "#22252c", "Left Leg": "#22252c"}
DUMMY_COLORS = {p: "#9aa4b5" for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}
DUMMY_COLORS["Torso"] = "#b9c2d3"

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


def hero_track():
    lib = mocap.load_library(LIB)
    follow = np.array([[plan_x(t), -0.9] for t in range(M)])
    A = [
        dict(clip="144_20", t0=3.0, t1=3.8, n=24, yaw=-90),          # 0-24   guard, a little breathing
        dict(clip="144_20", t0=8.7, t1=9.1, n=6),                    # 24-30  the load: sink
        dict(clip="49_04", t0=0.3, t1=1.0, n=14),                    # 30-44  the dash
        dict(clip="144_20", t0=2.0, t1=2.5, n=8),                    # 44-52  punch base (the arm is replaced below)
    ]
    aa, axz, aair = mocap.assemble(A, lib, follow=follow[:52], start_xz=(-8.0, -0.9))
    Bsp = [
        dict(clip="144_20", t0=8.8, t1=9.3, n=6, yaw=-90),           # 88-94  landing crouch
        dict(clip="144_20", t0=3.0, t1=4.2, n=22),                   # 94-116 rise to the guard
        dict(clip="07_01", t0=0.3, t1=2.3, n=28),                    # 116-144 walk away
    ]
    ba, bxz, bair = mocap.assemble(Bsp, lib, follow=follow[88:], start_xz=(float(follow[88][0]), -0.9))
    return aa, axz, aair, ba, bxz, bair


def author_keys():
    """The aerial fight, pose by pose (animation clock 52..87).  Angles in degrees, slides = piston push-back in studs."""
    base = dict(ry=-90, rx=0, rz=0, T_rx=0, T_ry=0, T_rz=0, H_rx=0, H_ry=0, RA_rx=0, RA_rz=8, LA_rx=0, LA_rz=-8, RL_rx=0, RL_rz=4, LL_rx=0, LL_rz=-4, RA_slide=0, LA_slide=0, RL_slide=0, LL_slide=0)
    keys = {
        51: dict(rx=-18, T_rx=-10, RA_rx=170, RA_rz=10, LA_rx=-50, LA_rz=-15, RL_rx=-35, RL_rz=6, LL_rx=40, LL_rz=-6, RL_slide=0.5, LL_slide=0.4),    # the uppercut's follow-through
        54: dict(rx=-28, T_rx=-14, RA_rx=120, RA_rz=14, LA_rx=-20, LA_rz=-20, RL_rx=45, RL_rz=8, LL_rx=45, LL_rz=-8, RL_slide=1.3, LL_slide=1.3),      # gather: a deep squat before the jump
        57: dict(rx=-6, T_rx=0, RA_rx=165, RA_rz=14, LA_rx=160, LA_rz=-14, RL_rx=-8, RL_rz=5, LL_rx=-10, LL_rz=-5),                                     # the take-off: stretch, arms up
        62: dict(rx=4, T_rx=0, RA_rx=130, RA_rz=40, LA_rx=120, LA_rz=-40, RL_rx=60, RL_rz=6, LL_rx=-25, LL_rz=-8, RL_slide=0.5),                        # rising, the right knee comes up
        68: dict(rx=16, T_rx=6, RA_rx=40, RA_rz=70, LA_rx=20, LA_rz=-70, RL_rx=130, RL_rz=6, LL_rx=-20, LL_rz=-6),                                      # leaning back, the leg is cocked
        72: dict(rx=30, T_rx=10, H_rx=10, RA_rx=-30, RA_rz=60, LA_rx=-40, LA_rz=-50, RL_rx=172, RL_rz=4, LL_rx=-15, LL_rz=-5),                          # the apex: leg straight up, held
        75: dict(rx=32, T_rx=10, H_rx=12, RA_rx=-34, RA_rz=62, LA_rx=-44, LA_rz=-52, RL_rx=176, RL_rz=4, LL_rx=-14, LL_rz=-5),                          # a breath at the top
        77: dict(rx=6, T_rx=-6, RA_rx=30, RA_rz=44, LA_rx=40, LA_rz=-44, RL_rx=100, RL_rz=4, LL_rx=-10, LL_rz=-6),                                      # the leg drops
        78: dict(rx=-32, T_rx=-24, H_rx=-12, RA_rx=70, RA_rz=30, LA_rx=80, LA_rz=-30, RL_rx=18, RL_rz=3, LL_rx=-12, LL_rz=-6),                          # CONTACT: the heel lands, the body folds over it
        81: dict(rx=-36, T_rx=-20, RA_rx=60, RA_rz=36, LA_rx=70, LA_rz=-36, RL_rx=-6, RL_rz=3, LL_rx=-5, LL_rz=-6),                                     # through
        85: dict(rx=-20, T_rx=-10, RA_rx=20, RA_rz=60, LA_rx=30, LA_rz=-60, RL_rx=12, RL_rz=6, LL_rx=18, LL_rz=-6),                                     # falling, arms out
        88: dict(rx=-28, T_rx=-20, RA_rx=70, RA_rz=18, LA_rx=60, LA_rz=-18, RL_rx=30, RL_rz=8, LL_rx=26, LL_rz=-8, RL_slide=1.5, LL_slide=1.4),        # the landing squat
    }
    ease = {51: "io", 54: "in", 57: "out", 62: "io", 68: "io", 72: "hold", 75: "in", 77: "in", 78: "back", 81: "io", 85: "in"}
    return base, keys, ease


NAMES20 = mocap.NAMES20


def authored(tau0: int, tau1: int) -> np.ndarray:
    base, keys, ease = author_keys()
    ks = sorted(keys)
    full = {k: {**base, **keys[k]} for k in ks}
    # carry the unspecified values forward so a key only has to say what changes
    prev = dict(base)
    for k in ks:
        d = dict(prev)
        d.update(keys[k])
        full[k] = d
        prev = d
    out = np.zeros((tau1 - tau0 + 1, 20))
    for i, t in enumerate(range(tau0, tau1 + 1)):
        j = max(0, min(len(ks) - 2, int(np.searchsorted(ks, t, side="right")) - 1))
        a, b = ks[j], ks[j + 1]
        u = ease_fn(ease.get(a, "io"), (t - a) / (b - a))
        for c, n in enumerate(NAMES20):
            out[i, c] = full[a][n] + (full[b][n] - full[a][n]) * u
    return out


def hero_angles():
    """The hero's 20 angles, his planar path and his height over the whole animation clock."""
    aa, axz, aair, ba, bxz, bair = hero_track()
    mid = authored(52, 87)
    n_mid = len(mid)
    # path and height of the aerial part: a flight of my own (ballistic: up to the apex at 72, then pulled down by the kick)
    mx = np.array([plan_x(t) for t in range(52, 88)])
    mz = np.full(n_mid, -0.9)
    air_mid = np.zeros(n_mid)
    for i, t in enumerate(range(52, 88)):
        if t < 55:
            air_mid[i] = 0.0
        elif t <= 72:
            u = (t - 55) / 17.0
            air_mid[i] = 8.6 * (1 - (1 - u) ** 2)                       # up, decelerating
        elif t <= 78:
            air_mid[i] = 8.6 - 0.9 * ((t - 72) / 6.0) ** 2
        else:
            u = (t - 78) / 9.0
            air_mid[i] = (8.6 - 0.9) * (1 - u ** 1.8)                   # the kick drives him down
    air_mid = np.clip(air_mid, 0, None)
    # splice the three parts; the wrapping angles are put on the branch nearest to the previous part, then cross-fade 3 images over each join
    parts = [aa.copy(), mid.copy(), ba.copy()]
    for k in (1, 2):
        for c in range(0, 16):
            parts[k][:, c] += 360.0 * np.round((parts[k - 1][-1, c] - parts[k][0, c]) / 360.0)
    ang = np.vstack(parts)
    xz = np.vstack([axz, np.stack([mx, mz], 1), bxz])
    air = np.concatenate([aair, air_mid, bair])
    for j in (52, 88):
        prev = ang[j - 1].copy()
        for i in range(3):
            w = (i + 1) / 4.0
            ang[j + i] = prev * (1 - w) + ang[j + i] * w
    return ang, xz, air


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# the dummy: a ballistic flight solved to pass through the fist and then the heel

def dummy_motion(fist: np.ndarray, heel: np.ndarray):
    """Positions (x, torso height, z) and the 16 angles of the dummy over the animation clock."""
    pos = np.zeros((M, 3))
    ang = np.zeros((M, 16))
    x0 = fist[0] + 0.55
    base = np.array([x0, 3.0, fist[2] - 0.15])
    pos[:] = base
    p0 = np.array([x0, max(fist[1], 3.0), base[2]])
    T1 = HIT2 - HIT1
    a = np.array([0.0, -G_AIR, 0.0])
    tgt = np.array([heel[0] + 0.15, heel[1] + 0.1, heel[2] * 0.4])
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
    r_hit2 = 5.8 / 0.04 * (1 - math.exp(-0.04 * (HIT2 - HIT1)))
    for t in range(M):
        if t <= HIT1:
            rx = 2.0 * math.sin(0.18 * t)
        elif t <= HIT2:
            rx = 5.8 / 0.04 * (1 - math.exp(-0.04 * (t - HIT1)))
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


def build() -> Scene:
    ang, xz, air = hero_angles()
    hero = Character("hero", Animation("hero", fps=FPS, archetype="cinematic"), colors=HERO_COLORS)
    key_hero(hero, ang, xz, air)
    fist = np.array(hero.limb_tip("Right Arm", HIT1))                 # where the uppercut lands, film image 48
    heel = np.array(hero.limb_tip("Right Leg", film_of(HIT2)))        # where the axe kick lands
    pos, dang, v0, (p_g, TG) = dummy_motion(fist, heel)
    dummy = Character("dummy", Animation("dummy", fps=FPS, archetype="cinematic"), colors=DUMMY_COLORS)
    key_dummy(dummy, pos, dang)

    cine = Cinematic(N, fps=FPS)
    cine.look = "studio"
    cine.sky_color, cine.floor_color = "#9fb0c8", "#43464e"
    f1, f2, fg = film_of(HIT1), film_of(HIT2), film_of(TG)
    hero_c = lambda f: tuple(float(v) for v in hero.world_parts(int(f))["Torso"][1])
    dum_c = lambda f: tuple(float(v) for v in dummy.world_parts(int(f))["Torso"][1])

    # ---- camera (world: the hero starts at x = -8 and meets the dummy near x = 3; both rise to about 12 studs; the lens sits on the +z side)
    cine.shot(0, 28, dolly((-13.0, 2.2, 13.5), (-11.0, 2.6, 12.0), (-2.5, 3.0, -0.4), (-2.0, 3.0, -0.4), fov=44, easing="sine_inout"))
    cine.shot(28, f1 - 6, tracking(hero_c, (3.0, 1.0, 12.5), look_dy=0.3, fov=(44, 38)))
    cine.shot(f1 - 6, f1 + 4, dolly((0.5, 2.6, 12.0), (1.5, 3.0, 10.8), (3.3, 3.5, 0.0), (3.3, 3.6, 0.0), fov=(36, 30), easing="expo_out"))
    cine.shot(f1 + 4, f2 - 5, autoframe(lambda f: [hero_c(f), dum_c(f)], f1 + 4, f2 - 5, azimuth=14, elevation=3.0, fov=40.0, fill=0.75, min_radius=5.0, follow=0.18, lift=0.0))
    cine.shot(f2 - 5, f2 + 8, dolly((11.0, 7.5, 17.0), (10.0, 8.0, 15.0), (4.8, 8.0, 0.0), (4.8, 7.4, 0.0), fov=(40, 34), easing="expo_out"))
    cine.shot(f2 + 8, fg + 4, dolly((11.0, 6.0, 16.5), (12.5, 2.4, 14.0), (5.3, 4.0, 0.0), (5.9, 1.3, 0.0), fov=(38, 38), roll=(0.0, -2.5), easing="expo_out"))
    cine.shot(fg + 4, N + 1, dolly((12.5, 2.4, 14.0), (19.0, 7.0, 20.0), (5.9, 1.3, 0.0), (9.0, 2.6, 0.0), fov=(38, 44), roll=(-2.5, 0.0), easing="sine_inout"))

    # ---- hit 1: the uppercut
    cine.punch_in(f1, 0.13, 9)
    cine.shake(f1, 9, 0.5)
    cine.screen_fx("white", f1, 2, alpha=0.85)
    cine.screen_fx("bw", f1 + 2, 3, seed=5, accent=True, focus=(0.55, 0.5), shards=16, bright=1.6)
    cine.ring(f1, 10, tuple(fist), 0.3, 3.4, 0.35, 0.05, "#ffffff", 0.95, 0.0, n=(1, 0, 0))
    cine.ring(f1, 8, (fist[0], 0.1, fist[2]), 0.6, 3.6, 0.3, 0.04, "#cfe9ff", 0.8, 0.0)
    cine.burst(f1, 8, tuple(fist), 0.4, 3.0, "#ffd27a", "#ffffff")
    cine.emit(f1, f1 + 6, origin=(fist[0], 0.3, fist[2]), rate=0, burst=26, vel=(0.2, 0.5), dir=(0, 1, 0), spread=1.1, grav=0.02, life=(14, 26), size=(0.5, 0.15),
              color=("#c9c2b2", "#8f897c"), alpha=(0.7, 0.0), add=False, shape="smoke", seed=3, radius=0.7)
    cine.trail(f1 - 8, f1 + 5, 0, "Right Arm", (0.0, -1.0, 0.0), 8, 0.5, 0.0, "#fff4d1", 0.9)

    # ---- dash: dust, speed lines
    d0, d1 = film_of(30), film_of(44)
    cine.emit(d0, d1, attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=2.6, vel=(0.02, 0.12), dir=(-1, 0.3, 0), spread=0.7, life=(16, 32), size=(0.9, 2.6),
              color=("#a8a49a", "#7a766c"), alpha=(0.4, 0.0), add=False, shape="smoke", seed=2, radius=0.4)
    cine.streaks(d0 + 2, d1 - d0, (-9.0, 2.6, -0.4), (-5.0, 3.0, -0.4), n=12, r0=0.4, r1=2.2, w=0.05, color="#ffffff", seed=4)

    # ---- the flight: a trail on the dummy, a pull on the camera
    cine.emit(f1 + 2, f2, attach={"char": 1, "part": "Torso", "off": [0, 0, 0]}, rate=1.6, vel=(0.01, 0.05), dir=(0, 1, 0), spread=0.9, life=(14, 24), size=(0.6, 0.15),
              color=("#e8edf7", "#9aa4b5"), alpha=(0.35, 0.0), add=True, shape="soft", seed=6, radius=0.5)
    cine.trail(film_of(66), f2 - 1, 0, "Right Leg", (0.0, -1.0, 0.0), 9, 0.7, 0.0, "#ff8a3a", 0.85)

    # ---- hit 2: the axe kick
    cine.punch_in(f2, 0.16, 10)
    cine.shake(f2, 12, 0.8)
    cine.screen_fx("black", f2, 1)
    cine.screen_fx("bw", f2 + 1, 4, seed=9, accent=True, focus=(0.5, 0.45), shards=18, bright=1.8)
    cine.flash(f2 + 5, 3, "#ffffff", 0.5)
    hp = tuple(float(v) for v in heel)
    cine.ring(f2, 12, hp, 0.4, 4.2, 0.4, 0.05, "#ffe2b0", 0.95, 0.0, n=(0, 1, 0))
    cine.dome(f2, 9, hp, 0.4, 3.0, "#ffd9a0", 0.55, 0.0)
    cine.slash(f2 - 4, 7, (heel[0], heel[1] + 1.6, heel[2]), (0, 0, 1), 2.4, 160, 20, 0.55, "#ffb86b", "#ffffff")

    # ---- the ground: the slam
    gp = (float(p_g[0]), 0.05, float(p_g[2]))
    cine.shake(fg, 20, 1.3)
    cine.punch_in(fg, 0.2, 12)
    cine.flash(fg, 3, "#ffffff", 0.55)
    for k, (r1, col) in enumerate(((5.5, "#ffffff"), (8.0, "#ffd9a0"), (11.0, "#9fb0c8"))):
        cine.ring(fg + 2 * k, 16 + 3 * k, gp, 0.5, r1, 0.5 - 0.1 * k, 0.04, col, 0.9 - 0.15 * k, 0.0)
    cine.cracks(fg, 20, gp, 6.5, 9, "#1c1d22", glow="#ffc477", width=0.14, seed=2, fade=(60, 40))
    cine.burst_debris(fg, gp, 38, 0.32, 0.55, (0.18, 0.5), ["#6d6f78", "#8a8d96", "#53555d"], seed=3, g=0.03)
    cine.emit(fg, fg + 14, origin=gp, rate=0, burst=60, vel=(0.28, 0.4), dir=(0, 1, 0), spread=1.6, grav=0.01, life=(24, 50), size=(1.2, 3.4), color=("#bdb9ae", "#8a8679"),
              alpha=(0.6, 0.0), add=False, shape="smoke", seed=5, radius=1.4)

    # ---- the landing, the walk away
    l0 = film_of(88)
    cine.emit(l0, l0 + 8, attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=0, burst=26, vel=(0.2, 0.2), dir=(0, 1, 0), spread=1.4, life=(16, 30), size=(0.8, 2.0),
              color=("#a8a49a", "#7a766c"), alpha=(0.45, 0.0), add=False, shape="smoke", seed=8, radius=0.8)
    cine.vignette.key(0, 0.15).key(f1, 0.15).key(f1 + 2, 0.4).key(f1 + 14, 0.15).key(N, 0.25)
    return Scene("Dragon montant", [hero, dummy], fps=FPS, cine=cine)
