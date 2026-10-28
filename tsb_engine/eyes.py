"""Eyes: measure an animation clip (frames at 30 fps) and diff a render against a reference, with numbers and pictures.

Why this exists: reading contact sheets by eye misses what makes a reel feel alive - pace, holds, how big the subject is,
how much of the screen the fx cover, where the motion goes. These measurements make those things visible and comparable.
Everything here is plain OpenCV / numpy / scipy / matplotlib (PySceneDetect is an optional cross-check for cuts).

A *clip* is a directory of frames (any image names, sorted), sampled at a constant ``fps``. For screen recordings use
``extract_video`` (ffmpeg, auto-detects the picture band and ignores the app UI on the right).

Per-frame metrics (``analyze``), each in 0..1 unless noted:

``diff``       mean absolute grey difference with the previous frame (0..255): the pose/camera update energy
``flow``       95th percentile optical-flow magnitude (px at working size): fast local motion (limbs, smears)
``flow_dx/dy`` mean flow of the fastest 15 % of pixels: where the motion goes (screen right / down are positive)
``subject_h``  vertical extent of everything that differs from the background (how big the characters are)
``subject_cx`` horizontal centre of that mass
``ink``        share of near-black pixels,  ``white`` share of near-white pixels,  ``cyan`` share of cyan-glow pixels
``edge``       edge density (detail / graphic busyness)
``hist``       histogram distance with the previous frame (cut detector)
"""

from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

WORK_W = 320


# ------------------------------------------------------------------ loading
def detect_band(video: str, samples: int = 24) -> tuple[int, int, int, int]:
    """(x, y, w, h) of the animated picture inside a screen recording: the tallest run of rows that are ever bright."""
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    rows = None
    for i in np.linspace(0, max(0, n - 1), samples).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        m = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).mean(1)
        rows = m if rows is None else np.maximum(rows, m)
    cap.release()
    on = rows > 60
    best, cur, start, best_run = 0, 0, 0, (0, 0)
    for y, v in enumerate(on):
        if v:
            if cur == 0:
                start = y
            cur += 1
            if cur > best:
                best, best_run = cur, (start, y)
        else:
            cur = 0
    w = int(cv2.VideoCapture(video).get(cv2.CAP_PROP_FRAME_WIDTH))
    return 0, best_run[0] + 2, w, best_run[1] - best_run[0] - 2


