"""Export everything a Roblox game needs from a scene: ``python tools/export_roblox.py berserker_ultimate``.

Writes to ``exports/``: ``<char>_ultimate.rbxmx`` + ``.luau`` (KeyframeSequence), ``ultimate_vfx_cues.md`` (fx in Roblox units)
and ``ultimate_hit_events.json`` (per-hit trauma / FOV punch / optional hit-stop / VFX seed + the camera shaker settings).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples import ultimate  # noqa: E402
from tsb_engine.roblox_cues import CAMERA_SHAKER, cue_sheet  # noqa: E402
from tsb_engine.roblox_export import to_luau, write_rbxmx  # noqa: E402

out = ROOT / "exports"
out.mkdir(exist_ok=True)
scene = ultimate.build()
marks = ultimate.roblox_markers()
for key, ch in zip(("berserker", "victim"), scene.characters):
    write_rbxmx(ch.anim, str(out / f"{key}_ultimate.rbxmx"), name=f"{key}_ultimate", extra_markers=marks[key])
    (out / f"{key}_ultimate.luau").write_text(to_luau(ch.anim, name=f"{key}_ultimate", extra_markers=marks[key]), encoding="utf-8")
(out / "ultimate_vfx_cues.md").write_text(cue_sheet(scene.cine), encoding="utf-8")
(out / "ultimate_hit_events.json").write_text(
    json.dumps({"camera_shaker": CAMERA_SHAKER, "hits": ultimate.hit_events(scene)}, indent=1), encoding="utf-8")
print("exported to", out)
