"""Test bench for the 'eyes' (tsb_engine/perception.py): clips made by the engine whose true content is known.

Each segment is 48 frames at 60 fps (24 images at 30 fps) with a hard cut between segments. The classes are the confusions
that matter when reading animation:

* ``ghost_jab``      ONE arm alternates between two extensions on every image while the torso stays put, with streaks/stars:
                     a *multi-hit illusion made by an animation strobe + VFX* (truth: MULTIHIT_VFX)
* ``smear_single``   a single punch drawn with an ink smear (truth: SINGLE_HIT_SMEAR)
* ``real_combo``     four distinct strikes with the body turning between them (truth: REAL_COMBO)
* ``camera_only``    characters hold still, the camera pans / orbits / dollies (truth: CAMERA_MOVE, no pose change)
* ``hard_cut``       static characters, the camera cuts to another angle in the middle (truth: CUT)
* ``held_cycle``     the hero holds one kick pose, the victim cycles 2-4 poses (truth: HELD_HERO_CYCLING_VICTIM)
* ``punctuation``    black frames then white frames (truth: PUNCT_BLACK, PUNCT_WHITE)
* ``vfx_wall``       a wall of huge strokes covering the screen (truth: VFX_WALL)
* ``held_vfx``       no pose change at all, only bursts / streaks / ink (truth: HELD_WITH_VFX)
* ``empty``          nobody on stage (truth: EMPTY)

Every class comes in several seeded variants (sizes, directions, speeds, camera angles) so a detector cannot just memorise one clip.
"""

from __future__ import annotations

import random

from tsb_engine.authoring import K, P, tp
from tsb_engine.cinematic import Cinematic, dolly, orbit
from tsb_engine.model import PARTS, ROOT, Animation, Pose
from tsb_engine.scene import Character, Scene
from tsb_engine.secondary import reference_outfit

SEG = 48
PAD = 40  # frames of calm stance between segments so the coat and hair settle after the reset
STRIDE = SEG + PAD
CLASSES = ["ghost_jab", "smear_single", "real_combo", "camera_only", "hard_cut", "held_cycle", "punctuation", "vfx_wall", "held_vfx", "empty"]
VARIANTS = 3
INK = "#0b0b0f"
HERO_COLORS = {"Torso": "#2b2b34", "Head": "#e9eef2", "Right Arm": "#1d1d25", "Left Arm": "#1d1d25", "Right Leg": "#16161c", "Left Leg": "#16161c"}
DUMMY_COLORS = {k: "#ececf0" for k in HERO_COLORS}

# what the eyes must say about each class (segment-level truth); ``cut`` = expected cut sample index inside the segment
TRUTH = {
    "ghost_jab": {"require": ["MULTIHIT_VFX"], "forbid": ["REAL_COMBO", "SINGLE_HIT_SMEAR", "CAMERA_MOVE"]},
    "smear_single": {"require": ["SINGLE_HIT_SMEAR"], "forbid": ["MULTIHIT_VFX", "REAL_COMBO"]},
    "real_combo": {"require": ["REAL_COMBO"], "forbid": ["MULTIHIT_VFX", "CAMERA_MOVE"]},
    "camera_only": {"require": ["CAMERA_MOVE"], "forbid": ["VICTIM_CYCLING", "MULTIHIT_VFX", "REAL_COMBO", "SINGLE_HIT_SMEAR"]},
    "hard_cut": {"require": ["CUT"], "forbid": ["VICTIM_CYCLING", "MULTIHIT_VFX", "REAL_COMBO"]},
    "held_cycle": {"require": ["VICTIM_CYCLING"], "forbid": ["MULTIHIT_VFX", "REAL_COMBO", "CAMERA_MOVE"]},
    "punctuation": {"require": ["PUNCT_BLACK", "PUNCT_WHITE"], "forbid": ["MULTIHIT_VFX", "REAL_COMBO"]},
    "vfx_wall": {"require": ["VFX_WALL"], "forbid": ["MULTIHIT_VFX", "REAL_COMBO"]},
    "held_vfx": {"require": ["HELD_WITH_VFX"], "forbid": ["VICTIM_CYCLING", "REAL_COMBO", "MULTIHIT_VFX", "CAMERA_MOVE"]},
    "empty": {"require": ["EMPTY"], "forbid": ["MULTIHIT_VFX", "REAL_COMBO", "VICTIM_CYCLING"]},
}

