"""Scenes: several characters placed in the world, plus export for the HTML viewer."""

from __future__ import annotations

from dataclasses import dataclass, field

from .kinematics import ROOT_REST_Y, SIZES, apply, compose, part_transforms, pose_transform
from .linter import lint
from .mathutil import Transform, Vec, rot_y, translate
from .model import PARTS, Animation

DEFAULT_COLORS = {
    "Torso": "#2f6fdd",
    "Head": "#f2c94c",
    "Right Arm": "#f2c94c",
    "Left Arm": "#f2c94c",
    "Right Leg": "#4a9b5b",
    "Left Leg": "#4a9b5b",
}


@dataclass
class Character:
    name: str
    anim: Animation
    base_pos: Vec = (0.0, 0.0, 0.0)  # world position of the point under the root (ground level)
    base_yaw: float = 0.0  # degrees; 0 = faces world -Z
    colors: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLORS))

    def base_transform(self) -> Transform:
        return (rot_y(self.base_yaw), self.base_pos)

    def world_parts(self, frame: float) -> dict[str, Transform]:
        root = compose(
            self.base_transform(),
            compose(translate((0.0, ROOT_REST_Y, 0.0)), pose_transform(self.anim.sample_root(frame))),
        )
        return part_transforms(self.anim.sample(frame), root=root)

    def limb_tip(self, part: str, frame: float) -> Vec:
        """World position of the free end of a limb (centre of its far face)."""
        return apply(self.world_parts(frame)[part], (0.0, -SIZES[part][1] / 2, 0.0))


@dataclass
class Scene:
    name: str
    characters: list[Character]
    fps: int = 60
    events: dict[str, object] = field(default_factory=dict)  # shown on the viewer timeline

    @property
    def n_frames(self) -> int:
        return max(c.anim.last_frame for c in self.characters) + 1


def export_viewer_data(scene: Scene) -> dict:
    """JSON-serialisable data for ``viewer/viewer.html``."""
    chars = []
    for c in scene.characters:
        frames = []
        for f in range(scene.n_frames):
            tf = c.world_parts(f)
            frames.append(
                [
                    [round(v, 4) for row in tf[p][0] for v in row] + [round(v, 4) for v in tf[p][1]]
                    for p in PARTS
                ]
            )
        findings = [fd.to_dict() for fd in lint(c.anim)]
        chars.append({"name": c.name, "colors": c.colors, "frames": frames, "findings": findings})
    return {
        "name": scene.name,
        "fps": scene.fps,
        "nFrames": scene.n_frames,
        "events": scene.events,
        "parts": list(PARTS),
        "sizes": {p: list(SIZES[p]) for p in PARTS},
        "characters": chars,
        "lookAt": [0.0, 3.0, -2.0],
        "ground": 16,
        "striker": scene.characters[0].anim.striker,
    }