def extract_video(video: str, out_dir: str, fps: int = 30, band: tuple[int, int, int, int] | None = None, max_frames: int | None = None) -> int:
    """Frames of ``video`` at ``fps`` into ``out_dir`` (cropped to the picture band)."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    x, y, w, h = band or detect_band(video)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},crop={w}:{h}:{x}:{y}"]
    if max_frames:
        cmd += ["-frames:v", str(max_frames)]
    cmd.append(str(Path(out_dir) / "f_%04d.png"))
    subprocess.run(cmd, check=True)
    return len(list(Path(out_dir).glob("f_*.png")))


def load_clip(path: str, width: int = WORK_W, mask_right: float = 0.0, last: int | None = None) -> np.ndarray:
    """Frames [N, h, w, 3] BGR uint8, resized to ``width``; ``mask_right`` drops that share of the right side (app UI)."""
    files = sorted(Path(path).glob("*.png"))
    if last:
        files = files[:last]
    out = []
    ims = [cv2.imread(str(f)) for f in files]
    # letterbox bars (rows that are black in every frame) are not picture: crop them
    probe = ims[:: max(1, len(ims) // 40)]
    rows = np.max([cv2.cvtColor(i, cv2.COLOR_BGR2GRAY).mean(1) for i in probe], 0)
    lit = np.where(rows > 10)[0]
    y0, y1 = (int(lit.min()), int(lit.max()) + 1) if len(lit) else (0, ims[0].shape[0])
    for im in ims:
        im = im[y0:y1]
        if mask_right:
            im = im[:, : int(im.shape[1] * (1 - mask_right))]
        h = int(round(im.shape[0] * width / im.shape[1]))
        out.append(cv2.resize(im, (width, h), interpolation=cv2.INTER_AREA))
    return np.stack(out)


# ------------------------------------------------------------------ metrics
@dataclass
class Clip:
    name: str
    fps: int
    frames: np.ndarray
    m: dict[str, np.ndarray] = field(default_factory=dict)
    cuts: list[int] = field(default_factory=list)  # first frame of every shot except 0
    shots: list[tuple[int, int]] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.frames)


def analyze(frames: np.ndarray, name: str = "clip", fps: int = 30, hold_thr: float = 0.8, cut_thr: float = 0.32) -> Clip:
    n, h, w, _ = frames.shape
    gray = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames])
    small = [cv2.resize(g, (160, int(h * 160 / w)), interpolation=cv2.INTER_AREA) for g in gray]
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    keys = ["diff", "flow", "flow_dx", "flow_dy", "subject_h", "subject_cx", "cover", "ink", "white", "cyan", "edge", "hist", "mean"]
    kernel = np.ones((5, 5), np.uint8)
    m = {k: np.zeros(n) for k in keys}
    hists = [cv2.calcHist([g], [0], None, [32], [0, 256]) for g in gray]
    for i in range(n):
        g = gray[i]
        hsv = cv2.cvtColor(frames[i], cv2.COLOR_BGR2HSV)
        m["mean"][i] = g.mean()
        m["ink"][i] = (g < 30).mean()
        m["white"][i] = (g > 235).mean()
        m["cyan"][i] = ((np.abs(hsv[..., 0].astype(int) - 90) < 14) & (hsv[..., 1] > 70) & (hsv[..., 2] > 150)).mean()
        m["edge"][i] = cv2.Canny(g, 60, 160).mean() / 255.0
        bg = np.median(g)
        mask = cv2.GaussianBlur(np.abs(g.astype(np.int16) - bg).astype(np.uint8), (5, 5), 0) > 45
        mask[:2] = False
        mask[-2:] = False
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel).astype(bool)  # drop shadows' thin lines, grid, noise
        m["cover"][i] = mask.mean()
        ys, xs = np.nonzero(mask)
        if len(ys) > 0.004 * h * w:
            m["subject_h"][i] = (np.percentile(ys, 97) - np.percentile(ys, 3)) / h
            m["subject_cx"][i] = xs.mean() / w
        else:
            m["subject_h"][i], m["subject_cx"][i] = 0.0, 0.5
        if i:
            m["diff"][i] = np.abs(g.astype(np.int16) - gray[i - 1].astype(np.int16)).mean()
            m["hist"][i] = cv2.compareHist(hists[i], hists[i - 1], cv2.HISTCMP_BHATTACHARYYA)
            fl = dis.calc(small[i - 1], small[i], None)
            mag = np.hypot(fl[..., 0], fl[..., 1])
            m["flow"][i] = np.percentile(mag, 95)
            top = mag >= np.percentile(mag, 85)
            m["flow_dx"][i], m["flow_dy"][i] = fl[..., 0][top].mean(), fl[..., 1][top].mean()
    clip = Clip(name, fps, frames, m)
    clip.hold_thr = hold_thr  # type: ignore[attr-defined]
    cuts = [i for i in range(1, n) if (m["hist"][i] > cut_thr and m["diff"][i] > 6) or (m["diff"][i] > 60)]
    # black / white punctuation frames are shots of their own: split at their edges
    flat = m["mean"]
    for i in range(1, n):
        a, b = flat[i - 1], flat[i]
        if (a < 12) != (b < 12) or (a > 238) != (b > 238):
            cuts.append(i)
    cuts = sorted(set(cuts))
    clip.cuts = cuts
    edges = [0] + cuts + [n]
    clip.shots = [(edges[k], edges[k + 1] - 1) for k in range(len(edges) - 1)]
    return clip


def scenedetect_cuts(video: str) -> list[int]:
    """PySceneDetect's content detector on a video file (cross-check for ``Clip.cuts``)."""
    from scenedetect import ContentDetector, detect

    return [s[0].get_frames() for s in detect(video, ContentDetector(threshold=24.0))][1:]


def hold_runs(clip: Clip) -> list[tuple[int, int]]:
    thr = clip.hold_thr  # type: ignore[attr-defined]
    runs, start = [], None
    for i in range(1, clip.n):
        if clip.m["diff"][i] < thr:
            start = i if start is None else start
        elif start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, clip.n - 1))
    return runs


