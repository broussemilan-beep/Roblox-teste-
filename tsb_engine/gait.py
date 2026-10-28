"""A run cycle for the R6 rig that does not look like a marionette.

What makes R6 running read as running, and what the first versions of this project got wrong (limbs flapped at random, nothing planted):

* the legs are rigid sticks: a leg swinging forward and back lifts the body only through the **planted foot**, so the root height is *derived* from the feet
  (``authoring.rest_on_ground``) instead of being keyed: that produces the bob (lowest when the legs are split, highest when they pass) for free and no sliding;
* the **stride and the speed are tied**: a foot planted during half a cycle travels ``2 L sin(amp)`` studs relative to the body, so the body must advance
  ``4 L sin(amp) / period`` studs per image or the feet skate (``stride_speed``);
* the **trailing leg swings further back than the leading leg forward** (it has to clear the ground), arms counter-swing the legs, the torso counter-rotates
  to the hips, the head stays level looking ahead, the root rolls a little with every step.

``run_keys`` writes the keys; the caller calls ``rest_on_ground`` on the same frames afterwards (it needs the finished pose).
"""

from __future__ import annotations

import math

from .authoring import K, P, root_pose, tp

LEG = 2.0  # R6 leg length in studs


def stride_speed(amp_deg: float, period: float) -> float:
    """Studs per image at which a foot planted for half a cycle does not slide."""
    return 4.0 * LEG * math.sin(math.radians(amp_deg)) / period


def run_keys(anim, f0: int, f1: int, path, period: float = 12.0, amp: float = 45.0, lean: float = 18.0, arm: float = 45.0,
             sword_arm: bool = False, phase0: float = 0.0, easing: str = "linear") -> None:
    """Key a run on every image of ``[f0, f1]``. ``path(f) -> (x, z, ry)``: world position under the torso and heading (degrees, the engine's ``ry``)."""
    for f in range(f0, f1 + 1):
        ph = 2.0 * math.pi * (f - f0) / period + phase0
        s, c2 = math.sin(ph), math.cos(2.0 * ph)
        lead = lambda v: amp * v if v > 0 else amp * 1.3 * v  # the trailing leg goes further back
        rl, ll = lead(s), lead(-s)
        ra = -arm * s
        la = arm * s
        x, z, ry = path(f)
        right_arm = P((-95 + 6 * c2, 0, -22)) if sword_arm else P((ra, 0, 9))
        K(anim, f, easing,
          R=root_pose(x, 3.0, z, 0.0, ry, 3.0 * s),
          T=tp(0.15, -lean + 2.5 * c2, 7.0 * s, 2.0 * s),
          H=P((lean * 0.85 - 2.0 * c2, -6.0 * s, 0)),
          RA=right_arm, LA=P((la, 0, -9)),
          RL=P((rl, 0, 3)), LL=P((ll, 0, -3)))


def add_air(char, frames, f0: int, period: float, height: float, phase0: float = 0.0) -> None:
    """Flight phases: call after ``rest_on_ground``. The body is lifted by ``height * sin^2(phase)``: zero at mid-stance (the passing pose, planted foot) and
    ``height`` when the legs are split (both feet in the air) - the spring of a real run. Rigid R6 legs alone bob only a few hundredths of a stud."""
    from .model import ROOT, Pose

    for f in frames:
        ph = 2.0 * math.pi * (f - f0) / period + phase0
        r = char.anim.sample_root(f)
        char.anim.set_key(ROOT, f, Pose((r.pos[0], r.pos[1] + height * math.sin(ph) ** 2, r.pos[2]), r.rot), "linear")
