"""Merge partial pose-fit JSONs (same schema) into one, later files overriding earlier ones.

usage: python tools/merge_poses.py OUT.json A.json B.json [...]
"""

from __future__ import annotations

import json
import sys


def main():
    out, parts = sys.argv[1], sys.argv[2:]
    docs = [json.load(open(p)) for p in parts]
    merged = dict(docs[0])
    by_frame = {}
    for d in docs:
        for fr in d["frames"]:
            by_frame[fr["f"]] = fr
    merged["frames"] = [by_frame[k] for k in sorted(by_frame)]
    json.dump(merged, open(out, "w"))
    print(len(merged["frames"]), "frames ->", out)


if __name__ == "__main__":
    main()
