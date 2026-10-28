"""Compare hand-read key poses (examples/practice_keys.py) with the reference crops: reference class map | proxy render, one row of pairs per key.

usage: python tools/keypose_lab.py FRAMES_DIR OUT.png [first last]
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.practice_keys import KEYS, NAMES  # noqa: E402
from tsb_engine import posefit  # noqa: E402

PAL = np.array([[0, 0, 0], [40, 40, 220], [220, 90, 40], [60, 190, 60], [40, 150, 240], [230, 220, 90], [40, 220, 230], [200, 200, 200]], np.uint8)


def vec(k: dict) -> np.ndarray:
    p = np.zeros(16)
    for n, v in k.items():
        if n in NAMES:
            p[NAMES.index(n)] = v
    return p


def main():
    fdir, out = sys.argv[1], sys.argv[2]
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    hi = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    tiles = []
    for f, k in sorted(KEYS.items()):
        if not lo <= f <= hi:
            continue
        im = cv2.imread(f"{fdir}/f_{f:04d}.png")
        lab = posefit.color_labels(im) if hasattr(posefit, "color_labels") else None
        ref = np.zeros((128, 128, 3), np.uint8)
        if lab is not None and (lab > 0).sum() > 200:
            tc, _ = posefit.normalise_labels(lab)
            ref = PAL[tc]
        m = posefit.render_labels(vec(k), 64, 76 - 10 * min(1.0, k.get("air", 0)), 17.0, 28.0)
        pr = PAL[m]
        t = np.hstack([ref, pr])
        cv2.putText(t, str(f), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        tiles.append(cv2.resize(t, (384, 192), interpolation=cv2.INTER_NEAREST))
    while len(tiles) % 3:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(out, np.vstack([np.hstack(tiles[i : i + 3]) for i in range(0, len(tiles), 3)]))
    print(len(tiles), "keys ->", out)


if __name__ == "__main__":
    main()
