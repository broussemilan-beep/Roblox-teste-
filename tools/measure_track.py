"""Measure where the rig is on screen in every reference image: median x of its coloured pixels and the lowest coloured pixel (its ground contact).

usage: python tools/measure_track.py FRAMES_DIR FIRST LAST OUT.json
Frames hidden or tinted by a fx (fewer than 600 coloured pixels) are written as null; the scene interpolates them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import posefit  # noqa: E402


def main():
    fdir, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    rows = {}
    for f in range(a, b + 1):
        im = cv2.imread(f"{fdir}/f_{f:04d}.png")
        lab = posefit.color_labels(im)
        fg = (lab > 0).astype(np.uint8)
        n, cc, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        keep = np.zeros_like(fg)
        for c in range(1, n):
            if st[c, cv2.CC_STAT_AREA] > 0.08 * max(st[1:, cv2.CC_STAT_AREA].max(), 1):
                keep[cc == c] = 1
        ys, xs = np.nonzero(keep)
        if len(xs) < 600:
            rows[f] = None
            continue
        rows[f] = {"x": float(np.median(xs)), "foot": float(np.percentile(ys, 99.5)), "top": float(np.percentile(ys, 0.5)), "w": float(xs.max() - xs.min()), "n": int(len(xs))}
    Path(out).write_text(json.dumps(rows))
    ok = [v for v in rows.values() if v]
    print(len(ok), "of", len(rows), "images measured")


if __name__ == "__main__":
    main()
