"""Run the eyes on clips whose content is known: python tools/eyes_bench.py [--render] [--dir /tmp/bench] [--verbose]

Builds ``examples/eyes_bench.py`` (ghost jab, single smear, real combo, camera-only, cut, held hero + cycling victim, punctuation,
VFX wall, VFX-only hit, empty stage; several seeded variants each), renders it with the viewer, reads every segment with
``tsb_engine.perception`` and checks the labels against the truth. Exit code 0 only when every class reaches ``--min-pass``.
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.eyes_bench import SEG, TRUTH, build  # noqa: E402
from tsb_engine import eyes, perception  # noqa: E402


def render(out: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_viewer.py"), "eyes_bench"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["node", str(ROOT / "tools" / "render_video.js"), str(ROOT / "viewer" / "output" / "eyes_bench.html"), out, "2", "0", "", "960"], check=True)


def judge(seg: dict, events: list, labels: set) -> tuple[bool, str]:
    truth = TRUTH[seg["class"]]
    miss = [r for r in truth["require"] if r not in labels]
    bad = [f for f in truth["forbid"] if f in labels]
    if seg["class"] == "hard_cut" and seg["cut"] is not None:
        cuts = [e for e in events if e.label == "CUT"]
        if not any(abs(e.start - seg["cut"]) <= 2 for e in cuts):
            miss.append(f"CUT@{seg['cut']}")
    ok = not miss and not bad
    return ok, ("" if ok else f"missing {miss} / unexpected {bad}")


def score_reference(frames_dir: str) -> bool:
    import json

    cp = json.loads((ROOT / "docs" / "research" / "reference-checkpoints.json").read_text(encoding="utf-8"))
    tol = cp["tolerance_frames"]
    pc = perception.perceive(eyes.load_clip(frames_dir, width=perception.WORK_W, mask_right=0.17, last=336))
    hit = 0
    print("\nreference checkpoints (my own reading is the truth):")
    for e in cp["expected"]:
        got = [x for x in pc.events if x.label == e["label"] and x.start <= e["end"] + tol and x.end >= e["start"] - tol]
        ok = bool(got)
        hit += ok
        print(f"  {'FOUND  ' if ok else 'MISSED '} {e['label']:<12} {e['start']}-{e['end']}  " + (f"read as {got[0].start}-{got[0].end}" if got else ""))
    extra = []
    for x in pc.events:
        if x.label in cp["forbid_outside"] and not any(x.label == e["label"] and x.start <= e["end"] + tol and x.end >= e["start"] - tol for e in cp["expected"]):
            extra.append(x)
    print(f"  recall {hit}/{len(cp['expected'])}; false detections of reliable classes: {extra or 'none'}")
    counts = {c: sum(1 for x in pc.events if x.label == c) for c in cp["unverified_classes"]}
    print(f"  NOT validated on this clip (do not trust without looking): {counts}")
    return hit == len(cp["expected"]) and not extra


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="/tmp/bench")
    p.add_argument("--render", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--min-pass", type=float, default=1.0)
    p.add_argument("--classes", default="")
    p.add_argument("--reference", default="", help="directory of the reference frames (tools/eyes.py ref ...): score against docs/research/reference-checkpoints.json")
    a = p.parse_args()
    if a.render or not Path(a.dir).exists():
        render(a.dir)
    _, segs = build()
    frames = eyes.load_clip(a.dir, width=perception.WORK_W)
    want = set(a.classes.split(",")) if a.classes else None
    res = defaultdict(list)
    for seg in segs:
        if want and seg["class"] not in want:
            continue
        clip = frames[seg["s0"] : seg["s1"] + 1]
        pc = perception.perceive(clip)
        labels = pc.labels_in(0, len(clip) - 1)
        ok, why = judge(seg, pc.events, labels)
        res[seg["class"]].append(ok)
        if a.verbose or not ok:
            print(f"{'PASS' if ok else 'FAIL'} {seg['class']:<14} v{seg['variant']} s{seg['s0']}-{seg['s1']} {why}")
            if not ok or a.verbose:
                print("     events:", [e for e in pc.events if e.label not in ('VFX_BURST',)] or "none")
    print()
    allok = True
    for cls, oks in res.items():
        rate = sum(oks) / len(oks)
        allok &= rate >= a.min_pass
        print(f"{cls:<14} {sum(oks)}/{len(oks)}  {'ok' if rate >= a.min_pass else 'FAIL'}")
    tot = sum(sum(v) for v in res.values())
    cnt = sum(len(v) for v in res.values())
    print(f"\nTOTAL {tot}/{cnt}")
    if a.reference:
        allok &= score_reference(a.reference)
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
