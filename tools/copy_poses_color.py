"""Copy the pose of a face-coloured test rig out of a screen recording (see ``tsb_engine.posefit`` colour section).

usage: python tools/copy_poses_color.py FRAMES_DIR FIRST LAST --elev 28 --out NAME.json [--overlay sheet.png]
Frames are ``f_%04d.png`` crops of the viewport. For each image: class map of the rig's face colours -> normalised crop -> search of 16 angles + scale + translation
(warm-started from the previous image). Writes angles, the crop (x0, y0, side in source pixels) and the fit's (tx, ty, s) so the image position can be recovered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tsb_engine import posefit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("--elev", type=float, default=28.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay")
    ap.add_argument("--iters", type=int, default=40)
    a = ap.parse_args()
    out = {"names": posefit.NAMES, "elev": a.elev, "first_frame": a.first, "frames": []}
    prev = None
    vis = []
    for f in range(a.first, a.last + 1):
        img = cv2.imread(str(Path(a.dir) / f"f_{f:04d}.png"))
        lab = posefit.color_labels(img)
        # drop tiny specks (fx), keep the big blob(s)
        fg = (lab > 0).astype(np.uint8)
        n, cc, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        keep = np.zeros_like(fg)
        for c in range(1, n):
            if st[c, cv2.CC_STAT_AREA] > 0.08 * max(st[1:, cv2.CC_STAT_AREA].max(), 1):
                keep[cc == c] = 1
        lab = lab * keep
        tc, (x0, y0, side) = posefit.normalise_labels(lab)
        if (lab > 0).sum() < 1800:   # the rig is hidden or tinted by a fx (purple / pink flash): no usable colours
            out["frames"].append({"f": f, "angles": None})
            continue
        fit = posefit.fit_frame_labels(tc, prev, prev, elev=a.elev, iters=a.iters, seed=f)
        prev = fit
        out["frames"].append({"f": f, "angles": [round(float(v), 1) for v in fit.params], "score": round(fit.iou, 3), "crop": [round(x0, 1), round(y0, 1), round(side, 1)],
                              "fit": [round(fit.tx, 2), round(fit.ty, 2), round(fit.s, 3)]})
        print(f, round(fit.iou, 2), flush=True)
        if a.overlay:
            m = posefit.render_labels(fit.params, fit.tx, fit.ty, fit.s, a.elev)
            pal = np.array([[0, 0, 0], [40, 40, 220], [220, 90, 40], [60, 190, 60], [40, 150, 240], [230, 220, 90], [40, 220, 230], [200, 200, 200]], np.uint8)
            both = np.hstack([pal[tc], pal[m]])
            cv2.putText(both, str(f), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            vis.append(both)
    Path(a.out).write_text(json.dumps(out))
    sc = [x["score"] for x in out["frames"] if x.get("angles")]
    print(f"{len(sc)} images, mean score {np.mean(sc):.2f}, min {np.min(sc):.2f}")
    if a.overlay and vis:
        cols = 6
        while len(vis) % cols:
            vis.append(np.zeros_like(vis[0]))
        cv2.imwrite(a.overlay, np.vstack([np.hstack(vis[i : i + cols]) for i in range(0, len(vis), cols)]))


if __name__ == "__main__":
    main()
