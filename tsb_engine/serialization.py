"""JSON (de)serialisation of animations.

Schema (``version`` 1)::

    {
      "version": 1, "name": "...", "fps": 60,
      "archetype": "heavy", "striker": "Right Arm",
      "events": {"windup": 14, "impact": 16, "hitstop": [16, 22]},
      "tracks": {
        "Torso": [{"frame": 0, "easing": "linear", "pos": [0,0,0], "rot": [0,0,0]}, ...],
        ...
      }
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from .model import Animation, Key, Pose


def to_dict(anim: Animation) -> dict:
    return {
        "version": 1,
        "name": anim.name,
        "fps": anim.fps,
        "archetype": anim.archetype,
        "striker": anim.striker,
        "events": anim.events,
        "tracks": {
            part: [
                {"frame": k.frame, "easing": k.easing, "pos": list(k.pose.pos), "rot": list(k.pose.rot)}
                for k in keys
            ]
            for part, keys in anim.tracks.items()
        },
    }


def from_dict(data: dict) -> Animation:
    if data.get("version") != 1:
        raise ValueError(f"unsupported animation schema version: {data.get('version')!r}")
    anim = Animation(
        name=data["name"],
        fps=data.get("fps", 60),
        archetype=data.get("archetype", "light"),
        striker=data.get("striker", "Right Arm"),
        events=data.get("events", {}),
    )
    for part, keys in data.get("tracks", {}).items():
        for k in keys:
            anim.set_key(
                part,
                int(k["frame"]),
                Pose(tuple(k.get("pos", (0, 0, 0))), tuple(k.get("rot", (0, 0, 0)))),  # type: ignore[arg-type]
                k.get("easing", "linear"),
            )
    return anim


def save(anim: Animation, path: str | Path) -> None:
    Path(path).write_text(json.dumps(to_dict(anim), indent=2) + "\n", encoding="utf-8")


def load(path: str | Path) -> Animation:
    return from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
