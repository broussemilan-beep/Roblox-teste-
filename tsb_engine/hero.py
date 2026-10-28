"""Follow the hero through a reference shot and measure what the *camera and the body* do: where he sits in the frame, how big he is, how fast he cycles.

The first versions of this project guessed the follow camera and the stride cadence; the user's verdict was "the follow is weird" and "the run looks like a
puppet". Measuring them is the cure: ``follow`` tracks one object with SAM 2 (``tracker.py``, one prompt = a few points *I* put on the hero's head, torso
and legs) and returns, per image,

* ``cx, cy``  centroid in picture heights (0..aspect, 0..1) - the framing: does the camera keep him on a fixed spot or does he drift?
* ``h, w``    height and width of the silhouette in picture heights - his size in frame (distance to the camera) and the leg spread (stride phase),
* ``area``    mask area, ``logit`` the model's own presence score (reliable above ~7).

``cadence`` reads the stride from the width signal: while running, the silhouette is widest twice per gait cycle (legs split front / back), so the width
period is half a cycle. Returns ``None`` when the signal is too short or flat (a head-on or a held pose).
"""

from __future__ import annotations

import numpy as np

from . import tracker


def follow(frames_bgr: list[np.ndarray], prompt_frame: int, points: list[tuple[float, float]], model_id: str = tracker.MODEL_ID) -> dict:
    masks, scores = tracker.track(frames_bgr, [tracker.Prompt(1, prompt_frame, points)], model_id, return_scores=True)
    m = tracker.measure(masks[1])
    h_px = frames_bgr[0].shape[0]
    n = len(frames_bgr)
    out = {k: [] for k in ("cx", "cy", "h", "w", "area")}
    for i in range(n):
        ys, xs = np.nonzero(masks[1][i])
        if len(xs) < 8:
            for k in out:
                out[k].append(None)
            continue
        out["cx"].append(round(float(xs.mean()) / h_px, 4))
        out["cy"].append(round(float(ys.mean()) / h_px, 4))
        out["h"].append(round(float(np.percentile(ys, 99) - np.percentile(ys, 1)) / h_px, 4))
        out["w"].append(round(float(np.percentile(xs, 99) - np.percentile(xs, 1)) / h_px, 4))
        out["area"].append(round(float(m["area"][i]), 5))
    sc = np.asarray(scores[1], float)
    rel, med = tracker.reliability(sc, prompt_frame)
    out["logit"] = [round(float(v), 2) for v in sc]
    out["reliability"], out["median_logit"] = rel, round(med, 2)
    out["cadence"] = cadence(out["w"], out["h"])
    return out


def cadence(w: list, h: list) -> dict | None:
    """Stride period from the spread signal w/h (frames): {'width_period', 'cycle_period', 'strength'}."""
    a = np.array([np.nan if (x is None or y in (None, 0)) else x / y for x, y in zip(w, h)], float)
    a = a[~np.isnan(a)]
    if len(a) < 10:
        return None
    a = a - np.convolve(a, np.ones(5) / 5, mode="same")  # drop the slow trend (approach / zoom)
    a = a[2:-2]
    if a.std() < 1e-4:
        return None
    ac = np.correlate(a, a, "full")[len(a) - 1 :]
    ac = ac / ac[0]
    peaks = [k for k in range(2, min(len(ac) - 1, 14)) if ac[k] > ac[k - 1] and ac[k] >= ac[k + 1] and ac[k] > 0.15]
    if not peaks:
        return None
    k = peaks[0]
    return {"width_period": k, "cycle_period": 2 * k, "strength": round(float(ac[k]), 2)}
