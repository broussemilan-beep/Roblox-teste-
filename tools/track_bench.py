"""Score the SAM 2 tracker on the labelled bench against the engine's exact part masks.

usage: python tools/track_bench.py [--dir /tmp/bench] [--classes ghost_jab,smear_single,real_combo,held_vfx] [--out /tmp/track_bench.json]

For every segment the hero's striking arm(s) are prompted with ONE point taken from the engine's own mask on the first frame (standing in
for "me pointing at the arm"), tracked through the segment, and compared with the engine's true arm mask on every frame (IoU). The tracked
reach (how far the arm extends toward the victim) is then analysed: a vfx-made multi-hit makes it flip back and forth on every image.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.eyes_bench import build  # noqa: E402
from tsb_engine import readability, tracker  # noqa: E402
from tsb_engine.model import PARTS  # noqa: E402

H = 392


def gt_masks(scene, f0_sample: int, n: int, part: str, size) -> np.ndarray:
    W, Hh = size
    out = []
    pid = 1 + PARTS.index(part)
    for k in range(n):
        ids = readability.render_ids(scene, 2 * (f0_sample + k), W // 2, Hh // 2)
        out.append(cv2.resize((ids == pid).astype(np.uint8), (W, Hh), interpolation=cv2.INTER_NEAREST).astype(bool))
    return np.stack(out)


def prompt_point(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return None
    cx, cy = xs.mean(), ys.mean()
    j = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    return float(xs[j]), float(ys[j])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="/tmp/bench")
    p.add_argument("--classes", default="ghost_jab,smear_single,real_combo,held_vfx")
    p.add_argument("--out", default="/tmp/track_bench.json")
    p.add_argument("--variants", type=int, default=3)
    a = p.parse_args()
    scene, segs = build()
    want = set(a.classes.split(","))
    res = []
    for seg in segs:
        if seg["class"] not in want or seg["variant"] >= a.variants:
            continue
        s0, n = seg["s0"], seg["s1"] - seg["s0"] + 1
        imgs = [cv2.imread(f"{a.dir}/f_{s0 + k:04d}.png") for k in range(n)]
        size = (imgs[0].shape[1], imgs[0].shape[0])
        arms = [seg["arm"]] if seg.get("arm") else ["Right Arm", "Left Arm"]
        gts = {arm: gt_masks(scene, s0, n, arm, size) for arm in arms}
        prompts, ids = [], {}
        for k, arm in enumerate(arms):
            first = next((i for i in range(n) if gts[arm][i].sum() > 60), None)
            pt = prompt_point(gts[arm][first]) if first is not None else None
            if pt is None:
                continue
            ids[arm] = k + 1
            prompts.append(tracker.Prompt(k + 1, first, points=[pt], labels=[1]))
        if not prompts:
            continue
        t = time.time()
        got = tracker.track(imgs, prompts)
        row = {"class": seg["class"], "variant": seg["variant"], "arms": {}, "seconds": round(time.time() - t, 1)}
        d_hero = gt_masks(scene, s0, n, "Torso", size)
        for arm, oid in ids.items():
            ious = [tracker.iou(got[oid][i], gts[arm][i]) for i in range(n) if gts[arm][i].sum() > 60]
            m = tracker.measure(got[oid], toward=1)
            gm = tracker.measure(gts[arm], toward=1)
            rev, rate = tracker.alternation(m["reach"][m["area"] > 0], 0.012)
            grev, grate = tracker.alternation(gm["reach"][gm["area"] > 0], 0.012)
            row["arms"][arm] = {"iou_mean": round(float(np.nanmean(ious)), 3), "iou_min": round(float(np.nanmin(ious)), 3),
                                "alt_tracked": [rev, round(rate, 2)], "alt_truth": [grev, round(grate, 2)],
                                "reach_range_tracked": round(float(np.ptp(m["reach"][m["area"] > 0])), 3), "reach_range_truth": round(float(np.ptp(gm["reach"][gm["area"] > 0])), 3)}
        res.append(row)
        print(json.dumps(row), flush=True)
        Path(a.out).write_text(json.dumps(res, indent=1))
    ious = [v["iou_mean"] for r in res for v in r["arms"].values()]
    print(f"\nmean IoU over {len(ious)} tracked arms: {np.mean(ious):.3f}")


if __name__ == "__main__":
    main()
