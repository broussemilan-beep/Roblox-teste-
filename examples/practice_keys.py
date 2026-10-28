"""Animated key poses of the « VFX Practice Day2 » combo - authored, not traced.

The reference (5 s loop, 40-pixel figure, motion blur) gives the *story and the timing*; the poses are written the way an animator would stage them: every action has an
anticipation (a counter-move), a fast release, an overshoot and a settle; weight is shown by crouching before every push and by landing low; the arms and the head
trail the torso by a frame or two (``LAG``); the facing turns through the body (twist) before the hips follow.

Story, in reference image numbers (the film starts at 48):
  48-52   guard, a small weight shift                       | 98-110  skid, plant, coil, THROW (magenta shock rings at 109)
  52-64   anticipation: turn to the right, sink, coil      | 110-120 recover, deep crouch (spring loaded)
  58-66   violet charge (tremor) | 64-82 counter-turn then a 1.5 turn SPIN | 120-134 LEAP, apex, dive
  82-96   low lunging dash with dust, flight, brake        | 137     IMPACT (rings), prone slide | 142-150 push up, spring | 150-156 beam lunge
  156-178 low slide then a forward roll                     | 178-196 rise, turn to the camera, guard (= the first pose, so the loop closes)

Conventions (measured with ``tools/keypose_lab.py``): ``ry`` is the yaw, 180 = facing the camera, 270 (= -90) = facing the right of the picture (the direction of travel),
0 (= -360) = back to the camera; it is written *unwrapped* so a turn goes the way it is authored. Negative ``T_rx`` / ``rx`` lean forward; ``*_rx`` > 0 swings a limb
forward; ``RA_rz`` > 0 and ``LA_rz`` < 0 raise the arms out to the sides; ``RL_rz`` > 0, ``LL_rz`` < 0 spread the legs. ``air`` = height of the lowest point above the ground.
"""

from __future__ import annotations

NAMES = ["ry", "rx", "rz", "T_rx", "T_ry", "T_rz", "H_rx", "H_ry", "RA_rx", "RA_rz", "LA_rx", "LA_rz", "RL_rx", "RL_rz", "LL_rx", "LL_rz"]

# seconds-of-animator-sense: the head trails the torso by 1 image, the arms by 2, the legs lead
LAG = {"head": 1.0, "arms": 2.0, "legs": 0.0}

GUARD = dict(RA_rx=45, RA_rz=14, LA_rx=45, LA_rz=-14, RL_rz=15, LL_rz=-15)

