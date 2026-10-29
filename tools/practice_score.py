"""Objective test bench for the « practice » scene: silhouette overlap with the reference, image by image, through the REAL recording camera (no Blender needed).

Reference mask = the face-coloured pixels of the rig in each reference image (``posefit.color_labels``, the grey ball head is not coloured so the head is left out of
both masks). Mine = convex hulls of the six parts projected with the calibrated camera and the solved track (``examples.practice``).

usage: python tools/practice_score.py [--cache /tmp/ref_masks.npz] [--by 8]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples import practice as P  # noqa: E402
from tsb_engine import posefit  # noqa: E402

W, H = 982, 686   # the reference crop: the left 982 px of the 1170 x 686 viewport
FRAMES = Path("/tmp/v3c")


def ref_mask(f: int) -> np.ndarray | None:
    im = cv2.imread(str(FRAMES / f"f_{f:04d}.png"))
    lab = posefit.color_labels(im)
    fg = (lab > 0).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if n < 2:
        return None
    keep = np.zeros_like(fg)
    big = st[1:, cv2.CC_STAT_AREA].max()
    for c in range(1, n):
        if st[c, cv2.CC_STAT_AREA] > 0.08 * big:
            keep[cc == c] = 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return keep if keep.sum() >= 600 else None   # hidden or tinted by a fx


def part_hulls(a: np.ndarray, X: float, h: float, Z: float) -> list[np.ndarray]:
    pts = P.world_corners(a, X, h, Z)            # 6 parts x 8 corners, order of PARTS
    uv = P.project(pts)
    from tsb_engine.model import PARTS
    out = []
    for i, name in enumerate(PARTS):
        if name == "Head":
            continue
        out.append(cv2.convexHull(uv[i * 8 : (i + 1) * 8].astype(np.float32)).reshape(-1, 2))
    return out


def my_mask(a: np.ndarray, X: float, h: float, Z: float) -> np.ndarray:
    m = np.zeros((H, W), np.uint8)
    for hull in part_hulls(a, X, h, Z):
        cv2.fillConvexPoly(m, np.round(hull).astype(np.int32), 1)
    return m


def iou(a: np.ndarray, b: np.ndarray) -> float:
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


def load_refs(cache: str | None) -> dict[int, np.ndarray]:
    if cache and Path(cache).exists():
        z = np.load(cache)
        return {int(k): z[k] for k in z.files}
    refs = {}
    for f in range(P.F0, P.F1 + 1):
        m = ref_mask(f)
        if m is not None:
            refs[f] = m
    if cache:
        np.savez_compressed(cache, **{str(k): v for k, v in refs.items()})
    return refs


def evaluate(ang: np.ndarray, refs: dict[int, np.ndarray]):
    X, Z, air = P.solve_track(ang)
    res = {}
    for i in range(P.N):
        f = P.F0 + i
        if f in refs:
            h = 3.0 + P.lowest(ang[i]) + float(air[i])
            res[f] = iou(my_mask(ang[i], float(X[i]), h, float(Z[i])).astype(bool), refs[f].astype(bool))
    return res, (X, Z, air)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/ref_masks.npz")
    ap.add_argument("--by", type=int, default=8)
    a = ap.parse_args()
    refs = load_refs(a.cache)
    res, _ = evaluate(P.keyed_angles(), refs)
    v = np.array(list(res.values()))
    print(f"{len(res)} scored images of {P.N}: mean IoU {v.mean():.3f}  median {np.median(v):.3f}  <0.3: {(v < 0.3).sum()}  >0.6: {(v > 0.6).sum()}")
    for f0 in range(P.F0, P.F1, a.by * 2):
        seg = [res[f] for f in range(f0, min(f0 + a.by * 2, P.F1 + 1)) if f in res]
        if seg:
            print(f"  {f0:3d}-{min(f0 + a.by * 2 - 1, P.F1):3d}: {np.mean(seg):.2f} (n={len(seg)})")


if __name__ == "__main__":
    main()
