"""Perception: read what is *happening* in a clip, not only how much changes.

``eyes.py`` measures (energy, coverage, size). This module interprets. It separates three things that look alike in a flat
difference image and are very different for an animator:

* **the bodies** - the dark actor (the striker, black coat) and the light actor (the victim, white R6): their silhouettes,
  how much each changes between frames *after removing the camera's own motion*, and whether those changes repeat;
* **the camera** - global motion (pan / orbit / dolly) estimated from the background, and hard cuts;
* **the VFX layer** - thin structures (speed lines, star spikes, ink tips), flat white/black punctuation frames, walls of strokes.

From these it labels events on the clip's timeline (frame indices at ``fps``):

``CUT``  ``CAMERA_MOVE``  ``EMPTY``  ``PUNCT_BLACK``  ``PUNCT_WHITE``  ``VFX_WALL``  ``VFX_BURST``  ``POSE_CHANGE``
``STROBE_POSE``       one actor flips between 2-3 states on (almost) every image: a multi-hit *illusion*
``MULTIHIT_VFX``      that strobe **plus** a VFX layer (bursts, streaks): a punch turned into a rapid multi-hit effect
``REAL_COMBO``        several *distinct* poses held for a few frames each: genuinely different hits
``SINGLE_HIT_SMEAR``  one or two pose changes accompanied by a VFX burst: a single hit sold by effects
``HELD_HERO_CYCLING_VICTIM``  the dark actor holds still while the light actor changes pose every 1-3 images
``HELD_WITH_VFX``     nobody changes pose, only effects appear: the hit is carried by the VFX

Validated against clips with known content in ``examples/eyes_bench.py`` (``tools/eyes_bench.py``). It is a classical
computer-vision reader (masks, optical flow, affine camera fit, shape IoU): fast and inspectable, **not** a learned model, so it can
be wrong on content far from what the bench contains; always check its events on ``pairs`` / ``window_sheet`` pictures.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

WORK_W = 320
ABRUPT = 0.22  # 1 - soft aligned IoU between consecutive frames above which the silhouette *jumped* (flutter and slow orbits stay below)


@dataclass
class Event:
    label: str
    start: int
    end: int
    conf: float = 1.0
    detail: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"{self.label}[{self.start}-{self.end}]"


def _open(m: np.ndarray, k: int) -> np.ndarray:
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((k, k), np.uint8)).astype(bool)


def _centroid(m: np.ndarray):
    ys, xs = np.nonzero(m)
    return (xs.mean(), ys.mean()) if len(xs) else None


def _aligned_iou(a: np.ndarray, b: np.ndarray, min_px: int = 40) -> float:
    """IoU of two masks after moving ``b``'s centroid onto ``a``'s (shape change without translation); nan if one is tiny."""
    if a.sum() < min_px or b.sum() < min_px:
        return float("nan")
    ca, cb = _centroid(a), _centroid(b)
    mat = np.float32([[1, 0, ca[0] - cb[0]], [0, 1, ca[1] - cb[1]]])
    bw = cv2.warpAffine(b.astype(np.uint8), mat, (a.shape[1], a.shape[0]), flags=cv2.INTER_NEAREST).astype(bool)
    u = (a | bw).sum()
    return float((a & bw).sum() / u) if u else 1.0


def _soft(m: np.ndarray) -> np.ndarray:
    """Blurred float mask: boundary noise of a few pixels no longer looks like a pose change."""
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.6)


def _soft_iou(a: np.ndarray, b: np.ndarray, min_px: float = 40.0) -> float:
    """sum(min)/sum(max) of two soft masks after centring ``b`` on ``a``; nan if one is tiny."""
    if a.sum() < min_px or b.sum() < min_px:
        return float("nan")
    ys, xs = np.mgrid[0 : a.shape[0], 0 : a.shape[1]]
    ca = ((xs * a).sum() / a.sum(), (ys * a).sum() / a.sum())
    cb = ((xs * b).sum() / b.sum(), (ys * b).sum() / b.sum())
    mat = np.float32([[1, 0, ca[0] - cb[0]], [0, 1, ca[1] - cb[1]]])
    bw = cv2.warpAffine(b, mat, (a.shape[1], a.shape[0]), flags=cv2.INTER_LINEAR)
    den = np.maximum(a, bw).sum()
    return float(np.minimum(a, bw).sum() / den) if den else 1.0


def _crop_sig(m: np.ndarray, n: int = 32) -> np.ndarray | None:
    """Bounding-box crop padded to a square and resized: a translation/scale-free signature of the pose."""
    ys, xs = np.nonzero(m)
    if len(xs) < 40:
        return None
    crop = m[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].astype(np.uint8)
    s = max(crop.shape)
    pad = np.zeros((s, s), np.uint8)
    pad[(s - crop.shape[0]) // 2 : (s - crop.shape[0]) // 2 + crop.shape[0], (s - crop.shape[1]) // 2 : (s - crop.shape[1]) // 2 + crop.shape[1]] = crop
    return cv2.resize(pad, (n, n), interpolation=cv2.INTER_AREA) > 0.5


def _sig_iou(a: np.ndarray | None, b: np.ndarray | None) -> float:
    if a is None or b is None:
        return float("nan")
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


@dataclass
class Perception:
    fps: int
    n: int
    series: dict[str, np.ndarray]
    events: list[Event]

    def labels_in(self, s: int, e: int) -> set[str]:
        return {ev.label for ev in self.events if ev.start <= e and ev.end >= s}

    def in_range(self, s: int, e: int) -> list[Event]:
        return [ev for ev in self.events if ev.start <= e and ev.end >= s]

    def timeline(self, min_len: int = 1) -> str:
        return "\n".join(f"{ev.start:>4}-{ev.end:<4} {ev.label:<26} conf {ev.conf:.2f} {ev.detail if ev.detail else ''}" for ev in self.events if ev.end - ev.start + 1 >= min_len)


# ------------------------------------------------------------------ per-frame measurements
def _measure(frames: np.ndarray) -> dict[str, np.ndarray]:
    n = len(frames)
    small = []
    for f in frames:
        h = int(round(f.shape[0] * WORK_W / f.shape[1]))
        small.append(cv2.resize(f, (WORK_W, h), interpolation=cv2.INTER_AREA))
    h, w = small[0].shape[:2]
    keys = ["mean", "white", "black", "cyan", "cover", "dark_area", "light_area", "thin", "new_thin", "star",
            "cam_tx", "cam_ty", "cam_s", "cam_rot", "cam_inl", "cam_n", "cam_expl", "hist", "diff", "d_act", "l_act", "d_act2", "l_act2",
            "d_shift", "l_shift", "wcore", "bg_same", "l_move", "l_h", "l_dx"]
    s = {k: np.zeros(n) for k in keys}
    D = [None] * n
    L = [None] * n
    thin_prev = None
    grays = []
    sig_d: list = [None] * n
    sig_l: list = [None] * n
    SD: list = [None] * n
    SL: list = [None] * n
    hists = []
    lowx: list = [None] * n
    for i, f in enumerate(small):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        grays.append(g)
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        bg = float(np.median(g))
        s["mean"][i] = g.mean()
        s["white"][i] = (g > 235).mean()
        s["black"][i] = (g < 30).mean()
        s["cyan"][i] = ((np.abs(hsv[..., 0].astype(int) - 90) < 14) & (hsv[..., 1] > 70) & (hsv[..., 2] > 150)).mean()
        dm = _open(g < bg * 0.45, 3)
        body_d = _open(dm, 7)
        sat = hsv[..., 1] / 255.0
        # the victim is the light actor: low-saturation bright pixels that are NOT the hero's own hair/cuffs (those touch the dark body)
        near_dark = cv2.dilate(body_d.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
        lm = (sat < 0.07) & (hsv[..., 2] > 115) & (g > bg + 8)
        flash = cv2.dilate((g > 247).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)   # star cores / streaks: VFX, not the victim
        body_l = _open(lm & ~near_dark & ~flash, 7)
        F = dm | (lm & ~near_dark) | (lm & near_dark & False)
        s["cover"][i] = ((g < bg * 0.45) | (np.abs(g.astype(np.int16) - bg) > 50)).mean()
        body = body_d | body_l
        Fall = dm | lm | (np.abs(g.astype(np.int16) - bg) > 50)
        thin = Fall & ~cv2.dilate(body.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        s["thin"][i] = thin.mean()
        if thin_prev is not None:
            newt = thin & ~cv2.dilate(thin_prev.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            s["new_thin"][i] = newt.mean()
        thin_prev = thin
        # star-like spiky component: big, low solidity
        cnt, lab, st, _ = cv2.connectedComponentsWithStats(Fall.astype(np.uint8), connectivity=8)
        star = 0
        for c in range(1, cnt):
            area = st[c, cv2.CC_STAT_AREA]
            if area < 0.004 * w * h:
                continue
            comp = (lab == c).astype(np.uint8)
            cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            hull = cv2.convexHull(cs[0])
            ha = cv2.contourArea(hull)
            if ha > 0 and area / ha < 0.55 and area < 0.12 * w * h:
                star += 1
        s["star"][i] = star
        D[i], L[i] = body_d, body_l
        s["dark_area"][i], s["light_area"][i] = body_d.mean(), body_l.mean()
        sig_d[i], sig_l[i] = _crop_sig(body_d), _crop_sig(body_l)
        SD[i], SL[i] = _soft(body_d), _soft(body_l)
        ys_l, xs_l = np.nonzero(body_l)
        if len(ys_l) > 60:   # the victim's feet: stars and flashes hover at chest height, so the base tells whether the body itself moved
            y0, y1 = np.percentile(ys_l, [1, 99])
            low = ys_l > y0 + 0.75 * (y1 - y0)
            s["l_h"][i] = (y1 - y0 + 1) / h
            lowx[i] = float(xs_l[low].mean() / h) if low.any() else None
        hists.append(cv2.calcHist([g], [0], None, [32], [0, 256]))
    # camera: track background features between consecutive frames, fit a similarity transform
    for i in range(1, n):
        g0, g1 = grays[i - 1], grays[i]
        s["diff"][i] = np.abs(g1.astype(np.int16) - g0.astype(np.int16)).mean()
        s["hist"][i] = cv2.compareHist(hists[i], hists[i - 1], cv2.HISTCMP_BHATTACHARYYA)
        bright0 = cv2.dilate((g0 > 235).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        s["wcore"][i] = ((g1 > 235) & ~bright0).mean()        # NEW blown-out white: flashes, star spikes, fresh streaks
        fg = cv2.dilate((D[i - 1] | L[i - 1] | D[i] | L[i]).astype(np.uint8), np.ones((9, 9), np.uint8))
        s["bg_same"][i] = float((np.abs(g1.astype(np.int16) - g0.astype(np.int16))[fg == 0] < 14).mean()) if (fg == 0).any() else 1.0
        pts = cv2.goodFeaturesToTrack(g0, 160, 0.01, 5, mask=(1 - fg).astype(np.uint8))
        A = None
        if pts is not None and len(pts) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, pts, None, winSize=(15, 15), maxLevel=2)
            ok = st.ravel() == 1
            if ok.sum() >= 12:
                A, inl = cv2.estimateAffinePartial2D(pts[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
                if A is not None:
                    s["cam_inl"][i] = inl.mean()
                    s["cam_n"][i] = ok.sum()
                    s["cam_tx"][i], s["cam_ty"][i] = A[0, 2] / w, A[1, 2] / h
                    sc = float(np.hypot(A[0, 0], A[1, 0]))
                    s["cam_s"][i] = sc - 1.0
                    s["cam_rot"][i] = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
        # how much of the raw change the camera model explains
        if A is not None:
            warped = cv2.warpAffine(g0, A, (w, h), borderMode=cv2.BORDER_REPLICATE)
            resid = np.abs(g1.astype(np.int16) - warped.astype(np.int16)).mean()
            s["cam_expl"][i] = 1.0 - resid / (s["diff"][i] + 1e-6)
        # body change after removing the camera: warp the previous masks, compare soft shapes without translation
        for name, M, S in (("d", D, SD), ("l", L, SL)):
            prev_soft = S[i - 1]
            prev_hard = M[i - 1]
            if A is not None and s["cam_inl"][i] > 0.5:
                prev_soft = cv2.warpAffine(prev_soft, A, (w, h), flags=cv2.INTER_LINEAR)
                prev_hard = cv2.warpAffine(prev_hard.astype(np.uint8), A, (w, h), flags=cv2.INTER_NEAREST).astype(bool)
            iou = _soft_iou(S[i], prev_soft)
            s[f"{name}_act"][i] = 0.0 if np.isnan(iou) else 1.0 - iou
            ca, cb = _centroid(M[i]), _centroid(prev_hard)
            s[f"{name}_shift"][i] = float(np.hypot(ca[0] - cb[0], ca[1] - cb[1]) / h) if ca and cb and M[i].sum() > 40 and prev_hard.sum() > 40 else 0.0
        if lowx[i] is not None and lowx[i - 1] is not None:
            s["l_move"][i] = abs(lowx[i] - lowx[i - 1]) + abs(s["l_h"][i] - s["l_h"][i - 1]) * 0.5
            s["l_dx"][i] = lowx[i] - lowx[i - 1]
        if i >= 2:
            for name, S in (("d", SD), ("l", SL)):
                v = _soft_iou(S[i], S[i - 2])
                s[f"{name}_act2"][i] = 0.0 if np.isnan(v) else 1.0 - v
    s["_sig_d"], s["_sig_l"] = sig_d, sig_l  # type: ignore[assignment]
    return s


# ------------------------------------------------------------------ events
def _runs(mask: np.ndarray, min_len: int = 1, gap: int = 0):
    out, start, last = [], None, None
    for i, v in enumerate(mask):
        if v:
            if start is None:
                start = i
            last = i
        elif start is not None and i - last > gap:
            if last - start + 1 >= min_len:
                out.append((start, last))
            start = None
    if start is not None and last - start + 1 >= min_len:
        out.append((start, last))
    return out


def perceive(frames: np.ndarray, fps: int = 30) -> Perception:
    """Label the clip's events. ``frames``: [N, h, w, 3] BGR (use ``eyes.load_clip`` to trim bars / mask app UI)."""
    s = _measure(frames)
    n = len(frames)
    ev: list[Event] = []
    mean, white, black, cyan, cover = s["mean"], s["white"], s["black"], s["cyan"], s["cover"]

    # ---- frame-level punctuation / emptiness / walls
    black_f = mean < 12
    white_f = (white > 0.6) & (cyan < 0.003) & ~black_f
    wall_f = (white > 0.12) & (cyan > 0.003) & ~black_f
    empty_f = (cover < 0.015) & ~black_f & ~(white > 0.5)
    for lab, m, ml in (("PUNCT_BLACK", black_f, 1), ("PUNCT_WHITE", white_f, 1), ("VFX_WALL", wall_f, 4), ("EMPTY", empty_f, 3)):
        for a, b in _runs(m, ml, gap=1 if lab == "VFX_WALL" else 0):
            ev.append(Event(lab, a, b))
    punct = black_f | white_f

    # ---- cuts: histogram jump + the camera model cannot explain the change
    cut_f = (s["bg_same"] < 0.8) & (s["diff"] > 8) & (s["cam_expl"] < 0.3) & ((s["cam_inl"] < 0.45) | (s["cam_n"] < 10)) & ~punct
    cut_f[1:] &= ~punct[:-1]  # the frame after a flash is a return, not a cut
    cut_f &= ~wall_f  # a wall of strokes re-rolls its layout every image: that is an effect, not a cut
    for i in np.nonzero(cut_f)[0]:
        ev.append(Event("CUT", int(i), int(i)))

    # ---- camera: a *consistent* background motion over a window (noise has random sign, a pan/orbit/dolly does not)
    def roll(v, k=8):
        out = np.zeros(n)
        for i in range(n):
            lo = max(0, i - k // 2)
            out[i] = v[lo : i + k // 2 + 1].mean()
        return out

    mtx, mty, ms, mrot = roll(s["cam_tx"]) * 100, roll(s["cam_ty"]) * 100, roll(s["cam_s"]) * 100, roll(s["cam_rot"])
    atx, aty, asc, arot = roll(np.abs(s["cam_tx"])) * 100, roll(np.abs(s["cam_ty"])) * 100, roll(np.abs(s["cam_s"])) * 100, roll(np.abs(s["cam_rot"]))
    big = (np.abs(mtx) > 0.5) | (np.abs(mty) > 0.5) | (np.abs(ms) > 0.45) | (np.abs(mrot) > 0.4)
    consistent = (np.abs(mtx) + np.abs(mty) + np.abs(ms) + np.abs(mrot)) > 0.6 * (atx + aty + asc + arot)
    cam_mag = np.abs(mtx) + np.abs(mty) + np.abs(ms) + np.abs(mrot)
    cam_f = big & consistent & (roll(s["cam_inl"]) > 0.6) & ~punct & ~cut_f & ~wall_f
    cam_runs = _runs(cam_f, 6, gap=2)
    for a, b in cam_runs:
        ev.append(Event("CAMERA_MOVE", a, b, detail={"mean_pct": round(float(cam_mag[a : b + 1].mean()), 2)}))
    cam_on = np.zeros(n, bool)
    for a, b in cam_runs:
        cam_on[a : b + 1] = True

    # ---- VFX bursts: new thin structures or spiky stars
    burst_f = ((s["new_thin"] > 0.008) | (s["star"] > 1) | (s["wcore"] > 0.004)) & ~punct & ~wall_f & ~cut_f
    bursts = _runs(burst_f, 1, gap=2)
    for a, b in bursts:
        ev.append(Event("VFX_BURST", a, b))

    # ---- pose reading on stable (non-punctuation, non-wall, non-empty) stretches
    ok = ~(punct | wall_f | empty_f | cut_f)
    ok[1:] &= ~(punct[:-1] | wall_f[:-1] | cut_f[:-1])
    seg_runs = _runs(ok, 8)
    for a, b in seg_runs:
        ev.extend(_read_poses(s, a, b, cam_on, bursts, fps))
    ev.sort(key=lambda e: (e.start, e.label))
    return Perception(fps, n, {k: v for k, v in s.items() if not k.startswith("_")}, ev)


def _states(act: np.ndarray, sig: list, a: int, b: int):
    """Stable stretches between abrupt silhouette jumps -> (n_states, transitions, dwell, rep signatures)."""
    abrupt = act[a : b + 1] > ABRUPT
    runs = _runs(~abrupt, 2)
    reps = []
    for s0, s1 in runs:
        i = a + (s0 + s1) // 2
        sg = sig[i]
        if sg is None:
            continue
        for r in reps:
            if _sig_iou(sg, r) > 0.8:
                break
        else:
            reps.append(sg)
    jumps = _runs(abrupt, 1)
    dwell = float(np.mean([e - s0 + 1 for s0, e in runs])) if runs else 0.0
    return len(reps), len(jumps), dwell, float(abrupt.mean())


def _read_poses(s, a: int, b: int, cam_on: np.ndarray, bursts, fps: int) -> list[Event]:
    """Name what is happening on a stable stretch from the signals that are reliable on dark-on-dark footage.

    * the **VFX layer** (blown-out white flashes and streaks on a mid-grey scene) is easy to see: how often it fires and where;
    * the **victim** (the light actor) is easy to see too: it reacts (shape change) or it does not;
    * the **dark actor's own pose** is *not* read: black limbs on a black coat are not separable by a classical reader. When the
      verdict depends on it the event says so and the window must be checked by eye (``window_sheet``).
    """
    out: list[Event] = []
    W = 24
    wc = s["wcore"]
    for w0 in range(a, max(a + 1, b - W + 2), 6):
        w1 = min(b, w0 + W - 1)
        if w1 - w0 < 11:
            continue
        sl = slice(w0, w1 + 1)
        n = w1 - w0 + 1
        thr = max(0.0004, float(np.median(wc[sl])) + 0.0004)
        active = wc[sl] > thr
        act_frac = float(active.mean())
        onsets = [i for i in range(n) if active[i] and (i == 0 or not active[i - 1])]
        l_mv = s["l_move"][sl]
        dx = s["l_dx"][sl]
        moving = np.abs(dx) > 0.01
        moves = float(moving.mean())
        pairs = [(dx[i], dx[i + 1]) for i in range(n - 1) if moving[i] and moving[i + 1]]
        rev = float(np.mean([p * q < 0 for p, q in pairs])) if len(pairs) >= 4 else 0.0   # shaken back and forth on every image
        react = lambda i: float(l_mv[i : i + 4].max()) > 0.025
        react_frac = float(np.mean([react(i) for i in onsets])) if onsets else 0.0
        victim_busy = float(np.mean(s["l_act"][sl] > 0.25))
        cam_frac = float(cam_on[sl].mean())
        det = {"flash_active": round(act_frac, 2), "flashes": len(onsets), "victim_react": round(react_frac, 2), "victim_moves": round(moves, 2), "victim_shake": round(rev, 2)}
        labels: list[str] = []
        victim_ok = float(np.mean(s["light_area"][sl] > 0.012)) > 0.7     # the victim must actually be on screen (not cut off / macro)
        if cam_frac < 0.2 and victim_ok:
            if act_frac >= 0.2 and moves >= 0.7 and rev >= 0.6:
                labels.append("MULTIHIT_VFX")          # a flash on (almost) every image and the victim is shaken back and forth each time
            elif len(onsets) >= 3 and react_frac >= 0.5 and rev < 0.6:
                labels.append("REAL_COMBO")            # separate flashes, the victim is sent back by each one
            elif act_frac >= 0.3 and len(onsets) >= 2 and react_frac < 0.45 and moves < 0.5:
                labels.append("HELD_WITH_VFX")         # effects fire but nobody reacts
            elif 1 <= len(onsets) <= 2 and react_frac >= 0.5:
                labels.append("SINGLE_HIT_SMEAR")
            elif victim_busy >= 0.4 and not len(onsets):
                labels.append("VICTIM_CYCLING")        # victim changes pose every 1-3 images with no flash
        for lab in labels:
            out.append(Event(lab, w0, w1, 0.7, det))
    # merge overlapping windows of the same label
    merged: list[Event] = []
    for ev in sorted(out, key=lambda e: (e.label, e.start)):
        if merged and merged[-1].label == ev.label and ev.start <= merged[-1].end + 1:
            merged[-1].end = max(merged[-1].end, ev.end)
        else:
            merged.append(ev)
    return merged