KEYS: dict[int, dict] = {
    # --- guard, then the weight shifts back onto the rear foot: anticipation of the turn --------------------------------
    48: dict(ry=180, **GUARD),
    50: dict(ry=186, rx=3, T_rx=-3, H_ry=-8, RA_rx=50, RA_rz=18, LA_rx=40, LA_rz=-12, RL_rz=17, LL_rz=-17),
    53: dict(ry=212, rx=-2, T_rx=-8, T_ry=12, H_ry=-18, RA_rx=75, RA_rz=14, LA_rx=30, LA_rz=-16, RL_rx=-12, RL_rz=17, LL_rx=18, LL_rz=-17),
    # --- turn to the right, sink into a lunge, the right arm swings back (cocked) ---------------------------------------
    56: dict(ry=250, rx=-8, T_rx=-24, T_ry=26, H_ry=-30, RA_rx=-75, RA_rz=22, LA_rx=105, LA_rz=-8, RL_rx=-48, RL_rz=8, LL_rx=52, LL_rz=-8),
    60: dict(ry=262, rx=6, rz=-4, T_rx=-32, T_ry=40, H_ry=-40, RA_rx=-115, RA_rz=26, LA_rx=115, LA_rz=-6, RL_rx=-58, RL_rz=8, LL_rx=62, LL_rz=-6),   # coiled, charging (violet)
    63: dict(ry=266, rx=7, rz=3, T_rx=-34, T_ry=44, H_ry=-42, RA_rx=-120, RA_rz=28, LA_rx=118, LA_rz=-6, RL_rx=-60, RL_rz=8, LL_rx=64, LL_rz=-6),
    # --- counter-turn (anticipation), then the whip: one and a half turns with the arms flung out ---------------------------
    65: dict(ry=300, rx=-4, T_rx=-30, T_ry=-45, H_ry=30, RA_rx=-40, RA_rz=40, LA_rx=60, LA_rz=-40, RL_rx=-40, RL_rz=14, LL_rx=45, LL_rz=-14),
    68: dict(ry=170, rx=-6, rz=-8, T_rx=-18, T_ry=0, H_ry=0, RA_rx=30, RA_rz=100, LA_rx=30, LA_rz=-100, RL_rx=-20, RL_rz=24, LL_rx=25, LL_rz=-24, air=0.7),
    72: dict(ry=0, rx=-6, rz=-14, T_rx=-14, RA_rx=10, RA_rz=105, LA_rx=10, LA_rz=-105, RL_rx=28, RL_rz=22, LL_rx=-26, LL_rz=-22, air=1.0),
    76: dict(ry=-170, rx=-6, rz=-14, T_rx=-14, RA_rx=10, RA_rz=100, LA_rx=10, LA_rz=-100, RL_rx=-26, RL_rz=22, LL_rx=28, LL_rz=-22, air=0.9),
    79: dict(ry=-330, rx=-10, rz=-8, T_rx=-20, RA_rx=30, RA_rz=85, LA_rx=30, LA_rz=-85, RL_rx=20, RL_rz=18, LL_rx=-20, LL_rz=-18, air=0.5),
    # --- the spin ends facing right, landing deep into the lunge; dust ---------------------------------------------------
    82: dict(ry=-440, rx=-22, T_rx=-38, T_ry=14, H_ry=-14, RA_rx=-70, RA_rz=18, LA_rx=60, LA_rz=-10, RL_rx=-62, RL_rz=6, LL_rx=68, LL_rz=-6),
    # --- the dash: contact, flight, contact, with the lean carrying forward -------------------------------------------
    85: dict(ry=-450, rx=-24, T_rx=-30, RA_rx=-85, RA_rz=10, LA_rx=95, LA_rz=-6, RL_rx=-55, LL_rx=70, air=0.9),
    88: dict(ry=-450, rx=-26, T_rx=-30, RA_rx=95, RA_rz=6, LA_rx=-85, LA_rz=-6, RL_rx=68, LL_rx=-60, air=0.0),
    91: dict(ry=-450, rx=-26, T_rx=-30, RA_rx=-90, RA_rz=6, LA_rx=95, LA_rz=-6, RL_rx=-60, LL_rx=70, air=0.7),
    94: dict(ry=-440, rx=-18, T_rx=-24, RA_rx=70, RA_rz=14, LA_rx=-60, LA_rz=-10, RL_rx=62, LL_rx=-40, air=0.1),
    # --- brake: the feet plant wide, the body swings round to show its back, the weight comes back up --------------------------
    97: dict(ry=-395, rx=6, T_rx=-18, T_ry=-20, H_ry=25, RA_rx=30, RA_rz=60, LA_rx=-40, LA_rz=-50, RL_rx=52, RL_rz=20, LL_rx=-18, LL_rz=-20),
    # --- stance (back to the camera): arm out toward the right, the other behind; then COIL and THROW --------------------------
    100: dict(ry=-362, rx=-4, T_rx=-24, T_ry=-14, H_ry=12, RA_rx=10, RA_rz=96, LA_rx=-30, LA_rz=-26, RL_rx=44, RL_rz=18, LL_rx=-6, LL_rz=-16),
    103: dict(ry=-360, rx=-6, T_rx=-30, T_ry=18, H_ry=-8, RA_rx=70, RA_rz=14, LA_rx=-25, LA_rz=-30, RL_rx=48, RL_rz=20, LL_rx=-8, LL_rz=-18),   # arm pulled across: anticipation
    106: dict(ry=-352, rx=-10, T_rx=-40, T_ry=34, H_ry=-14, RA_rx=95, RA_rz=-8, LA_rx=-40, LA_rz=-36, RL_rx=52, RL_rz=22, LL_rx=-12, LL_rz=-20),
    108: dict(ry=-372, rx=-4, T_rx=-22, T_ry=-34, H_ry=18, RA_rx=6, RA_rz=104, LA_rx=-55, LA_rz=-22, RL_rx=40, RL_rz=16, LL_rx=-4, LL_rz=-14),   # THROW (rings at 109)
    110: dict(ry=-378, rx=-3, T_rx=-24, T_ry=-40, H_ry=22, RA_rx=0, RA_rz=96, LA_rx=-60, LA_rz=-18, RL_rx=40, RL_rz=16, LL_rx=-4, LL_rz=-14),    # overshoot, hold
    # --- recover into a deep crouch facing the camera, arms hugging in (spring loaded) -------------------------------------
    114: dict(ry=-440, rx=-8, T_rx=-36, T_ry=10, H_ry=-8, RA_rx=70, RA_rz=10, LA_rx=60, LA_rz=-10, RL_rx=62, RL_rz=12, LL_rx=48, LL_rz=-12),
    118: dict(ry=-520, rx=-12, T_rx=-44, RA_rx=-30, RA_rz=22, LA_rx=-20, LA_rz=-22, RL_rx=70, RL_rz=16, LL_rx=64, LL_rz=-16),
    121: dict(ry=-535, rx=-14, T_rx=-48, RA_rx=-70, RA_rz=18, LA_rx=-60, LA_rz=-18, RL_rx=76, RL_rz=14, LL_rx=70, LL_rz=-14),   # lowest point before the leap
    # --- LEAP: stretch on take-off, turn to the right in the air, tuck at the apex, then dive ------------------------------------
    124: dict(ry=-530, rx=-4, rz=18, T_rx=0, RA_rx=-150, RA_rz=22, LA_rx=-135, LA_rz=-22, RL_rx=-14, RL_rz=10, LL_rx=12, LL_rz=-10, air=0.9),
    128: dict(ry=-480, rx=-16, rz=10, T_rx=-24, T_ry=-20, RA_rx=-30, RA_rz=70, LA_rx=40, LA_rz=-80, RL_rx=62, RL_rz=12, LL_rx=64, LL_rz=-12, air=2.3),   # apex, knees up
    131: dict(ry=-450, rx=-34, T_rx=-10, RA_rx=150, RA_rz=14, LA_rx=150, LA_rz=-14, RL_rx=-22, RL_rz=6, LL_rx=-26, LL_rz=-6, air=1.9),                   # dive begins: superman
    134: dict(ry=-450, rx=-62, T_rx=-6, RA_rx=170, RA_rz=10, LA_rx=170, LA_rz=-10, RL_rx=-24, LL_rx=-18, air=1.0),
    # --- IMPACT at 137: a prone slide, then it pushes up ----------------------------------------------------------------------
    137: dict(ry=-450, rx=-84, rz=0, T_rx=-4, RA_rx=175, LA_rx=175, RL_rx=-14, LL_rx=-10, air=0.0),
    141: dict(ry=-450, rx=-88, rz=2, T_rx=0, RA_rx=170, LA_rx=172, RL_rx=-10, LL_rx=-6),
    144: dict(ry=-450, rx=-78, T_rx=-18, RA_rx=140, RA_rz=14, LA_rx=140, LA_rz=-14, RL_rx=20, LL_rx=34),
    147: dict(ry=-450, rx=-42, T_rx=-48, RA_rx=100, RA_rz=14, LA_rx=104, LA_rz=-14, RL_rx=72, RL_rz=8, LL_rx=66, LL_rz=-8),   # knees under, pushing
    # --- spring into the beam lunge: arms thrown forward, the body recoils, rings of violet ------------------------------------
    150: dict(ry=-450, rx=-12, T_rx=-24, RA_rx=100, RA_rz=4, LA_rx=102, LA_rz=-4, RL_rx=-46, RL_rz=6, LL_rx=54, LL_rz=-6),
    153: dict(ry=-450, rx=6, T_rx=-14, RA_rx=108, RA_rz=2, LA_rx=108, LA_rz=-2, RL_rx=-40, RL_rz=6, LL_rx=48, LL_rz=-6),     # recoil: the beam pushes the chest back
    156: dict(ry=-450, rx=-22, T_rx=-30, RA_rx=70, RA_rz=14, LA_rx=60, LA_rz=-12, RL_rx=-50, RL_rz=8, LL_rx=60, LL_rz=-8),
    # --- low slide into a forward roll (a real roll: the pitch keeps going, limbs tucked) ------------------------------------------
    160: dict(ry=-450, rx=-62, T_rx=-24, RA_rx=130, LA_rx=130, RL_rx=34, LL_rx=40),
    164: dict(ry=-450, rx=-120, T_rx=-50, RA_rx=100, RA_rz=10, LA_rx=100, LA_rz=-10, RL_rx=90, RL_rz=8, LL_rx=88, LL_rz=-8),
    168: dict(ry=-450, rx=-205, T_rx=-60, RA_rx=100, LA_rx=100, RL_rx=100, LL_rx=98),
    172: dict(ry=-450, rx=-295, T_rx=-60, RA_rx=100, LA_rx=100, RL_rx=100, LL_rx=98),
    176: dict(ry=-450, rx=-355, T_rx=-44, RA_rx=60, RA_rz=18, LA_rx=60, LA_rz=-18, RL_rx=82, RL_rz=10, LL_rx=78, LL_rz=-10),
    # --- rise, turn to the camera (the head leads the turn), a small settle, the guard again ---------------------------------------
    180: dict(ry=-462, rx=-368, T_rx=-30, T_ry=-14, H_ry=-24, RA_rx=40, RA_rz=20, LA_rx=40, LA_rz=-20, RL_rx=44, RL_rz=14, LL_rx=40, LL_rz=-14),
    184: dict(ry=-500, rx=-362, T_rx=-10, T_ry=-10, H_ry=-14, RA_rx=60, RA_rz=18, LA_rx=50, LA_rz=-16, RL_rx=12, RL_rz=16, LL_rx=10, LL_rz=-16),
    188: dict(ry=-535, rx=-357, T_rx=2, RA_rx=34, RA_rz=14, LA_rx=36, LA_rz=-14, RL_rz=15, LL_rz=-15),
    192: dict(ry=-540, rx=-360, T_rx=-2, RA_rx=48, RA_rz=14, LA_rx=48, LA_rz=-14, RL_rz=15, LL_rz=-15),
    196: dict(ry=-540, rx=-360, **GUARD),
}
