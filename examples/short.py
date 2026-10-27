"""A ~11 s monochrome combat short, built with the techniques measured in docs/research/reference-analysis.md.

Original choreography; the *craft* follows the reference study: pace as contrast (bursts vs holds), the dash is
hidden behind ink slices + an empty-stage blink, strikes enter on their most extreme pose with ink smears, a pose-cycle
juggle, manga impact frames and black frames as punctuation, an acting beat, a slash storm and secondary motion
(hat, hair, coat) that never stops. Authored at 60 fps and shown on a 30 fps clock (``Scene.hold = 2``).

World: the hero starts at z = +2 and faces -Z; the dummy stands at z = -9 facing him. The side camera sits on +X so
screen-right is -Z.
"""

from __future__ import annotations

import math
import random

from tsb_engine.authoring import K, P, keep_above_ground, point_world, tp, tremble
from tsb_engine.cinematic import Cinematic, dolly, orbit, tracking
from tsb_engine.footwork import bake_footwork
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene
from tsb_engine.secondary import coat_and_hair

N_FRAMES = 660
HERO_Z, DUMMY_Z = 2.0, -9.0
INK = "#0b0b0f"
HERO_COLORS = {"Torso": "#17171d", "Head": "#e6ebf0", "Right Arm": "#0e0e12", "Left Arm": "#0e0e12", "Right Leg": "#0a0a0d", "Left Leg": "#0a0a0d"}
DUMMY_COLORS = {k: "#ececf0" for k in HERO_COLORS}
CYAN = "#7ff0ff"


