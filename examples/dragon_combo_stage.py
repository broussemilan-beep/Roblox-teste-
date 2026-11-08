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
    for (x, z, s) in ((14.5, 4.5, 1.6), (17.5, -6.5, 2.2), (-3.5, 7.5, 1.3), (1.5, -9.5, 1.8)):      # rubble for scale and parallax
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
    cine.shot(47, 54, autoframe(lambda f: [hero_c(f), dum_c(f)], 47, 54, azimuth=-78.0, elevation=7.0, fov=42.0, fill=0.8, min_radius=2.6, follow=0.5, lift=0.5, pad=0.8))     # jab
    cine.shot(54, 61, autoframe(lambda f: [hero_c(f), dum_c(f)], 54, 61, azimuth=-118.0, elevation=5.0, fov=42.0, fill=0.8, min_radius=2.6, follow=0.5, lift=0.5, pad=0.8))   # hook, from the other side
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
    cine.shot(153, 193, dolly((-4.0, 1.7, 3.6), (-8.0, 2.2, 4.6), (8.0, 3.3, HERO_Z), (5.2, 3.4, HERO_Z), fov=44, easing="sine_inout"))                           # he walks toward the lens
    cine.shot(193, N + 1, dolly((-8.0, 2.2, 4.6), (-14.0, 7.5, 8.0), (5.2, 3.4, HERO_Z), (8.0, 2.6, HERO_Z), fov=(44, 38), easing="sine_inout"))                  # the final crane

    # ---------------------------------------------------------------- the hits
    hits = {c["f"]: c for c in C.CONTACTS}
    sizes = {50: 0.8, 57: 0.9, 64: 1.0, 76: 1.5, 90: 0.9, 95: 0.9, 100: 1.1, 114: 1.8}
    for f, c in hits.items():
        p, s = tip(f), sizes[f]
        cine.shake(f, 8 + int(6 * s), 0.35 * s)
        cine.punch_in(f, 0.05 + 0.05 * s, 6)
        cine.mesh("star", f, 9, p, r0=2.0 * s, r1=4.2 * s, color=V_EDGE, a=1.0, strength=12.0, dim=0.6 * s, ease=3.0, fade=1.2)
        cine.ring(f, 10, p, 0.3, 2.4 * s + 1.0, 0.45, 0.05, V_CORE, 0.9, 0.0, n=(0, 0, 1))
    cine.screen_fx("white", 76, 1, alpha=0.5)
    cine.screen_fx("bw", 77, 3, seed=5, accent=True, focus=(0.55, 0.5), shards=5, bright=1.6, ink=True, strokes=10, ink_glow=(0.85, 0.25, 1.0))
    cine.screen_fx("black", 114, 1)
    cine.screen_fx("bw", 115, 3, seed=9, accent=True, focus=(0.5, 0.45), shards=6, bright=1.8, ink=True, strokes=12, ink_glow=(0.85, 0.25, 1.0))

    scene = Scene("Dragon Combo", [hero, dummy], fps=C.FPS, cine=cine)
    scene.report = []
    return scene
