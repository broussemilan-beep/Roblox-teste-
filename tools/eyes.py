"""Eyes for animation work: read a clip's motion, pace and fx, and diff my render against a reference.

  python tools/eyes.py ref VIDEO OUTDIR [--frames N]          screen recording -> frames at 30 fps (picture band auto-cropped)
  python tools/eyes.py film SCENE OUTDIR                      render a scene's film camera at 30 fps (clean, no HUD)
  python tools/eyes.py analyze DIR OUTDIR [--mask-right 0.17] measurements + rhythm.png + report.json
  python tools/eyes.py compare REF_DIR MINE_DIR OUTDIR        side-by-side measurements, diagnosis, compare.png, beats.md
  python tools/eyes.py hot DIR OUT.png [--top 6 --radius 3]   every frame around the strongest motion peaks (catches 2-frame smears)
  python tools/eyes.py trail DIR A B OUT.png                  where things moved between frames A..B (colour = time)
  python tools/eyes.py flow DIR I OUT.png                     optical flow of frame I (hue = direction, brightness = speed)

Typical loop: ``film duel_short /tmp/mine`` then ``compare /tmp/ref /tmp/mine /tmp/cmp`` and read ``diagnosis.txt``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import eyes  # noqa: E402

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
    s = sp.add_parser("hot"); s.add_argument("dir"); s.add_argument("out"); s.add_argument("--top", type=int, default=6); s.add_argument("--radius", type=int, default=3); s.add_argument("--mask-right", type=float, default=0.0); s.add_argument("--last", type=int); s.set_defaults(f=cmd_hot)
    s = sp.add_parser("trail"); s.add_argument("dir"); s.add_argument("a", type=int); s.add_argument("b", type=int); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.set_defaults(f=cmd_trail)
    s = sp.add_parser("flow"); s.add_argument("dir"); s.add_argument("i", type=int); s.add_argument("out"); s.add_argument("--mask-right", type=float, default=0.0); s.set_defaults(f=cmd_flow)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
