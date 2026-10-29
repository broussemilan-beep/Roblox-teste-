"""Cut the CMU clips actually used by the combo and store ONLY their retargeted R6 angles (docs/research/mocap-r6/clips.npz).

The raw BVH files are not kept in the repository (CMU: free to use, not to re-sell the data); only the derived angles of the few seconds used are stored.

usage: python tools/mocap_library.py BVH_DIR
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import mocap  # noqa: E402

# id -> (start s, end s) kept at 60 images/s (the first image of a CMU file is a T-pose, skipped)
CUTS = {
    "144_20": (0.2, 18.9), "102_11": (0.05, 1.5), "49_04": (0.05, 2.1), "09_01": (0.05, 1.2), "105_39": (0.05, 3.7), "140_01": (0.05, 6.9),
    "07_01": (0.05, 6.0), "144_05": (0.2, 23.0), "144_13": (0.2, 16.0), "144_01": (0.2, 20.0), "111_21": (0.2, 19.0),
}
OUT = ROOT / "docs" / "research" / "mocap-r6" / "clips.npz"


def main():
    d = Path(sys.argv[1])
    store = {}
    for cid, (t0, t1) in CUTS.items():
        f = d / f"{cid}.bvh"
        if not f.exists():
            print("missing", cid)
            continue
        b = mocap.parse(f)
        pos, rot = mocap.fk(b)
        c = mocap.retarget(b, pos, rot, name=cid)
        a, e = int(t0 * c.fps), min(int(t1 * c.fps), len(c))
        step = int(round(c.fps / 60))
        sl = slice(a, e, step)
        store[f"{cid}_ang"], store[f"{cid}_xz"], store[f"{cid}_air"] = c.ang[sl].astype(np.float32), c.xz[sl].astype(np.float32), c.air[sl].astype(np.float32)
        store[f"{cid}_fps"] = np.array(c.fps / step)
        print(cid, len(c.ang[sl]), "images at", c.fps / step, "fps")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, **store)
    print("->", OUT, round(OUT.stat().st_size / 1024), "KiB")


if __name__ == "__main__":
    main()
