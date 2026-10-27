"""TSB-style R6 combat animation toolkit: model, forward kinematics, pose helpers, linter."""

from .linter import Finding, Thresholds, format_report, lint
from .model import PARTS, Animation, Key, Pose
from .moves import plant_legs, torso_pose

__all__ = [
    "Animation",
    "Finding",
    "Key",
    "PARTS",
    "Pose",
    "Thresholds",
    "format_report",
    "lint",
    "plant_legs",
    "torso_pose",
]
