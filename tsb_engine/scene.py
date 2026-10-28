"""Scenes: several characters placed in the world, plus export for the HTML viewer."""

from __future__ import annotations

from dataclasses import dataclass, field

from .kinematics import ROOT_REST_Y, SIZES, apply, compose, part_transforms, pose_transform
from .cinematic import Cinematic
from .linter import lint
from .mathutil import Transform, Vec, rot_y, translate
from .model import PARTS, Animation
from .secondary import Outfit

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
    outfit: Outfit | None = None  # secondary-motion extras (hair, coat tails, hat), preview only
    face: str = "std"  # "std" (dots + line) or "smirk" (round glasses, one-sided smile)
    face_colors: dict[str, str] | None = None  # paint every face of every part (the R6 "face test" dummy): front/back/right/left/top/bottom -> hex
    head_shape: str = "box"  # "box" | "ball" (a light rounded head, as on the test dummy)
    hide: tuple[str, ...] = ()  # parts not drawn in the preview (replaced by an ``Attach`` mesh, e.g. a mannequin's round head)

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
    markers: list[dict] = field(default_factory=list)  # {"f": 12, "label": "...", "act": bool, "hold": n}
    bands: list[dict] = field(default_factory=list)  # {"f0": a, "f1": b, "label": "...", "show": bool}
    cine: Cinematic | None = None
    hold: int = 1  # animate on a slower clock: characters (and extras) update every `hold` frames (2 = twos)

    @property
    def n_frames(self) -> int:
        if self.cine is not None:
            return self.cine.n_frames
        return max(c.anim.last_frame for c in self.characters) + 1


def export_viewer_data(scene: Scene) -> dict:
    """JSON-serialisable data for ``viewer/viewer.html``."""
    chars = []
    meshes: dict = {}
    for c in scene.characters:
        frames = []
        for f in range(scene.n_frames):
            tf = c.world_parts(f - f % scene.hold)
            frames.append(
                [
                    [round(v, 4) for row in tf[p][0] for v in row] + [round(v, 4) for v in tf[p][1]]
                    for p in PARTS
                ]
            )
        findings = [fd.to_dict() for fd in lint(c.anim)]
        extras = []
        if c.outfit is not None:
            for tr in c.outfit.simulate(c, scene.n_frames, scene.hold, scene.fps):
                extras.append({"name": tr.name, "shape": tr.shape, "size": [round(v, 3) for v in tr.size], "color": tr.color, "vis": list(tr.vis) if tr.vis else None,
                               "frames": [[round(v, 4) for row in t[0] for v in row] + [round(v, 4) for v in t[1]] for t in tr.frames]})
        for mname, mesh in (c.outfit.meshes() if c.outfit is not None else {}).items():
            meshes[mname] = {"v": [round(float(x), 4) for x in mesh.v.reshape(-1)], "f": [int(i) for i in mesh.f.reshape(-1)],
                             "m": [int(i) for i in mesh.mat], "cols": list(mesh.materials)}
        chars.append({"name": c.name, "face": c.face, "colors": c.colors, "frames": frames, "findings": findings, "extras": extras, "hide": list(c.hide), "faceColors": c.face_colors, "headShape": c.head_shape})
    markers = list(scene.markers)
    bands = list(scene.bands)
    ev = scene.events
    if isinstance(ev.get("windup"), int):
        markers.append({"f": ev["windup"], "label": "armé"})
    if isinstance(ev.get("impact"), int):
        markers.append({"f": ev["impact"], "label": "impact"})
    if isinstance(ev.get("hitstop"), (list, tuple)):
        bands.append({"f0": ev["hitstop"][0], "f1": ev["hitstop"][1], "label": "hitstop"})
    data = {
        "name": scene.name,
        "fps": scene.fps,
        "nFrames": scene.n_frames,
        "events": scene.events,
        "parts": list(PARTS),
        "sizes": {p: list(SIZES[p]) for p in PARTS},
        "characters": chars,
        "meshes": meshes,
        "lookAt": [0.0, 3.0, -2.0],
        "ground": 16,
        "striker": scene.characters[0].anim.striker if scene.cine is None else None,
        "markers": markers,
        "bands": bands,
    }
    if scene.cine is not None:
        data["cine"] = scene.cine.to_dict()
    return data
