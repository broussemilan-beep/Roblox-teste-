"""Copy the hero's animation out of a reference shot: track him (SAM 2), fit the R6 rig to his silhouette on every image, save the joint angles.

usage: python tools/copy_poses.py FRAMES_DIR FIRST LAST PROMPT_FRAME X,Y X,Y ... --out docs/research/reference-poses/NAME.json
Frame files are ``f_%04d.png`` named by absolute image index. Writes per image: the 16 angles (``tsb_engine.posefit.NAMES``), the fit's IoU and the SAM presence logit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tsb_engine import posefit, tracker  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("prompt", type=int)
    ap.add_argument("points", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay")
    a = ap.parse_args()
    frames = [cv2.imread(str(Path(a.dir) / f"f_{f:04d}.png")) for f in range(a.first, a.last + 1)]
    pts = [tuple(float(v) for v in p.split(",")) for p in a.points]
    masks, scores = tracker.track(frames, [tracker.Prompt(1, a.prompt - a.first, points=pts)], return_scores=True)
    ms = list(masks[1])
    fits = posefit.fit_sequence(ms)
    out = {"names": posefit.NAMES, "first_frame": a.first, "prompt": {"frame": a.prompt, "points": [list(p) for p in pts]}, "frames": []}
    for i, (m, f) in enumerate(zip(ms, fits)):
        out["frames"].append({"f": a.first + i, "angles": None if f is None else [round(float(v), 1) for v in f.params], "iou": None if f is None else round(f.iou, 3),
                              "logit": round(float(scores[1][i]), 1)})
    Path(a.out).write_text(json.dumps(out))
    ious = [x["iou"] for x in out["frames"] if x["iou"] is not None]
    print(f"{len(ious)} images fitted, mean IoU {np.mean(ious):.2f}, min {np.min(ious):.2f}")
    if a.overlay:
        ims = []
        for i, (m, f) in enumerate(zip(ms, fits)):
            if f is None:
                continue
            o = posefit.overlay(m, f, 128)
            cv2.putText(o, str(a.first + i), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            ims.append(o)
        cols = 10
        while len(ims) % cols:
            ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(a.overlay, np.vstack([np.hstack(ims[i : i + cols]) for i in range(0, len(ims), cols)]))


if __name__ == "__main__":
    main()
