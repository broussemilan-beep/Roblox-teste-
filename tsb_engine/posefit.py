"""Copy an animation out of a video: fit the R6 rig to the hero's silhouette on every image.

The project's own hand-made poses ("a pose library", random accents) read as scribbles next to the reference. Instead of inventing poses I cannot see, extract them: the hero
is segmented in the reference (SAM 2, ``tracker.py`` / ``hero.py``, or a hard threshold on the black-on-white impact frames), then the 16 joint angles of the rig, a scale and a
translation are searched so that the rig's projected silhouette overlaps the mask as much as possible (maximum IoU), image after image, each image warm-started from the previous one
and pulled toward it (temporal coherence).

Model of the camera: orthographic (weak perspective), looking along world -Z, so a hero running along +X is seen from the side; ``ry`` (the heading) is one of the searched
angles, so a three-quarter view is just a different ``ry``. This is an approximation of a perspective video: the *angles* are what is kept, positions and scale come from the film's own
path and camera.

What this cannot do (said once): a silhouette is ambiguous (left and right limbs swap, a limb pointing at the camera is invisible, arms and legs of the same side overlap); the temporal
prior only picks the smoothest of the equally good answers, so the result is a plausible copy, not the true pose; the mask also contains the hair, the blade and the dust that the R6 rig does not
have, which caps the IoU.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from .authoring import root_pose
from .kinematics import corners, part_transforms, pose_transform
from .mathutil import compose, translate
from .model import PARTS, Pose

NAMES = ["ry", "rx", "rz", "T_rx", "T_ry", "T_rz", "H_rx", "H_ry", "RA_rx", "RA_rz", "LA_rx", "LA_rz", "RL_rx", "RL_rz", "LL_rx", "LL_rz"]
LO = np.array([-720, -200, -120, -90, -70, -45, -60, -70, -200, -100, -200, -100, -120, -60, -120, -60], float)
HI = np.array([720, 200, 120, 60, 70, 45, 70, 70, 200, 100, 200, 100, 120, 60, 120, 60], float)
HERO_H = 5.5  # studs, standing, for the initial scale
CANVAS = 128


def sample(p: np.ndarray) -> dict[str, Pose]:
    return {
        "Torso": Pose((0, 0, 0), (p[3], p[4], p[5])),
        "Head": Pose((0, 0, 0), (p[6], p[7], 0)),
        "Right Arm": Pose((0, 0, 0), (p[8], 0, p[9])),
        "Left Arm": Pose((0, 0, 0), (p[10], 0, p[11])),
        "Right Leg": Pose((0, 0, 0), (p[12], 0, p[13])),
        "Left Leg": Pose((0, 0, 0), (p[14], 0, p[15])),
    }


def part_polys(p: np.ndarray) -> list[np.ndarray]:
    """Orthographic screen polygons (studs, x right / y up) of the six parts, root at the origin; the root attitude uses the engine's intrinsic helper."""
    root = compose(translate((0.0, 3.0, 0.0)), pose_transform(root_pose(0.0, 3.0, 0.0, p[1], p[0], p[2])))
    tf = part_transforms(sample(p), root=root)
    out = []
    for part in PARTS:
        c = np.array(corners(part, tf[part]), float)
        pts = np.stack([c[:, 0], c[:, 1]], 1)
        out.append(cv2.convexHull(pts.astype(np.float32)).reshape(-1, 2))
    return out


def render(p: np.ndarray, tx: float, ty: float, s: float, size: int = CANVAS) -> np.ndarray:
    m = np.zeros((size, size), np.uint8)
    for poly in part_polys(p):
        pts = np.stack([tx + s * poly[:, 0], ty - s * poly[:, 1]], 1)
        cv2.fillConvexPoly(m, np.round(pts).astype(np.int32), 1)
    return m


