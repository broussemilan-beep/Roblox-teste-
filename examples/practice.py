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

from examples.practice_keys import EASE, HITSTOP, HITSTOP_CATCHUP, KEYS, LAG, NAMES, SHAKES
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
# camera: scaled by 0.711 so that the rig's apparent size (fitted: 29.7 px per stud) matches the unprojected depth (16.5 studs)
CAM = (0.0, 15.4 * 0.711, 22.4 * 0.711)
ASPECT = VIEW_W / VIEW_H
FOCAL = (VIEW_H / 2.0) / math.tan(math.radians(FOV) / 2.0)
FACES = {"front": "#e03a30", "back": "#2f56e0", "right": "#36b04a", "left": "#f0932a", "top": "#47c4f0", "bottom": "#f0d322"}
COLORS = {p: "#cfd1d8" for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}
VIOLET, MAGENTA = ("#8a5cff", "#3a1c9a"), "#c64cff"


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


TRACK = Path(__file__).resolve().parent.parent / "docs" / "research" / "reference-poses" / "practice_track.json"
AIR_SPANS = ((75, 90), (122, 136))   # reference images where the rig is off the ground (its lowest pixel rises above the ground line)
PX_PER_STUD = 30.0


def measured_track():
    """Reference screen track per image of the loop: median x of the rig's pixels and its lowest pixel (``tools/measure_track.py``), smoothed."""
    d = json.loads(TRACK.read_text())
    x = np.full(N, np.nan)
    foot = np.full(N, np.nan)
    for k, v in d.items():
        i = int(k) - F0
        if 0 <= i < N and v:
            x[i], foot[i] = v["x"], v["foot"]
    idx = np.arange(N)
    for arr in (x, foot):
        ok = ~np.isnan(arr)
        arr[:] = np.interp(idx, idx[ok], arr[ok])
    def med(v, k=5):
        pad = np.pad(v, k // 2, mode="edge")
        return np.array([np.median(pad[i : i + k]) for i in range(len(v))])
    g = np.exp(-0.5 * (np.arange(-3, 4) / 1.2) ** 2)
    g /= g.sum()
    sm = lambda v: np.convolve(np.pad(med(v), 3, mode="edge"), g, mode="valid")
    return sm(x), sm(foot)


def ground_baseline(foot: np.ndarray) -> np.ndarray:
    """Pixel row of the ground contact: the measured lowest pixel where the rig stands, a straight run across the jumps."""
    base = foot.copy()
    for a, b in AIR_SPANS:
        a, b = a - F0, b - F0
        base[a : b + 1] = np.linspace(foot[a - 1], foot[b + 1], b - a + 1)
    return base


def world_corners(a: np.ndarray, X: float, h: float, Z: float) -> np.ndarray:
    """The 48 corners of the posed rig in the world (root: torso-centre height ``h``)."""
    from tsb_engine.kinematics import corners, part_transforms, pose_transform
    from tsb_engine.mathutil import compose, translate
    from tsb_engine.model import PARTS, Pose

    v = [float(t) for t in a[:16]]
    root = compose(translate((0.0, 3.0, 0.0)), pose_transform(root_pose(X, h, Z, v[1], v[0], v[2])))
    pose = {"Torso": Pose((0, 0, 0), (v[3], v[4], v[5])), "Head": Pose((0, 0, 0), (v[6], v[7], 0)), "Right Arm": Pose((0, 0, 0), (v[8], 0, v[9])),
            "Left Arm": Pose((0, 0, 0), (v[10], 0, v[11])), "Right Leg": Pose((0, 0, 0), (v[12], 0, v[13])), "Left Leg": Pose((0, 0, 0), (v[14], 0, v[15]))}
    tf = part_transforms(pose, root=root)
    return np.array([c for p in PARTS for c in corners(p, tf[p])], float)


def project(pts: np.ndarray) -> np.ndarray:
    """World points -> picture pixels of the recording (columns: u, v)."""
    f, r, up = camera_basis()
    d = pts - np.array(CAM)
    z = d @ f
    return np.stack([VIEW_W / 2 + FOCAL * (d @ r) / z, VIEW_H / 2 - FOCAL * (d @ up) / z], 1)


def solve_track(ang: np.ndarray):
    """Place the rig so that, in the recording's camera, its median x and its lowest pixel fall where the reference's do, image by image.

    Jump heights come from the reference too: the lowest pixel above the ground line, converted to studs.  Returns (X, Z, air)."""
    xm, foot = measured_track()
    base = ground_baseline(foot)
    air = np.clip((base - foot) / PX_PER_STUD, 0.0, 2.4)
    X, Z = np.zeros(N), np.zeros(N)
    for i in range(N):
        g = on_ground(xm[i], base[i])
        x, z = float(g[0]), float(g[2])
        h = 3.0 + lowest(ang[i]) + air[i]
        for _ in range(5):
            def err(x_, z_):
                uv = project(world_corners(ang[i], x_, h, z_))
                return np.array([np.median(uv[:, 0]) - xm[i], np.percentile(uv[:, 1], 99.5) - foot[i]])
            e0 = err(x, z)
            J = np.stack([(err(x + 0.05, z) - e0) / 0.05, (err(x, z + 0.05) - e0) / 0.05], 1)
            try:
                dx, dz = np.linalg.solve(J, -e0)
            except np.linalg.LinAlgError:
                break
            x, z = x + float(np.clip(dx, -1.5, 1.5)), z + float(np.clip(dz, -1.5, 1.5))
        X[i], Z[i] = x, z
    return X, Z, air


def keyed_angles() -> np.ndarray:
    """(N, 17): the 16 joint angles + ``air`` for each image: Catmull-Rom through the authored keys, with the overlap an animator adds
    (the head trails the torso, the arms trail more: ``LAG``) and a tremor on the torso while the charge builds."""
    ts = np.array(sorted(KEYS), float)
    vals = np.zeros((len(ts), 17))
    for j, t in enumerate(ts):
        for n, v in KEYS[int(t)].items():
            vals[j, (NAMES + ["air"]).index(n)] = v

    def ease(u: float, style: str) -> float:
        if style == "hold":
            return 0.0
        if style == "in":
            return u**2.4
        if style == "out":
            return 1.0 - (1.0 - u) ** 2.4
        if style == "lin":
            return u
        if style == "back":   # Back Out: overshoots the target by ~10% then settles (the tutorials' overshoot after an impact)
            c1 = 1.70158
            return 1.0 + (c1 + 1.0) * (u - 1.0) ** 3 + c1 * (u - 1.0) ** 2
        return 0.5 * (2 * u) ** 2.0 if u < 0.5 else 1.0 - 0.5 * (2 * (1 - u)) ** 2.0   # "io"

    def at(t: float) -> np.ndarray:
        t = float(np.clip(t, ts[0], ts[-1]))
        j = int(np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 2))
        u = (t - ts[j]) / (ts[j + 1] - ts[j])
        return vals[j] + (vals[j + 1] - vals[j]) * ease(u, EASE.get(int(ts[j]), "io"))

    def clock(t: float) -> float:
        """Pose clock with the hit-stops: it stands still for ``n`` images at the impact, then runs a little faster until it is back on the real time."""
        for t0, n in HITSTOP.items():
            if t0 <= t < t0 + n:
                return float(t0)
            if t0 + n <= t < t0 + n + HITSTOP_CATCHUP:
                return t0 + (t - t0 - n) * (n + HITSTOP_CATCHUP) / HITSTOP_CATCHUP
        return t

    out = np.zeros((N, 17))
    for i in range(N):
        t = F0 + i
        tc = clock(float(t))
        out[i] = at(tc)
        out[i, 6:8] = at(clock(t - LAG["head"]))[6:8]
        out[i, 8:12] = at(clock(t - LAG["arms"]))[8:12]
        for t0, n in HITSTOP.items():   # the tiny twist that keeps the frozen pose alive
            if t0 <= t < t0 + n:
                out[i, 5] += 2.0 * (1 if (t - t0) % 2 == 0 else -1)
        for t0, amp in SHAKES.items():   # impact stop: a short decaying shake of the whole body
            if t0 <= t <= t0 + 5:
                k = (1.0 - (t - t0) / 6.0) * amp
                out[i, 2] += k * math.sin((t - t0) * 4.1)
                out[i, 5] += 0.8 * k * math.sin((t - t0) * 5.3 + 0.7)
                out[i, 3] += 0.6 * k * math.sin((t - t0) * 3.7)
        if 57 <= t <= 64:   # the charge: the whole body vibrates, harder as it fills
            k = (t - 56) / 8.0
            out[i, 2] += 2.6 * k * math.sin(t * 2.7)
            out[i, 5] += 3.0 * k * math.sin(t * 3.3 + 1.0)
    out[:, 16] = np.maximum(out[:, 16], 0.0)
    return out