def hero_anim(a: Animation) -> None:
    # ---- B1 (0-48): crouched, gathering; the coat and hair keep moving by themselves
    K(a, 0, T=tp(0.75, -32, 0), H=P((26, 0, 0)), RA=P((26, 0, 12)), LA=P((-24, 0, -12)))
    K(a, 22, "sine_inout", T=tp(0.85, -36, 6), H=P((30, 0, 0)), RA=P((30, 0, 14)), LA=P((-28, 0, -14)))
    K(a, 40, "quad_in", T=tp(0.98, -40, 30), H=P((34, 0, 0)), RA=P((-52, 0, 18)), LA=P((74, 0, -16)))
    K(a, 49, "linear", T=tp(0.98, -40, 30), H=P((34, 0, 0)), RA=P((-56, 0, 18)), LA=P((78, 0, -16)))
    tremble(a, "T", 0, 40, 0.9, 0.0, 3)
    tremble(a, "RA", 1, 41, 2.0, 0.02, 3)
    bake_footwork(a, {"Right Leg": (1.5, 0.3), "Left Leg": (-1.5, 0.3)}, [], 0, 49)

    # ---- B2 (50-61): the hero leaves the stage (never show the travel)
    K(a, 50, "linear", R=P(pos=(0, 0, 0)))
    K(a, 51, "linear", R=P(pos=(0, 0, 60)))
    K(a, 61, "linear", R=P(pos=(0, 0, 60)))

    # ---- B3 (62-97): he re-enters directly on contact 1: body flat, leg driving into the dummy's chest
    K(a, 62, "linear", R=P((-82, 0, 0), (0, 1.55, -7.0)), T=tp(0.0, -6, 0), H=P((60, 0, 0)), RA=P((-60, 0, 24)), LA=P((120, 0, -22)),
      RL=P((176, 0, 4)), LL=P((-30, 0, -6)))
    K(a, 68, "cubic_out", R=P((-82, 0, 0), (0, 1.55, -7.8)), RL=P((176, 0, 4)))
    K(a, 80, "quad_in", R=P((-40, 0, 0), (0, 1.1, -10.5)), T=tp(0.2, -14, 0), RA=P((20, 0, 20)), LA=P((60, 0, -20)), RL=P((70, 0, 4)), LL=P((20, 0, -6)))
    # ---- B4 (98-150): three more contacts, each entered on its most extreme pose
    K(a, 92, "linear", R=P((-20, 0, 0), (0, 0.5, -15.0)), T=tp(0.6, -30, 0), RL=P((40, 0, 4)), LL=P((-20, 0, -6)))
    # C2 (104): spin heel kick (yaw passes 90 deg at contact so the leg points -Z)
    for f, ry in ((98, -200), (100, -110), (102, 0), (104, 90), (106, 170), (108, 250)):
        K(a, f, "linear", R=P((0, ry, 0), (0, 0.4, -19.2 + (f - 104) * 0.05)), T=tp(0.2, 0, 0, 18), H=P((10, 0, 0)), RA=P((0, 0, 110)), LA=P((0, 0, -70)),
          RL=P((10, 0, 100 if f >= 102 else 60)), LL=P((0, 0, -4)))
    K(a, 112, "linear", R=P((0, 270, 0), (0, 0.3, -21.0)), T=tp(0.5, -25, 0), RL=P((30, 0, 4)), LL=P((-10, 0, -6)), RA=P((30, 0, 10)), LA=P((30, 0, -10)))
    # C3 (122): cartwheel along the travel axis, hand strikes as it passes under the dummy
    for f, rz, z, y in ((114, 0, -21.6, 0.0), (117, 40, -22.4, 0.9), (120, 80, -23.2, 1.7), (122, 100, -23.5, 1.8), (125, 150, -24.2, 1.2), (128, 190, -25.0, 0.3)):
        K(a, f, "linear", R=P((0, 90, rz), (0, y, z)), T=tp(0.0, 0, 0), H=P((0, 0, 0)), RA=P((0, 0, 170)), LA=P((0, 0, 165)), RL=P((0, 0, 35)), LL=P((0, 0, -35)))
    # C4 (138): slide kick from the ground, then he rises
    K(a, 132, "linear", R=P((0, 0, 0), (0, 0.0, -25.0)), T=tp(0.9, -30, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    K(a, 138, "cubic_out", R=P((60, 0, 0), (0, -1.0, -25.6)), T=tp(0.0, -10, 0), H=P((-20, 0, 0)), RA=P((60, 0, 20)), LA=P((100, 0, -30)), RL=P((80, 0, 3)), LL=P((-10, 0, -3)))
    K(a, 150, "quad_out", R=P((0, 0, 0), (0, 0.0, -26.6)), T=tp(0.8, -30, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))


def dpos(wx: float, h: float, wz: float) -> tuple[float, float, float]:
    """Dummy Root offset (local frame, base yaw 180) that puts its torso centre at world (wx, h, wz)."""
    return (-wx, h - 3.0, DUMMY_Z - wz)


def fly(a: Animation, f0: int, f1: int, p0, p1, apex: float, r0, r1, step: int = 2) -> None:
    """Rigid flight of the dummy between two world points (x, h, z) with a parabolic arc and a steady tumble."""
    for f in range(f0, f1 + 1, step):
        u = (f - f0) / (f1 - f0)
        pos = tuple(p0[i] + (p1[i] - p0[i]) * u for i in range(3))
        h = pos[1] + 4.0 * apex * u * (1.0 - u)
        rot = tuple(r0[i] + (r1[i] - r0[i]) * u for i in range(3))
        K(a, f, "linear", R=P(rot, dpos(pos[0], h, pos[2])))


def stiff(a: Animation, f: int, arms=(30, 30), legs=(0, 0), tilt=8) -> None:
    K(a, f, "linear", T=tp(0.0, tilt), RA=P((arms[0], 0, 10)), LA=P((arms[1], 0, -10)), RL=P((legs[0], 0, 3)), LL=P((legs[1], 0, -3)))


def dummy_anim(a: Animation) -> None:
    K(a, 0, T=tp(0.0, 0), H=P((0, 0, 0)), RA=P((8, 0, 4)), LA=P((8, 0, -4)))
    K(a, 61, "linear", R=P(pos=(0, 0, 0)), T=tp(0.0, 0))
    # C1 (62): struck in the chest: a stiff board launched diagonally
    stiff(a, 62)
    fly(a, 62, 104, (0, 3.0, -9.0), (0, 4.4, -19.0), 3.4, (0, 0, 0), (-250, 0, 0))
    # C2 (104): spin heel kick: sent back up and over
    fly(a, 106, 122, (0, 4.4, -19.4), (0, 3.4, -23.0), 2.6, (-250, 0, 0), (-400, 0, 0))
    # C3 (122): cartwheel strike: popped straight up
    fly(a, 124, 138, (0, 3.4, -23.2), (0, 3.1, -23.4), 3.2, (-400, 0, 0), (-480, 0, 0))
    # C4 (138): slide kick under him: launched vertically
    fly(a, 140, 150, (0, 3.1, -23.6), (0, 9.5, -24.6), 0.0, (-480, 0, 0), (-640, 0, 0))


KICK_A = dict(T=tp(0.3, -10, 0, -8), H=P((10, 0, 0)), RL=P((112, 0, 4)), LL=P((-14, 0, -4)), RA=P((-50, 0, 20)), LA=P((62, 0, -20)))
KICK_B = dict(T=tp(0.3, -8, 0, 8), H=P((10, 0, 0)), LL=P((104, 0, -4)), RL=P((-12, 0, 4)), LA=P((-50, 0, -20)), RA=P((62, 0, 20)))


def hero_late(a: Animation) -> None:
    # ---- B5 (150-176): off-screen run-in while the camera is on a macro
    K(a, 156, "linear", R=P((0, 0, 0), (0, 0.0, -30.0)), T=tp(0.8, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    # ---- B6 (176-256): juggle: two kick poses alternate every 4 frames, he barely travels
    for i, f in enumerate(range(176, 256, 4)):
        K(a, f, "linear", R=P((0, 0, 0), (0, 0.0, -32.0 - 0.02 * (f - 176))), **(KICK_A if i % 2 == 0 else KICK_B))
    # ---- B7 (256-300): the finisher: flying kick that sends him sliding across the ground
    K(a, 256, "linear", R=P((-20, 0, 0), (0, 0.3, -34.0)), T=tp(0.6, -28, 0), RL=P((60, 0, 4)), LL=P((-20, 0, -4)), RA=P((-40, 0, 20)), LA=P((60, 0, -20)))
    K(a, 262, "cubic_out", R=P((-82, 0, 0), (0, 1.0, -38.0)), T=tp(0.0, -6, 0), H=P((60, 0, 0)), RA=P((-60, 0, 24)), LA=P((120, 0, -22)), RL=P((176, 0, 4)), LL=P((-30, 0, -6)))
    K(a, 272, "quad_out", R=P((-30, 0, 0), (0, 0.4, -41.0)), T=tp(0.4, -20, 0), RL=P((60, 0, 4)), LL=P((10, 0, -6)))
    K(a, 284, "quad_out", R=P((0, 0, 0), (0, 0.0, -41.0)), T=tp(0.9, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    # ---- B8 (300-340): lull: he slides back to the frame edge and coils (anticipation)
    K(a, 300, "linear", R=P((0, 0, 0), (0, 0.0, -41.0)), T=tp(0.9, -32, 0), RA=P((30, 0, 10)), LA=P((30, 0, -10)))
    K(a, 318, "sine_inout", R=P((0, 0, 0), (0, 0.0, -36.0)), T=tp(1.05, -38, 18), H=P((34, 0, 0)), RA=P((-30, 0, 16)), LA=P((60, 0, -16)), RL=P((40, 0, 4)), LL=P((-10, 0, -4)))
    K(a, 338, "quad_in", R=P((0, 0, 0), (0, 0.0, -35.0)), T=tp(1.1, -40, 26), H=P((36, 0, 0)), RA=P((-52, 0, 18)), LA=P((78, 0, -16)), RL=P((40, 0, 4)), LL=P((-10, 0, -4)))
    # ---- B9 (340-376): turns to the camera: impact frame, then the smirk (hand on the hat brim)
    K(a, 340, "linear", R=P((0, -90, 0), (0, 0.0, -35.0)), T=tp(0.1, 4, 0), H=P((-6, 0, 0)), RA=P((150, 0, 22)), LA=P((10, 0, -10)), RL=P((0, 0, 4)), LL=P((0, 0, -4)))
    K(a, 376, "sine_inout", R=P((0, -90, 0), (0, 0.0, -35.0)), T=tp(0.1, 6, 0), H=P((-10, 8, 4)), RA=P((158, 0, 22)), LA=P((10, 0, -10)))
    # ---- B10 (376-400): leaps skyward
    K(a, 384, "cubic_out", R=P((-10, 0, 0), (0, 2.5, -36.0)), T=tp(0.5, -30, 0), RA=P((-30, 0, 20)), LA=P((-30, 0, -20)), RL=P((30, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 400, "linear", R=P((-20, 0, 0), (0, 15.0, -40.0)), T=tp(0.2, -14, 0), H=P((20, 0, 0)), RA=P((120, 0, 30)), LA=P((-40, 0, -30)), RL=P((60, 0, 4)), LL=P((-20, 0, -4)))
    K(a, 436, "sine_inout", R=P((-26, 0, 0), (0, 15.6, -40.0)), T=tp(0.2, -18, 0), H=P((24, 0, 0)), RA=P((136, 0, 26)), LA=P((-52, 0, -24)), RL=P((70, 0, 4)), LL=P((-28, 0, -4)))
    K(a, 470, "sine_inout", R=P((-30, 0, 0), (0, 16.0, -40.0)), T=tp(0.2, -22, 0), H=P((26, 0, 0)), RA=P((146, 0, 22)), LA=P((-60, 0, -20)), RL=P((76, 0, 4)), LL=P((-32, 0, -4)))
    # ---- B12 (470-660): back on the ground, hat macro, crouched over the fallen dummy
    K(a, 478, "cubic_in", R=P((0, 0, 0), (0, 0.0, -41.0)), T=tp(0.8, -30, 0), H=P((30, 0, 0)), RA=P((30, 0, 10)), LA=P((30, 0, -10)), RL=P((30, 0, 4)), LL=P((30, 0, -4)))
    K(a, 520, "sine_inout", R=P((0, 0, 0), (0, 0.0, -41.0)), T=tp(0.95, -36, 10), H=P((38, 0, 0)), RA=P((30, 0, 10)), LA=P((60, 0, -10)))
    K(a, 660, "sine_inout", R=P((0, 0, 0), (0, 0.0, -41.0)), T=tp(1.0, -38, 14), H=P((36, 0, 0)), RA=P((26, 0, 10)), LA=P((64, 0, -12)))
    bake_footwork(a, {"Right Leg": (1.5, -41.0 + 0.3), "Left Leg": (-1.5, -41.0 + 0.3)}, [], 478, 660)


def dummy_late(a: Animation) -> None:
    # B5/B6: launched by C4, he is juggled in place around z = -33: three poses cycle every 4 frames
    fly(a, 150, 172, (0, 9.5, -24.6), (0, 4.6, -33.0), 2.0, (-640, 0, 0), (-720, 0, 0))
    cyc = [((0, 0, 0), 4.4, -33.0), ((-62, 0, 0), 3.8, -33.8), ((-22, 0, 0), 4.1, -33.3)]
    for i, f in enumerate(range(174, 256, 4)):
        rot, h, z = cyc[i % 3]
        K(a, f, "linear", R=P(rot, dpos(0, h + 0.12 * math.sin(i * 0.9), z)))
        stiff(a, f, arms=(40, 40), tilt=6)
    # B7: the finisher sends him horizontally across the ground
    fly(a, 258, 276, (0, 4.4, -33.4), (0, 1.0, -46.0), 0.6, (0, 0, 0), (-90, 0, 0))
    fly(a, 278, 296, (0, 1.0, -46.0), (0, 0.8, -52.0), 0.0, (-90, 0, 0), (-90, 0, 0))
    # B8: lies there, then falls out of the sky near the camera's right edge
    K(a, 300, "linear", R=P((-90, 0, 0), dpos(0, 0.8, -52.0)))
    K(a, 322, "linear", R=P((-90, 0, 0), dpos(0, 0.8, -52.0)))
    # B10/B11: he is up in the sky, tumbling, where the slash storm eats him
    fly(a, 330, 400, (0, 40.0, -42.0), (0, 18.0, -40.0), 0.0, (0, 0, 0), (-360, 0, 0))
    fly(a, 402, 470, (0, 18.0, -40.0), (0, 14.0, -40.0), 0.0, (-360, 0, 0), (-540, 0, 0))
    # B12: crashes down and lies face up next to the hero
    fly(a, 472, 482, (0, 14.0, -40.0), (0, 0.8, -44.2), 0.0, (-540, 0, 0), (-630, 0, 0))
    K(a, 660, "linear", R=P((-630, 0, 0), dpos(0, 0.8, -44.2)))


def shift_root_z(a: Animation, from_frame: int, dz: float) -> None:
    from tsb_engine.model import ROOT, Key, Pose

    a.tracks[ROOT] = [Key(k.frame, Pose((k.pose.pos[0], k.pose.pos[1], k.pose.pos[2] + dz), k.pose.rot), k.easing) if k.frame >= from_frame else k
                      for k in a.tracks[ROOT]]


def char_point(char: Character, part: str, off=(0.0, 0.0, 0.0)):
    from tsb_engine.kinematics import apply

    return lambda f: apply(char.world_parts(int(f))[part], off)


def build(n_frames: int = N_FRAMES) -> Scene:
    hero = Character("hero", Animation("hero", fps=60, archetype="cinematic"), base_pos=(0, 0, HERO_Z), colors=HERO_COLORS, outfit=coat_and_hair(), face="smirk")
    dummy = Character("dummy", Animation("dummy", fps=60, archetype="cinematic"), base_pos=(0, 0, DUMMY_Z), base_yaw=180.0, colors=DUMMY_COLORS)
    hero_anim(hero.anim)
    hero_late(hero.anim)
    shift_root_z(hero.anim, 156, -HERO_Z)  # late beats were authored in world z
    dummy_anim(dummy.anim)
    dummy_late(dummy.anim)
    for ch in (hero, dummy):  # no part below the floor (linter TSB001)
        keep_above_ground(ch, range(n_frames))
    cine = Cinematic(n_frames)
    cine.sky_color, cine.floor_color = "#7d8794", "#8c9098"
    cine.shot(0, n_frames, dolly((15, 3.4, -3.5), (15, 3.4, -3.5), (0, 1.9, -3.5), (0, 1.9, -3.5), fov=44))  # fallback
    cine.bars.key(0, 0.05)

    # B2: three ink slices on the hero, then nothing
    cine.slices(46, 5, (0, 2.0, HERO_Z), 3, h=4.0, w=0.2, spread=0.55, seed=1)
    cine.ink_path(50, 8, [(0, 0.2, HERO_Z + 0.4), (0, 2.6, HERO_Z + 0.4), (0, 5.2, HERO_Z + 0.4)], 0.18, INK, rag=0.2, seed=2, grow=2)
    # B3 / B4 contacts: (frame, point on the dummy) -> ink on the striking limb, star, speed streaks, shake
    def hit(t, part, star, k, torso=True):
        cine.ink_trail(t, t + 14, 0, part, (0, -1.0, 0), 12, 2.0, 0.0, INK, rag=0.4, seed=10 + k, alpha=0.85)
        if torso:
            cine.ink_trail(t, t + 12, 0, "Torso", (0, 0, 0), 10, 1.5, 0.0, INK, rag=0.45, seed=20 + k, alpha=0.5)
        cine.streaks(t, 12, (0, star[1], star[2] + 5.0), (0, star[1], star[2] + 0.5), n=14, r0=0.4, r1=1.6, w=0.07, seed=30 + k)
        cine.burst(t + 1, 12, star, 0.3, 3.2, "#f2f2f4", "#ffffff", spikes=11, streaks=6, seed=40 + k)
        for j in range(2):  # thin white wind arcs around the contact
            cine.ink_arc(t + 1 + j, 10, (star[0], star[1], star[2]), (1, 0, 0.05), 2.4 + 1.1 * j, -60 + 70 * j, 130 + 60 * j, 0.14, "#ffffff", rag=0.1, seed=50 + k + j, grow=4, alpha=0.6)
        cine.shake(t, 8, 0.15)
    hit(62, "Right Leg", (0, 3.0, DUMMY_Z + 0.4), 1)
    hit(104, "Right Leg", (0, 4.4, -19.2), 2)
    hit(122, "Right Arm", (0, 3.4, -23.4), 3)
    hit(138, "Right Leg", (0, 3.1, -24.2), 4)
    cine.shot(0, 61, dolly((15, 3.4, -3.5), (15, 3.4, -3.5), (0, 1.9, -3.5), (0, 1.9, -3.5), fov=44))
    cine.shot(62, 97, dolly((15, 3.6, -6), (15, 3.6, -11), (0, 2.6, -6), (0, 2.8, -11), fov=44, easing="sine_inout"))
    cine.shot(98, 149, dolly((15, 3.6, -15), (15, 3.4, -24), (0, 2.8, -15), (0, 2.6, -24), fov=44, easing="sine_inout"))
    cine.shot(150, n_frames - 1, dolly((15, 3.4, -26), (15, 3.4, -26), (0, 2.4, -26), (0, 2.4, -26), fov=44))
    # ---------------- B5 (150-175): whip-in macro on the coat, ragged white spikes for two frames
    cine.screen_fx("burst", 150, 3, seed=7)
    cine.shot(150, 175, tracking(char_point(hero, "Head"), (2.6, 0.2, -1.0), look_dy=0.0, fov=(26, 23), offset_end=(2.3, 0.2, -0.9)))
    cine.hand.key(150, 0.0)
    # ---------------- B6 (176-255): ground-level juggle: stars + persistent ink swirls, camera tilted
    cine.shot(176, 255, dolly((13, 0.5, -31.2), (13.6, 0.6, -32.0), (0, 3.2, -32.6), (0, 3.2, -32.6), fov=48, roll=(-4.0, 3.0), easing="sine_inout"))
    rng = random.Random(9)
    for i, f in enumerate(range(178, 254, 12)):
        cine.burst(f, 8, (0, 3.9, -33.6), 0.3, 2.3, "#f2f2f4", "#ffffff", spikes=10, streaks=5, seed=60 + i)
        cine.ink_arc(f, 26, (0, 3.9, -33.4), (1, 0.15, 0.1), 3.2 + 0.5 * (i % 2), rng.uniform(-90, 0), rng.uniform(150, 230), 0.8, INK, rag=0.5, seed=70 + i, grow=5, alpha=0.5)
        cine.streaks(f, 6, (0, 3.9, -31.0), (0, 3.9, -33.4), n=8, r0=0.3, r1=1.0, w=0.06, seed=80 + i)
        cine.shake(f, 6, 0.1)
    # ---------------- B7 (256-299): finisher: contact, a long ink streak along the ground, dust
    hit(262, "Right Leg", (0, 4.4, -35.4), 5, torso=False)
    cine.ink_path(264, 40, [(0, 0.5, -35.0), (0, 0.5, -42.0), (0, 0.5, -52.0)], 1.0, INK, rag=0.5, seed=90, grow=6, alpha=0.95)
    cine.burst(270, 12, (0, 1.4, -46.0), 0.3, 3.2, "#f2f2f4", "#ffffff", spikes=12, streaks=6, seed=91)
    cine.emit(270, 270, origin=(0, 0.5, -46.0), rate=0, burst=26, vel=(0.08, 0.3), dir=(0, 0.5, -1), spread=1.0, grav=0.004, drag=0.05, life=(24, 60),
              size=(1.0, 2.6), color=("#c9ccd2", "#8a8f99"), alpha=(0.7, 0.0), add=False, shape="smoke", radius=0.8, seed=92)
    cine.shot(256, 299, dolly((16, 1.8, -36), (16, 1.5, -46), (0, 1.8, -38), (0, 1.4, -48), fov=42, easing="sine_inout"))
    # ---------------- B8 (300-339): lull, static wide, a hint of handheld
    cine.shot(300, 339, dolly((16, 3.0, -42), (16, 3.0, -41), (0, 1.8, -42), (0, 1.8, -41), fov=44))
    cine.hand.key(300, 0.02).key(339, 0.02)
    # ---------------- B9 (340-375): manga impact frame, then the smirk with a speech bubble
    cine.shot(340, 347, dolly((8, 3.6, -35), (7, 3.6, -35), (0, 3.4, -35), (0, 3.4, -35), fov=(42, 38)))
    cine.screen_fx("bw", 340, 8, seed=11, accent=True, focus=(0.5, 0.45), shards=18)
    cine.shot(348, 375, dolly((4.8, 5.0, -35.0), (4.2, 5.0, -35.0), (0, 4.8, -35), (0, 4.8, -35), fov=(34, 30), easing="linear"))
    cine.screen_fx("bubble", 352, 24, focus=(0.7, 0.22))
    # ---------------- B10 (376-399): the leap, camera looks up at the sky
    cine.shot(376, 399, tracking(char_point(hero, "Torso"), (13, -3, 0), look_dy=2.5, fov=(44, 48)))
    cine.streaks(384, 14, (0, 2.0, -36), (0, 14.0, -40), n=10, r0=0.5, r1=1.4, w=0.07, seed=95)
    cine.sky_color = "#7d8794"
    # ---------------- B11 (400-483): the slash storm: white strokes with a cyan glow, re-posed every frame
    cine.shot(400, 483, dolly((14, 12.0, -40), (14, 12.0, -40), (0, 15.5, -40), (0, 15.5, -40), fov=44))
    pos, tgt, _fov, _roll = cine.camera_state(420)
    fwd = tuple(tgt[i] - pos[i] for i in range(3))
    fl = math.sqrt(sum(x * x for x in fwd))
    fwd = tuple(x / fl for x in fwd)
    right = (fwd[1] * 0.0 - fwd[2] * 1.0, fwd[2] * 0.0 - fwd[0] * 0.0, fwd[0] * 1.0 - fwd[1] * 0.0)  # fwd x up(0,1,0) -> (-fz, 0, fx)
    right = (-fwd[2], 0.0, fwd[0])
    rl = math.sqrt(sum(x * x for x in right))
    right = tuple(x / rl for x in right)
    up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
    plane = tuple(pos[i] + fwd[i] * 9.0 for i in range(3))
    rs = random.Random(21)
    for f in range(400, 484, 2):
        amount = 7 if f < 458 else max(0, 7 - (f - 458) // 4)
        for k in range(amount):
            th = rs.uniform(0, math.pi)
            off = rs.uniform(-3.2, 3.2)
            ln = rs.uniform(9.0, 13.0)
            ca, sa = math.cos(th), math.sin(th)
            mids = []
            for j in range(5):
                t = (j / 4 - 0.5) * 2 * ln
                bend = 0.8 * math.sin(j / 4 * math.pi) * rs.uniform(-1, 1)
                x = ca * t - sa * (off + bend)
                y = sa * t + ca * (off + bend)
                mids.append(tuple(plane[i] + right[i] * x * 1.15 + up[i] * y for i in range(3)))
            cine.ink_path(f, 3, mids, rs.uniform(0.22, 0.55), "#ffffff", glow=CYAN, rag=0.3, seed=rs.randint(1, 9999), grow=1, alpha=0.97)
    cine.flash(466, 6, "#ffffff", 1.0)
    # ---------------- B12 (484-659): crash, hat macro, blink rhythm, final hold
    cine.emit(482, 484, origin=(0, 0.5, -44.2), rate=0, burst=30, vel=(0.1, 0.35), dir=(0, 0.5, 1), spread=1.0, grav=0.004, drag=0.05, life=(26, 70),
              size=(1.0, 2.8), color=("#c9ccd2", "#8a8f99"), alpha=(0.7, 0.0), add=False, shape="smoke", radius=0.8, seed=96)
    cine.shot(485, 499, tracking(char_point(hero, "Head"), (3.2, 0.3, 0.9), look_dy=0.0, fov=(30, 27), offset_end=(2.8, 0.35, 0.8)))
    cine.screen_fx("burst", 500, 4, seed=13)
    cine.screen_fx("black", 504, 4)
    cine.screen_fx("glint", 508, 2, focus=(0.5, 0.5))
    cine.shot(500, 549, dolly((7.5, 1.7, -42.6), (6.0, 1.5, -42.6), (0, 1.5, -42.6), (0, 1.4, -42.6), fov=(40, 34), easing="sine_inout"))
    cine.screen_fx("black", 550, 6)
    cine.screen_fx("bw", 556, 6, seed=17, accent=True, focus=(0.55, 0.5), shards=14)
    cine.shot(556, n_frames - 1, dolly((6.4, 1.8, -42.6), (4.6, 1.5, -42.6), (0, 1.6, -42.6), (0, 1.3, -42.6), fov=(40, 31), easing="sine_inout"))
    cine.bright.key(0, 1.0).key(n_frames - 14, 1.0).key(n_frames - 1, 0.0, "quad_in")
    cine.hand.key(484, 0.015).key(n_frames - 1, 0.015)
    sc = Scene("Duel (court métrage)", [hero, dummy], cine=cine, hold=2)
    sc.markers = [{"f": 0, "label": "anticipation", "act": True}, {"f": 50, "label": "blink"}, {"f": 62, "label": "contact"}]
    return sc
