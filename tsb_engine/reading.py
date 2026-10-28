"""Reading ledger: what I claim to see, checked against what the eyes measure.

Misreading a reference (taking a VFX-made multi-hit for several real hits, missing a 2-frame black frame, calling a camera move a pose
change) is the expensive error. This module makes the reading explicit and testable:

1. ``skeleton(perception)`` writes a reading template from the measured events (shot boundaries, punctuation, walls, camera moves);
2. I fill in, per shot, what I *looked at and saw* (``viewed`` frame ranges, ``hits``, ``vfx_multihit``, ``camera``, ``victim``...);
3. ``validate(reading, perception)`` returns contradictions between the claims and the measurements, and the frames that were never looked at.

A contradiction is not proof that the claim is wrong - the measurements have known blind spots (``perception`` docstring) - it is the list
of places to look again with ``window_sheet`` before writing the final analysis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .perception import Perception


@dataclass
class Issue:
    shot: tuple[int, int]
    kind: str      # "contradiction" | "unviewed" | "missing"
    message: str

    def __str__(self) -> str:
        return f"[{self.kind}] shots {self.shot[0]}-{self.shot[1]}: {self.message}"


def shots_from(pc: Perception) -> list[tuple[int, int]]:
    """Shot boundaries: measured cuts, punctuation frames and walls split the clip."""
    marks = {0, pc.n}
    for ev in pc.events:
        if ev.label in ("CUT",):
            marks.add(ev.start)
        elif ev.label in ("PUNCT_BLACK", "PUNCT_WHITE", "VFX_WALL", "EMPTY"):
            marks.add(ev.start)
            marks.add(ev.end + 1)
    ks = sorted(m for m in marks if 0 <= m <= pc.n)
    return [(a, b - 1) for a, b in zip(ks, ks[1:]) if b > a]


def skeleton(pc: Perception) -> dict:
    """A reading template to fill in: one entry per measured shot, with the measured facts next to empty claims."""
    out = []
    for a, b in shots_from(pc):
        labels = sorted({e.label for e in pc.in_range(a, b) if e.label not in ("VFX_BURST",)})
        out.append({"start": a, "end": b, "measured": labels, "viewed": [], "camera": "", "hits": None, "vfx_multihit": None,
                    "victim": "", "punct": "", "notes": ""})
    return {"fps": pc.fps, "frames": pc.n, "shots": out}


def _covered(viewed: list, a: int, b: int) -> float:
    have = set()
    for r in viewed:
        lo, hi = (r, r) if isinstance(r, int) else (r[0], r[1])
        have.update(range(max(a, lo), min(b, hi) + 1))
    return len(have) / (b - a + 1)


def validate(reading: dict, pc: Perception, min_cover: float = 1.0, long_shot: int = 12) -> list[Issue]:
    issues: list[Issue] = []
    measured = shots_from(pc)
    claimed = [(s["start"], s["end"]) for s in reading["shots"]]
    for a, b in measured:
        if not any(ca <= a and b <= cb or (ca <= b and a <= cb) for ca, cb in claimed):
            issues.append(Issue((a, b), "missing", "a measured shot has no entry in the reading"))
    for s in reading["shots"]:
        a, b = s["start"], s["end"]
        labels = {e.label for e in pc.in_range(a, b)}
        n = b - a + 1
        cover = _covered(s.get("viewed", []), a, b)
        need = 1.0 if n < long_shot else min_cover * 0.6
        if cover < need:
            issues.append(Issue((a, b), "unviewed", f"only {cover:.0%} of the frames were looked at (need {need:.0%}): open the window sheet"))
        cam = (s.get("camera") or "").lower()
        if cam == "static" and "CAMERA_MOVE" in labels:
            issues.append(Issue((a, b), "contradiction", "claimed a static camera but a consistent background motion was measured"))
        if cam in ("pan", "orbit", "dolly", "move") and "CAMERA_MOVE" not in labels and n >= 8:
            issues.append(Issue((a, b), "contradiction", "claimed a camera move but none was measured over this shot"))
        p = (s.get("punct") or "").lower()
        if p == "black" and "PUNCT_BLACK" not in labels:
            issues.append(Issue((a, b), "contradiction", "claimed black frames, none measured"))
        if p == "white" and "PUNCT_WHITE" not in labels:
            issues.append(Issue((a, b), "contradiction", "claimed white frames, none measured"))
        if p in ("", "none") and (labels & {"PUNCT_BLACK", "PUNCT_WHITE"}):
            issues.append(Issue((a, b), "contradiction", "a black/white punctuation frame was measured here and not written down"))
        if s.get("hits") is not None and s["hits"] >= 3 and "MULTIHIT_VFX" in labels and s.get("vfx_multihit") is not True:
            issues.append(Issue((a, b), "contradiction", f"claimed {s['hits']} distinct hits but the clip shows a flash on every image with the victim shaken: check whether it is ONE pose + VFX"))
        if s.get("vfx_multihit") is True and "REAL_COMBO" in labels:
            issues.append(Issue((a, b), "contradiction", "claimed a VFX-made multi-hit but separate flashes with a reacting victim were measured"))
        if s.get("hits") is not None and s["hits"] >= 1 and not labels & {"SINGLE_HIT_SMEAR", "REAL_COMBO", "MULTIHIT_VFX", "HELD_WITH_VFX", "VFX_BURST"} and n >= 6:
            issues.append(Issue((a, b), "contradiction", "claimed hits but no flash/burst was measured"))
        v = (s.get("victim") or "").lower()
        if v == "cycling" and "VICTIM_CYCLING" not in labels:
            issues.append(Issue((a, b), "contradiction", "claimed a cycling victim, not measured (check by eye: the measure needs the victim fully on screen)"))
    return issues


def load(path: str) -> dict:
    return json.loads(open(path, encoding="utf-8").read())


def save(obj: dict, path: str) -> None:
    open(path, "w", encoding="utf-8").write(json.dumps(obj, indent=1, ensure_ascii=False))