# ------------------------------------------------------------------ summary
def summarize(clip: Clip) -> dict:
    m, n = clip.m, clip.n
    lens = np.array([b - a + 1 for a, b in clip.shots])
    holds = hold_runs(clip)
    held = int(sum(b - a + 1 for a, b in holds))
    big = m["subject_h"] > 0.92
    chars = (~big) & (m["subject_h"] > 0.05) & (m["ink"] < 0.5) & (m["white"] < 0.5) & (m["cover"] < 0.45)
    return {
        "name": clip.name,
        "frames": n,
        "seconds": round(n / clip.fps, 2),
        "shots": len(clip.shots),
        "shot_len_median": float(np.median(lens)),
        "shot_len_p10": float(np.percentile(lens, 10)),
        "shot_len_p90": float(np.percentile(lens, 90)),
        "shots_le_4f": int((lens <= 4).sum()),
        "shots_ge_24f": int((lens >= 24).sum()),
        "held_frac": round(held / n, 3),
        "longest_hold": int(max([b - a + 1 for a, b in holds] or [0])),
        "motion_mean": round(float(m["diff"].mean()), 2),
        "motion_p90": round(float(np.percentile(m["diff"], 90)), 2),
        "flow_p95_mean": round(float(m["flow"].mean()), 2),
        "subject_h_median": round(float(np.median(m["subject_h"][chars])) if chars.any() else 0.0, 3),
        "macro_frac": round(float(big.mean()), 3),
        "cover_mean": round(float(m["cover"].mean()), 3),
        "cover_p90": round(float(np.percentile(m["cover"], 90)), 3),
        "ink_p90": round(float(np.percentile(m["ink"], 90)), 3),
        "ink_frames_gt8": int((m["ink"] > 0.08).sum()),
        "white_frames_gt60": int((m["white"] > 0.6).sum()),
        "black_frames": int((m["mean"] < 12).sum()),
        "cyan_frames_gt4": int((m["cyan"] > 0.04).sum()),
        "cyan_peak": round(float(m["cyan"].max()), 3),
        "edge_mean": round(float(m["edge"].mean()), 3),
    }


# ------------------------------------------------------------------ alignment (DTW) and beat table
FEATURES = ["diff", "subject_h", "cover", "ink", "white", "cyan", "edge", "mean"]


def _feat(clip: Clip) -> np.ndarray:
    cols = []
    for k in FEATURES:
        v = clip.m[k].astype(float)
        if k == "diff":
            v = np.log1p(v)
        cols.append(v)
    return np.stack(cols, 1)


def dtw_path(ref: Clip, mine: Clip, band: float = 0.35) -> list[tuple[int, int]]:
    """Monotonic alignment of ``mine`` frames onto ``ref`` frames (Sakoe-Chiba band), on standardised features."""
    a, b = _feat(ref), _feat(mine)
    mu, sd = a.mean(0), a.std(0) + 1e-6
    a, b = (a - mu) / sd, (b - mu) / sd
    n, mm = len(a), len(b)
    cost = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    inf = 1e18
    acc = np.full((n + 1, mm + 1), inf)
    acc[0, 0] = 0
    w = int(band * max(n, mm))
    for i in range(1, n + 1):
        c = int(i * mm / n)
        for j in range(max(1, c - w), min(mm, c + w) + 1):
            acc[i, j] = cost[i - 1, j - 1] + min(acc[i - 1, j], acc[i, j - 1], acc[i - 1, j - 1])
    i, j, path = n, mm, []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        step = np.argmin([acc[i - 1, j - 1], acc[i - 1, j], acc[i, j - 1]])
        i, j = (i - 1, j - 1) if step == 0 else ((i - 1, j) if step == 1 else (i, j - 1))
    return path[::-1]


