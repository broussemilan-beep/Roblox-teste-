"""Secondary motion for R6 characters: hair, coat tails, scarves and hats that never stop moving.

The reference study (docs/research/reference-analysis.md) shows hair, hat and coat tails reacting to every move,
even during holds. Roblox does this with accessories + cloth/spring scripts; here we simulate it so the preview
shows the same follow-through. Extras are *preview* parts: they are not part of the exported KeyframeSequence
(accessories are driven by the game, not by animation tracks).

Model: each strand is a verlet rope anchored on a part. Per step:
  1. integrate with drag and gravity,
  2. pull each point toward "hang along the rest direction" (stiffness),
  3. enforce the segment lengths (3 relaxation passes).
Segments are drawn as boxes whose long axis follows the rope; the box side axis follows the parent part so the
strand does not twist randomly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .kinematics import apply
from .mathutil import Mat, Transform, Vec, mat_vec

Vec3 = Vec


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def _len(a: Vec) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _norm(a: Vec) -> Vec:
    n = _len(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-9 else (0.0, 1.0, 0.0)


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass
class ExtraTrack:
    """A preview part with one world transform per frame."""

    name: str
    size: Vec
    color: str
    frames: list[Transform]
    shape: str = "box"  # "box" | "cyl" (round, axis Y) | "ell" (ellipsoid)
    vis: tuple[int, int] | None = None  # shown only on images vis[0]..vis[1] (inclusive); None = always


@dataclass
class Strand:
    """A hanging rope of boxes (hair lock, coat tail, scarf end).

    ``anchor`` is in the parent part's local frame (the part's centre is the origin, +Y up, -Z front);
    ``rest_dir`` is the direction (parent frame) the strand hangs towards at rest.
    """

    name: str
    parent: str
    anchor: Vec
    segments: int
    seg_len: float
    width: float
    depth: float
    color: str
    rest_dir: Vec = (0.0, -1.0, 0.0)
    gravity: float = 40.0  # studs/s^2 pulling down
    stiffness: float = 6.0  # 1/s, how fast the strand returns to its rest direction
    drag: float = 3.0  # 1/s
    taper: float = 0.85  # width multiplier per segment
    shape: str = "box"

    def simulate(self, char, n_frames: int, hold: int = 1, fps: int = 60) -> list[ExtraTrack]:
        dt = hold / fps
        sub = 4
        h = dt / sub
        ov = 1.7 if self.shape == "ell" else 1.0  # round segments overlap so a lock reads as one piece
        tracks = [ExtraTrack(f"{self.name}{i}", (self.width * self.taper**i, self.seg_len * ov, self.depth), self.color, [], self.shape) for i in range(self.segments)]
        pts: list[Vec] | None = None
        prev: list[Vec] | None = None
        last_out: list[Transform] | None = None
        for f in range(n_frames):
            if f % hold == 0 or last_out is None:
                tf = char.world_parts(f)[self.parent]
                rot: Mat = tf[0]
                anchor = apply(tf, self.anchor)
                rest_world = _norm(mat_vec(rot, self.rest_dir))
                side = _norm(mat_vec(rot, (1.0, 0.0, 0.0)))
                if pts is None:
                    pts = [_add(anchor, _mul(rest_world, self.seg_len * i)) for i in range(self.segments + 1)]
                    prev = list(pts)
                for _ in range(sub):
                    pts[0] = anchor
                    prev[0] = anchor
                    for i in range(1, len(pts)):
                        vel = _mul(_sub(pts[i], prev[i]), 1.0 - min(0.95, self.drag * h))
                        target = _add(pts[i - 1], _mul(rest_world, self.seg_len))
                        pull = _mul(_sub(target, pts[i]), min(1.0, self.stiffness * h))
                        nxt = _add(_add(pts[i], vel), pull)
                        nxt = (nxt[0], nxt[1] - self.gravity * h * h, nxt[2])
                        prev[i] = pts[i]
                        pts[i] = nxt
                    for _ in range(3):
                        for i in range(1, len(pts)):
                            d = _sub(pts[i], pts[i - 1])
                            ln = _len(d) or 1e-9
                            pts[i] = _add(pts[i - 1], _mul(d, self.seg_len / ln))
                    for i in range(1, len(pts)):  # stay above the ground
                        if pts[i][1] < 0.05:
                            pts[i] = (pts[i][0], 0.05, pts[i][2])
                out: list[Transform] = []
                for i in range(self.segments):
                    a, b = pts[i], pts[i + 1]
                    yax = _norm(_sub(a, b))  # box +Y points to the parent end
                    xax = _sub(side, _mul(yax, _dot(side, yax)))
                    xax = _norm(xax) if _len(xax) > 1e-4 else _norm(_cross(yax, (0.0, 0.0, 1.0)))
                    zax = _cross(xax, yax)
                    mid = _mul(_add(a, b), 0.5)
                    out.append((((xax[0], yax[0], zax[0]), (xax[1], yax[1], zax[1]), (xax[2], yax[2], zax[2])), mid))
                last_out = out
            for t, tr in zip(last_out, tracks):
                tr.frames.append(t)
        return tracks


@dataclass
class Rigid:
    """A box glued to a part (hat crown, hat brim, belt, glasses...)."""

    name: str
    parent: str
    offset: Vec
    size: Vec
    color: str
    tilt: tuple[float, float, float] = (0.0, 0.0, 0.0)  # degrees, Roblox CFrame.Angles order, in the parent's frame
    shape: str = "box"

    def simulate(self, char, n_frames: int, hold: int = 1, fps: int = 60) -> list[ExtraTrack]:
        from .mathutil import compose, euler, translate

        local = compose(translate(self.offset), (euler(self.tilt), (0.0, 0.0, 0.0)))
        out = []
        for f in range(n_frames):
            ff = f - f % hold
            out.append(compose(char.world_parts(ff)[self.parent], local))
        return [ExtraTrack(self.name, self.size, self.color, out, self.shape)]


@dataclass
class Attach:
    """A real triangle mesh (``tsb_engine.modeling.Mesh``) glued to a part, modelled in that part's local frame (origin = part centre).

    ``offset``/``tilt`` move it relative to the part (Roblox CFrame.Angles order, degrees). The mesh keeps its own per-face colours.
    """

    name: str
    parent: str
    mesh: object
    offset: Vec = (0.0, 0.0, 0.0)
    tilt: tuple[float, float, float] = (0.0, 0.0, 0.0)
    vis: tuple[int, int] | None = None  # visible only on these images (e.g. the drawn blade)

    def simulate(self, char, n_frames: int, hold: int = 1, fps: int = 60) -> list[ExtraTrack]:
        from .mathutil import compose, euler, translate

        local = compose(translate(self.offset), (euler(self.tilt), (0.0, 0.0, 0.0)))
        out = []
        for f in range(n_frames):
            ff = f - f % hold
            out.append(compose(char.world_parts(ff)[self.parent], local))
        return [ExtraTrack(self.name, (2.0, 2.0, 2.0), "#888888", out, "mesh:" + self.mesh.name, self.vis)]


@dataclass
class Outfit:
    """A set of extras for one character."""

    items: list[object] = field(default_factory=list)

    def meshes(self) -> dict:
        """Distinct triangle meshes used by ``Attach`` items, by name."""
        return {it.mesh.name: it.mesh for it in self.items if isinstance(it, Attach)}

    def simulate(self, char, n_frames: int, hold: int = 1, fps: int = 60) -> list[ExtraTrack]:
        tracks: list[ExtraTrack] = []
        for it in self.items:
            tracks += it.simulate(char, n_frames, hold, fps)
        return tracks


def coat_and_hair(coat: str = "#101015", hair: str = "#e8edf2", hat: str = "#0b0b0f") -> Outfit:
    """Dark long coat (three tails), white hair locks and a wide-brim hat: the silhouette of the reference character."""
    items: list[object] = [
        Rigid("belt", "Torso", (0.0, -0.78, 0.0), (2.06, 0.2, 1.06), "#d9dade"),
        Rigid("cuff_r", "Right Arm", (0.0, -0.82, 0.0), (1.08, 0.16, 1.08), "#d9dade"),
        Rigid("cuff_l", "Left Arm", (0.0, -0.82, 0.0), (1.08, 0.16, 1.08), "#d9dade"),
        Rigid("boot_r", "Right Leg", (0.0, -0.8, 0.0), (1.06, 0.2, 1.06), "#d9dade"),
        Rigid("boot_l", "Left Leg", (0.0, -0.8, 0.0), (1.06, 0.2, 1.06), "#d9dade"),
        Rigid("hat_brim", "Head", (0.0, 0.62, 0.0), (1.9, 0.12, 1.9), hat, (4.0, 0.0, 0.0)),
        Rigid("hat_crown", "Head", (0.0, 0.92, 0.0), (1.1, 0.55, 1.1), hat),
        Strand("coat_back", "Torso", (0.0, -0.95, 0.5), 4, 0.62, 1.7, 0.18, coat, rest_dir=(0.0, -1.0, 0.25), gravity=34, stiffness=5, drag=2.6, taper=0.9),
        Strand("coat_l", "Torso", (-0.8, -0.95, 0.45), 3, 0.6, 0.55, 0.16, coat, rest_dir=(-0.25, -1.0, 0.35), gravity=34, stiffness=5, drag=2.6),
        Strand("coat_r", "Torso", (0.8, -0.95, 0.45), 3, 0.6, 0.55, 0.16, coat, rest_dir=(0.25, -1.0, 0.35), gravity=34, stiffness=5, drag=2.6),
        Strand("hair_a", "Head", (-0.55, 0.0, 0.5), 4, 0.5, 0.55, 0.4, hair, rest_dir=(-0.25, -1.0, 0.5), gravity=24, stiffness=3.0, drag=2.2, taper=0.84, shape="ell"),
        Strand("hair_b", "Head", (0.0, 0.0, 0.8), 5, 0.52, 0.8, 0.42, hair, rest_dir=(0.0, -1.0, 0.6), gravity=24, stiffness=3.0, drag=2.2, taper=0.86, shape="ell"),
        Strand("hair_c", "Head", (0.55, 0.0, 0.5), 4, 0.5, 0.55, 0.4, hair, rest_dir=(0.25, -1.0, 0.5), gravity=24, stiffness=3.0, drag=2.2, taper=0.84, shape="ell"),
    ]
    return Outfit(items)


def reference_outfit(coat: str = "#0c0c10", hair: str = "#eef2f6", hat: str = "#08080b", band: str = "#26262d") -> Outfit:
    """The signature silhouette of the study reference: a wide round-brim hat with a banded crown and a speech-bubble sticker,
    a big shock of white hair (fringe over one eye + long locks), a flared long coat with broad tails, a striped belt.

    Volumes use round primitives (``cyl`` / ``ell``) so the figure reads as one mass instead of stacked boxes.
    """
    sticker = "#f7f7f9"
    items: list[object] = [
        Rigid("hat_brim", "Head", (0.0, 0.58, 0.0), (3.2, 0.12, 3.2), hat, (6.0, 0.0, 3.0), "cyl"),
        Rigid("hat_crown", "Head", (0.0, 0.98, 0.0), (1.7, 0.85, 1.7), hat, shape="cyl"),
        Rigid("hat_band", "Head", (0.0, 0.7, 0.0), (1.78, 0.2, 1.78), band, shape="cyl"),
        Rigid("sticker", "Head", (0.78, 0.92, -0.55), (0.55, 0.55, 0.1), sticker, (0.0, 40.0, 0.0), "ell"),
        Rigid("hair_cap", "Head", (0.0, 0.16, 0.38), (1.6, 1.38, 1.0), hair, shape="ell"),
        Rigid("fringe", "Head", (-0.22, 0.32, -0.52), (0.85, 0.46, 0.22), hair, (0.0, 0.0, -14.0), "ell"),
        Rigid("belt", "Torso", (0.0, -0.78, 0.0), (2.06, 0.2, 1.06), "#d9dade"),
        Rigid("cuff_r", "Right Arm", (0.0, -0.82, 0.0), (1.08, 0.16, 1.08), "#d9dade"),
        Rigid("cuff_l", "Left Arm", (0.0, -0.82, 0.0), (1.08, 0.16, 1.08), "#d9dade"),
        Rigid("boot_r", "Right Leg", (0.0, -0.8, 0.0), (1.06, 0.2, 1.06), "#d9dade"),
        Rigid("boot_l", "Left Leg", (0.0, -0.8, 0.0), (1.06, 0.2, 1.06), "#d9dade"),
        Rigid("hat_brim", "Head", (0.0, 0.62, 0.0), (1.9, 0.12, 1.9), hat, (4.0, 0.0, 0.0)),
        Rigid("hat_crown", "Head", (0.0, 0.92, 0.0), (1.1, 0.55, 1.1), hat),
        Strand("coat_back", "Torso", (0.0, -0.95, 0.5), 4, 0.62, 1.7, 0.18, coat, rest_dir=(0.0, -1.0, 0.25), gravity=34, stiffness=5, drag=2.6, taper=0.9),
        Strand("coat_l", "Torso", (-0.8, -0.95, 0.45), 3, 0.6, 0.55, 0.16, coat, rest_dir=(-0.25, -1.0, 0.35), gravity=34, stiffness=5, drag=2.6),
        Strand("coat_r", "Torso", (0.8, -0.95, 0.45), 3, 0.6, 0.55, 0.16, coat, rest_dir=(0.25, -1.0, 0.35), gravity=34, stiffness=5, drag=2.6),
        Strand("hair_a", "Head", (-0.35, 0.35, 0.5), 3, 0.42, 0.34, 0.12, hair, rest_dir=(-0.2, -1.0, 0.5), gravity=24, stiffness=3.2, drag=2.2),
        Strand("hair_b", "Head", (0.0, 0.35, 0.52), 3, 0.5, 0.4, 0.12, hair, rest_dir=(0.0, -1.0, 0.6), gravity=24, stiffness=3.2, drag=2.2),
        Strand("hair_c", "Head", (0.35, 0.35, 0.5), 3, 0.42, 0.34, 0.12, hair, rest_dir=(0.2, -1.0, 0.5), gravity=24, stiffness=3.2, drag=2.2),
    ]
    return Outfit(items)


def reference_outfit(coat: str = "#0c0c10", hair: str = "#eef2f6", hat: str = "#08080b", band: str = "#26262d") -> Outfit:
    """The signature silhouette of the study reference: a wide round-brim hat with a banded crown and a speech-bubble sticker,
    a big shock of white hair (fringe over one eye + long locks), a flared long coat with broad tails, a striped belt.

    Volumes use round primitives (``cyl`` / ``ell``) so the figure reads as one mass instead of stacked boxes.
    """
    sticker = "#f7f7f9"
    items: list[object] = [
        Rigid("hat_brim", "Head", (0.0, 0.58, 0.0), (3.2, 0.12, 3.2), hat, (6.0, 0.0, 3.0), "cyl"),
        Rigid("hat_crown", "Head", (0.0, 0.98, 0.0), (1.7, 0.85, 1.7), hat, shape="cyl"),
        Rigid("hat_band", "Head", (0.0, 0.7, 0.0), (1.78, 0.2, 1.78), band, shape="cyl"),
        Rigid("sticker", "Head", (0.78, 0.92, -0.55), (0.55, 0.55, 0.1), sticker, (0.0, 40.0, 0.0), "ell"),
        Rigid("hair_back", "Head", (0.0, 0.05, 0.42), (1.75, 1.45, 1.05), hair, shape="ell"),
        Rigid("hair_l", "Head", (-0.62, 0.02, 0.02), (0.5, 1.15, 0.95), hair, shape="ell"),
        Rigid("hair_r", "Head", (0.62, 0.02, 0.02), (0.5, 1.15, 0.95), hair, shape="ell"),
        Rigid("fringe", "Head", (-0.22, 0.34, -0.5), (0.85, 0.5, 0.22), hair, (0.0, 0.0, -14.0), "ell"),
        Rigid("belt", "Torso", (0.0, -0.78, 0.0), (2.1, 0.26, 1.1), "#d9dade"),
        Rigid("belt_dark", "Torso", (0.0, -0.78, 0.0), (2.14, 0.1, 1.14), "#15151a"),
        Rigid("waist", "Torso", (0.0, -1.0, 0.05), (2.5, 0.8, 1.65), coat, shape="ell"),
        Rigid("cuff_r", "Right Arm", (0.0, -0.82, 0.0), (1.12, 0.22, 1.12), "#e6e6ea"),
        Rigid("cuff_l", "Left Arm", (0.0, -0.82, 0.0), (1.12, 0.22, 1.12), "#e6e6ea"),
        Rigid("boot_r", "Right Leg", (0.0, -0.8, 0.0), (1.1, 0.22, 1.1), "#d9dade"),
        Rigid("boot_l", "Left Leg", (0.0, -0.8, 0.0), (1.1, 0.22, 1.1), "#d9dade"),
        Strand("coat_back", "Torso", (0.0, -1.0, 0.55), 5, 0.6, 2.1, 0.2, coat, rest_dir=(0.0, -1.0, 0.3), gravity=34, stiffness=4.5, drag=2.4, taper=0.92),
        Strand("coat_l", "Torso", (-0.95, -1.0, 0.35), 4, 0.58, 0.95, 0.2, coat, rest_dir=(-0.4, -1.0, 0.3), gravity=34, stiffness=4.5, drag=2.4, taper=0.9),
        Strand("coat_r", "Torso", (0.95, -1.0, 0.35), 4, 0.58, 0.95, 0.2, coat, rest_dir=(0.4, -1.0, 0.3), gravity=34, stiffness=4.5, drag=2.4, taper=0.9),
        Strand("hair_a", "Head", (-0.5, 0.2, 0.6), 4, 0.5, 0.5, 0.32, hair, rest_dir=(-0.2, -1.0, 0.5), gravity=24, stiffness=3.0, drag=2.2, taper=0.82, shape="ell"),
        Strand("hair_b", "Head", (0.0, 0.2, 0.7), 5, 0.52, 0.62, 0.34, hair, rest_dir=(0.0, -1.0, 0.6), gravity=24, stiffness=3.0, drag=2.2, taper=0.84, shape="ell"),
        Strand("hair_c", "Head", (0.5, 0.2, 0.6), 4, 0.5, 0.5, 0.32, hair, rest_dir=(0.2, -1.0, 0.5), gravity=24, stiffness=3.0, drag=2.2, taper=0.82, shape="ell"),
    ]
    return Outfit(items)
