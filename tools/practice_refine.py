"""Refine the hand-authored key poses of « practice » against the reference silhouettes, within small bounds around what I authored.

Each key's 16 angles are searched (cross-entropy) to raise the mean silhouette IoU of the images the key influences (its two neighbours' span), with a penalty for
leaving the authored pose (so the animator's intent - anticipation, overshoot, the story - is kept) and hard bounds around it. The track (X, Z, air) is held fixed during
the search and solved again at the end.

usage: python tools/practice_refine.py [--passes 2] [--out docs/research/reference-poses/practice_keys_refined.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

os.environ["PRACTICE_AUTHORED_ONLY"] = "1"   # refine from the authored keys, not from a previous refinement
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import practice_score as S  # noqa: E402
from examples import practice as P  # noqa: E402
from examples.practice_keys import KEYS, NAMES  # noqa: E402

BOUND = np.array([45, 40, 40, 35, 35, 25, 30, 30, 50, 40, 50, 40, 45, 25, 45, 25], float)   # per angle, around the authored value
SCALE = 35.0
W_PRIOR = 0.10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--pop", type=int, default=36)
    ap.add_argument("--iters", type=int, default=5)
    ap.add_argument("--out", default=str(ROOT / "docs/research/reference-poses/practice_keys_refined.json"))
    a = ap.parse_args()
    refs = S.load_refs("/tmp/ref_masks.npz")
    keys = sorted(KEYS)
    base = {f: np.array([KEYS[f].get(n, 0.0) for n in NAMES], float) for f in keys}
    cur = {f: v.copy() for f, v in base.items()}
    ang0 = P.keyed_angles()
    X, Z, air = P.solve_track(ang0)
    rng = np.random.RandomState(1)

    def apply(f, v):
        for n, x in zip(NAMES, v):
            KEYS[f][n] = float(x)

    def cost_frames(frames):
        ang = P.keyed_angles()
        c = []
        for f in frames:
            i = f - P.F0
            if f in refs and 0 <= i < P.N:
                h = 3.0 + P.lowest(ang[i]) + float(air[i])
                c.append(1.0 - S.iou(S.my_mask(ang[i], float(X[i]), h, float(Z[i])).astype(bool), refs[f].astype(bool)))
        return float(np.mean(c)) if c else 0.0

    def total():
        ang = P.keyed_angles()
        r, _ = S.evaluate(ang, refs)
        return float(np.mean(list(r.values())))

    print("start mean IoU", round(total(), 4), flush=True)
    for ps in range(a.passes):
        t0 = time.time()
        for k, f in enumerate(keys):
            lo_f = keys[k - 1] if k > 0 else f
            hi_f = keys[k + 1] if k + 1 < len(keys) else f
            frames = range(max(lo_f - 1, P.F0), min(hi_f + 3, P.F1 + 1))
            v0 = cur[f].copy()
            apply(f, v0)
            best_v, best_c = v0, cost_frames(frames) + 0.0
            mean, sd = v0.copy(), np.full(16, 9.0)
            lo, hi = base[f] - BOUND, base[f] + BOUND
            for it in range(a.iters):
                cand = np.clip(mean + rng.randn(a.pop, 16) * sd, lo, hi)
                cand[0] = mean
                cs = []
                for v in cand:
                    apply(f, v)
                    cs.append(cost_frames(frames) + W_PRIOR * float(np.mean(((v - base[f]) / SCALE) ** 2)))
                cs = np.array(cs)
                order = np.argsort(cs)
                if cs[order[0]] < best_c + W_PRIOR * float(np.mean(((best_v - base[f]) / SCALE) ** 2)):
                    best_v, best_c = cand[order[0]].copy(), cost_frames(frames)
                elite = cand[order[: max(5, a.pop // 6)]]
                mean = 0.5 * mean + 0.5 * elite.mean(0)
                sd = 0.6 * sd + 0.4 * (elite.std(0) + 1.5)
            cur[f] = best_v
            apply(f, best_v)
        print(f"pass {ps + 1}: mean IoU {total():.4f}  ({time.time() - t0:.0f}s)", flush=True)
        json.dump({str(f): {n: round(float(x), 1) for n, x in zip(NAMES, cur[f])} for f in keys}, open(a.out, "w"), indent=1)
    X2, Z2, air2 = P.solve_track(P.keyed_angles())
    print("final mean IoU (track re-solved)", round(float(np.mean(list(S.evaluate(P.keyed_angles(), refs)[0].values()))), 4))


if __name__ == "__main__":
    main()