def lowest(a: np.ndarray) -> float:
    """Root height (above its 3-stud standing value) that puts the lowest corner of the posed rig on the ground."""
    return -float(world_corners(a, 0.0, 3.0, 0.0)[:, 1].min())


def build() -> Scene:
    hero = Character("rig", Animation("rig", fps=FPS, archetype="cinematic"), colors=COLORS, face_colors=FACES, head_shape="ball")
    ang = keyed_angles()
    X, Z, air = solve_track(ang)
    for i in range(N):
        a = ang[i]
        K(hero.anim, i, "linear", R=root_pose(float(X[i]), 3.0 + lowest(a) + float(air[i]), float(Z[i]), a[1], a[0], a[2]), T=P((a[3], a[4], a[5])), H=P((a[6], a[7], 0)),
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
    cine.emit(fr(62), fr(100), attach=foot, rate=2.2, vel=(0.01, 0.06), dir=(0, 1, 0), spread=1.4, life=(22, 44), size=(1.0, 3.2), color=("#6f7178", "#4f5056"), alpha=(0.30, 0.0), add=False, seed=2, radius=0.6, shape="smoke")
    cine.emit(fr(120), fr(136), attach=foot, rate=2.0, vel=(0.01, 0.05), dir=(0, 1, 0), spread=1.2, life=(20, 40), size=(1.0, 2.8), color=("#6f7178", "#4f5056"), alpha=(0.26, 0.0), add=False, seed=3, radius=0.6, shape="smoke")
    cine.emit(fr(156), fr(172), attach=foot, rate=1.6, vel=(0.01, 0.05), dir=(0, 1, 0), spread=1.2, life=(10, 22), size=(0.7, 1.9), color=("#6f7178", "#4f5056"), alpha=(0.20, 0.0), add=False, seed=4, radius=0.6, shape="smoke")
    # the charge: a violet aura rising off the body, a soft glow
    cine.emit(fr(56), fr(66), attach=chest, rate=7.0, vel=(0.03, 0.16), dir=(0, 1, 0), spread=0.7, grav=-0.01, life=(10, 22), size=(0.7, 0.2), color=VIOLET, alpha=(0.9, 0.0), add=True, seed=6, radius=0.9, shape="soft")
    cine.glow(fr(57), fr(65), attach=chest, r0=0.8, r1=1.7, color="#5a30d8", a0=0.16, a1=0.0)
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
