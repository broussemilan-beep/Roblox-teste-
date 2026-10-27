"""Animation data model: sparse per-part tracks of poses with easing.

A ``Pose`` is a joint transform *relative to the rest pose*:

* ``pos``  – translation in studs, expressed in the parent joint frame
             (this is how "dislocation" / smear offsets are written).
* ``rot``  – rotation in degrees (rx, ry, rz), Roblox ``CFrame.Angles`` order.

For ``Torso`` the parent frame is the HumanoidRootPart (kept fixed, never animated).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

PARTS = ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")
# Optional whole-body track (knockback, jumps). Pose.pos/rot are relative to the character's
# base placement in the scene, in the character's own frame (it always faces local -Z).
ROOT = "Root"


@dataclass(frozen=True)
class Pose:
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def lerp(self, other: "Pose", t: float) -> "Pose":
        return Pose(
            tuple(a + (b - a) * t for a, b in zip(self.pos, other.pos)),  # type: ignore[arg-type]
            tuple(a + (b - a) * t for a, b in zip(self.rot, other.rot)),  # type: ignore[arg-type]
        )


REST = Pose()

EASINGS: dict[str, Callable[[float], float]] = {
    "constant": lambda t: 0.0,  # hold the starting key until the next key
    "linear": lambda t: t,
    "quad_in": lambda t: t * t,
    "cubic_in": lambda t: t * t * t,
    "quad_out": lambda t: 1 - (1 - t) ** 2,
    "cubic_out": lambda t: 1 - (1 - t) ** 3,
    "expo_out": lambda t: 1.0 if t >= 1 else 1 - 2 ** (-10 * t),
    "sine_inout": lambda t: -(math.cos(math.pi * t) - 1) / 2,
}


@dataclass(frozen=True)
class Key:
    frame: int
    pose: Pose
    easing: str = "linear"  # easing of the segment that *starts* at this key


@dataclass
class Animation:
    name: str
    fps: int = 60
    archetype: str = "light"  # "light" | "heavy" | "power" | "reaction" (see linter)
    striker: str = "Right Arm"
    # name -> frame, or name -> [start, end] (e.g. "hitstop")
    events: dict[str, object] = field(default_factory=dict)
    tracks: dict[str, list[Key]] = field(default_factory=dict)

    def set_key(self, part: str, frame: int, pose: Pose, easing: str = "linear") -> None:
        if part not in PARTS and part != ROOT:
            raise ValueError(f"unknown R6 part: {part!r}")
        if easing not in EASINGS:
            raise ValueError(f"unknown easing: {easing!r}")
        track = [k for k in self.tracks.get(part, []) if k.frame != frame]
        track.append(Key(frame, pose, easing))
        track.sort(key=lambda k: k.frame)
        self.tracks[part] = track

    @property
    def last_frame(self) -> int:
        frames = [k.frame for t in self.tracks.values() for k in t]
        return max(frames) if frames else 0

    def sample_part(self, part: str, frame: float) -> Pose:
        track = self.tracks.get(part)
        if not track:
            return REST
        if frame <= track[0].frame:
            return track[0].pose
        if frame >= track[-1].frame:
            return track[-1].pose
        for a, b in zip(track, track[1:]):
            if a.frame <= frame < b.frame:
                t = (frame - a.frame) / (b.frame - a.frame)
                return a.pose.lerp(b.pose, EASINGS[a.easing](t))
        return track[-1].pose

    def sample(self, frame: float) -> dict[str, Pose]:
        return {p: self.sample_part(p, frame) for p in PARTS}

    def sample_root(self, frame: float) -> Pose:
        return self.sample_part(ROOT, frame)

    def event_frame(self, name: str) -> int | None:
        value = self.events.get(name)
        return int(value) if isinstance(value, (int, float)) else None

    def event_range(self, name: str) -> tuple[int, int] | None:
        value = self.events.get(name)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return int(value[0]), int(value[1])
        return None
