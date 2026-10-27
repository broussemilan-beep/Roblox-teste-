"""Cinematic layer for ultimates: camera shots, set dressing, debris, effects, screen effects.

Everything here is *data*: the HTML viewer turns it into pictures (and a Roblox exporter could
turn it into CFrame/Tween scripts later). Only primitives that exist in Roblox are used:
boxes (Parts/MeshParts), rings/domes/sparks (ParticleEmitter or Mesh), beams/trails, a point
light-like glow, and ColorCorrection-style screen tints (flash, vignette, brightness).
No custom shaders, no frame-freeze tricks.

Units: studs and frames (default 60 fps). World: Y up, a character with yaw 0 faces -Z.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from .model import EASINGS

Vec = tuple[float, float, float]
CamState = tuple[Vec, Vec, float, float]  # position, target, fov (deg), roll (deg)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp3(a: Vec, b: Vec, t: float) -> Vec:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def ease(name: str, u: float) -> float:
    return EASINGS[name](max(0.0, min(1.0, u)))


class Track:
    """Scalar value over time with per-segment easing (value holds after the last key)."""

    def __init__(self, default: float = 0.0):
        self.default = default
        self.keys: list[tuple[int, float, str]] = []

    def key(self, frame: int, value: float, easing: str = "linear") -> "Track":
        self.keys = [k for k in self.keys if k[0] != frame] + [(frame, value, easing)]
        self.keys.sort()
        return self

    def at(self, frame: float) -> float:
        if not self.keys:
            return self.default
        if frame <= self.keys[0][0]:
            return self.keys[0][1]
        for (f0, v0, e), (f1, v1, _) in zip(self.keys, self.keys[1:]):
            if f0 <= frame < f1:
                return lerp(v0, v1, ease(e, (frame - f0) / (f1 - f0)))
        return self.keys[-1][1]


# ---------------------------------------------------------------- camera helpers
def orbit(
    center: Vec,
    radius: float,
    yaw0: float,
    yaw1: float,
    height0: float,
    height1: float,
    look_dy: float = 0.0,
    fov: float | tuple[float, float] = 50.0,
    roll: float = 0.0,
    easing: str = "sine_inout",
) -> Callable[[float, float], CamState]:
    """Camera circling ``center``. yaw 0 = camera on +Z looking towards -Z; 90 = camera on +X."""

    def fn(u: float, f: float) -> CamState:
        e = ease(easing, u)
        yaw = math.radians(lerp(yaw0, yaw1, e))
        h = lerp(height0, height1, e)
        pos = (center[0] + radius * math.sin(yaw), h, center[2] + radius * math.cos(yaw))
        tgt = (center[0], center[1] + look_dy, center[2])
        fv = fov if isinstance(fov, (int, float)) else lerp(fov[0], fov[1], e)
        return pos, tgt, fv, roll

    return fn


def dolly(
    pos0: Vec,
    pos1: Vec,
    tgt0: Vec,
    tgt1: Vec,
    fov: float | tuple[float, float] = 50.0,
    roll: float | tuple[float, float] = 0.0,
    easing: str = "sine_inout",
) -> Callable[[float, float], CamState]:
    """Straight move between two framings."""

    def fn(u: float, f: float) -> CamState:
        e = ease(easing, u)
        fv = fov if isinstance(fov, (int, float)) else lerp(fov[0], fov[1], e)
        rl = roll if isinstance(roll, (int, float)) else lerp(roll[0], roll[1], e)
        return lerp3(pos0, pos1, e), lerp3(tgt0, tgt1, e), fv, rl

    return fn


def tracking(
    target_at: Callable[[float], Vec],
    offset: Vec,
    look_dy: float = 0.0,
    fov: float | tuple[float, float] = 50.0,
    roll: float = 0.0,
    offset_end: Vec | None = None,
) -> Callable[[float, float], CamState]:
    """Camera glued to a moving point (``target_at(frame)``) with a (changing) offset."""

    def fn(u: float, f: float) -> CamState:
        t = target_at(f)
        off = offset if offset_end is None else lerp3(offset, offset_end, u)
        fv = fov if isinstance(fov, (int, float)) else lerp(fov[0], fov[1], u)
        return (t[0] + off[0], t[1] + off[1], t[2] + off[2]), (t[0], t[1] + look_dy, t[2]), fv, roll

    return fn


# ---------------------------------------------------------------- the cinematic
@dataclass
class Cinematic:
    n_frames: int
    fps: int = 60
    shots: list[tuple[int, int, Callable[[float, float], CamState]]] = field(default_factory=list)
    shakes: list[tuple[int, int, float]] = field(default_factory=list)
    kicks: list[tuple[int, int, float]] = field(default_factory=list)
    props: list[dict] = field(default_factory=list)
    debris: list[dict] = field(default_factory=list)
    fx: list[dict] = field(default_factory=list)
    flashes: list[dict] = field(default_factory=list)
    bright: Track = field(default_factory=lambda: Track(1.0))
    vignette: Track = field(default_factory=lambda: Track(0.0))
    bars: Track = field(default_factory=lambda: Track(0.0))
    speed: Track = field(default_factory=lambda: Track(0.0))
    tint: Track = field(default_factory=lambda: Track(0.0))
    tint_color: str = "#ff5a1f"
    floor_color: str = "#d8dce3"
    sky_color: str = "#c9d3e3"
    seed: int = 7
    sheets: dict = field(default_factory=dict)

    # --- camera
    def shot(self, f0: int, f1: int, fn: Callable[[float, float], CamState]) -> None:
        self.shots.append((f0, f1, fn))

    def shake(self, f0: int, dur: int, amp: float) -> None:
        self.shakes.append((f0, dur, amp))

    def camera_state(self, f: int) -> CamState:
        chosen = None
        for f0, f1, fn in self.shots:
            if f0 <= f <= f1:
                chosen = (f0, f1, fn)
        if chosen is None:
            raise ValueError(f"no camera shot covers frame {f}")
        f0, f1, fn = chosen
        pos, tgt, fov, roll = fn((f - f0) / max(1, f1 - f0), f)
        dx = dy = dz = droll = 0.0
        for s0, dur, amp in self.shakes:
            if s0 <= f < s0 + dur:
                k = (1 - (f - s0) / dur) ** 1.5 * amp
                dx += k * (math.sin(f * 2.3 + 1.1) + 0.6 * math.sin(f * 5.1))
                dy += k * (math.sin(f * 2.9 + 0.4) + 0.6 * math.sin(f * 4.3 + 2))
                dz += k * 0.5 * math.sin(f * 3.7)
                droll += k * 2.0 * math.sin(f * 3.1)
        for k0, kd, ka in self.kicks:
            if k0 <= f < k0 + kd:
                fov *= 1.0 - ka * (1 - (f - k0) / kd) ** 2
        pos = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
        tgt = (tgt[0] + dx, tgt[1] + dy, tgt[2] + dz)
        return pos, tgt, fov, roll + droll

    # --- set dressing
    def prop(self, c: Vec, size: Vec, color: str, yaw: float = 0.0, vis: tuple[int, int] | None = None) -> None:
        self.props.append(
            {"c": list(c), "size": list(size), "color": color, "yaw": yaw, "v": list(vis or (0, self.n_frames + 1))}
        )

    def debris_piece(
        self, t0: int, p: Vec, v: Vec, size: Vec, color: str, w: Vec = (0, 0, 0),
        g: float = 0.02, bounce: float = 0.35, life: int | None = None,
        g2: float | None = None, tg: int | None = None,
    ) -> None:
        """One box with ballistic motion. ``g`` is downward acceleration (studs/frame^2; negative lifts).
        From frame ``tg`` on, gravity switches to ``g2`` (e.g. levitating rocks that fall at the roar)."""
        self.debris.append(
            {"g2": g2, "tg": tg, "t0": t0, "p": [round(x, 3) for x in p], "v": [round(x, 4) for x in v], "w": [round(x, 3) for x in w],
             "size": [round(x, 3) for x in size], "color": color, "g": g, "bounce": bounce,
             "life": life if life is not None else self.n_frames + 1}
        )

    def shatter(
        self, t0: int, center: Vec, size: Vec, color: str, splits: tuple[int, int, int],
        origin: Vec, speed: float, up: float = 0.25, spin: float = 6.0, seed: int = 1,
        colors: list[str] | None = None, g: float = 0.02,
    ) -> None:
        """Replace a box by a grid of pieces thrown away from ``origin``."""
        rnd = random.Random(self.seed * 1000 + seed)
        nx, ny, nz = splits
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    sz = (size[0] / nx, size[1] / ny, size[2] / nz)
                    p = (
                        center[0] - size[0] / 2 + sz[0] * (ix + 0.5),
                        center[1] - size[1] / 2 + sz[1] * (iy + 0.5),
                        center[2] - size[2] / 2 + sz[2] * (iz + 0.5),
                    )
                    d = (p[0] - origin[0], p[1] - origin[1], p[2] - origin[2])
                    n = math.sqrt(sum(c * c for c in d)) or 1.0
                    k = speed * (0.55 + 0.9 * rnd.random()) / (1 + n * 0.04)
                    v = (d[0] / n * k, d[1] / n * k * 0.6 + up * rnd.random(), d[2] / n * k)
                    w = tuple((rnd.random() - 0.5) * 2 * spin for _ in range(3))
                    col = rnd.choice(colors) if colors else color
                    shrink = 0.82 + 0.16 * rnd.random()
                    self.debris_piece(t0, p, v, (sz[0] * shrink, sz[1] * shrink, sz[2] * shrink), col, w, g)

    def burst_debris(
        self, t0: int, origin: Vec, count: int, speed: float, up: float, size: tuple[float, float],
        colors: list[str], seed: int = 1, spread: Vec = (1, 0.4, 1), g: float = 0.02, direction: Vec | None = None,
    ) -> None:
        rnd = random.Random(self.seed * 1000 + seed)
        for _ in range(count):
            a = rnd.random() * math.tau
            r = math.sqrt(rnd.random())
            d = (math.cos(a) * r * spread[0], rnd.random() * spread[1], math.sin(a) * r * spread[2])
            if direction:
                d = (d[0] * 0.5 + direction[0], d[1] * 0.5 + direction[1], d[2] * 0.5 + direction[2])
            k = speed * (0.4 + rnd.random() * 0.9)
            s = lerp(size[0], size[1], rnd.random())
            self.debris_piece(
                t0, (origin[0] + d[0] * 0.3, max(origin[1], 0.2), origin[2] + d[2] * 0.3),
                (d[0] * k, up * (0.4 + rnd.random()), d[2] * k),
                (s, s * (0.5 + rnd.random() * 0.8), s * (0.6 + rnd.random() * 0.7)),
                rnd.choice(colors), tuple((rnd.random() - 0.5) * 12 for _ in range(3)), g,
            )

    # --- effects (all times in frames)
    def ring(self, t0: int, dur: int, c: Vec, r0: float, r1: float, w0: float, w1: float, color: str,
             a0: float = 0.9, a1: float = 0.0, n: Vec = (0, 1, 0), add: bool = True, easing: str = "expo_out") -> None:
        self.fx.append({"type": "ring", "t0": t0, "dur": dur, "c": list(c), "r0": r0, "r1": r1, "w0": w0, "w1": w1,
                        "color": color, "a0": a0, "a1": a1, "n": list(n), "add": add, "ease": easing})

    def dome(self, t0: int, dur: int, c: Vec, r0: float, r1: float, color: str, a0: float = 0.9, a1: float = 0.0,
             add: bool = True, easing: str = "expo_out") -> None:
        self.fx.append({"type": "dome", "t0": t0, "dur": dur, "c": list(c), "r0": r0, "r1": r1, "color": color,
                        "a0": a0, "a1": a1, "add": add, "ease": easing})

    def emit(self, t0: int, t1: int, origin: Vec | None = None, attach: dict | None = None, rate: float = 2.0,
             burst: int = 0, vel: tuple[float, float] = (0.05, 0.25), dir: Vec = (0, 1, 0), spread: float = 0.6,
             grav: float = 0.0, drag: float = 0.0, life: tuple[int, int] = (20, 40), size: tuple[float, float] = (0.3, 0.1),
             size_var: float = 0.3, color: tuple[str, str] = ("#ffd27a", "#ff4d00"), alpha: tuple[float, float] = (0.9, 0.0),
             add: bool = True, seed: int = 1, radius: float = 0.0, converge: float = 0.0, stretch: float = 0.0,
             shape: str = "soft") -> None:
        """Particles. ``attach={"char": i, "part": "Right Arm", "off": [0,-1,0]}`` follows a body part.
        ``converge`` > 0 spawns on a sphere of that radius moving inwards (charge-up).
        ``shape``: soft (default glow), spark (velocity-stretched streak, ``stretch`` = length in frames of travel),
        flame (teardrop that rises), smoke (lumpy puff, use add=False), shard (flat flying chip), disc (hard dot)."""
        self.fx.append({"type": "emit", "t0": t0, "t1": t1, "origin": list(origin) if origin else None, "attach": attach,
                        "rate": rate, "burst": burst, "vel": list(vel), "dir": list(dir), "spread": spread, "grav": grav,
                        "drag": drag, "life": list(life), "size": list(size), "sizeVar": size_var, "color": list(color),
                        "alpha": list(alpha), "add": add, "seed": self.seed * 100 + seed, "radius": radius,
                        "converge": converge, "stretch": stretch, "shape": shape})

    def trail(self, t0: int, t1: int, char: int, part: str, tip: Vec, length: int, w0: float, w1: float,
              color: str, alpha: float = 0.9) -> None:
        self.fx.append({"type": "trail", "t0": t0, "t1": t1, "char": char, "part": part, "tip": list(tip),
                        "len": length, "w0": w0, "w1": w1, "color": color, "a": alpha})

    def line(self, t0: int, dur: int, a: Vec, b: Vec, w0: float, w1: float, color: str, a0: float = 0.9,
             a1: float = 0.0, add: bool = True, easing: str = "expo_out") -> None:
        self.fx.append({"type": "line", "t0": t0, "dur": dur, "a": list(a), "b": list(b), "w0": w0, "w1": w1,
                        "color": color, "a0": a0, "a1": a1, "add": add, "ease": easing})

    def cracks(self, t0: int, dur: int, c: Vec, length: float, branches: int, color: str, glow: str | None = None,
               width: float = 0.12, n: Vec = (0, 1, 0), seed: int = 1, fade: tuple[int, int] | None = None) -> None:
        self.fx.append({"type": "cracks", "t0": t0, "dur": dur, "c": list(c), "len": length, "branches": branches,
                        "color": color, "glow": glow, "w": width, "n": list(n), "seed": self.seed * 100 + seed,
                        "fade": list(fade) if fade else None})

    def strip(self, t0: int, dur: int, a: Vec, b: Vec, layers: list[tuple[float, str, float]], easing: str = "linear",
              fade: tuple[int, int] | None = None, add: bool = True) -> None:
        """Ground strip growing from a to b; layers = [(width, color, alpha), ...] drawn wide to narrow."""
        self.fx.append({"type": "strip", "t0": t0, "dur": dur, "a": list(a), "b": list(b),
                        "layers": [list(l) for l in layers], "ease": easing, "fade": list(fade) if fade else None, "add": add})

    def use_sheet(self, name: str, path: str, grid: int, frames: int) -> None:
        """Embed a baked flipbook sheet (tsb_engine.textures) so sprites/particles can play it like a Roblox flipbook."""
        import base64

        with open(path, "rb") as fh:
            self.sheets[name] = {"src": "data:image/png;base64," + base64.b64encode(fh.read()).decode(), "grid": grid, "frames": frames}

    def sprite(self, sheet: str, t0: int, dur: int, c: Vec, size0: float, size1: float, rot: float = 0.0,
               alpha: float = 1.0, add: bool = False, speed: float = 1.0) -> None:
        """Camera-facing flipbook quad (a ParticleEmitter with a flipbook texture, Lifetime = dur frames)."""
        if sheet in self.sheets:
            self.fx.append({"type": "sprite", "sheet": sheet, "t0": t0, "dur": dur, "c": list(c), "size0": size0, "size1": size1,
                            "rot": rot, "alpha": alpha, "add": add, "speed": speed})

    def burst(self, t0: int, dur: int, c: Vec, r0: float, r1: float, color: str = "#ffb43a", core: str = "#ffffff",
              spikes: int = 11, streaks: int = 9, rot: float = 0.0, seed: int = 1) -> None:
        """Camera-facing hit sprite: jagged star + hot core + radial streaks (a flipbook-style impact burst)."""
        self.fx.append({"type": "burst", "t0": t0, "dur": dur, "c": list(c), "r0": r0, "r1": r1, "color": color, "core": core,
                        "n": spikes, "streaks": streaks, "rot": rot, "seed": self.seed * 100 + seed})
        self.sprite("impact_star", t0, dur + 3, c, r0 * 1.6, r1 * 2.1, rot=rot * 1.7, alpha=0.9 if r1 < 4.5 else 0.5, add=False)

    def glow(self, t0: int, t1: int, c: Vec | None = None, attach: dict | None = None, r0: float = 1.0, r1: float = 1.0,
             color: str = "#ffb43a", a0: float = 0.9, a1: float = 0.9, flare: float = 0.0, pulse: float = 0.0) -> None:
        """Soft light blob (optionally with an anamorphic flare) at a point or following a body part."""
        self.fx.append({"type": "glow", "t0": t0, "t1": t1, "c": list(c) if c else None, "attach": attach, "r0": r0, "r1": r1,
                        "color": color, "a0": a0, "a1": a1, "flare": flare, "pulse": pulse})

    def bolt(self, t0: int, t1: int, a: Vec | None = None, b: Vec | None = None, attach_a: dict | None = None,
             attach_b: dict | None = None, width: float = 0.12, color: str = "#8fd0ff", core: str = "#ffffff",
             segs: int = 9, jitter: float = 0.9, branch: float = 0.25, flicker: bool = True, seed: int = 1) -> None:
        """Jagged lightning (a Beam with a lightning texture in Roblox); re-rolled every 2 frames."""
        self.fx.append({"type": "bolt", "t0": t0, "t1": t1, "a": list(a) if a else None, "b": list(b) if b else None,
                        "attachA": attach_a, "attachB": attach_b, "w": width, "color": color, "core": core, "segs": segs,
                        "jitter": jitter, "branch": branch, "flicker": flicker, "seed": self.seed * 100 + seed})

    def slash(self, t0: int, dur: int, c: Vec, n: Vec, r: float, a0: float, a1: float, w: float = 0.7,
              color: str = "#ffb43a", core: str = "#ffffff") -> None:
        """Crescent smear that sweeps from angle a0 to a1 (degrees) in the plane with normal n (a thick tapered Trail)."""
        self.fx.append({"type": "slash", "t0": t0, "dur": dur, "c": list(c), "n": list(n), "r": r, "a0": a0, "a1": a1,
                        "w": w, "color": color, "core": core})

    def punch_in(self, f0: int, amount: float = 0.12, dur: int = 8) -> None:
        """Quick field-of-view kick (the camera pushes in and settles) - the camera-side half of an impact."""
        self.kicks.append((f0, dur, amount))

    # --- screen effects
    def flash(self, t0: int, dur: int, color: str = "#ffffff", peak: float = 1.0) -> None:
        self.flashes.append({"t0": t0, "dur": dur, "color": color, "peak": peak})

    # --- export
    def to_dict(self) -> dict:
        cam = []
        for f in range(self.n_frames):
            p, t, fov, roll = self.camera_state(f)
            cam.append([round(x, 3) for x in (*p, *t)] + [round(fov, 2), round(roll, 2)])
        rng = range(self.n_frames)
        return {
            "camera": cam, "props": self.props, "debris": self.debris, "fx": self.fx,
            "screen": {
                "bright": [round(self.bright.at(f), 3) for f in rng],
                "vignette": [round(self.vignette.at(f), 3) for f in rng],
                "bars": [round(self.bars.at(f), 3) for f in rng],
                "speed": [round(self.speed.at(f), 3) for f in rng],
                "tint": [round(self.tint.at(f), 3) for f in rng],
                "tintColor": self.tint_color, "flashes": self.flashes,
            },
            "floorColor": self.floor_color, "skyColor": self.sky_color, "sheets": self.sheets,
        }