def anchor_path(ref: Clip, mine: Clip, anchors: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Piecewise-linear alignment from hand-picked (ref frame, my frame) pairs, e.g. the first contact in both clips."""
    pts = sorted({(0, 0), (ref.n - 1, mine.n - 1), *anchors})
    path = []
    for i in range(ref.n):
        xs = [a for a, _ in pts]
        j = float(np.interp(i, xs, [b for _, b in pts]))
        path.append((i, int(round(min(mine.n - 1, max(0, j))))))
    return path


def beat_table(ref: Clip, mine: Clip, path: list[tuple[int, int]]) -> list[dict]:
    """For each reference shot: its numbers next to the numbers of the frames of my film aligned to it."""
    by_ref: dict[int, list[int]] = {}
    for i, j in path:
        by_ref.setdefault(i, []).append(j)
    rows = []
    for k, (a, b) in enumerate(ref.shots):
        js = sorted({j for i in range(a, b + 1) for j in by_ref.get(i, [])})
        if not js:
            continue
        ia = np.arange(a, b + 1)
        row = {"ref_shot": k, "ref": [a, b], "mine": [js[0], js[-1]], "ref_len": b - a + 1, "mine_len": js[-1] - js[0] + 1}
        for key in ("subject_h", "cover", "ink", "white", "cyan", "edge", "diff"):
            row[f"ref_{key}"] = round(float(ref.m[key][ia].mean()), 3)
            row[f"mine_{key}"] = round(float(mine.m[key][js].mean()), 3)
        rows.append(row)
    return rows


# ------------------------------------------------------------------ diagnosis
def diagnose(ref: dict, mine: dict) -> list[str]:
    """Plain-language gaps between two summaries, with what to change in the film."""
    out: list[str] = []

    def cmp(key, label, lo=0.7, hi=1.4, low_fix="", high_fix="", fmt="{:.2f}"):
        r, m = ref[key], mine[key]
        if r == 0 and m == 0:
            return
        ratio = (m + 1e-9) / (r + 1e-9)
        tag = "ok " if lo <= ratio <= hi else ("LOW" if ratio < lo else "HIGH")
        line = f"[{tag}] {label}: ref {fmt.format(r)}  mine {fmt.format(m)}"
        if tag == "LOW" and low_fix:
            line += f"  -> {low_fix}"
        if tag == "HIGH" and high_fix:
            line += f"  -> {high_fix}"
        out.append(line)

    cmp("shots", "number of shots per clip", 0.75, 1.3, "cut more: the reference changes shot constantly", "fewer, longer shots", "{:.0f}")
    cmp("shot_len_median", "median shot length (frames @30)", 0.6, 1.6, "shots too short", "shots too long: cut or add a punctuation beat", "{:.0f}")
    cmp("shots_le_4f", "very short shots (<=4 f)", 0.5, 1.8, "add bursts of 1-4 frame shots (impact frames, black, glint, storm layouts)", "too choppy", "{:.0f}")
    cmp("shots_ge_24f", "long holds (>=24 f)", 0.5, 1.8, "add real holds (macros, final hold)", "too many long shots", "{:.0f}")
    cmp("held_frac", "share of frames identical to the previous", 0.5, 2.0, "animate on twos more and hold poses (juggle: hold the hero)", "too static", "{:.2f}")
    cmp("motion_mean", "mean update energy", 0.6, 1.6, "too calm: bigger pose changes per frame, more camera/fx motion", "too frantic", "{:.2f}")
    cmp("motion_p90", "peak update energy (p90)", 0.6, 1.6, "peaks too weak: sharper contact poses, bigger fx pops", "peaks too strong", "{:.2f}")
    cmp("flow_p95_mean", "fast local motion (flow p95)", 0.6, 1.6, "limbs/fx move too little", "too much local motion", "{:.2f}")
    cmp("subject_h_median", "character height in non-macro frames", 0.75, 1.3, "characters too small: tighter camera (autoframe fill up / lower fov)", "characters too big", "{:.2f}")
    cmp("macro_frac", "share of macro frames (subject fills frame)", 0.5, 1.8, "add macro shots", "too many macro frames", "{:.2f}")
    cmp("cover_mean", "screen taken by characters + fx (mean)", 0.7, 1.4, "too empty: bigger characters / bigger fx", "too crowded", "{:.3f}")
    cmp("cover_p90", "screen taken by characters + fx (p90)", 0.7, 1.4, "peaks too small: bigger ink, strokes, stars", "peaks too heavy", "{:.3f}")
    cmp("ink_p90", "ink / dark coverage p90", 0.6, 1.6, "ink and black fx too small: widen ink trails, add black stars/swirls", "too dark", "{:.3f}")
    cmp("ink_frames_gt8", "frames with >8% black", 0.6, 1.7, "more black graphics on screen", "too much black", "{:.0f}")
    cmp("white_frames_gt60", "mostly-white frames (impact/flash)", 0.4, 2.5, "add white-out / manga impact frames", "too many white frames", "{:.0f}")
    cmp("black_frames", "black frames", 0.4, 2.5, "add black punctuation frames", "too many black frames", "{:.0f}")
    cmp("cyan_frames_gt4", "frames with cyan glow", 0.5, 1.8, "storm too short or too faint: wider strokes, longer", "too much cyan", "{:.0f}")
    cmp("cyan_peak", "peak cyan coverage", 0.6, 1.6, "storm strokes too thin", "storm too dense", "{:.3f}")
    cmp("edge_mean", "edge density (graphic busyness)", 0.6, 1.6, "too flat/empty: more detail, hatching, lines", "too busy", "{:.3f}")
    return out


# ------------------------------------------------------------------ pictures
def _thumb_strip(clip: Clip, k: int = 14, h: int = 64) -> np.ndarray:
    idx = np.linspace(0, clip.n - 1, k).astype(int)
    ims = []
    for i in idx:
        im = cv2.cvtColor(clip.frames[i], cv2.COLOR_BGR2RGB)
        ims.append(cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h)))
    return np.concatenate(ims, 1)


def plot_clip(clip: Clip, out: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = np.arange(clip.n) / clip.fps
    fig, ax = plt.subplots(5, 1, figsize=(14, 9), sharex=True, gridspec_kw={"height_ratios": [1.1, 1, 1, 1, 1]})
    ax[0].imshow(_thumb_strip(clip), aspect="auto", extent=(0, t[-1], 0, 1))
    ax[0].set_yticks([])
    ax[0].set_title(f"{clip.name}: {clip.n} frames, {len(clip.shots)} shots", loc="left")
    ax[1].plot(t, clip.m["diff"], "k", lw=1)
    ax[1].set_ylabel("update energy")
    ax[2].plot(t, clip.m["flow"], "tab:purple", lw=1)
    ax[2].set_ylabel("flow p95")
    ax[3].plot(t, clip.m["subject_h"], "tab:green", lw=1.2)
    ax[3].set_ylabel("subject height")
    ax[3].set_ylim(0, 1.05)
    ax[4].plot(t, clip.m["ink"], "k", lw=1, label="black")
    ax[4].plot(t, clip.m["white"], "tab:gray", lw=1, label="white")
    ax[4].plot(t, clip.m["cyan"], "tab:cyan", lw=1.4, label="cyan")
    ax[4].legend(loc="upper right", ncol=3, fontsize=8)
    ax[4].set_ylabel("coverage")
    ax[4].set_xlabel("seconds")
    for a in ax[1:]:
        for c in clip.cuts:
            a.axvline(c / clip.fps, color="tab:red", lw=0.4, alpha=0.6)
    fig.tight_layout()
    fig.savefig(out, dpi=90)
    plt.close(fig)


def plot_compare(ref: Clip, mine: Clip, out: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(6, 1, figsize=(14, 11), sharex=True, gridspec_kw={"height_ratios": [0.9, 0.9, 1, 1, 1, 1]})
    tr, tm = np.arange(ref.n) / ref.fps, np.arange(mine.n) / mine.fps
    ax[0].imshow(_thumb_strip(ref), aspect="auto", extent=(0, tr[-1], 0, 1)); ax[0].set_yticks([]); ax[0].set_title("reference", loc="left")
    ax[1].imshow(_thumb_strip(mine), aspect="auto", extent=(0, tm[-1], 0, 1)); ax[1].set_yticks([]); ax[1].set_title("mine", loc="left")
    for a, key, lab in ((ax[2], "diff", "update energy"), (ax[3], "subject_h", "subject height"), (ax[4], "ink", "black coverage"), (ax[5], "cyan", "cyan coverage")):
        a.plot(tr, ref.m[key], "k", lw=1.1, label="reference")
        a.plot(tm, mine.m[key], color="tab:orange", lw=1.1, label="mine")
        a.set_ylabel(lab)
        for c in ref.cuts:
            a.axvline(c / ref.fps, color="k", lw=0.3, alpha=0.35)
        for c in mine.cuts:
            a.axvline(c / mine.fps, color="tab:orange", lw=0.3, alpha=0.35)
    ax[2].legend(loc="upper right", fontsize=8)
    ax[5].set_xlabel("seconds")
    fig.tight_layout()
    fig.savefig(out, dpi=90)
    plt.close(fig)


def motion_trail(frames: np.ndarray, a: int, b: int, thr: int = 22, max_steps: int = 10) -> np.ndarray:
    """Where things moved between frames a..b, coloured by *when* (blue early -> red late), over the first frame.

    Windows longer than ``max_steps`` are sampled evenly; use short windows (<= 10 frames) to read an arc.
    """
    idx = np.unique(np.linspace(a, b, min(b - a + 1, max_steps + 1)).astype(int))
    base = cv2.cvtColor(frames[idx[0]], cv2.COLOR_BGR2GRAY)
    canvas = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR).astype(np.float32) * 0.5
    for n in range(1, len(idx)):
        d = cv2.absdiff(cv2.cvtColor(frames[idx[n]], cv2.COLOR_BGR2GRAY), cv2.cvtColor(frames[idx[n - 1]], cv2.COLOR_BGR2GRAY))
        mask = cv2.GaussianBlur(d, (3, 3), 0) > thr
        hue = int(120 * (1 - n / max(1, len(idx) - 1)))  # 120 = blue (early) .. 0 = red (late)
        col = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0, 0].astype(np.float32)
        edge = mask & ~cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)  # outlines keep earlier steps visible
        canvas[mask] = canvas[mask] * 0.55 + col * 0.45
        canvas[edge] = col
    return np.clip(canvas, 0, 255).astype(np.uint8)


def flow_picture(frames: np.ndarray, i: int) -> np.ndarray:
    """Optical flow between frame i-1 and i: hue = direction, brightness = speed relative to the frame's fastest 1 %."""
    g0, g1 = (cv2.cvtColor(frames[k], cv2.COLOR_BGR2GRAY) for k in (i - 1, i))
    fl = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, ang = cv2.cartToPolar(fl[..., 0], fl[..., 1])
    hsv = np.zeros((*g0.shape, 3), np.uint8)
    hsv[..., 0] = (ang * 90 / np.pi).astype(np.uint8)
    hsv[..., 1] = 255
    hsv[..., 2] = np.clip(mag / (np.percentile(mag, 99) + 1e-6) * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def pair_sheet(ref: Clip, mine: Clip, beats: list[dict], out: str, cols: int = 4, min_len: int = 1, width: int = 330) -> None:
    """Reference frame above my aligned frame, for every reference shot: the visual diff, shot by shot."""
    cells = []
    for b in beats:
        if b["ref_len"] < min_len:
            continue
        ri = (b["ref"][0] + b["ref"][1]) // 2
        mi = (b["mine"][0] + b["mine"][1]) // 2
        a = cv2.resize(ref.frames[ri], (width, int(width * ref.frames.shape[1] / ref.frames.shape[2])))
        c = cv2.resize(mine.frames[mi], (width, int(width * mine.frames.shape[1] / mine.frames.shape[2])))
        cell = np.concatenate([a, np.full((3, width, 3), (0, 0, 255), np.uint8), c])
        cv2.putText(cell, f"shot {b['ref_shot']}  ref f{ri}", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cv2.putText(cell, f"mine f{mi}", (4, a.shape[0] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)
        cells.append(cell)
    if not cells:
        return
    h = max(c.shape[0] for c in cells)
    rows = []
    for r in range(0, len(cells), cols):
        row = cells[r : r + cols]
        row += [np.zeros_like(cells[0])] * (cols - len(row))
        rows.append(np.concatenate([np.pad(c, ((0, h - c.shape[0]), (2, 2), (0, 0))) for c in row], 1))
    cv2.imwrite(out, np.concatenate(rows, 0))


def clip_to_json(clip: Clip) -> dict:
    return {"summary": summarize(clip), "shots": clip.shots, "cuts": clip.cuts, "holds": hold_runs(clip),
            "series": {k: [round(float(x), 4) for x in v] for k, v in clip.m.items()}}


def save_json(obj, path: str) -> None:
    Path(path).write_text(json.dumps(obj, indent=1), encoding="utf-8")
