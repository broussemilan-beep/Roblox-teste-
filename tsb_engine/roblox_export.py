"""Export an Animation to Roblox: a KeyframeSequence ``.rbxmx`` and a Luau builder script.

Sources of the facts used here (all opened while researching, see docs/research/github-survey.md):

* Stock R6 Motor6D C0/C1 (``gat516/martial-world``, ``art/player/techniques/green_dragon_whirlwind.py``):
  each joint has C0 and C1 sharing the same rotation matrix ``M`` (RootJoint and Neck: the same ``M``).
* A ``Pose.CFrame`` is the Motor6D ``Transform``: ``world(Part1) = Part0 * C0 * Transform * C1^-1``.
* ``.rbxmx`` structure: ``rojo-rbx/rbx-dom`` XML docs (https://dom.rojo.space/xml.html) and Studio-saved files.

This engine expresses limb rotations in the *torso frame* with plain translations for C0/C1, so a pose
maps to Roblox as ``Transform = M^-1 * X * M`` where ``X`` is the engine's joint transform. The
mapping is checked in the tests by re-running Roblox's forward kinematics and comparing it with
``kinematics.part_transforms``. What is NOT verified is how Studio reacts to a hand-written file:
Roblox warns that ``.rbxm``/``.rbxmx`` edited outside Studio "might not upload or function", so the
Luau builder is provided as a fallback that creates the KeyframeSequence inside Studio.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .kinematics import pose_transform
from .mathutil import Mat, Transform, Vec, compose, mat_mul, transpose, translate
from .model import PARTS, ROOT, Animation, Pose

# Motor6D rotation shared by C0 and C1 (row-major R00 R01 R02 R10 R11 R12 R20 R21 R22).
_M_SPINE: Mat = ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))  # RootJoint, Neck
_M_RIGHT: Mat = ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))  # Right Shoulder, Right Hip
_M_LEFT: Mat = ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))  # Left Shoulder, Left Hip

# part -> (Motor6D name, C0 position, C1 position, shared rotation)
R6_JOINTS: dict[str, tuple[str, Vec, Vec, Mat]] = {
    "Torso": ("RootJoint", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), _M_SPINE),
    "Head": ("Neck", (0.0, 1.0, 0.0), (0.0, -0.5, 0.0), _M_SPINE),
    "Right Arm": ("Right Shoulder", (1.0, 0.5, 0.0), (-0.5, 0.5, 0.0), _M_RIGHT),
    "Left Arm": ("Left Shoulder", (-1.0, 0.5, 0.0), (0.5, 0.5, 0.0), _M_LEFT),
    "Right Leg": ("Right Hip", (1.0, -1.0, 0.0), (0.5, 1.0, 0.0), _M_RIGHT),
    "Left Leg": ("Left Hip", (-1.0, -1.0, 0.0), (-0.5, 1.0, 0.0), _M_LEFT),
}

# Roblox enums (numeric values written by Studio)
PRIORITY = {"Idle": 0, "Movement": 1, "Action": 2, "Action2": 3, "Action3": 4, "Action4": 5, "Core": 1000}
EVENT_MARKERS = {"windup": "Windup", "impact": "Hit", "hitstop": "Hit Stop", "dash": "Dash", "launch": "Launch"}


def pose_cframe(part: str, sample: dict[str, Pose], root: Pose | None = None) -> Transform:
    """Roblox ``Pose.CFrame`` (= Motor6D Transform) of ``part`` for an engine sample."""
    m = R6_JOINTS[part][3]
    x = pose_transform(sample.get(part, Pose()))
    if part == "Torso" and root is not None:
        x = compose(pose_transform(root), x)  # the HumanoidRootPart stays put: root motion lives in RootJoint
    rot = mat_mul(mat_mul(transpose(m), x[0]), m)
    mt = transpose(m)
    pos = tuple(sum(mt[i][k] * x[1][k] for k in range(3)) for i in range(3))
    return rot, pos  # type: ignore[return-value]


def roblox_forward_kinematics(cframes: dict[str, Transform]) -> dict[str, Transform]:
    """What Roblox computes: HRP at (0, 3, 0), ``W(limb) = W(Torso) * C0 * Transform * C1^-1``."""
    hrp = translate((0.0, 3.0, 0.0))
    out: dict[str, Transform] = {}
    for part, (_name, c0, c1, m) in R6_JOINTS.items():
        c0t, c1t = (m, c0), (m, c1)
        inv_c1 = (transpose(m), tuple(-sum(transpose(m)[i][k] * c1[k] for k in range(3)) for i in range(3)))
        parent = hrp if part == "Torso" else out["Torso"]
        out[part] = compose(compose(compose(parent, c0t), cframes[part]), inv_c1)
        del c1t
    return out


# ---------------------------------------------------------------- sampling
def keyframe_times(anim: Animation, step: int = 1, start: int = 0, end: int | None = None, authored: bool = True) -> list[int]:
    """Frames to export: a regular grid every ``step`` frames, plus (``authored``) every key the animator placed and the frame
    just before each *constant* (held) segment ends - so cuts, teleports and holds survive a coarse ``step``.

    Roblox interpolates between exported keyframes (Linear easing): without these extra keys a 60-stud blink-cut would be
    exported as a smooth slide (see ``export_check``: 35 studs of error at step 2).
    """
    last = anim.last_frame if end is None else end
    frames = set(range(start, last + 1, max(1, step)))
    frames.add(last)
    if authored:
        for track in anim.tracks.values():
            for k, nxt in zip(track, track[1:] + [None]):
                if start <= k.frame <= last:
                    frames.add(k.frame)
                if nxt is not None and k.easing == "constant" and start <= nxt.frame - 1 <= last and nxt.frame - 1 > k.frame:
                    frames.add(nxt.frame - 1)
    return sorted(frames)


def _cf_xml(t: Transform, pad: str) -> str:
    (r, p) = t
    comp = [("X", p[0]), ("Y", p[1]), ("Z", p[2])] + [
        (f"R{i}{j}", r[i][j]) for i in range(3) for j in range(3)
    ]
    inner = "".join(f"<{k}>{_num(v)}</{k}>" for k, v in comp)
    return f'{pad}<CoordinateFrame name="CFrame">{inner}</CoordinateFrame>\n'


def _num(v: float) -> str:
    if abs(v) < 5e-7:
        return "0"
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def markers_for(anim: Animation, fps: int) -> list[tuple[int, str]]:
    """(frame, marker name) for the animation's events (``impact`` -> ``Hit``...)."""
    out: list[tuple[int, str]] = []
    for name in anim.events:
        label = EVENT_MARKERS.get(name, name.title())
        rng = anim.event_range(name)
        f = anim.event_frame(name)
        if f is not None:
            out.append((f, label))
        elif rng is not None:
            out.append((rng[0], label))
    return sorted(out)


