"""Round-trip check of the Roblox export: python tools/check_export.py duel_short [hero|dummy] [--steps 1,2,3,4,6]

Exports the animation to .rbxmx text, plays it back with Roblox's rules (Linear easing = CFrame:Lerp, Motor6D forward kinematics)
and prints the largest difference (studs) against the engine. Use it before trusting a resampled export (step > 1).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from examples.scenes import SCENES  # noqa: E402
from tsb_engine.export_check import check_export, optimize_keys, suggest_step  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("scene")
    p.add_argument("character", nargs="?", default=None)
    p.add_argument("--steps", default="1,2,3,4,6")
    p.add_argument("--tolerance", type=float, default=0.05)
    p.add_argument("--optimize", action="store_true", help="adaptive keyframes: fewest keys within the tolerance")
    a = p.parse_args()
    scene = SCENES[a.scene]()
    for ch in scene.characters:
        if a.character and ch.name != a.character:
            continue
        steps = tuple(int(x) for x in a.steps.split(","))
        best, reports = suggest_step(ch.anim, a.tolerance, steps)
        print(f"== {ch.name} ({ch.anim.last_frame + 1} frames, dislocation up to {reports[0].dislocation:.2f} studs by design)")
        for r in reports:
            print("  " + r.line())
        print(f"  -> largest key step within {a.tolerance} studs: {best}")
        if a.optimize:
            ks = optimize_keys(ch.anim, a.tolerance)
            r = check_export(ch.anim, keys_at=ks)
            print(f"  adaptive: {len(ks)} keys of {ch.anim.last_frame + 1} frames, max error {r.max_error:.3f} studs ({r.line()})")


if __name__ == "__main__":
    main()