BASE = dict(T=tp(0.0, 0), H=P((0, 0, 0)), RA=P((10, 0, 6)), LA=P((10, 0, -6)), RL=P((0, 0, 3)), LL=P((0, 0, -3)))


def _stand(a: Animation, f: int, easing: str = "linear", **over) -> None:
    keys = dict(BASE)
    keys.update(over)
    K(a, f, easing, **keys)


def _react(da: Animation, t: int, push: float = 0.35, fold: float = -24.0) -> None:
    """The victim folds and is pushed back by ``push`` studs at ``t`` (30 fps sample = 2 frames), then settles."""
    K(da, t, "quad_out", R=P(pos=(0, 0, push)), T=tp(0.0, fold), H=P((-34, 0, 0)), RA=P((-30, 0, 24)), LA=P((-40, 0, -24)))
    K(da, t + 6, "sine_inout", R=P(pos=(0, 0, push * 0.3)), T=tp(0.0, fold * 0.25), H=P((6, 0, 0)), RA=P((20, 0, 12)), LA=P((20, 0, -12)))
    K(da, t + 10, "sine_inout", R=P(pos=(0, 0, 0)), T=tp(0.0, 0), H=P((0, 0, 0)), RA=P((10, 0, 6)), LA=P((10, 0, -6)))


