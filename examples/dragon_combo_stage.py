"""Staging of « Dragon Combo » v2: the night arena, FEW and LONG shots (every shot shows both fighters whole, in a readable profile), effects kept small on the light hits
and big only on the three moments that matter (the uppercut that launches, the axe kick, the slam)."""

from __future__ import annotations

import math
import os

import numpy as np

from tsb_engine.cinematic import Cinematic, autoframe, dolly, tracking
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from . import dragon_combo as C
from .dragon_rise import orbit_pos

HERO_Z = C.HERO_Z
N = C.NN
T = C.T

# palette: a cold night (slate / indigo), the hero in orange, every light effect in violet -> magenta with a white-hot core
SKY_TOP, SKY_HOR, FLOOR = "#060a1e", "#4a3a86", "#1b2236"
V_CORE, V_MAIN, V_EDGE, V_ICE = "#f4e4ff", "#a066ff", "#ff3fd0", "#7fe0ff"


def dress(cine: Cinematic):
    stone, dark, warm = "#3d4670", "#242b4a", "#566191"
    cine.prop((0, 3.0, -24), (70, 6.0, 2.4), stone)
    cine.prop((0, 6.5, -24), (70, 0.9, 3.0), dark)
    for x in (-27, -18, -9, 0, 9, 18, 27):
        cine.prop((x, 7.0, -21.5), (2.6, 14.0, 2.6), warm)
        cine.prop((x, 14.4, -21.5), (3.6, 0.9, 3.6), dark)
        cine.prop((x, 0.5, -21.5), (3.6, 1.0, 3.6), dark)
    for i in range(4):
        cine.prop((4.0, 0.35 + 0.7 * i, -17.0 + 1.1 * i), (22.0 - 2.0 * i, 0.7, 2.2), stone)
    for k, (x, h, c) in enumerate([(-46, 26, "#2a3260"), (-34, 38, "#252d58"), (-18, 22, "#2d3566"), (12, 30, "#262e5b"), (30, 42, "#222a52"), (48, 24, "#2b3362")]):
        cine.prop((x, h / 2, -70 - 6 * (k % 3)), (9 + (k % 3) * 3, h, 9), c)
    for (x, z, s) in ((-3.5, 7.5, 1.3), (1.5, -9.5, 1.8), (16.0, -9.0, 1.6)):      # rubble for scale and parallax (none near the cameras' paths)
        cine.prop((x, s / 2, z), (s * 1.6, s, s * 1.3), "#2f3860", yaw=20 * x)


