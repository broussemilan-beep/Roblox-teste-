"""« VFX Practice Day2 » - a reproduction of a TikTok Roblox Studio VFX test (screen recording, 5 s loop of one combo, fixed Studio camera).

What the reference is (read frame by frame, docs/research/reference-analysis-3.md): the classic R6 *face test* dummy - every face of every part painted (FRONT red, BACK blue,
RIGHT green, LEFT orange, TOP light blue, BOTTOM yellow, light round head) - doing one combo from the left of the picture to the right: stand, charge (violet aura), crouched dash with a
grey dust trail, a spin with thin white arcs, a jump, a slam with a magenta shock-ring stack, a violet beam, a roll and a stand. The camera never moves (Studio default FOV 70, pitched
down ~28 degrees, ~27 studs away).

**The animation is copied, not invented**: ``tools/copy_poses_color.py`` fitted the rig's 16 joint angles + position to the colour map of every image
(``docs/research/reference-poses/practice_48_196.json``); this scene replays them (smoothed, gaps interpolated) and places the rig in the world by unprojecting the fitted ground point
through the calibrated camera. The VFX are rebuilt from what is seen (smoke, aura, rings, beam), they are not copied pixels.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tsb_engine.authoring import K, P, root_pose
from tsb_engine.cinematic import Cinematic, dolly
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

POSES = Path(__file__).resolve().parent.parent / "docs" / "research" / "reference-poses" / "practice_48_196.json"
F0, F1 = 48, 196          # reference images used (the loop)
N = F1 - F0 + 1
FPS = 30
VIEW_W, VIEW_H = 1170.0, 686.0   # the Studio viewport in the recording (pixels)
FOV, PITCH = 70.0, 28.0          # Studio default vertical FOV; the horizon sits ~83 px below the top of the viewport -> pitch 28 degrees
CAM = (0.0, 15.4, 22.4)          # camera position: ~27 studs from the action, height such that the standing rig is 5.5 studs
ASPECT = VIEW_W / VIEW_H
FOCAL = (VIEW_H / 2.0) / math.tan(math.radians(FOV) / 2.0)
FACES = {"front": "#e03a30", "back": "#2f56e0", "right": "#36b04a", "left": "#f0932a", "top": "#47c4f0", "bottom": "#f0d322"}
COLORS = {p: "#cfd1d8" for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}
VIOLET, MAGENTA = ("#b07cff", "#4a2aa8"), "#d85cff"


def camera_basis():
    e = math.radians(PITCH)
    return (np.array([0.0, -math.sin(e), -math.cos(e)]), np.array([1.0, 0.0, 0.0]), np.array([0.0, math.cos(e), -math.sin(e)]))


def ray(u: float, v: float):
    f, r, up = camera_basis()
    return np.array(CAM), f + ((u - VIEW_W / 2) / FOCAL) * r - ((v - VIEW_H / 2) / FOCAL) * up


def on_ground(u: float, v: float) -> np.ndarray:
    o, d = ray(u, v)
    return o + (-o[1] / d[1]) * d


def on_plane(u: float, v: float, p0: np.ndarray, n: np.ndarray) -> np.ndarray:
    o, d = ray(u, v)
    t = float((p0 - o) @ n) / float(d @ n)
    return o + t * d


def load_track():
    """Per image of the loop: 16 angles and the pixel of the rig's ground point, gaps interpolated, angles smoothed."""
    d = json.loads(POSES.read_text())
    ang = np.full((N, 16), np.nan)
    pix = np.full((N, 2), np.nan)
    for fr in d["frames"]:
        i = fr["f"] - F0
        if 0 <= i < N and fr.get("angles"):
            ang[i] = fr["angles"]
            x0, y0, side = fr["crop"]
            tx, ty, _ = fr["fit"]
            pix[i] = (x0 + tx * side / 128.0, y0 + ty * side / 128.0 + 420 * 0)   # v3c rows are viewport rows (the crop started at the viewport top)
    idx = np.arange(N)
    for arr in (ang, pix):
        for k in range(arr.shape[1]):
            ok = ~np.isnan(arr[:, k])
            if ok.sum() >= 2:
                arr[:, k] = np.interp(idx, idx[ok], arr[ok, k])
    sm = ang.copy()
    for k in range(16):
        pad = np.pad(ang[:, k], 1, mode="edge")
        sm[:, k] = 0.25 * pad[:-2] + 0.5 * pad[1:-1] + 0.25 * pad[2:]
    px = np.convolve(np.pad(pix[:, 0], 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
    py = np.convolve(np.pad(pix[:, 1], 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
    return sm, px, py


def build() -> Scene:
    hero = Character("rig", Animation("rig", fps=FPS, archetype="cinematic"), colors=COLORS, face_colors=FACES, head_shape="ball")
    ang, px, py = load_track()
    # the vertical plane the rig moves in: through its ground point on the first and the last image (both standing)
    pl, pr = on_ground(px[0], py[0]), on_ground(px[-1], py[-1])
    along = (pr - pl) * np.array([1, 0, 1])
    along /= np.linalg.norm(along)
    normal = np.array([-along[2], 0.0, along[0]])
    for i in range(N):
        o = on_plane(px[i], py[i], pl, normal)
        y = max(0.0, float(o[1]))
        a = ang[i]
        K(hero.anim, i, "linear", R=root_pose(float(o[0]), 3.0 + y, float(o[2]), a[1], a[0], a[2]), T=P((a[3], a[4], a[5])), H=P((a[6], a[7], 0)),
          RA=P((a[8], 0, a[9])), LA=P((a[10], 0, a[11])), RL=P((a[12], 0, a[13])), LL=P((a[14], 0, a[15])))
    cine = Cinematic(N, fps=FPS)
    cine.look = "studio"
    cine.aspect = ASPECT
    cine.sky_color, cine.floor_color = "#a4a9b7", "#3d3e44"
    f, _, _ = camera_basis()
    tgt = tuple(np.array(CAM) + f * 10.0)
    cine.shot(0, N - 1, dolly(CAM, CAM, tgt, tgt, fov=FOV))
    torso = lambda f_: tuple(float(v) for v in np.array(hero.world_parts(int(f_))["Torso"][1]))
    foot = {"char": 0, "part": "Right Leg", "off": [0, -1.0, 0]}
    chest = {"char": 0, "part": "Torso", "off": [0, 0.4, 0]}
    fr = lambda v3: v3 - F0   # film image of a reference image index

    # grey dust: a trail behind the dash and the spin, a burst on every landing
    cine.emit(fr(62), fr(100), attach=foot, rate=2.2, vel=(0.01, 0.06), dir=(0, 1, 0), spread=1.4, life=(22, 44), size=(1.0, 3.2), color=("#8e9099", "#6b6d75"), alpha=(0.35, 0.0), add=False, seed=2, radius=0.6, shape="smoke")
    cine.emit(fr(120), fr(136), attach=foot, rate=2.0, vel=(0.01, 0.05), dir=(0, 1, 0), spread=1.2, life=(20, 40), size=(1.0, 2.8), color=("#8e9099", "#6b6d75"), alpha=(0.3, 0.0), add=False, seed=3, radius=0.6, shape="smoke")
    cine.emit(fr(156), fr(176), attach=foot, rate=2.4, vel=(0.01, 0.06), dir=(0, 1, 0), spread=1.4, life=(22, 44), size=(1.0, 3.0), color=("#8e9099", "#6b6d75"), alpha=(0.35, 0.0), add=False, seed=4, radius=0.6, shape="smoke")
    cine.emit(fr(16), fr(34), attach=foot, rate=2.0, vel=(0.01, 0.05), dir=(0, 1, 0), spread=1.2, life=(20, 38), size=(0.9, 2.6), color=("#8e9099", "#6b6d75"), alpha=(0.3, 0.0), add=False, seed=5, radius=0.6, shape="smoke")
    # the charge: a violet aura rising off the body, a soft glow
    cine.emit(fr(56), fr(66), attach=chest, rate=7.0, vel=(0.03, 0.16), dir=(0, 1, 0), spread=0.7, grav=-0.01, life=(10, 22), size=(0.7, 0.2), color=VIOLET, alpha=(0.9, 0.0), add=True, seed=6, radius=0.9, shape="soft")
    cine.glow(fr(57), fr(65), attach=chest, r0=1.2, r1=2.4, color="#7a4cff", a0=0.6, a1=0.0)
    # the spin: thin white arcs circling the body
    for k in range(4):
        cine.ring(fr(74) + 2 * k, 8, torso(fr(76)), 1.7 + 0.2 * k, 2.6 + 0.2 * k, 0.05, 0.02, "#ffffff", 0.8, 0.0, n=(0, 1, 0), add=True, easing="quad_out")
    # the violet shock-ring stack (110-116), the slam (138-142) and the beam (150-156): stacked horizontal rings, a cloud of motes, a flat glow
    def stack(t0: int, c, rmax: float, n: int = 7, dur: int = 8, y0: float = 0.4, dy: float = 0.45):
        for k in range(n):
            cine.ring(t0 + k // 3, dur, (c[0], y0 + dy * k, c[2]), 0.6, rmax * (0.7 + 0.05 * k), 0.10, 0.04, MAGENTA, 0.9, 0.0, n=(0, 1, 0), add=True, easing="quad_out")

    for t0, reach, big in ((fr(109), 2.4, 2.8), (fr(137), 0.0, 4.2)):
        c = torso(t0 + 2)
        c = (c[0] + reach, 0.0, c[2])
        stack(t0, c, big)
        cine.glow(t0, t0 + 8, c=(c[0], 1.6, c[2]), r0=2.0, r1=5.0, color="#c06cff", a0=0.8, a1=0.0, flare=0.3)
        cine.emit(t0, t0 + 6, origin=(c[0], 1.6, c[2]), burst=70, rate=0.0, vel=(0.05, 0.16), dir=(0, 1, 0), spread=2.4, life=(10, 22), size=(0.5, 0.1), color=VIOLET, alpha=(0.9, 0.0), add=True, seed=int(t0), radius=1.6, shape="soft")
    c = torso(fr(152))
    cine.streaks(fr(150), 8, (c[0] + 1.0, 1.5, c[2]), (c[0] + 9.0, 1.7, c[2]), n=26, r0=0.1, r1=1.6, w=0.06, color="#d889ff", seed=7)
    cine.glow(fr(150), fr(157), c=(c[0] + 4.0, 1.6, c[2]), r0=2.0, r1=4.5, color="#b46cff", a0=0.8, a1=0.0, flare=0.4)
    return Scene("VFX Practice Day2 - reproduction", [hero], fps=FPS, cine=cine)
