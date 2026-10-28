"""Object tracking with SAM 2.1 (Meta): point at a thing on one frame, get its exact mask on every frame.

Why: black limbs on a black coat, dark ink strokes and the white victim cannot be told apart by thresholds. A promptable video
segmenter can: *I* look at a frame, say "this is the right arm / this is an ink streak / this is the dummy", and the tracker follows
that object through the clip. The masks are then measured (``measure``): area, centroid, bounding box, reach, frame-to-frame change,
back-and-forth alternation. That gives numbers for what a reader of the clip needs: does this limb flip between two poses every image
(a VFX-made multi-hit) or sweep through different poses (real hits)? Does the victim change pose while the hero holds?

Needs ``pip install torch transformers`` (CPU is enough: ~1-2 s per frame for the tiny model) and a one-time download of
``facebook/sam2.1-hiera-tiny`` from the Hugging Face hub. The model is **not** perfect on this footage (flat, dark, block shapes); the
bench (``tools/eyes_bench.py --track``) scores it against the engine's exact per-part masks, see docs/research/eyes-validation.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MODEL_ID = "facebook/sam2.1-hiera-tiny"
_CACHE: dict = {}


def load(model_id: str = MODEL_ID, device: str = "cpu"):
    """(model, processor), cached."""
    key = (model_id, device)
    if key not in _CACHE:
        import torch
        from transformers import Sam2VideoModel, Sam2VideoProcessor

        torch.set_num_threads(max(1, torch.get_num_threads()))
        model = Sam2VideoModel.from_pretrained(model_id).to(device).eval()
        proc = Sam2VideoProcessor.from_pretrained(model_id)
        _CACHE[key] = (model, proc)
    return _CACHE[key]


@dataclass
class Prompt:
    obj: int                       # object id (1, 2, ...)
    frame: int                     # frame the prompt is given on
    points: list[tuple[float, float]] | None = None   # (x, y) in pixels of that frame
    labels: list[int] | None = None                   # 1 = on the object, 0 = not on it
    box: tuple[float, float, float, float] | None = None  # (x0, y0, x1, y1)


def track(frames_bgr: list[np.ndarray], prompts: list[Prompt], model_id: str = MODEL_ID, device: str = "cpu", return_scores: bool = False):
    """Boolean masks [N, H, W] per object id, tracked forward and backward from each object's prompt frame.

    ``return_scores=True`` returns ``(masks, scores)`` where ``scores[obj][i]`` is the model's own object-presence logit on frame ``i``
    (high = the object is there, low/negative = the tracker lost it).
    """
    import torch

    model, proc = load(model_id, device)
    rgb = [np.ascontiguousarray(f[..., ::-1]) for f in frames_bgr]
    h, w = rgb[0].shape[:2]
    out: dict[int, np.ndarray] = {p.obj: np.zeros((len(rgb), h, w), bool) for p in prompts}
    scores: dict[int, np.ndarray] = {p.obj: np.full(len(rgb), np.nan) for p in prompts}
    for p in prompts:  # one session per object: objects may be first visible on different frames
        for reverse in (False, True):
            if reverse and p.frame == 0:
                continue
            if not reverse and p.frame == len(rgb) - 1 and False:
                continue
            session = proc.init_video_session(video=rgb, inference_device=device, dtype=torch.float32)
            kw = {}
            if p.points:
                kw["input_points"] = [[[list(map(float, pt)) for pt in p.points]]]
                kw["input_labels"] = [[list(p.labels or [1] * len(p.points))]]
            if p.box is not None:
                kw["input_boxes"] = [[list(map(float, p.box))]]
            proc.add_inputs_to_inference_session(inference_session=session, frame_idx=p.frame, obj_ids=p.obj, original_size=(h, w), **kw)
            with torch.no_grad():
                model(inference_session=session, frame_idx=p.frame)
                for o in model.propagate_in_video_iterator(session, start_frame_idx=p.frame, reverse=reverse):
                    masks = proc.post_process_masks([o.pred_masks], original_sizes=[[h, w]], binarize=True)[0]
                    for k, oid in enumerate(o.object_ids):
                        out[int(oid)][o.frame_idx] |= masks[k, 0].cpu().numpy().astype(bool)
                        scores[int(oid)][o.frame_idx] = float(o.object_score_logits[k].flatten()[0])
    return (out, scores) if return_scores else out


def propose(frame_bgr: np.ndarray, model_id: str = MODEL_ID, points_per_side: int = 16, min_area: float = 0.002, max_masks: int = 40) -> list[dict]:
    """Automatic candidates on one frame: [{'id', 'mask', 'point', 'area'}], biggest first, for a numbered overlay.

    A grid of point prompts is run through the SAM 2 image model and near-duplicate masks are dropped. The caller looks at
    ``overlay(frame, candidates)``, decides which numbers are which object, and tracks them.
    """
    import torch
    from transformers import Sam2Model, Sam2Processor

    key = ("image", model_id)
    if key not in _CACHE:
        _CACHE[key] = (Sam2Model.from_pretrained(model_id).eval(), Sam2Processor.from_pretrained(model_id))
    model, proc = _CACHE[key]
    rgb = np.ascontiguousarray(frame_bgr[..., ::-1])
    h, w = rgb.shape[:2]
    gx = np.linspace(0.05, 0.95, points_per_side)
    pts = [[float(x * w), float(y * h)] for y in gx for x in gx]
    cands: list[dict] = []
    with torch.no_grad():
        for i in range(0, len(pts), 16):
            chunk = pts[i : i + 16]
            inp = proc(images=rgb, input_points=[[[p] for p in chunk]], input_labels=[[[1] for _ in chunk]], return_tensors="pt")
            out = model(**inp, multimask_output=False)
            masks = proc.post_process_masks(out.pred_masks, inp["original_sizes"], binarize=True)[0]
            for k, p in enumerate(chunk):
                m = masks[k, 0].cpu().numpy().astype(bool)
                if m.mean() >= min_area and m.mean() < 0.6:
                    cands.append({"mask": m, "point": tuple(p), "area": float(m.mean())})
    cands.sort(key=lambda c: -c["area"])
    keep: list[dict] = []
    for c in cands:
        if all(iou(c["mask"], k["mask"]) < 0.7 for k in keep):
            keep.append(c)
        if len(keep) >= max_masks:
            break
    for i, c in enumerate(keep, 1):
        c["id"] = i
    return keep


def overlay(frame_bgr: np.ndarray, cands: list[dict]) -> np.ndarray:
    """The frame with every candidate tinted and numbered, to choose from by eye."""
    import cv2

    out = frame_bgr.copy().astype(np.float32)
    rng = np.random.RandomState(1)
    for c in cands:
        col = rng.randint(60, 255, 3).astype(np.float32)
        out[c["mask"]] = out[c["mask"]] * 0.55 + col * 0.45
    out = out.astype(np.uint8)
    for c in cands:
        ys, xs = np.nonzero(c["mask"])
        cx, cy = int(xs.mean()), int(ys.mean())
        cv2.putText(out, str(c["id"]), (cx - 6, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
        cv2.putText(out, str(c["id"]), (cx - 6, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return out


# ------------------------------------------------------------------ measuring a tracked object
def measure(masks: np.ndarray, toward: int = 1) -> dict[str, np.ndarray]:
    """Per-frame numbers of one tracked mask. ``toward``: +1 if the other actor is on the right of this one, -1 if on the left."""
    n, h, w = masks.shape
    keys = ["area", "cx", "cy", "x0", "x1", "y0", "y1", "reach", "change"]
    m = {k: np.zeros(n) for k in keys}
    for i in range(n):
        ys, xs = np.nonzero(masks[i])
        if len(xs) < 8:
            m["area"][i] = 0
            continue
        m["area"][i] = len(xs) / (h * w)
        m["cx"][i], m["cy"][i] = xs.mean() / h, ys.mean() / h
        m["x0"][i], m["x1"][i] = np.percentile(xs, 1) / h, np.percentile(xs, 99) / h
        m["y0"][i], m["y1"][i] = np.percentile(ys, 1) / h, np.percentile(ys, 99) / h
        m["reach"][i] = (m["x1"][i] if toward > 0 else -m["x0"][i])
        if i and masks[i - 1].any():
            a, b = masks[i - 1], masks[i]
            u = (a | b).sum()
            m["change"][i] = 1.0 - (a & b).sum() / u if u else 0.0
    return m


def reliability(scores: np.ndarray, prompt_frame: int = 0, good: float = 7.0, bad: float = 5.0) -> tuple[str, float]:
    """('good' | 'doubtful' | 'lost', median presence logit away from the prompt frame).

    Calibrated on the bench (``tools/track_bench.py`` + the confidence test): tracks that followed the arm held a median logit of 8-10;
    tracks that lost it sat between 0 and 4. In between, look at the overlay before believing any number.
    """
    s = np.array(scores, float)
    s = np.delete(s, prompt_frame) if 0 <= prompt_frame < len(s) else s
    med = float(np.nanmedian(s)) if len(s) else float("nan")
    return ("good" if med >= good else "lost" if med < bad else "doubtful"), med


def strobe(reach: np.ndarray, area: np.ndarray, min_step: float = 0.012, rate: float = 0.8, min_steps: int = 8) -> dict:
    """Does the tracked limb flip between two extensions on (almost) every image?  -> {'strobe': bool, 'reversals', 'rate', 'steps'}"""
    r = reach[area > 0]
    d = np.diff(r)
    big = d[np.abs(d) > min_step]
    rev, rt = alternation(r, min_step)
    return {"strobe": bool(len(big) >= min_steps and rt >= rate), "reversals": rev, "rate": round(rt, 2), "steps": int(len(big))}


def alternation(signal: np.ndarray, min_step: float) -> tuple[int, float]:
    """(reversals, fraction of steps that reverse) of a 1-D signal, counting only steps larger than ``min_step``."""
    d = np.diff(signal)
    d = d[np.abs(d) > min_step]
    if len(d) < 3:
        return 0, 0.0
    rev = int((d[1:] * d[:-1] < 0).sum())
    return rev, rev / (len(d) - 1)


def iou(a: np.ndarray, b: np.ndarray) -> float:
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else float("nan")