def build_scene() -> Scene:
    ang, xz, air, pos, dang, tips = C.build_motion()
    hero = Character("hero", Animation("hero", fps=C.FPS, archetype="cinematic"), colors=C.HERO_COLORS)
    C.key_hero(hero, ang, xz, air)
    dummy = Character("dummy", Animation("dummy", fps=C.FPS, archetype="cinematic"), colors=C.DUMMY_COLORS)
    C.key_dummy(dummy, pos, dang)

    cine = Cinematic(N, fps=C.FPS)
    cine.look = "arena"
    cine.mood = "night"
    cine.sky_color, cine.horizon_color, cine.floor_color = SKY_TOP, SKY_HOR, FLOOR
    dress(cine)
    hero_c = lambda f: tuple(float(v) for v in hero.world_parts(int(f))["Torso"][1])
    dum_c = lambda f: tuple(float(v) for v in dummy.world_parts(int(f))["Torso"][1])
    ahead = lambda f, dx, dy, dz: (hero_c(f)[0] + dx, hero_c(f)[1] + dy, hero_c(f)[2] + dz)
    tip = lambda f: tuple(float(v) for v in tips[f])      # f: OLD clock (a contact frame)
    hero_o = lambda f: hero_c(T(f))                          # hero centre at an OLD-clock frame
    gx, gy, gz = C.GROUND_POS

    if os.environ.get("DC_CAM") == "lab":          # pose lab: both bodies in pure profile, to judge the poses
        cine.shot(0, N + 1, autoframe(lambda f: [hero_c(f), dum_c(f)], 0, N, azimuth=0.0, elevation=2.0, fov=40.0, fill=0.8, min_radius=3.4, follow=0.5, lift=0.3, pad=1.0))
        scene = Scene("Dragon Combo", [hero, dummy], fps=C.FPS, cine=cine)
        scene.report = []
        return scene

    # ---------------------------------------------------------------- cameras (frames: old clock through T)
    both = lambda: (lambda f: [hero_c(f), dum_c(f)])
    cine.shot(0, T(30), dolly((-20.5, 4.6, 1.6), (-18.4, 4.2, 1.2), (-3.0, 3.0, -1.4), (-1.0, 3.0, -1.4), fov=(50, 46), easing="sine_inout"))                     # gameplay: behind the player
    cine.shot(T(30), T(46), tracking(lambda f: ahead(f, 3.2, 0.3, -0.4), (-11.0, 1.8, 3.2), fov=(52, 70), offset_end=(-9.0, 1.4, 3.0)))                              # the dash
    # the ground combo, ONE shot: both fighters whole, seen almost in profile so that every arm / leg extension is readable
    cine.shot(T(46), T(70), autoframe(both(), T(46), T(70), azimuth=-28.0, elevation=4.0, fov=38.0, fill=0.8, min_radius=5.2, follow=0.55, lift=0.4, pad=1.3))
    # the uppercut launches him: the camera drops back and follows both bodies up
    cine.shot(T(70), T(90), autoframe(both(), T(70), T(90), azimuth=-34.0, elevation=6.0, fov=44.0, fill=0.8, min_radius=6.0, follow=0.5, lift=0.8, pad=1.5))
    # the air combo: a slow quarter turn, both whole
    cine.shot(T(90), T(108), autoframe(both(), T(90), T(108), azimuth=-40.0, azimuth_end=-8.0, elevation=6.0, fov=44.0, fill=0.8, min_radius=6.5, follow=0.5, lift=1.0, pad=1.5))
    # the axe kick: low profile, the dummy above, the hero's leg coming down
    cine.shot(T(108), T(122), autoframe(both(), T(108), T(122), azimuth=-10.0, azimuth_end=-24.0, elevation=-2.0, fov=44.0, fill=0.8, min_radius=6.5, follow=0.5, lift=1.0, pad=1.5))
    gm = (gx - 1.2, 2.0, gz + 1.2)
    # the slam: one wide shot from above the crater that pushes in slowly (the cracks and the smoke have to be seen)
    cine.shot(T(122), T(140), dolly(orbit_pos(gm, 26, 9, 22.0), orbit_pos(gm, 30, 6, 16.0), (gm[0] - 1.0, 4.5, gm[2]), gm, fov=(36, 34), roll=(0.0, -1.5), easing="expo_out"))
    cine.shot(T(140), T(153), tracking(lambda f: (hero_c(f)[0], hero_c(f)[1] + 0.4, hero_c(f)[2] - 0.2), (-12.0, 0.0, 7.0), fov=(34, 33)))                          # he turns toward the lens
    cine.shot(T(153), T(193), dolly((-2.0, 1.7, 3.8), (-6.0, 2.2, 4.8), (8.0, 3.3, HERO_Z), (5.2, 3.4, HERO_Z), fov=42, easing="sine_inout"))                       # he walks toward the lens
    cine.shot(T(193), N + 1, dolly((-6.0, 2.2, 4.8), (-13.0, 7.5, 8.0), (5.2, 3.4, HERO_Z), (8.0, 2.6, HERO_Z), fov=(42, 38), easing="sine_inout"))                # the final crane

    # ---------------------------------------------------------------- the effects
    PI2 = math.pi / 2
    # the dash: a few air rings behind him and speed lines
    for k, ff in enumerate(range(32, 46, 4)):
        hc = hero_o(ff)
        cine.mesh("wind", T(ff), 10, (hc[0] - 0.6, hc[1] - 0.4, hc[2]), r0=0.9, r1=3.0, color=V_ICE, a=0.7, strength=1.3, spin=0.2, rot=(0.0, PI2, 0.0), ease=2.2, fade=1.2, seed=30 + k)
    cine.streaks(T(32), 16, (hero_o(32)[0] - 5.0, 2.6, HERO_Z + 0.4), (hero_o(45)[0] + 2.0, 3.0, HERO_Z + 0.4), n=10, r0=0.4, r1=2.2, w=0.05, color=V_ICE, seed=4)
    cine.emit(T(32), T(45), attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=2.0, vel=(0.02, 0.12), dir=(-1, 0.3, 0), spread=0.7, life=(16, 32), size=(0.9, 2.4),
              color=("#8c91b8", "#4b5078"), alpha=(0.35, 0.0), add=False, shape="smoke", seed=2, radius=0.4)

    # every contact: small and CLEAN (a star, one ring); the VFX never sit on the striking limb for more than a few frames.  The big ones get their own block below.
    hits = {c["f"]: c for c in C.CONTACTS}
    sizes = {50: 0.7, 57: 0.8, 64: 0.9, 76: 1.4, 90: 0.8, 95: 0.8, 100: 1.0, 114: 1.6}
    for f, c in hits.items():
        p, s_, g = tip(f), sizes[f], T(f)
        cine.shake(g, 8 + int(5 * s_), 0.3 * s_)
        cine.punch_in(g, 0.04 + 0.04 * s_, 6)
        cine.mesh("star", g, 8, p, r0=1.6 * s_, r1=3.4 * s_, color=V_EDGE, a=1.0, strength=8.0, dim=0.5 * s_, ease=3.0, fade=1.3, seed=f)
        cine.mesh("wind", g, 11, p, r0=0.6, r1=2.8 * s_ + 0.4, color=V_CORE, a=0.9, strength=2.4, spin=0.25, rot=(0.0, PI2, 0.0), ease=2.6, fade=1.0, seed=f + 1)
        cine.ring(g, 10, p, 0.3, 1.9 * s_ + 0.8, 0.4, 0.05, V_CORE, 0.8, 0.0, n=(0, 0, 1))
        if f in (76, 114):
            cine.mesh("blades", g, 11, p, r0=0.8, r1=2.6 * s_ + 0.8, color=V_CORE, edge=V_MAIN, a=1.0, strength=6.0, n=7, spin=0.6, rise=0.3, width=0.9, rot=(0.0, PI2, 0.0), ease=2.4, fade=0.9, seed=f + 2)
        if c["mode"] == "g" and f in (64, 76):                                  # a puff of dust at the dummy's feet
            d = tuple(float(v) for v in c["_dummy"])
            cine.mesh("smoke", g, 22, (d[0], 0.6, d[2]), n=3, r0=0.9, r1=1.8, spread=1.0, color="#8c93bc", a=0.8, rise=0.9, seed=f)
    # the uppercut: a column of light rises with the fist, then an ink frame
    p76, g76 = tip(76), T(76)
    cine.mesh("pillar", g76, 14, (p76[0], 0.0, p76[2]), r0=0.8, r1=0.8, color=V_MAIN, a=1.0, strength=6.5, height=16.0, dim=0.4, fade=1.0, seed=7)
    cine.mesh("dome", g76, 9, (p76[0], 0.0, p76[2]), r0=0.6, r1=3.6, color=V_MAIN, a=1.0, strength=4.0, height=0.8, rim=0.6, fill=0.08, ease=3.0, fade=1.2, seed=3)
    sc1 = (p76[0] - 0.2, p76[1] - 1.5, p76[2] - 0.3)
    cine.slash(T(72), 10, sc1, (1, 0, 0), 2.7, 75, -125, 1.2, V_MAIN, V_CORE)
    cine.streaks(g76, 10, (p76[0], 0.5, p76[2]), (p76[0], 13.0, p76[2]), n=14, r0=1.6, r1=2.4, w=0.07, color=V_CORE, seed=11)
    cine.screen_fx("bw", g76 + 2, 3, seed=5, accent=True, focus=(0.55, 0.5), shards=5, bright=1.5, ink=True, strokes=10, ink_glow=(0.85, 0.25, 1.0))
    # the spinning kick: a flat disc of blades around the hero (smaller than v1)
    hs = hero_o(99)
    cine.mesh("blades", T(97), 16, (hs[0], hs[1] - 0.6, hs[2]), r0=1.4, r1=5.2, color=V_CORE, edge=V_EDGE, a=1.0, strength=6.5, n=10, spin=0.9, rise=0.25, width=1.0, ease=2.2, fade=1.0, seed=21)
    # the leap: a short trail
    for k, ff in enumerate(range(83, 90, 3)):
        hc = hero_o(ff)
        cine.mesh("wind", T(ff), 10, (hc[0] - 0.2, hc[1] - 1.5, hc[2]), r0=0.8, r1=2.8, color=V_ICE, a=0.8, strength=1.6, spin=0.2, ease=2.2, fade=1.1, seed=40 + k)
    # the axe kick
    p114, g114 = tip(114), T(114)
    cine.mesh("pillar", g114, 16, (p114[0], 0.0, p114[2]), r0=1.0, r1=1.0, color=V_MAIN, a=1.0, strength=6.5, height=22.0, dim=0.5, fade=1.0, seed=8)
    cine.slash(T(108), 10, (p114[0] + 0.4, p114[1] + 1.8, p114[2]), (0.9, 0.1, 0.45), 3.6, -100, 70, 1.4, V_MAIN, V_CORE)
    cine.streaks(T(108), 12, (p114[0], p114[1] + 11.0, p114[2]), (p114[0], p114[1] - 1.0, p114[2]), n=14, r0=1.8, r1=2.2, w=0.07, color=V_CORE, seed=13)
    cine.screen_fx("bw", g114 + 2, 3, seed=9, accent=True, focus=(0.5, 0.45), shards=6, bright=1.6, ink=True, strokes=12, ink_glow=(0.85, 0.25, 1.0))
    # the dummy hits the floor: a glowing crater, a column of light, a short dome, a disc of blades, rings, debris, volumetric smoke
    g0 = T(C.GROUND_HIT)
    gp = (gx, 0.05, gz)
    cine.shake(g0, 24, 1.3)
    cine.punch_in(g0, 0.18, 12)
    cine.flash(g0, 2, "#ffffff", 0.3)
    cine.mesh("crater", g0, N - g0 - 1, (gx, 0.0, gz), r0=9.5, r1=9.5, color=V_CORE, edge="#b03cff", a=1.0, strength=6.5, seed=2, branches=18)
    cine.mesh("pillar", g0, 14, (gx, 0.0, gz), r0=1.1, r1=1.1, color=V_MAIN, a=1.0, strength=6.5, height=19.0, dim=0.8, fade=1.0, seed=9)
    cine.mesh("dome", g0, 5, (gx, 0.0, gz), r0=0.8, r1=6.0, color=V_MAIN, a=1.0, strength=1.6, height=0.7, rim=0.5, fill=0.02, ease=3.0, fade=1.8, seed=9)
    cine.mesh("blades", g0, 16, (gx, 0.2, gz), r0=2.0, r1=10.0, color=V_CORE, edge=V_EDGE, a=1.0, strength=6.0, n=14, spin=0.45, rise=0.5, lift=0.3, width=1.1, ease=2.2, fade=0.9, seed=10)
    for k, (r1, dl) in enumerate(((9.0, 0), (14.0, 4))):
        cine.mesh("wind", g0 + dl, 18, (gx, 0.15 + 0.1 * k, gz), r0=1.5, r1=r1, color=V_CORE, a=0.9, strength=2.0, spin=0.22, ease=2.4, fade=1.0, seed=11 + k)
    cine.mesh("star", g0, 9, (gx, 1.8, gz), r0=4.0, r1=8.0, color=V_EDGE, a=1.0, strength=10.0, dim=0.7, ease=3.0, fade=1.3, seed=g0)
    cine.mesh("smoke", g0, 70, (gx, 0.8, gz), n=9, r0=2.4, r1=5.0, spread=3.6, color="#7c84ac", a=1.0, rise=3.2, seed=31, fade=1.0)
    for k, (r1, col) in enumerate(((7.5, "#ffffff"), (11.0, V_CORE), (15.0, V_MAIN))):
        cine.ring(g0 + 3 * k, 18 + 3 * k, gp, 0.5, r1, 0.5 - 0.1 * k, 0.04, col, 0.9 - 0.15 * k, 0.0)
    cine.burst_debris(g0, gp, 50, 0.34, 0.6, (0.4, 1.1), ["#40476e", "#565f8a", "#343a5e"], seed=3, g=0.03)
    cine.emit(g0 + 6, N - 1, origin=(gx, 0.3, gz), rate=3.0, vel=(0.03, 0.12), dir=(0, 1, 0), spread=0.9, grav=-0.0012, life=(34, 70), size=(0.16, 0.05), color=(V_CORE, V_EDGE),
              alpha=(1.0, 0.0), add=True, shape="soft", seed=21, radius=2.8)
    # the landing: dust
    hl = hero_o(124)
    cine.ring(T(124), 12, (hl[0], 0.1, hl[2]), 0.5, 5.0, 0.6, 0.05, V_CORE, 0.8, 0.0)
    cine.mesh("smoke", T(124), 40, (hl[0], 0.6, hl[2]), n=3, r0=1.0, r1=2.2, spread=1.4, color="#8c93bc", a=0.9, rise=0.9, seed=5)
    cine.vignette.key(0, 0.2).key(T(76), 0.2).key(T(80), 0.34).key(T(92), 0.2).key(T(114), 0.2).key(T(118), 0.36).key(T(132), 0.25).key(N, 0.3)

    scene = Scene("Dragon Combo", [hero, dummy], fps=C.FPS, cine=cine)
    scene.report = []
    return scene
