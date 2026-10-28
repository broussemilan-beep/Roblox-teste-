"""Readability checks for a pose *as seen from the shot camera* (numpy z-buffer, no viewer needed).

The linter judges the rig; this module judges the picture. A key pose that is correct on paper can still be a black
clump on screen: limbs hidden behind the torso, the character tiny in the frame, the strike pointing at the lens.
These are the things a human animator fixes by looking, so we measure them and fix them in a loop.

Metrics per character and frame (all in 0..1 unless noted):

* ``height``    silhouette height / frame height (combat shots want 0.3-0.7, macros more)
* ``visible``   per part: pixels visible / pixels the part would cover alone (self- and other-occlusion)
* ``limb_min``  worst visibility among the four limbs (a limb under 0.35 vanishes into the body)
* ``inside``    fraction of the silhouette that is inside the frame
* ``fill``      silhouette area / bounding-box area (a spread-out pose with air between limbs scores low, a clump high)

Camera model = the viewer's: vertical field of view, 16:9, roll, look-at basis (see ``viewer.template.html`` ``basis``).
Extras (hat, hair, coat) are ignored: the six R6 blocks carry the silhouette.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .kinematics import SIZES
from .mathutil import apply
from .model import PARTS

NEAR = 0.25
LIMBS = ("Right Arm", "Left Arm", "Right Leg", "Left Leg")
# faces as indices into the 8 corners produced by product((-1, 1), repeat=3): bit 2 = x, bit 1 = y, bit 0 = z
_FACES = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]


def _corners(part: str, tf) -> list[tuple[float, float, float]]:
    sx, sy, sz = SIZES[part]
    out = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                out.append(apply(tf, (x * sx / 2, y * sy / 2, z * sz / 2)))
    return out


def _basis(pos, tgt, roll):
    f = np.array(tgt, float) - np.array(pos, float)
    f /= np.linalg.norm(f) or 1.0
    up = np.array([0.0, 0.0, -1.0]) if abs(f[1]) > 0.98 else np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r) or 1.0
    u = np.cross(r, f)
    if roll:
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        r, u = r * c + u * s, u * c - r * s
    return np.array(pos, float), f, r, u


def _clip_near(poly):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ina, inb = a[2] >= NEAR, b[2] >= NEAR
        if ina:
            out.append(a)
        if ina != inb:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return out


def _fill_poly(zbuf, ids, pts, pid, W, H):
    """Rasterise a convex camera-space polygon (x, y, z) with a z-buffer."""
    n = len(pts)
    if n < 3:
        return
    for k in range(1, n - 1):
        tri = (pts[0], pts[k], pts[k + 1])
        xs = [t[0] for t in tri]
        ys = [t[1] for t in tri]
        x0, x1 = max(0, int(math.floor(min(xs)))), min(W - 1, int(math.ceil(max(xs))))
        y0, y1 = max(0, int(math.floor(min(ys)))), min(H - 1, int(math.ceil(max(ys))))
        if x0 > x1 or y0 > y1:
            continue
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = w0 * az + w1 * bz + w2 * cz
        sub_z = zbuf[y0 : y1 + 1, x0 : x1 + 1]
        sub_i = ids[y0 : y1 + 1, x0 : x1 + 1]
        upd = inside & (z < sub_z)
        sub_z[upd] = z[upd]
        sub_i[upd] = pid


def render_ids(scene, f: int, W: int = 320, H: int = 180, only: tuple[int, int] | None = None) -> np.ndarray:
    """Part-id image for frame ``f``. id = 1 + char_index * 6 + part_index. ``only`` restricts to one (char, part).

    The picture is ``W x H``; give ``W = round(H * scene.cine.aspect)`` for films with a non-16:9 aspect."""
    pos, tgt, fov, roll = scene.cine.camera_state(f)
    o, fw, r, u = _basis(pos, tgt, roll)
    focal = (H / 2) / math.tan(math.radians(fov) / 2)
    zbuf = np.full((H, W), np.inf)
    ids = np.zeros((H, W), np.int16)
    for ci, ch in enumerate(scene.characters):
        wp = ch.world_parts(f - f % scene.hold)
        for pi, part in enumerate(PARTS):
            if only is not None and only != (ci, pi):
                continue
            cs = []
            for p in _corners(part, wp[part]):
                d = np.array(p) - o
                cs.append((float(d @ r), float(d @ u), float(d @ fw)))
            for face in _FACES:
                poly = _clip_near([cs[i] for i in face])
                if len(poly) < 3:
                    continue
                pts = [(W / 2 + focal * x / z, H / 2 - focal * y / z, z) for x, y, z in poly]
                _fill_poly(zbuf, ids, pts, 1 + ci * 6 + pi, W, H)
    return ids


@dataclass
class PoseReport:
    char: str
    frame: int
    height: float
    inside: float
    fill: float
    visible: dict[str, float]
    limb_min: float
    area: int

    def flags(self, tall=(0.28, 0.95), min_limb=0.35, min_inside=0.85) -> list[str]:
        out = []
        if self.area == 0:
            return ["not on screen"]
        if self.height < tall[0]:
            out.append(f"tiny in frame ({self.height:.2f})")
        if self.height > tall[1]:
            out.append(f"fills more than the frame ({self.height:.2f})")
        if self.limb_min < min_limb:
            worst = min(LIMBS, key=lambda p: self.visible[p])
            out.append(f"{worst} hidden ({self.limb_min:.2f})")
        if self.inside < min_inside:
            out.append(f"cut by frame edge ({self.inside:.2f})")
        return out


def report(scene, f: int, W: int = 320, H: int = 180, solo: bool = True) -> list[PoseReport]:
    ids = render_ids(scene, f, W, H)
    reps = []
    for ci, ch in enumerate(scene.characters):
        mask = (ids >= 1 + ci * 6) & (ids < 1 + ci * 6 + 6)
        area = int(mask.sum())
        vis: dict[str, float] = {}
        for pi, part in enumerate(PARTS):
            got = int((ids == 1 + ci * 6 + pi).sum())
            if solo:
                alone = int((render_ids(scene, f, W, H, only=(ci, pi)) > 0).sum())
                vis[part] = got / alone if alone else 1.0
            else:
                vis[part] = 1.0
        if area:
            ys, xs = np.nonzero(mask)
            height = (ys.max() - ys.min() + 1) / H
            box = (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)
            fill = area / box
        else:
            height = fill = 0.0
        # share of the silhouette inside the frame: project with a margin by re-rendering a wider canvas is costly;
        # approximate with how many silhouette pixels touch the border
        if area:
            border = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
            inside = 1.0 - min(1.0, border / max(1, math.sqrt(area)) * 0.25)
        else:
            inside = 0.0
        reps.append(PoseReport(ch.name, f, height, inside, fill, vis, min(vis[p] for p in LIMBS), area))
    return reps


def format_reports(scene, frames: list[int], **kw) -> str:
    lines = [f"{'f':>4} {'char':<7}{'h':>5}{'fill':>6}{'limb':>6}  flags"]
    for f in frames:
        for r in report(scene, f, **kw):
            lines.append(f"{f:>4} {r.char:<7}{r.height:>5.2f}{r.fill:>6.2f}{r.limb_min:>6.2f}  {'; '.join(r.flags())}")
    return "\n".join(lines)
