"""Animation linter: turns craft rules into checks on the keyed data.

Confidence levels (every finding carries one):

* ``physical``  – follows from the rig geometry (e.g. a leg corner below the ground).
* ``heuristic`` – a rule of thumb whose threshold is a *starting value* to tune on real
                  animations. Thresholds live in :class:`Thresholds`.
* ``style``     – an aesthetic preference (TSB/anime look), not a correctness rule.

Nothing here corrects the animation; it only reports.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .kinematics import SIZES, lowest_point, lowest_y, part_transforms, root_transform
from .mathutil import apply
from .model import PARTS, Animation, Pose


@dataclass
class Thresholds:
    ground_eps: float = 0.03
    snap_max_frames: dict[str, int] = field(
        default_factory=lambda: {"light": 4, "heavy": 2, "power": 2}
    )
    torso_twist_min_deg: dict[str, float] = field(
        default_factory=lambda: {"light": 20.0, "heavy": 90.0, "power": 80.0}
    )
    asym_min_deg: float = 10.0
    overlap_min_lag_frames: int = 1
    overlap_window_after_impact: int = 6
    dislocation_max_studs: float = 1.5
    dislocation_visible_studs: float = 0.3
    dislocation_max_frames: int = 4
    still_max_frames: int = 6
    foot_plant_height: float = 0.1
    foot_drift_max_per_frame: float = 0.15
    pos_weight: float = 20.0  # 1 stud of motion counts as this many degrees of speed


@dataclass
class Finding:
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str
    frames: tuple[int, int] | None = None
    confidence: str = "heuristic"

    def to_dict(self) -> dict:
        return asdict(self)


def _mirror_rot(rot: tuple[float, float, float]) -> tuple[float, float, float]:
    return (rot[0], -rot[1], -rot[2])


def _asymmetry(a: Pose, b: Pose) -> float:
    """Degrees-equivalent difference between a limb and the *mirror* of its partner."""
    mb = _mirror_rot(b.rot)
    rot_diff = max(abs(x - y) for x, y in zip(a.rot, mb))
    pos_diff = max(abs(x - y) for x, y in zip(a.pos, (-b.pos[0], b.pos[1], b.pos[2])))
    return max(rot_diff, pos_diff * 20.0)


def _speed(anim: Animation, part: str, f: int, t: Thresholds) -> float:
    a, b = anim.sample_part(part, f - 1), anim.sample_part(part, f)
    return sum(abs(x - y) for x, y in zip(a.rot, b.rot)) + t.pos_weight * sum(
        abs(x - y) for x, y in zip(a.pos, b.pos)
    )


def _peak_frame(anim: Animation, part: str, lo: int, hi: int, t: Thresholds) -> tuple[int, float]:
    """Earliest frame whose speed is within 2% of the maximum (stable on plateaus/ties)."""
    speeds = {f: _speed(anim, part, f, t) for f in range(max(lo, 1), hi + 1)}
    if not speeds:
        return lo, 0.0
    top = max(speeds.values())
    first = min(f for f, v in speeds.items() if v >= 0.98 * top)
    return first, top


def check_clipping(anim: Animation, t: Thresholds) -> list[Finding]:
    depths = [
        (f, lowest_y(anim.sample(f), root=root_transform(anim.sample_root(f))))
        for f in range(anim.last_frame + 1)
    ]
    bad = [(f, d) for f, d in depths if d < -t.ground_eps]
    if not bad:
        return []
    worst = min(d for _, d in bad)
    return [
        Finding(
            "TSB001",
            "error",
            f"Body parts go below the ground (worst {worst:.2f} studs) on {len(bad)} frame(s). "
            "Tilt/spread the legs (moves.plant_legs) or allow it explicitly for a crater.",
            (bad[0][0], bad[-1][0]),
            "physical",
        )
    ]


def check_events(anim: Animation) -> tuple[int | None, int | None, list[Finding]]:
    w, i = anim.event_frame("windup"), anim.event_frame("impact")
    if w is None or i is None:
        return None, None, [
            Finding(
                "TSB009",
                "info",
                "Events 'windup' and 'impact' are missing: snap, twist, symmetry, overlap and "
                "dislocation checks were skipped.",
                None,
                "physical",
            )
        ]
    if w >= i:
        return None, None, [
            Finding("TSB011", "error", f"'windup' ({w}) must be before 'impact' ({i}).", (w, i), "physical")
        ]
    return w, i, []


def check_snap(anim: Animation, w: int, i: int, t: Thresholds) -> list[Finding]:
    limit = t.snap_max_frames.get(anim.archetype, t.snap_max_frames["light"])
    frames = i - w
    if frames > limit:
        return [
            Finding(
                "TSB002",
                "warning",
                f"Strike travel is {frames} frames (windup {w} -> impact {i}); "
                f"'{anim.archetype}' attacks target <= {limit}. The hit will read as soft.",
                (w, i),
            )
        ]
    return []


def check_twist(anim: Animation, w: int, i: int, t: Thresholds) -> list[Finding]:
    need = t.torso_twist_min_deg.get(anim.archetype, t.torso_twist_min_deg["light"])
    span = abs(anim.sample_part("Torso", i).rot[1] - anim.sample_part("Torso", w).rot[1])
    if span < need:
        return [
            Finding(
                "TSB003",
                "warning",
                f"Torso yaw only changes {span:.0f} deg between windup and impact; "
                f"'{anim.archetype}' attacks target >= {need:.0f} deg.",
                (w, i),
            )
        ]
    return []


def check_symmetry(anim: Animation, w: int, i: int, t: Thresholds) -> list[Finding]:
    out: list[Finding] = []
    for frame in (w, i):
        s = anim.sample(frame)
        for a, b, label in (("Right Arm", "Left Arm", "arms"), ("Right Leg", "Left Leg", "legs")):
            if _asymmetry(s[a], s[b]) < t.asym_min_deg:
                out.append(
                    Finding(
                        "TSB004",
                        "warning",
                        f"Key pose at frame {frame}: {label} are (nearly) mirror-symmetric "
                        f"(< {t.asym_min_deg:.0f} deg apart). Break the symmetry.",
                        (frame, frame),
                    )
                )
    return out


def check_overlap(anim: Animation, w: int, i: int, t: Thresholds) -> list[Finding]:
    hi = i + t.overlap_window_after_impact
    torso_f, torso_v = _peak_frame(anim, "Torso", w, hi, t)
    if torso_v <= 0:
        return []
    out: list[Finding] = []
    for part in ("Head", anim.striker):
        f, v = _peak_frame(anim, part, w, hi, t)
        if v <= 0:
            continue
        if f - torso_f < t.overlap_min_lag_frames:
            out.append(
                Finding(
                    "TSB005",
                    "warning",
                    f"{part} peaks at frame {f}, torso at {torso_f}: no follow-through lag "
                    f"(expected >= {t.overlap_min_lag_frames} frame after the torso).",
                    (torso_f, f),
                )
            )
    return out


def check_dislocation(anim: Animation, w: int, i: int, t: Thresholds) -> list[Finding]:
    mags = [
        (f, math.sqrt(sum(c * c for c in anim.sample_part(anim.striker, f).pos)))
        for f in range(anim.last_frame + 1)
    ]
    peak_f, peak = max(mags, key=lambda m: m[1])
    out: list[Finding] = []
    if peak > t.dislocation_max_studs:
        out.append(
            Finding(
                "TSB006",
                "error",
                f"{anim.striker} detaches {peak:.2f} studs from the shoulder (max "
                f"{t.dislocation_max_studs}); the illusion breaks.",
                (peak_f, peak_f),
            )
        )
    run, longest = 0, 0
    for _, m in mags:
        run = run + 1 if m > t.dislocation_visible_studs else 0
        longest = max(longest, run)
    if longest > t.dislocation_max_frames:
        out.append(
            Finding(
                "TSB006",
                "warning",
                f"{anim.striker} stays visibly detached for {longest} consecutive frames "
                f"(max {t.dislocation_max_frames}); it will look like a glitch, not a smear.",
                None,
            )
        )
    if anim.archetype in ("heavy", "power") and peak < t.dislocation_visible_studs:
        out.append(
            Finding(
                "TSB010",
                "info",
                f"No visible dislocation (peak {peak:.2f} studs) on a '{anim.archetype}' strike. "
                "Optional smear: a brief forward offset of the striking limb at impact.",
                (w, i),
                "style",
            )
        )
    return out


def check_statue(anim: Animation, t: Thresholds) -> list[Finding]:
    last = anim.last_frame
    speeds = [sum(_speed(anim, p, f, t) for p in PARTS) for f in range(1, last + 1)]
    moving = [f for f, s in enumerate(speeds, start=1) if s > 1e-6]
    if not moving:
        return [Finding("TSB007", "warning", "The animation never moves.", None)]
    lo, hi = moving[0], moving[-1]
    hitstop = anim.event_range("hitstop")
    out: list[Finding] = []
    run_start = None
    for f in range(lo, hi + 2):
        still = f <= hi and speeds[f - 1] <= 1e-6
        if hitstop and hitstop[0] <= f <= hitstop[1]:
            still = False
        if still and run_start is None:
            run_start = f
        elif not still and run_start is not None:
            length = f - run_start
            if length > t.still_max_frames:
                out.append(
                    Finding(
                        "TSB007",
                        "warning",
                        f"Completely frozen for {length} frames ({run_start}-{f - 1}) outside a "
                        "declared hitstop. Add a moving hold (slow drift) so it doesn't look crashed.",
                        (run_start, f - 1),
                    )
                )
            run_start = None
    return out


def check_foot_slide(anim: Animation, t: Thresholds) -> list[Finding]:
    if anim.events.get("dash"):
        return []
    worst, worst_f = 0.0, 0
    prev: dict[str, tuple[float, float] | None] = {"Right Leg": None, "Left Leg": None}
    for f in range(anim.last_frame + 1):
        tf = part_transforms(anim.sample(f), root=root_transform(anim.sample_root(f)))
        for leg in prev:
            contact = lowest_point(leg, tf[leg])
            sole = apply(tf[leg], (0.0, -SIZES[leg][1] / 2, 0.0))  # stable point: sole centre
            if contact[1] <= t.foot_plant_height:
                if prev[leg] is not None:
                    d = math.hypot(sole[0] - prev[leg][0], sole[2] - prev[leg][1])  # type: ignore[index]
                    if d > worst:
                        worst, worst_f = d, f
                prev[leg] = (sole[0], sole[2])
            else:
                prev[leg] = None
    if worst > t.foot_drift_max_per_frame:
        return [
            Finding(
                "TSB008",
                "info",
                f"A planted foot moves {worst:.2f} studs in one frame (frame {worst_f}): possible "
                "foot sliding. Ignore if it is an intentional slide/dash (set the 'dash' event).",
                (worst_f, worst_f),
                "physical",
            )
        ]
    return []


def lint(anim: Animation, thresholds: Thresholds | None = None) -> list[Finding]:
    t = thresholds or Thresholds()
    findings: list[Finding] = []
    findings += check_clipping(anim, t)
    if anim.archetype == "reaction":  # victim/idle clips have no windup -> impact structure
        w = i = None
    else:
        w, i, ev = check_events(anim)
        findings += ev
    if w is not None and i is not None:
        findings += check_snap(anim, w, i, t)
        findings += check_twist(anim, w, i, t)
        findings += check_symmetry(anim, w, i, t)
        findings += check_overlap(anim, w, i, t)
        findings += check_dislocation(anim, w, i, t)
    findings += check_statue(anim, t)
    findings += check_foot_slide(anim, t)
    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda f: (order[f.severity], f.code))


def format_report(anim: Animation, findings: list[Finding]) -> str:
    lines = [f"{anim.name}  ({anim.archetype}, striker={anim.striker}, {anim.last_frame + 1} frames @ {anim.fps} fps)"]
    if not findings:
        lines.append("  no findings")
    for f in findings:
        where = f" [frames {f.frames[0]}-{f.frames[1]}]" if f.frames else ""
        lines.append(f"  {f.severity.upper():7} {f.code} ({f.confidence}){where}: {f.message}")
    return "\n".join(lines)