def build(seed: int = 5) -> tuple[Scene, list[dict]]:
    rng = random.Random(seed)
    hero = Character("hero", Animation("hero", fps=60, archetype="cinematic"), base_pos=(0, 0, 0), colors=HERO_COLORS, outfit=reference_outfit(), face="smirk")
    dummy = Character("dummy", Animation("dummy", fps=60, archetype="cinematic"), base_pos=(0, 0, -3.2), base_yaw=180.0, colors=DUMMY_COLORS)
    order = [(c, v) for v in range(VARIANTS) for c in CLASSES]
    rng.shuffle(order)
    n = STRIDE * len(order)
    cine = Cinematic(n)
    cine.aspect = 888 / 362
    cine.sky_color, cine.floor_color = "#8f9cab", "#8c9098"
    cine.shot(0, n - 1, dolly((14, 3.2, -1.6), (14, 3.2, -1.6), (0, 2.6, -1.6), (0, 2.6, -1.6), fov=36))
    ha, da = hero.anim, dummy.anim
    segs: list[dict] = []

    def cam(f0, f1, dist=10.5, h=3.0, fov=34.0, sway=0.0, tz=-1.6):
        cine.shot(f0, f1, dolly((dist, h, tz), (dist - sway, h, tz), (0, 2.6, tz), (0, 2.6, tz), fov=fov))

    for si, (cls, var) in enumerate(order):
        p0 = si * STRIDE
        f0, f1 = p0 + PAD, p0 + PAD + SEG - 1
        r = random.Random(seed * 1000 + si)
        meta = {"class": cls, "variant": var, "f0": f0, "f1": f1, "s0": f0 // 2, "s1": f1 // 2, "p0": p0 // 2, "cut": None}
        # calm stance during the pad (cut camera, nothing happens), then the segment starts from a settled body
        for anim in (ha, da):
            for f in (p0, p0 + 2):
                _stand(anim, f, "constant")
                K(anim, f, "constant", R=P(pos=(0, 0, 0)))
        cam(p0, f0 - 1, 10.5, 3.0, 34.0)
        dist, fov, h = r.uniform(9, 12), r.uniform(30, 38), r.uniform(2.6, 3.4)
        cam(f0, f1, dist, h, fov)
        side = r.choice([-1, 1])  # which arm / direction
        if cls == "ghost_jab":
            arm = "RA" if side > 0 else "LA"
            yaw = -r.uniform(20, 45) * side
            amp = r.uniform(0.9, 1.5)
            for i, f in enumerate(range(f0, f1 + 1, 2)):
                out = i % 2 == 0
                pos = (0.0, 0.0, -amp if out else -0.15)
                rot = (-85 if out else -72, 0, 12 * side + (6 if out else -6))
                keys = {"T": tp(0.0, -6, yaw), arm: Pose(pos, rot)}
                K(ha, f, "constant", **keys)
            for f in range(f0 + 2, f1 - 2, 2):  # a new flash and fan of streaks on every image (30 fps), re-rolled each time
                cine.streaks(f, 2, (0, 3.6, -7.0), (0, 3.6, -3.4), n=10, r0=0.3, r1=1.1, w=0.06, seed=f)
                cine.burst(f, 2, (0, 3.6, -3.3 + 0.05 * ((f // 2) % 3)), 0.2, 1.0 + 0.2 * ((f // 2) % 2), "#f2f2f4", "#ffffff", spikes=9, streaks=4, seed=f, sprite=False)
            for i, f in enumerate(range(f0 + 2, f1 - 2, 2)):  # the victim is shaken by every flash
                K(da, f, "constant", R=P(pos=(0, 0, 0.22 * (1 if i % 2 else -1))), T=tp(0.0, -10 if i % 2 else 4), H=P((-14 if i % 2 else 10, 0, 0)))
        elif cls == "smear_single":
            arm = "RA" if side > 0 else "LA"
            part = "Right Arm" if side > 0 else "Left Arm"
            wind = {"T": tp(0.2, 8, 40 * side), arm: P((20, 0, 20 * side))}
            hit = {"T": tp(0.0, -10, -30 * side), arm: P((-88, 0, 10 * side))}
            _stand(ha, f0 + 1, "linear", **wind)
            _stand(ha, f0 + 18, "quad_in", **wind)
            _stand(ha, f0 + 22, "linear", **hit)
            _stand(ha, f0 + 34, "sine_inout", **hit)
            _stand(ha, f1, "constant")
            cine.ink_trail(f0 + 20, f0 + 34, 0, part, (0, -1.0, 0), 10, 3.4, 0.0, INK, rag=0.4, seed=si, alpha=1.0)
            _react(da, f0 + 22)
            cine.burst(f0 + 22, 10, (0, 3.6, -3.3), 0.2, 1.6, "#f2f2f4", "#ffffff", spikes=11, streaks=5, seed=si)
            cine.streaks(f0 + 22, 8, (0, 3.6, -6.5), (0, 3.6, -3.4), n=10, r0=0.3, r1=1.1, w=0.06, seed=si)
        elif cls == "real_combo":
            seq = [
                ("RA", dict(T=tp(0.0, -8, -45), RA=P((-88, 0, 10)), LA=P((30, 0, -20))), 0),
                ("LA", dict(T=tp(0.0, -8, 45), LA=P((-88, 0, -10)), RA=P((30, 0, 20))), 12),
                ("RL", dict(T=tp(0.4, 14, -10), RL=P((95, 0, 4)), RA=P((-30, 0, 40)), LA=P((60, 0, -30))), 24),
                ("LA", dict(T=tp(0.2, -4, 60), LA=P((-30, 0, -80)), RA=P((20, 0, 30))), 36),
            ]
            for name, keys, off in seq:
                _stand(ha, f0 + off, "quad_in", **{k: v for k, v in keys.items()})
            _stand(ha, f0 + 46, "linear")
            _stand(ha, f1, "constant")
            for off in (6, 18, 30, 42):
                _react(da, f0 + off, push=0.3 + 0.1 * (off % 3))
                cine.burst(f0 + off, 6, (0, 3.6, -3.3), 0.2, 1.1, "#f2f2f4", "#ffffff", spikes=9, streaks=3, seed=si * 7 + off)
        elif cls == "camera_only":
            kind = r.choice(["pan", "orbit", "dolly"])
            for f in range(f0, f1 + 1, 6):  # a tiny breathing so nothing is mathematically frozen
                _stand(ha, f, "sine_inout", H=P((2 * ((f // 6) % 2), 0, 0)))
            if kind == "pan":
                cine.shot(f0, f1, dolly((14, 3.2, -1.0 * side), (14, 3.2, -1.0 * side - 3.2 * side), (0, 2.6, -1.0 * side), (0, 2.6, -1.0 * side - 3.2 * side), fov=fov))
            elif kind == "orbit":
                cine.shot(f0, f1, orbit((0, 2.6, -1.6), dist, 60, 110, h, h + 0.5, fov=fov) if side > 0 else orbit((0, 2.6, -1.6), dist, 115, 65, h, h + 0.5, fov=fov))
            else:
                cine.shot(f0, f1, dolly((dist + 3, h, -1.6), (dist - 5, h, -1.6), (0, 2.6, -1.6), (0, 2.6, -1.6), fov=fov))
            meta["kind"] = kind
        elif cls == "hard_cut":
            mid = f0 + SEG // 2
            cam(f0, mid - 1, 10.5, 3.0, 34.0)
            cine.shot(mid, f1, dolly((-6.0, 6.0, 5.5), (-6.0, 6.0, 5.5), (0, 2.4, -2.0), (0, 2.4, -2.0), fov=44))
            for f in range(f0, f1 + 1, 6):
                _stand(ha, f, "sine_inout", H=P((2 * ((f // 6) % 2), 0, 0)))
            meta["cut"] = (SEG // 2) // 2  # sample index inside the segment
        elif cls == "held_cycle":
            kick = dict(T=tp(0.3, -18, 0), H=P((8, 0, 0)), RA=P((-70, 0, 20)), LA=P((75, 0, -10)), RL=P((100, 0, 4)), LL=P((-6, 0, -4)))
            for f in range(f0, f1 + 1, 16):  # a hold that is not mathematically frozen
                _stand(ha, f, "sine_inout", **kick)
            ncyc = r.choice([2, 3, 4])
            poses = [((-38, 0, 0), 2.0, 0), ((150, 0, 0), 2.7, -30), ((-92, 0, 0), 1.2, 0), ((42, 0, 0), 2.3, 6)][:ncyc]
            for i, f in enumerate(range(f0, f1 + 1, 4)):
                rot, hh, fold = poses[i % ncyc]
                K(da, f, "constant", R=P(rot, (0, hh, -0.4)), T=tp(0.0, fold), RA=P((40, 0, 18)), LA=P((30, 0, -18)))
            for f in range(f0 + 4, f1, 14):
                cine.ink_arc(f, 24, (0, 3.8, -3.2), (1, 0.1, 0.1), 3.0, -140, -20, 0.8, INK, rag=0.5, seed=f, grow=4, alpha=0.5)
        elif cls == "punctuation":
            for f in range(f0, f1 + 1, 6):
                _stand(ha, f, "sine_inout", H=P((2 * ((f // 6) % 2), 0, 0)))
            cine.screen_fx("black", f0 + 16, 4)
            cine.screen_fx("white", f0 + 26, 4)
        elif cls == "vfx_wall":
            for f in range(f0, f1 + 1, 6):
                _stand(ha, f, "sine_inout", H=P((2 * ((f // 6) % 2), 0, 0)))
            cine.screen_fx("strokes", f0 + 8, 30, n0=r.choice([9, 11, 13]), n1=r.choice([4, 6]), w=r.uniform(0.2, 0.28), glow="#8ff3ff", seed=si, layouts=5)
        elif cls == "held_vfx":
            for f in range(f0, f1 + 1, 6):
                _stand(ha, f, "sine_inout", H=P((2 * ((f // 6) % 2), 0, 0)))
            for f in range(f0 + 4, f1 - 6, 10):
                cine.burst(f, 8, (0, 3.6 + r.uniform(-0.5, 0.5), -3.0), 0.2, r.uniform(1.4, 2.0), "#f2f2f4", "#ffffff", spikes=11, streaks=5, seed=f)
                cine.streaks(f, 6, (0, 3.6, -6.5), (0, 3.6, -3.2), n=12, r0=0.3, r1=1.2, w=0.06, seed=f)
                cine.ink_arc(f, 20, (0, 3.6, -1.6), (1, 0.1, 0.1), 3.2, -150, -20, 1.0, INK, rag=0.5, seed=f, grow=4, alpha=0.9)
        elif cls == "empty":
            K(ha, f0, "linear", R=P(pos=(0, 0, 80)))
            K(da, f0, "linear", R=P(pos=(80, 0, 0)))
        for anim in (ha, da):  # hold the last pose of the segment (constant) so nothing glides into the next one
            for part in (*PARTS, ROOT):
                anim.set_key(part, f1, anim.sample_part(part, f1), "constant")
        segs.append(meta)
    return Scene("Eyes bench", [hero, dummy], cine=cine, hold=1), segs
