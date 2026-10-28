"""Round-trip check of the Roblox export: what Roblox would play vs what the engine shows.

An animation can look right in the preview and wrong in the game when the export changes it (resampling, rotation
interpolation, rounding, joint mapping). This module closes the loop *offline*:

1. export the animation to ``.rbxmx`` text and parse it back (the same file Studio would read),
2. play it the way Roblox does: a Pose CFrame is the Motor6D ``Transform``; between two keyframes with Linear easing the
   CFrame is interpolated (rotation by quaternion slerp, position linearly - ``CFrame:Lerp`` semantics, **[unverified]**
   against the engine; see docs/research/rnd-audit.md),
3. run Roblox's forward kinematics ``W(limb) = W(Torso) * C0 * Transform * C1^-1`` and compare every box corner with the
   engine's own kinematics.

The error is a distance in studs. ``step=1`` (a key every frame) should be ~0; larger steps show how much the game
would drift from what you approved. A limb that visibly detaches in the game shows up as a large error on that part.
(Detaching *by design* - the engine's dislocation - is reported separately as ``dislocation`` in studs.)
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .kinematics import corners, part_transforms
from .mathutil import Mat, Transform, apply, compose
from .model import PARTS, Animation
from .roblox_export import R6_JOINTS, keyframe_times, pose_cframe, roblox_forward_kinematics, to_rbxmx


# ---------------------------------------------------------------- tiny quaternion helpers
def _mat_to_quat(m: Mat) -> tuple[float, float, float, float]:
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return (0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s)
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return ((m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s)
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return ((m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s)
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return ((m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s)


def _quat_to_mat(q: tuple[float, float, float, float]) -> Mat:
    w, x, y, z = q
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def _slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = tuple(-x for x in b), -d
    if d > 0.9995:
        q = tuple(x + (y - x) * t for x, y in zip(a, b))
    else:
        th = math.acos(min(1.0, d))
        s = math.sin(th)
        wa, wb = math.sin((1 - t) * th) / s, math.sin(t * th) / s
        q = tuple(wa * x + wb * y for x, y in zip(a, b))
    n = math.sqrt(sum(x * x for x in q)) or 1.0
    return tuple(x / n for x in q)


def lerp_cframe(a: Transform, b: Transform, t: float) -> Transform:
    """``CFrame:Lerp`` semantics: slerp the rotation, lerp the position."""
    q = _slerp(_mat_to_quat(a[0]), _mat_to_quat(b[0]), t)
    return _quat_to_mat(q), tuple(a[1][i] + (b[1][i] - a[1][i]) * t for i in range(3))  # type: ignore[return-value]


# ---------------------------------------------------------------- parsing the exported file
def parse_rbxmx(text: str) -> list[tuple[float, dict[str, Transform]]]:
    """[(time, {part: Transform})] read back from the KeyframeSequence text."""
    root = ET.fromstring(text)
    seq = root.find("Item")
    out = []
    for kf in seq.findall("Item[@class='Keyframe']"):
        t = float(kf.find("Properties/float[@name='Time']").text)
        poses: dict[str, Transform] = {}

        def walk(item):
            for p in item.findall("Item[@class='Pose']"):
                name = p.find("Properties/string[@name='Name']").text
                cf = p.find("Properties/CoordinateFrame[@name='CFrame']")
                v = {c.tag: float(c.text) for c in cf}
                poses[name] = (
                    tuple(tuple(v[f"R{i}{j}"] for j in range(3)) for i in range(3)),
                    (v["X"], v["Y"], v["Z"]),
                )
                walk(p)

        walk(kf)
        out.append((t, poses))
    return out


def play(keys: list[tuple[float, dict[str, Transform]]], t: float) -> dict[str, Transform]:
    """Pose CFrames at time ``t`` with Linear easing between the surrounding keyframes."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return {p: lerp_cframe(a[p], b[p], u) for p in PARTS}
    return keys[-1][1]


# ---------------------------------------------------------------- comparison
@dataclass
class ExportReport:
    step: int
    keys: int
    worst: dict[str, float]       # part -> max corner error in studs
    worst_frame: dict[str, int]   # part -> frame where it happens
    mean: float
    dislocation: float            # largest limb translation the animation asks for (by design), studs

    @property
    def max_error(self) -> float:
        return max(self.worst.values())

    def line(self) -> str:
        w = max(self.worst, key=self.worst.get)
        return f"step {self.step}: {self.keys} keys, max error {self.max_error:.3f} studs ({w} @ frame {self.worst_frame[w]}), mean {self.mean:.4f}"


