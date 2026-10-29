"""« VFX Practice Day2 » again, but moved by REAL human motion: gestures of the CMU Graphics Lab motion capture database retargeted to the R6 rig
(``tsb_engine/mocap.py``, clips in ``docs/research/mocap-r6/clips.npz``), cut, sped up to the combo's timing and chained with cross-fades.

The story and its timing are the reference's (aura 56-66, spin 74, throw 109, slam 137, beam 150: image numbers of the recording, the film starts at 48); the VFX of
``examples/practice.py`` are reused untouched, they follow the rig.  CMU data: free to use, not to re-sell.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tsb_engine import mocap

from . import practice

LIB = Path(__file__).resolve().parent.parent / "docs" / "research" / "mocap-r6" / "clips.npz"
START = (-14.1, -1.27)   # the reference's first ground point (X, Z), from practice.solve_track

# film images are reference images - 48; each gesture: stored clip, seconds taken from it, images it gets (30 per second)
SPEC = [
    dict(clip="144_20", t0=3.0, t1=3.4, n=10, yaw=180),                 # 0-10    guard, facing the camera
    dict(clip="144_20", t0=8.4, t1=9.2, n=10, yaw=250),                 # 10-20   sink into the lunge, turning to the right: the charge
    dict(clip="102_11", t0=0.3, t1=1.2, n=14),                          # 20-34   the spin
    dict(clip="49_04", t0=0.3, t1=2.0, n=22, yaw=-90),                  # 34-56   run to the right and leap
    dict(clip="144_20", t0=2.0, t1=2.6, n=10, yaw=0),                   # 56-66   plant, back to the camera: stance, then the throw at 61
    dict(clip="144_20", t0=8.6, t1=9.4, n=10),                          # 66-76   crouch
    dict(clip="105_39", t0=1.0, t1=2.2, n=14),                          # 76-90   the leap, landing at 90
    dict(clip="144_20", t0=8.5, t1=9.4, n=12, yaw=-90),                 # 90-102  deep lunge
    dict(clip="144_20", t0=6.3, t1=7.0, n=10),                          # 102-112 the beam: arm thrown out
    dict(clip="144_01", t0=1.75, t1=3.3, n=22, align=True),             # 112-134 a cartwheel to the right (the reference tumbles and slides)
    dict(clip="144_20", t0=3.0, t1=4.0, n=15, yaw=180),                 # 134-149 back up into the guard (the loop closes)
]


def motion():
    lib = mocap.load_library(LIB)
    ref = practice.keyed_angles()
    RX, RZ, _ = practice.solve_track(ref)   # the reference's measured ground track
    ang, xz, air = mocap.assemble(SPEC, lib, follow=np.stack([RX, RZ], 1), start_xz=(float(RX[0]), float(RZ[0])))
    n = practice.N
    if len(ang) != n:   # trim or hold the last pose to the film's length
        ang = np.vstack([ang, np.repeat(ang[-1:], max(0, n - len(ang)), 0)])[:n]
        xz = np.vstack([xz, np.repeat(xz[-1:], max(0, n - len(xz)), 0)])[:n]
        air = np.concatenate([air, np.repeat(air[-1:], max(0, n - len(air)))])[:n]
    return ang, xz[:, 0], xz[:, 1], air


def build():
    return practice.build(motion=motion())
