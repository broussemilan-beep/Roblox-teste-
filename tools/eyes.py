"""Eyes for animation work: read a clip's motion, pace and fx, and diff my render against a reference.

  python tools/eyes.py ref VIDEO OUTDIR [--frames N]          screen recording -> frames at 30 fps (picture band auto-cropped)
  python tools/eyes.py film SCENE OUTDIR                      render a scene's film camera at 30 fps (clean, no HUD)
  python tools/eyes.py analyze DIR OUTDIR [--mask-right 0.17] measurements + rhythm.png + report.json
  python tools/eyes.py compare REF_DIR MINE_DIR OUTDIR        side-by-side measurements, diagnosis, compare.png, beats.md
  python tools/eyes.py read DIR OUT [--mask-right 0.17]        events timeline + hot windows + reading.json template
  python tools/eyes.py check DIR READING.json                  contradictions between my written reading and the measurements
  python tools/eyes.py propose DIR FRAME OUT.png               SAM 2: numbered candidate objects on one frame (+ OUT.json prompt points)
  python tools/eyes.py track DIR OUT --obj arm=F:X,Y ...       SAM 2: follow objects I pointed at; reliability + strobe verdict + overlay strip
  python tools/eyes.py hot DIR OUT.png [--top 6 --radius 3]   every frame around the strongest motion peaks (catches 2-frame smears)
  python tools/eyes.py trail DIR A B OUT.png                  where things moved between frames A..B (colour = time)
  python tools/eyes.py flow DIR I OUT.png                     optical flow of frame I (hue = direction, brightness = speed)

Typical loop: ``film duel_short /tmp/mine`` then ``compare /tmp/ref /tmp/mine /tmp/cmp`` and read ``diagnosis.txt``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import eyes, perception, reading  # noqa: E402

UI_RIGHT = 0.17  # share of the right side hidden by the TikTok buttons in screen recordings


def cmd_ref(a):
    n = eyes.extract_video(a.video, a.out, fps=a.fps, max_frames=a.frames)
    print(f"{n} frames -> {a.out}")


def cmd_film(a):
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_viewer.py"), a.scene], check=True, stdout=subprocess.DEVNULL)
    html = ROOT / "viewer" / "output" / f"{a.scene}.html"
    step = max(1, round(60 / a.fps))
    subprocess.run(["node", str(ROOT / "tools" / "render_video.js"), str(html), a.out, str(step), "0", "", str(a.width)], check=True)


def _load(path, mask, last=None):
    return eyes.analyze(eyes.load_clip(path, mask_right=mask, last=last), name=Path(path).name)


def cmd_analyze(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    clip = _load(a.dir, a.mask_right, a.last)
    eyes.plot_clip(clip, str(out / "rhythm.png"))
    eyes.save_json(eyes.clip_to_json(clip), str(out / "report.json"))
    for k, v in eyes.summarize(clip).items():
        print(f"{k:>20}: {v}")
    print("shots:", [f"{s}-{e}" for s, e in clip.shots])
    print("holds >= 6f:", [f"{s}-{e}" for s, e in eyes.hold_runs(clip) if e - s + 1 >= 6])


def cmd_compare(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ref = _load(a.ref, a.ref_mask, a.ref_last)
    mine = _load(a.mine, 0.0, None)
    sr, sm = eyes.summarize(ref), eyes.summarize(mine)
    lines = eyes.diagnose(sr, sm)
    anchors = [tuple(int(v) for v in x.split(':')) for x in a.anchors.split(',')] if a.anchors else None
    path = eyes.anchor_path(ref, mine, anchors) if anchors else eyes.dtw_path(ref, mine)
    beats = eyes.beat_table(ref, mine, path)
    eyes.plot_compare(ref, mine, str(out / "compare.png"))
    eyes.pair_sheet(ref, mine, [b for b in beats if b["ref_len"] >= a.min_shot], str(out / "pairs.png"))
    eyes.plot_clip(ref, str(out / "ref_rhythm.png"))
    eyes.plot_clip(mine, str(out / "mine_rhythm.png"))
    eyes.save_json({"ref": eyes.clip_to_json(ref), "mine": eyes.clip_to_json(mine), "diagnosis": lines, "beats": beats}, str(out / "report.json"))
    (out / "diagnosis.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    md = ["| ref shot | ref frames | my frames | len ref/mine | height ref/mine | black ref/mine | cyan ref/mine | white ref/mine | energy ref/mine |", "|---|---|---|---|---|---|---|---|---|"]
    for b in beats:
        md.append(f"| {b['ref_shot']} | {b['ref'][0]}-{b['ref'][1]} | {b['mine'][0]}-{b['mine'][1]} | {b['ref_len']}/{b['mine_len']} | {b['ref_subject_h']}/{b['mine_subject_h']} | "
                  f"{b['ref_ink']}/{b['mine_ink']} | {b['ref_cyan']}/{b['mine_cyan']} | {b['ref_white']}/{b['mine_white']} | {b['ref_diff']}/{b['mine_diff']} |")
    (out / "beats.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}/compare.png, pairs.png, diagnosis.txt, beats.md, report.json")


def cmd_read(a):
    """Perceive a clip: timeline of events, every frame around the strongest peaks, and a reading template to fill in."""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = eyes.load_clip(a.dir, width=perception.WORK_W, mask_right=a.mask_right, last=a.last)
    pc = perception.perceive(frames, fps=a.fps)
    full = eyes.analyze(eyes.load_clip(a.dir, mask_right=a.mask_right, last=a.last), name=Path(a.dir).name)
    eyes.window_sheet(full, eyes.hot_windows(full, a.top, a.radius), str(out / "hot_windows.png"))
    eyes.plot_clip(full, str(out / "rhythm.png"))
    reading.save(reading.skeleton(pc), str(out / "reading.json"))
    (out / "timeline.txt").write_text(pc.timeline() + "\n", encoding="utf-8")
    print(pc.timeline())
    print(f"\nwrote {out}/timeline.txt, hot_windows.png, rhythm.png, reading.json (fill it in, then: eyes.py check)")
    print("RELIABLE: PUNCT_BLACK/WHITE, VFX_WALL, EMPTY, CAMERA_MOVE (validated). ADVISORY ONLY: CUT, hit labels, VICTIM_CYCLING (see docs/research/eyes-validation.md)")


def cmd_check(a):
    frames = eyes.load_clip(a.dir, width=perception.WORK_W, mask_right=a.mask_right, last=a.last)
    pc = perception.perceive(frames, fps=a.fps)
    issues = reading.validate(reading.load(a.reading), pc)
    for i in issues:
        print(i)
    print(f"\n{len(issues)} issue(s)")
    sys.exit(1 if issues else 0)


def _frames(path, first, last, step=1):
    files = sorted(Path(path).glob("*.png"))[first : last + 1 : step]
    return [cv2.imread(str(f)) for f in files], list(range(first, first + len(files) * step, step))


def cmd_propose(a):
    """Number the candidate objects on one frame so they can be chosen by eye, then tracked."""
    from tsb_engine import tracker

    frames, _ = _frames(a.dir, a.frame, a.frame)
    cands = tracker.propose(frames[0], points_per_side=a.grid, max_masks=a.max)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(a.out, tracker.overlay(frames[0], cands))
    info = [{"id": c["id"], "point": [round(c["point"][0], 1), round(c["point"][1], 1)], "area": round(c["area"], 4)} for c in cands]
    Path(a.out).with_suffix(".json").write_text(json.dumps(info, indent=1))
    print(f"{len(cands)} candidates -> {a.out} (+ .json with a prompt point for each id)")


def cmd_track(a):
    """Track objects chosen by eye. --obj NAME=FRAME:X,Y[:X,Y...][!X,Y] (frame index inside the range; '!' = negative point)."""
    from tsb_engine import tracker

    frames, idx = _frames(a.dir, a.first, a.last, a.step)
    prompts, names = [], {}
    for k, spec in enumerate(a.obj, 1):
        name, rest = spec.split("=")
        fr, pts = rest.split(":", 1)
        pos, _, neg = pts.partition("!")
        points = [tuple(float(v) for v in q.split(",")) for q in pos.split(":") if q]
        labels = [1] * len(points)
        if neg:
            points += [tuple(float(v) for v in q.split(",")) for q in neg.split(":") if q]
            labels += [0] * (len(points) - len(labels))
        prompts.append(tracker.Prompt(k, int(fr), points=points, labels=labels))
        names[k] = name
    masks, scores = tracker.track(frames, prompts, return_scores=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    cols = [(0, 0, 255), (0, 200, 0), (255, 120, 0), (0, 200, 255), (255, 0, 200)]
    for k, name in names.items():
        m = tracker.measure(masks[k], toward=a.toward)
        rel, med = tracker.reliability(scores[k], prompts[k - 1].frame)
        st = tracker.strobe(m["reach"], m["area"])
        report[name] = {"reliability": rel, "median_presence_logit": round(med, 1), **st,
                        "reach_range": round(float(np.ptp(m["reach"][m["area"] > 0])) if (m["area"] > 0).any() else 0.0, 3),
                        "frames": [int(i) for i in idx], "reach": [round(float(v), 4) for v in m["reach"]], "scores": [round(float(v), 1) for v in scores[k]]}
        meaning = {"strobe": "STROBE: flips between two extensions on every image (one pose + VFX / multi-hit illusion)",
                   "cycling": "CYCLING: keeps changing pose (no return to the same value 2 images later)",
                   "moving": "MOVING: smooth sweep in one direction at a time", "steady": "STEADY: held pose", "unknown": "too few frames"}
        verdict = meaning[st["kind"]] if rel == "good" else f"track {rel}: look at the overlay before using any number ({st['kind']} if it were right)"
        print(f"{name:<14} track {rel:<8} (logit {med:>5.1f})  reach range {report[name]['reach_range']:.2f}  big steps {st['big_frac']:.0%}, 2-back/1-back ratio {st['ratio']}  -> {verdict}")
    cells = []
    for i, fr in enumerate(frames):
        im = fr.copy()
        for k, name in names.items():
            m = masks[k][i]
            c = np.array(cols[(k - 1) % len(cols)], np.float32)
            im[m] = (im[m] * 0.45 + c * 0.55).astype(np.uint8)
        cv2.putText(im, str(idx[i]), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cells.append(cv2.resize(im, (320, int(320 * im.shape[0] / im.shape[1]))))
    ncol = 5
    while len(cells) % ncol:
        cells.append(np.zeros_like(cells[0]))
    cv2.imwrite(str(out / "track.png"), np.concatenate([np.concatenate(cells[r : r + ncol], 1) for r in range(0, len(cells), ncol)], 0))
    (out / "track.json").write_text(json.dumps(report, indent=1))
    print(f"wrote {out}/track.png (colour = object) and track.json")


def cmd_hot(a):
    clip = _load(a.dir, a.mask_right, a.last)
    wins = eyes.hot_windows(clip, a.top, a.radius)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    eyes.window_sheet(clip, wins, a.out)
    print("windows (start, peak, end):", wins)


def cmd_trail(a):
    fr = eyes.load_clip(a.dir, mask_right=a.mask_right)
    cv2.imwrite(a.out, cv2.resize(eyes.motion_trail(fr, a.a, a.b), None, fx=2, fy=2))


def cmd_flow(a):
    fr = eyes.load_clip(a.dir, mask_right=a.mask_right)
    cv2.imwrite(a.out, cv2.resize(eyes.flow_picture(fr, a.i), None, fx=2, fy=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("ref"); s.add_argument("video"); s.add_argument("out"); s.add_argument("--fps", type=int, default=30); s.add_argument("--frames", type=int); s.set_defaults(f=cmd_ref)
    s = sp.add_parser("film"); s.add_argument("scene"); s.add_argument("out"); s.add_argument("--fps", type=int, default=30); s.add_argument("--width", type=int, default=960); s.set_defaults(f=cmd_film)
    s = sp.add_parser("analyze"); s.add_argument("dir"); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.add_argument("--last", type=int); s.set_defaults(f=cmd_analyze)
    s = sp.add_parser("compare"); s.add_argument("ref"); s.add_argument("mine"); s.add_argument("out"); s.add_argument("--ref-mask", type=float, default=UI_RIGHT); s.add_argument("--ref-last", type=int); s.add_argument("--min-shot", type=int, default=3); s.add_argument("--anchors", help="ref:mine,ref:mine,... frames (30 fps) that must line up"); s.set_defaults(f=cmd_compare)
    s = sp.add_parser("read"); s.add_argument("dir"); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.add_argument("--last", type=int); s.add_argument("--fps", type=int, default=30); s.add_argument("--top", type=int, default=6); s.add_argument("--radius", type=int, default=3); s.set_defaults(f=cmd_read)
    s = sp.add_parser("check"); s.add_argument("dir"); s.add_argument("reading"); s.add_argument("--mask-right", type=float, default=0.0); s.add_argument("--last", type=int); s.add_argument("--fps", type=int, default=30); s.set_defaults(f=cmd_check)
    s = sp.add_parser("propose"); s.add_argument("dir"); s.add_argument("frame", type=int); s.add_argument("out"); s.add_argument("--grid", type=int, default=16); s.add_argument("--max", type=int, default=40); s.set_defaults(f=cmd_propose)
    s = sp.add_parser("track"); s.add_argument("dir"); s.add_argument("out"); s.add_argument("--obj", action="append", required=True); s.add_argument("--first", type=int, default=0); s.add_argument("--last", type=int, default=29); s.add_argument("--step", type=int, default=1); s.add_argument("--toward", type=int, default=1, help="+1 if the other actor is on the right of the tracked one, -1 if on the left"); s.set_defaults(f=cmd_track)
    s = sp.add_parser("hot"); s.add_argument("dir"); s.add_argument("out"); s.add_argument("--top", type=int, default=6); s.add_argument("--radius", type=int, default=3); s.add_argument("--mask-right", type=float, default=0.0); s.add_argument("--last", type=int); s.set_defaults(f=cmd_hot)
    s = sp.add_parser("trail"); s.add_argument("dir"); s.add_argument("a", type=int); s.add_argument("b", type=int); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.set_defaults(f=cmd_trail)
    s = sp.add_parser("flow"); s.add_argument("dir"); s.add_argument("i", type=int); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.set_defaults(f=cmd_flow)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