def to_rbxmx(
    anim: Animation, name: str | None = None, fps: int | None = None, priority: str = "Action",
    loop: bool = False, step: int = 1, extra_markers: list[tuple[int, str]] | None = None,
    frames: list[int] | None = None,
) -> str:
    """KeyframeSequence as ``.rbxmx`` text. One keyframe every ``step`` frames (or exactly ``frames``), Linear easing, R6 rig."""
    fps = fps or anim.fps
    frames = sorted(set(frames)) if frames else keyframe_times(anim, step)
    markers = markers_for(anim, fps) + list(extra_markers or [])
    marker_at: dict[int, list[str]] = {}
    for f, label in markers:  # snap markers to the nearest exported keyframe (markers must sit on keyframes)
        snapped = min(frames, key=lambda k: abs(k - f))
        marker_at.setdefault(snapped, []).append(label)
    ref = [0]

    def nxt() -> str:
        ref[0] += 1
        return f"RBX{ref[0] - 1}"

    lines = ['<roblox version="4">', f' <Item class="KeyframeSequence" referent="{nxt()}">', "  <Properties>",
             f'   <string name="Name">{escape(name or anim.name)}</string>',
             f'   <bool name="Loop">{"true" if loop else "false"}</bool>',
             f'   <token name="Priority">{PRIORITY[priority]}</token>', "  </Properties>"]

    def pose(pname: str, cf: Transform, weight: int, depth: int) -> list[str]:
        pad = "  " * depth
        return [f'{pad}<Item class="Pose" referent="{nxt()}">', f"{pad} <Properties>",
                f'{pad}  <string name="Name">{pname}</string>', _cf_xml(cf, pad + "  ").rstrip("\n"),
                f'{pad}  <float name="Weight">{weight}</float>',
                f'{pad}  <token name="EasingStyle">0</token>', f'{pad}  <token name="EasingDirection">0</token>',
                f"{pad} </Properties>"]

    identity: Transform = ((( 1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0))
    for f in frames:
        sample = anim.sample(f)
        root = anim.sample_root(f)
        cfs = {p: pose_cframe(p, sample, root) for p in PARTS}
        lines += [f'  <Item class="Keyframe" referent="{nxt()}">', "   <Properties>",
                  '    <string name="Name">Keyframe</string>', f'    <float name="Time">{_num(f / fps)}</float>', "   </Properties>"]
        lines += pose("HumanoidRootPart", identity, 0, 3)
        lines += pose("Torso", cfs["Torso"], 1, 4)
        for limb in PARTS:
            if limb == "Torso":
                continue
            lines += pose(limb, cfs[limb], 1, 5)
            lines.append("      </Item>")
        lines += ["    </Item>", "   </Item>"]
        for label in marker_at.get(f, []):
            lines += [f'   <Item class="KeyframeMarker" referent="{nxt()}">', "    <Properties>",
                      f'     <string name="Name">{escape(label)}</string>', '     <string name="Value"></string>',
                      "    </Properties>", "   </Item>"]
        lines.append("  </Item>")
    lines += [" </Item>", "</roblox>"]
    return "\n".join(lines) + "\n"


def to_luau(anim: Animation, name: str | None = None, fps: int | None = None, priority: str = "Action", step: int = 1,
            extra_markers: list[tuple[int, str]] | None = None, frames: list[int] | None = None) -> str:
    """Luau script to paste in Studio's command bar: builds the KeyframeSequence in ServerStorage."""
    fps = fps or anim.fps
    frames = sorted(set(frames)) if frames else keyframe_times(anim, step)
    marker_at: dict[int, list[str]] = {}
    for f, label in markers_for(anim, fps) + list(extra_markers or []):
        marker_at.setdefault(min(frames, key=lambda k: abs(k - f)), []).append(label)

    def cf(t: Transform) -> str:
        r, p = t
        vals = [p[0], p[1], p[2]] + [r[i][j] for i in range(3) for j in range(3)]
        return "CFrame.new(" + ",".join(_num(v) for v in vals) + ")"

    out = ['-- Generated by tsb_engine.roblox_export (R6). Run in the Studio command bar.',
           'local ks = Instance.new("KeyframeSequence")', f'ks.Name = "{name or anim.name}"', "ks.Loop = false",
           f"ks.Priority = Enum.AnimationPriority.{priority}",
           "local function pose(parent, n, cframe, w)", '\tlocal p = Instance.new("Pose")', "\tp.Name = n",
           "\tp.CFrame = cframe", "\tp.Weight = w", "\tp.EasingStyle = Enum.PoseEasingStyle.Linear",
           "\tp.EasingDirection = Enum.PoseEasingDirection.In", "\tp.Parent = parent", "\treturn p", "end"]
    for f in frames:
        sample, root = anim.sample(f), anim.sample_root(f)
        out += [f"do", '\tlocal k = Instance.new("Keyframe")', f"\tk.Time = {_num(f / fps)}", "\tk.Parent = ks",
                '\tlocal hrp = pose(k, "HumanoidRootPart", CFrame.new(), 0)',
                f'\tlocal torso = pose(hrp, "Torso", {cf(pose_cframe("Torso", sample, root))}, 1)']
        for limb in PARTS:
            if limb != "Torso":
                out.append(f'\tpose(torso, "{limb}", {cf(pose_cframe(limb, sample, root))}, 1)')
        for label in marker_at.get(f, []):
            out += ['\tlocal m = Instance.new("KeyframeMarker")', f'\tm.Name = "{label}"', "\tm.Parent = k"]
        out.append("end")
    out += ["ks.Parent = game:GetService(\"ServerStorage\")",
            'print("KeyframeSequence created in ServerStorage: open it with the Animation Editor (Import) or the plugin of your choice.")']
    return "\n".join(out) + "\n"


def write_rbxmx(anim: Animation, path: str, **kwargs) -> str:
    text = to_rbxmx(anim, **kwargs)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


__all__ = ["R6_JOINTS", "pose_cframe", "roblox_forward_kinematics", "to_rbxmx", "to_luau", "write_rbxmx", "ROOT"]
