"""Staging of « Dragon Combo »: the night arena, the cameras (TSB-style: behind the player, hit cams, a half-turn around the juggle, a final crane) and the effects."""

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
N = C.N

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
    tip = lambda f: tuple(float(v) for v in tips[f])
    gx, gy, gz = C.GROUND_POS

    if os.environ.get("DC_CAM") == "lab":          # pose lab: both bodies in pure profile, to judge the poses
        cine.shot(0, N + 1, autoframe(lambda f: [hero_c(f), dum_c(f)], 0, N, azimuth=0.0, elevation=2.0, fov=40.0, fill=0.8, min_radius=3.4, follow=0.5, lift=0.3, pad=1.0))
        scene = Scene("Dragon Combo", [hero, dummy], fps=C.FPS, cine=cine)
        scene.report = []
        return scene

    # ---------------------------------------------------------------- cameras
    cine.shot(0, 30, dolly((-20.5, 4.6, 1.6), (-18.4, 4.2, 1.2), (-3.0, 3.0, -1.4), (-1.0, 3.0, -1.4), fov=(50, 46), easing="sine_inout"))                          # gameplay: behind the player
    cine.shot(30, 47, tracking(lambda f: ahead(f, 3.2, 0.3, -0.4), (-11.0, 1.8, 3.2), fov=(52, 78), offset_end=(-9.0, 1.4, 3.0)))                                  # the dash: the field of view opens with the speed
    cine.shot(47, 54, autoframe(lambda f: [hero_c(f), dum_c(f)], 47, 54, azimuth=-50.0, elevation=8.0, fov=42.0, fill=0.8, min_radius=2.6, follow=0.5, lift=0.5, pad=0.8))     # jab, three-quarter from behind
    cine.shot(54, 61, autoframe(lambda f: [hero_c(f), dum_c(f)], 54, 61, azimuth=-136.0, elevation=5.0, fov=42.0, fill=0.8, min_radius=2.6, follow=0.5, lift=0.5, pad=0.8))   # hook, from the other side
    cine.shot(61, 68, autoframe(lambda f: [hero_c(f), dum_c(f)], 61, 68, azimuth=34.0, elevation=2.0, fov=42.0, fill=0.8, min_radius=2.6, follow=0.5, lift=0.4, pad=0.8))     # kick, a low front cam
    cine.shot(68, 80, tracking(lambda f: ahead(f, 3.0, 1.5, -0.6), (-10.6, -0.4, 3.6), fov=(46, 38), offset_end=(-9.4, -0.6, 3.4)))                                  # the uppercut, from behind and below
    cine.shot(80, 90, autoframe(lambda f: [hero_c(f), dum_c(f)], 80, 90, azimuth=-72.0, elevation=11.0, fov=46.0, fill=0.72, min_radius=3.2, follow=0.35, lift=0.4, pad=1.0))  # the leap
    cine.shot(90, 108, autoframe(lambda f: [hero_c(f), dum_c(f)], 90, 108, azimuth=-72.0, azimuth_end=112.0, elevation=7.0, fov=42.0, fill=0.78, min_radius=3.2, follow=0.45, lift=0.6, pad=1.0))   # half a turn around the juggle
    cine.shot(108, 114, autoframe(lambda f: [hero_c(f), dum_c(f)], 108, 114, azimuth=-34.0, azimuth_end=-58.0, elevation=-7.0, fov=42.0, fill=0.74, min_radius=3.4, follow=0.5, lift=0.2, pad=1.0))   # from below, the leg comes up
    hp = tip(114)
    cine.shot(114, 119, dolly((hp[0] + 9.5, hp[1] - 2.4, hp[2] + 5.6), (hp[0] + 7.4, hp[1] - 1.8, hp[2] + 4.8), (hp[0] - 0.8, hp[1] + 1.4, hp[2]), (hp[0] - 0.8, hp[1] + 0.2, hp[2]), fov=(38, 33), roll=(-4.0, 0.0), easing="expo_out"))
    gm = (gx - 1.2, 2.0, gz + 1.2)
    cine.shot(119, 127, dolly(orbit_pos(gm, 26, 8, 20.0), orbit_pos(gm, 34, 4, 15.0), (gm[0] - 1.0, 6.5, gm[2]), gm, fov=(34, 32), roll=(0.0, -2.0), easing="expo_out"))
    cine.shot(127, 138, dolly(orbit_pos(gm, 30, 4, 16.5), orbit_pos(gm, 14, 8, 20.0), gm, (gm[0] - 0.6, 2.4, gm[2]), fov=34, easing="sine_inout"))
    cine.shot(138, 153, tracking(lambda f: (hero_c(f)[0], hero_c(f)[1] + 0.4, hero_c(f)[2] - 0.2), (-8.0, -1.2, 4.2), fov=(38, 36)))                              # he turns toward the lens
    cine.shot(153, 193, dolly((-2.0, 1.7, 3.8), (-6.0, 2.2, 4.8), (8.0, 3.3, HERO_Z), (5.2, 3.4, HERO_Z), fov=42, easing="sine_inout"))                           # he walks toward the lens
    cine.shot(193, N + 1, dolly((-6.0, 2.2, 4.8), (-13.0, 7.5, 8.0), (5.2, 3.4, HERO_Z), (8.0, 2.6, HERO_Z), fov=(42, 38), easing="sine_inout"))                  # the final crane

    # ---------------------------------------------------------------- the effects
    PI2 = math.pi / 2
    # the dash: air rings thrown off behind him, speed lines, dust
    for k, ff in enumerate(range(32, 46, 3)):
        hc = hero_c(ff)
        cine.mesh("wind", ff, 10, (hc[0] - 0.6, hc[1] - 0.4, hc[2]), r0=0.9, r1=3.4, color=V_ICE, a=0.8, strength=1.6, spin=0.2, rot=(0.0, PI2, 0.0), ease=2.2, fade=1.2, seed=30 + k)
    cine.streaks(32, 13, (hero_c(32)[0] - 5.0, 2.6, HERO_Z + 0.4), (hero_c(45)[0] + 2.0, 3.0, HERO_Z + 0.4), n=12, r0=0.4, r1=2.2, w=0.05, color=V_ICE, seed=4)
    cine.emit(32, 45, attach={"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}, rate=2.4, vel=(0.02, 0.12), dir=(-1, 0.3, 0), spread=0.7, life=(16, 32), size=(0.9, 2.6),
              color=("#8c91b8", "#4b5078"), alpha=(0.4, 0.0), add=False, shape="smoke", seed=2, radius=0.4)

    hits = {c["f"]: c for c in C.CONTACTS}
    sizes = {50: 0.8, 57: 0.9, 64: 1.0, 76: 1.5, 90: 0.9, 95: 0.9, 100: 1.1, 114: 1.8}
    for f, c in hits.items():
        p, s_ = tip(f), sizes[f]
        cine.shake(f, 8 + int(6 * s_), 0.35 * s_)
        cine.punch_in(f, 0.05 + 0.05 * s_, 6)
        cine.mesh("star", f, 9, p, r0=2.4 * s_, r1=5.0 * s_, color=V_EDGE, a=1.0, strength=13.0, dim=0.6 * s_, ease=3.0, fade=1.2, seed=f)
        cine.mesh("wind", f, 11, p, r0=0.8, r1=3.6 * s_ + 0.6, color=V_CORE, a=1.0, strength=3.2, spin=0.25, rot=(0.0, PI2, 0.0), ease=2.6, fade=1.0, seed=f + 1)
        cine.mesh("blades", f, 11, p, r0=0.8, r1=3.0 * s_ + 1.0, color=V_CORE, edge=V_MAIN, a=1.0, strength=8.0, n=5 + int(4 * s_), spin=0.6, rise=0.3, width=0.9, rot=(0.0, PI2, 0.0), ease=2.4, fade=0.9, seed=f + 2)
        cine.ring(f, 10, p, 0.3, 2.4 * s_ + 1.0, 0.45, 0.05, V_CORE, 0.9, 0.0, n=(0, 0, 1))
        if c["mode"] == "g":                                                    # a puff of dust at the dummy's feet on the ground hits
            d = tuple(float(v) for v in c["_dummy"])
            cine.mesh("smoke", f, 22, (d[0], 0.6, d[2]), n=3, r0=0.9, r1=2.0, spread=1.0, color="#8c93bc", a=1.0, rise=0.9, seed=f)
    # the uppercut: a column of light rises with the fist, ribbons and speed lines
    p76 = tip(76)
    cine.mesh("pillar", 76, 12, (p76[0], 0.0, p76[2]), r0=0.9, r1=0.9, color=V_MAIN, a=1.0, strength=6.0, height=16.0, dim=0.4, fade=1.0, seed=7)
    cine.mesh("dome", 76, 9, (p76[0], 0.0, p76[2]), r0=0.6, r1=4.4, color=V_MAIN, a=1.0, strength=5.0, height=0.8, rim=0.6, fill=0.1, ease=3.0, fade=1.2, seed=3)
    sc1 = (p76[0] - 0.2, p76[1] - 1.5, p76[2] - 0.3)
    cine.slash(71, 8, sc1, (1, 0, 0), 2.7, 75, -125, 1.4, V_MAIN, V_CORE)
    cine.slash(72, 8, sc1, (1, 0, 0), 3.8, 60, -140, 0.8, V_CORE, "#ffffff")
    cine.streaks(76, 8, (p76[0], 0.5, p76[2]), (p76[0], 13.0, p76[2]), n=18, r0=1.6, r1=2.4, w=0.07, color=V_CORE, seed=11)
    cine.screen_fx("white", 76, 1, alpha=0.5)
    cine.screen_fx("bw", 77, 3, seed=5, accent=True, focus=(0.55, 0.5), shards=5, bright=1.6, ink=True, strokes=10, ink_glow=(0.85, 0.25, 1.0))
    # the spinning kick: a flat disc of blades around the hero
    hs = hero_c(99)
    cine.mesh("blades", 97, 14, (hs[0], hs[1] - 0.6, hs[2]), r0=1.6, r1=7.0, color=V_CORE, edge=V_EDGE, a=1.0, strength=8.0, n=14, spin=0.9, rise=0.25, width=1.2, ease=2.2, fade=1.0, seed=21)
    # the leap: a rocket trail
    for k, ff in enumerate(range(83, 90, 2)):
        hc = hero_c(ff)
        cine.mesh("wind", ff, 9, (hc[0] - 0.2, hc[1] - 1.5, hc[2]), r0=0.8, r1=3.2, color=V_ICE, a=0.9, strength=2.0, spin=0.2, ease=2.2, fade=1.1, seed=40 + k)
    cine.streaks(83, 8, (hero_c(83)[0], hero_c(83)[1] - 2.0, HERO_Z), (hero_c(90)[0], hero_c(90)[1] + 1.0, HERO_Z), n=14, r0=0.5, r1=1.6, w=0.05, color=V_ICE, seed=12)
    # the axe kick
    p114 = tip(114)
    cine.mesh("pillar", 114, 14, (p114[0], 0.0, p114[2]), r0=1.1, r1=1.1, color=V_MAIN, a=1.0, strength=7.0, height=22.0, dim=0.5, fade=1.0, seed=8)
    cine.mesh("dome", 114, 10, p114, r0=0.6, r1=5.0, color=V_MAIN, a=1.0, strength=5.0, height=0.8, rim=0.6, fill=0.1, ease=3.0, fade=1.2, seed=4)
    cine.slash(108, 8, (p114[0] + 0.4, p114[1] + 1.8, p114[2]), (0.9, 0.1, 0.45), 3.6, -100, 70, 1.6, V_MAIN, V_CORE)
    cine.slash(109, 8, (p114[0] + 0.4, p114[1] + 1.8, p114[2]), (0.9, 0.1, 0.45), 4.9, -110, 60, 0.9, V_CORE, "#ffffff")
    cine.streaks(108, 9, (p114[0], p114[1] + 11.0, p114[2]), (p114[0], p114[1] - 1.0, p114[2]), n=20, r0=1.8, r1=2.2, w=0.07, color=V_CORE, seed=13)
    cine.screen_fx("black", 114, 1)
    cine.screen_fx("bw", 115, 3, seed=9, accent=True, focus=(0.5, 0.45), shards=6, bright=1.8, ink=True, strokes=12, ink_glow=(0.85, 0.25, 1.0))
    # the dummy hits the floor: a glowing crater, a column of light, a dome, a disc of blades, rings, debris, volumetric smoke
    g0 = C.GROUND_HIT
    gp = (gx, 0.05, gz)
    cine.shake(g0, 22, 1.4)
    cine.punch_in(g0, 0.2, 12)
    cine.flash(g0, 3, "#ffffff", 0.5)
    cine.mesh("crater", g0, N - g0 - 1, (gx, 0.0, gz), r0=9.5, r1=9.5, color=V_CORE, edge="#b03cff", a=1.0, strength=7.0, seed=2, branches=18)
    cine.mesh("pillar", g0, 13, (gx, 0.0, gz), r0=1.2, r1=1.2, color=V_MAIN, a=1.0, strength=7.0, height=19.0, dim=1.0, fade=1.0, seed=9)
    cine.mesh("dome", g0, 7, (gx, 0.0, gz), r0=0.8, r1=6.5, color=V_MAIN, a=1.0, strength=2.6, height=0.7, rim=0.5, fill=0.03, ease=3.0, fade=1.8, seed=9)
    cine.mesh("blades", g0, 15, (gx, 0.2, gz), r0=2.0, r1=11.0, color=V_CORE, edge=V_EDGE, a=1.0, strength=7.0, n=16, spin=0.45, rise=0.5, lift=0.3, width=1.2, ease=2.2, fade=0.9, seed=10)
    for k, (r1, dl) in enumerate(((9.0, 0), (13.0, 3), (17.0, 6))):
        cine.mesh("wind", g0 + dl, 16, (gx, 0.15 + 0.1 * k, gz), r0=1.5, r1=r1, color=V_CORE, a=1.0, strength=2.4, spin=0.22, ease=2.4, fade=1.0, seed=11 + k)
    cine.mesh("star", g0, 9, (gx, 1.8, gz), r0=5.0, r1=10.0, color=V_EDGE, a=1.0, strength=14.0, dim=0.8, ease=3.0, fade=1.2, seed=g0)
    cine.mesh("smoke", g0, 90, (gx, 0.8, gz), n=9, r0=2.4, r1=5.0, spread=3.6, color="#7c84ac", a=1.0, rise=3.2, seed=31, fade=1.0)
    for k, (r1, col) in enumerate(((7.5, "#ffffff"), (11.0, V_CORE), (15.0, V_MAIN))):
        cine.ring(g0 + 2 * k, 16 + 3 * k, gp, 0.5, r1, 0.5 - 0.1 * k, 0.04, col, 0.9 - 0.15 * k, 0.0)
    cine.burst_debris(g0, gp, 50, 0.34, 0.6, (0.4, 1.1), ["#40476e", "#565f8a", "#343a5e"], seed=3, g=0.03)
    cine.emit(g0 + 4, N - 1, origin=(gx, 0.3, gz), rate=3.4, vel=(0.03, 0.12), dir=(0, 1, 0), spread=0.9, grav=-0.0012, life=(34, 70), size=(0.16, 0.05), color=(V_CORE, V_EDGE),
              alpha=(1.0, 0.0), add=True, shape="soft", seed=21, radius=2.8)
    # the landing: dust
    hl = hero_c(124)
    cine.ring(124, 12, (hl[0], 0.1, hl[2]), 0.5, 5.0, 0.6, 0.05, V_CORE, 0.8, 0.0)
    cine.mesh("smoke", 124, 40, (hl[0], 0.6, hl[2]), n=3, r0=1.0, r1=2.2, spread=1.4, color="#8c93bc", a=0.9, rise=0.9, seed=5)
    cine.vignette.key(0, 0.2).key(76, 0.2).key(80, 0.42).key(92, 0.2).key(114, 0.2).key(118, 0.45).key(132, 0.25).key(N, 0.3)

    scene = Scene("Dragon Combo", [hero, dummy], fps=C.FPS, cine=cine)
    scene.report = []
    return scene