def engine_world(anim: Animation, frame: int) -> dict[str, Transform]:
    """The engine's world transforms for a character standing at the origin (HRP at (0, 3, 0)) with the Root track applied."""
    from .kinematics import root_transform

    return part_transforms(anim.sample(frame), root=root_transform(anim.sample_root(frame)))


def check_export(anim: Animation, step: int = 1, fps: int | None = None, frames: list[int] | None = None,
                 keys_at: list[int] | None = None) -> ExportReport:
    """Export with ``step`` (or exactly ``keys_at``), read it back, play it like Roblox and measure the error on every frame."""
    fps = fps or anim.fps
    keys = parse_rbxmx(to_rbxmx(anim, step=step, fps=fps, frames=keys_at))
    frames = frames if frames is not None else list(range(0, anim.last_frame + 1))
    worst = {p: 0.0 for p in PARTS}
    worst_f = {p: 0 for p in PARTS}
    tot, n = 0.0, 0
    for f in frames:
        mine = engine_world(anim, f)
        theirs = roblox_forward_kinematics(play(keys, f / fps))
        for p in PARTS:
            e = max(math.dist(a, b) for a, b in zip(corners(p, mine[p]), corners(p, theirs[p])))
            tot += e
            n += 1
            if e > worst[p]:
                worst[p], worst_f[p] = e, f
    disl = 0.0
    for p in PARTS:
        if p == "Torso":
            continue
        for k in anim.tracks.get(p, []):
            disl = max(disl, math.sqrt(sum(c * c for c in k.pose.pos)))
    return ExportReport(step, len(keys), worst, worst_f, tot / max(1, n), disl)


def suggest_step(anim: Animation, tolerance: float = 0.05, steps=(1, 2, 3, 4, 6)) -> tuple[int, list[ExportReport]]:
    """Largest key step whose worst error stays under ``tolerance`` studs (fewer keys = lighter file)."""
    reports = [check_export(anim, s) for s in steps]
    ok = [r.step for r in reports if r.max_error <= tolerance]
    return (max(ok) if ok else 1), reports


def optimize_keys(anim: Animation, tolerance: float = 0.05, base_step: int = 6, max_rounds: int = 60) -> list[int]:
    """Fewest keyframes that keep the Roblox playback within ``tolerance`` studs of the engine on every frame.

    Starts from a coarse grid plus every authored key (see ``keyframe_times``) and keeps inserting a key at the worst frame of
    each segment that is still off, so fast spins get dense keys and slow holds get almost none.
    """
    last = anim.last_frame
    fps = anim.fps
    mine = {f: engine_world(anim, f) for f in range(last + 1)}
    box = {f: {p: corners(p, mine[f][p]) for p in PARTS} for f in mine}
    cf_cache: dict[int, dict[str, Transform]] = {}

    def cfs(f: int) -> dict[str, Transform]:
        if f not in cf_cache:
            sample, root = anim.sample(f), anim.sample_root(f)
            cf_cache[f] = {p: pose_cframe(p, sample, root) for p in PARTS}
        return cf_cache[f]

    def err(f: int, a: int, b: int) -> float:
        u = 0.0 if b == a else (f - a) / (b - a)
        ca, cb = cfs(a), cfs(b)
        theirs = roblox_forward_kinematics({p: lerp_cframe(ca[p], cb[p], u) for p in PARTS})
        return max(math.dist(x, y) for p in PARTS for x, y in zip(box[f][p], corners(p, theirs[p])))

    keys = set(keyframe_times(anim, base_step))
    for _ in range(max_rounds):
        ks = sorted(keys)
        added = False
        for a, b in zip(ks, ks[1:]):
            if b - a < 2:
                continue
            worst_f, worst_e = None, tolerance
            for f in range(a + 1, b):
                e = err(f, a, b)
                if e > worst_e:
                    worst_f, worst_e = f, e
            if worst_f is not None:
                keys.add(worst_f)
                added = True
        if not added:
            break
    return sorted(keys)
