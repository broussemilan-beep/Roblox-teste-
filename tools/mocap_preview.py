"""Stick-figure contact sheet of a BVH clip (to pick which seconds to use).

usage: python tools/mocap_preview.py FILE.bvh OUT.png [--t0 0 --t1 20 --n 36 --view front|side|three]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import mocap  # noqa: E402

BONES = [("Hips", "LowerBack"), ("LowerBack", "Spine"), ("Spine", "Spine1"), ("Spine1", "Neck"), ("Neck", "Head"),
         ("Spine1", "LeftShoulder"), ("LeftShoulder", "LeftArm"), ("LeftArm", "LeftForeArm"), ("LeftForeArm", "LeftHand"),
         ("Spine1", "RightShoulder"), ("RightShoulder", "RightArm"), ("RightArm", "RightForeArm"), ("RightForeArm", "RightHand"),
         ("Hips", "LeftUpLeg"), ("LeftUpLeg", "LeftLeg"), ("LeftLeg", "LeftFoot"), ("LeftFoot", "LeftToeBase"),
         ("Hips", "RightUpLeg"), ("RightUpLeg", "RightLeg"), ("RightLeg", "RightFoot"), ("RightFoot", "RightToeBase")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvh")
    ap.add_argument("out")
    ap.add_argument("--t0", type=float, default=0)
    ap.add_argument("--t1", type=float, default=None)
    ap.add_argument("--n", type=int, default=36)
    ap.add_argument("--view", default="three")
    a = ap.parse_args()
    b = mocap.parse(a.bvh)
    pos, _ = mocap.fk(b)
    ix = {n: i for i, n in enumerate(b.names)}
    t1 = a.t1 if a.t1 is not None else len(pos) / b.fps
    frames = np.linspace(int(a.t0 * b.fps), min(int(t1 * b.fps), len(pos) - 1), a.n).astype(int)
    tiles = []
    ang = np.radians(35 if a.view == "three" else (0 if a.view == "front" else 90))
    c, s = np.cos(ang), np.sin(ang)
    lo = pos[..., 1].min(); hi = pos[..., 1].max()
    for f in frames:
        P = pos[f]
        center = P[ix["Hips"]]
        x = (P[:, 0] - center[0]) * c + (P[:, 2] - center[2]) * s
        y = P[:, 1]
        im = np.full((220, 160, 3), 30, np.uint8)
        sc = 200.0 / max(hi - lo, 1e-6) * 0.9
        pt = lambda j: (int(80 + x[j] * sc), int(210 - (y[j] - lo) * sc))
        cv2.line(im, (0, int(210 - (0 - lo) * sc * 0) ), (160, 210), (60, 60, 60), 1)
        for u, v in BONES:
            if u in ix and v in ix:
                col = (80, 200, 255) if "Left" in u + v else ((255, 160, 80) if "Right" in u + v else (200, 200, 200))
                cv2.line(im, pt(ix[u]), pt(ix[v]), col, 2)
        cv2.circle(im, pt(ix["Head"]), 5, (255, 255, 255), -1)
        cv2.putText(im, f"{f / b.fps:.2f}s", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(im)
    cols = 9
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(a.out, np.vstack([np.hstack(tiles[i : i + cols]) for i in range(0, len(tiles), cols)]))
    print(Path(a.bvh).name, "frames", len(pos), "fps", round(b.fps), "dur", round(len(pos) / b.fps, 1), "s ->", a.out)


if __name__ == "__main__":
    main()