def normalise_mask(mask: np.ndarray, size: int = CANVAS) -> tuple[np.ndarray, tuple[float, float, float]]:
    """Crop the mask to its bounding box (square, with margin) and resize to ``size``; returns (mask, (x0, y0, side) of the crop in the source image)."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return np.zeros((size, size), np.uint8), (0.0, 0.0, 1.0)
    cx, cy = (xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) * 1.25 + 4
    x0, y0 = cx - side / 2, cy - side / 2
    M = np.array([[size / side, 0, -x0 * size / side], [0, size / side, -y0 * size / side]], np.float32)
    out = cv2.warpAffine(mask.astype(np.uint8), M, (size, size), flags=cv2.INTER_AREA)
    return (out > 0).astype(np.uint8), (float(x0), float(y0), float(side))


def iou(a: np.ndarray, b: np.ndarray) -> float:
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


@dataclass
class Fit:
    params: np.ndarray  # 16 joint angles (degrees)
    tx: float
    ty: float
    s: float  # pixels per stud on the CANVAS
    iou: float


def _cost(theta: np.ndarray, target: np.ndarray, prev: np.ndarray | None, w_prev: float) -> float:
    p = np.clip(theta[:16], LO, HI)
    m = render(p, theta[16], theta[17], theta[18])
    c = 1.0 - iou(m, target)
    if prev is not None:
        c += w_prev * float(np.sum(((p - prev[:16]) / 60.0) ** 2)) / 16.0
    c += 0.5 * float(np.sum(np.maximum(0, np.abs(theta[:16]) - HI) ** 2)) / 1e4
    return c


def fit_frame(mask_c: np.ndarray, init: Fit | None, prev: Fit | None = None, pop: int = 90, iters: int = 36, w_prev: float = 0.35, seed: int = 0) -> Fit:
    """Cross-entropy search of the 19 numbers (16 angles, tx, ty, s) for one normalised mask."""
    rng = np.random.RandomState(seed)
    if init is None:
        base = np.zeros(19)
        base[0] = 270.0
        base[3] = -20
        base[6] = 15
        base[16], base[17], base[18] = CANVAS / 2, CANVAS * 0.55, CANVAS * 0.80 / HERO_H
        sd = np.concatenate([[25, 25, 20, 20, 15, 10, 15, 15, 60, 40, 60, 40, 45, 25, 45, 25], [4, 4, 3]])
    else:
        base = np.concatenate([init.params, [init.tx, init.ty, init.s]])
        sd = np.concatenate([[12, 12, 10, 10, 8, 5, 8, 8, 35, 20, 35, 20, 25, 12, 25, 12], [3, 3, 2]])
    prev_p = None if prev is None else np.concatenate([prev.params, [prev.tx, prev.ty, prev.s]])
    mean, best, best_c = base.copy(), base.copy(), _cost(base, mask_c, prev_p, w_prev)
    for it in range(iters):
        cand = mean + rng.randn(pop, 19) * sd
        cand[0] = mean  # elitism: keep the mean in the pool
        costs = np.array([_cost(c, mask_c, prev_p, w_prev) for c in cand])
        order = np.argsort(costs)
        if costs[order[0]] < best_c:
            best_c, best = float(costs[order[0]]), cand[order[0]].copy()
        elite = cand[order[: max(6, pop // 6)]]
        mean = 0.5 * mean + 0.5 * elite.mean(0)
        sd = 0.5 * sd + 0.5 * (elite.std(0) + 0.05 * np.concatenate([np.ones(16) * 2, [0.3, 0.3, 0.1]]))
    p = np.clip(best[:16], LO, HI)
    return Fit(p, float(best[16]), float(best[17]), float(best[18]), iou(render(p, best[16], best[17], best[18]), mask_c))


def fit_sequence(masks: list[np.ndarray], restarts: int = 2, **kw) -> list[Fit]:
    """Fit every mask of a shot in order, each warm-started from (and pulled toward) the previous image; a blank mask repeats the previous fit."""
    fits: list[Fit | None] = []
    prev: Fit | None = None
    for i, m in enumerate(masks):
        mc, _ = normalise_mask(m)
        if mc.sum() < 30:
            fits.append(prev)
            continue
        best = None
        for r in range(restarts):
            f = fit_frame(mc, prev, prev, seed=i * 7 + r, **kw)
            if best is None or f.iou > best.iou:
                best = f
        fits.append(best)
        prev = best
    return fits  # type: ignore[return-value]


def overlay(mask: np.ndarray, fit: Fit, size: int = 256) -> np.ndarray:
    """Reference mask (green) and the fitted rig (red) on the normalised canvas, for looking at the fit."""
    mc, _ = normalise_mask(mask)
    mm = render(fit.params, fit.tx, fit.ty, fit.s)
    img = np.zeros((CANVAS, CANVAS, 3), np.uint8)
    img[..., 1] = mc * 200
    img[..., 2] = mm * 200
    img[(mc > 0) & (mm > 0)] = (200, 200, 60)
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_NEAREST)
