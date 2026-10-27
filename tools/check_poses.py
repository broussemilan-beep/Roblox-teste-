"""Readability report of a scene's frames as seen from its cameras: python tools/check_poses.py duel_short 62,104,262"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from examples.scenes import SCENES  # noqa: E402
from tsb_engine.readability import format_reports  # noqa: E402

if __name__ == "__main__":
    scene = SCENES[sys.argv[1]]()
    frames = [int(x) for x in sys.argv[2].split(",")]
    print(format_reports(scene, frames))
