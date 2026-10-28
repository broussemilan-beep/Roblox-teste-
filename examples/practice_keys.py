"""Hand-read key poses of the « VFX Practice Day2 » rig, one per reference image (the automatic fit was too noisy: 40 px figure, motion blur, tinted frames).

Conventions (measured with ``tools/keypose_lab.py``): ``ry`` 180 = facing the camera, 270 = facing the right of the picture (the direction of travel), 0 = back to the camera, 90 = facing left.
Negative ``T_rx`` / ``rx`` lean forward; positive limb ``*_rx`` swings forward; ``RA_rz`` > 0 and ``LA_rz`` < 0 raise the arms out to the sides.
``air`` = height of the lowest point above the ground (studs). Everything not listed stays at 0.
"""

from __future__ import annotations

NAMES = ["ry", "rx", "rz", "T_rx", "T_ry", "T_rz", "H_rx", "H_ry", "RA_rx", "RA_rz", "LA_rx", "LA_rz", "RL_rx", "RL_rz", "LL_rx", "LL_rz"]

KEYS: dict[int, dict] = {
    48: dict(ry=180, RA_rx=40, RA_rz=15, LA_rx=40, LA_rz=-15, RL_rz=14, LL_rz=-14),
    52: dict(ry=215, T_rx=-12, RA_rx=60, RA_rz=20, LA_rx=60, LA_rz=-20, RL_rx=-20, RL_rz=14, LL_rx=25, LL_rz=-14),
    56: dict(ry=250, rx=-12, T_rx=-18, RA_rx=170, LA_rx=60, RL_rx=-35, LL_rx=35),
    60: dict(ry=200, rz=-30, T_rx=-10, RA_rx=140, RA_rz=40, LA_rx=100, LA_rz=-30, RL_rx=-30, LL_rx=30),
    64: dict(ry=100, rx=50, T_rx=10, RA_rx=60, RA_rz=60, LA_rx=60, LA_rz=-60, RL_rx=60, LL_rx=40, air=0.6),
    68: dict(ry=10, rx=-15, T_rx=-20, RA_rx=90, RA_rz=60, LA_rx=90, LA_rz=-60, RL_rx=-40, RL_rz=15, LL_rx=40, LL_rz=-15),
    72: dict(ry=5, rx=-18, T_rx=-30, RA_rx=70, RA_rz=80, LA_rx=70, LA_rz=-80, RL_rx=-30, RL_rz=12, LL_rx=30, LL_rz=-12),
    76: dict(ry=-100, rx=-12, T_rx=-20, RA_rx=60, RA_rz=90, LA_rx=60, LA_rz=-90, RL_rx=-30, LL_rx=30),
    80: dict(ry=-170, rx=-15, T_rx=-20, RA_rx=120, RA_rz=50, LA_rx=60, LA_rz=-30, RL_rx=-40, LL_rx=40),
    84: dict(ry=-120, rx=-20, T_rx=-20, RA_rx=140, LA_rx=60, RL_rx=30, LL_rx=-40, air=1.4),
    88: dict(ry=-90, rx=-20, T_rx=-30, RA_rx=130, LA_rx=-60, RL_rx=60, RL_rz=8, LL_rx=-50, LL_rz=-8),
    92: dict(ry=-60, rx=-22, T_rx=-35, RA_rx=-40, LA_rx=100, RL_rx=65, LL_rx=-45),
    98: dict(ry=0, rx=-5, T_rx=-30, RA_rx=60, RA_rz=100, LA_rx=60, LA_rz=-30, RL_rx=45, RL_rz=15, LL_rx=-5, LL_rz=-15),
    102: dict(ry=0, rx=-5, T_rx=-20, H_ry=-40, RA_rx=5, RA_rz=100, LA_rx=-30, LA_rz=-20, RL_rx=45, RL_rz=15, LL_rx=15, LL_rz=-12),
    108: dict(ry=300, rx=-8, T_rx=-25, RA_rx=70, RA_rz=100, LA_rx=40, LA_rz=-40, RL_rx=40, LL_rx=-25),
    114: dict(ry=300, rx=-10, T_rx=-20, RA_rx=70, RA_rz=90, LA_rx=40, LA_rz=-30, RL_rx=45, LL_rx=-30),
    120: dict(ry=200, rx=-10, T_rx=-30, RA_rx=130, RA_rz=30, LA_rx=40, LA_rz=-40, RL_rx=60, LL_rx=-40),
    124: dict(ry=10, rx=-12, rz=22, T_rx=-15, RA_rx=-20, RA_rz=40, LA_rx=60, LA_rz=-40, RL_rx=-40, LL_rx=50, air=0.8),
    128: dict(ry=-25, rx=-14, rz=8, T_rx=-18, T_ry=-15, RA_rx=-70, RA_rz=35, LA_rx=95, LA_rz=-25, RL_rx=-55, RL_rz=8, LL_rx=45, LL_rz=-6, air=2.0),
    132: dict(ry=-40, rx=-35, T_rx=-20, RA_rx=-120, RA_rz=40, LA_rx=60, LA_rz=-60, RL_rx=-40, LL_rx=50, air=1.8),
    138: dict(ry=-80, rx=-80, T_rx=-10, RA_rx=170, LA_rx=170, RL_rx=20, LL_rx=-10, air=1.2),
    144: dict(ry=-150, rx=-30, T_rx=-40, RA_rx=130, RA_rz=20, LA_rx=130, LA_rz=-20, RL_rx=65, LL_rx=-60),
    150: dict(ry=10, rx=-35, T_rx=-45, RA_rx=60, RA_rz=50, LA_rx=60, LA_rz=-50, RL_rx=-30, RL_rz=25, LL_rx=50, LL_rz=-25),
    156: dict(ry=-120, rx=-45, T_rx=-35, RA_rx=-90, LA_rx=-60, RL_rx=-30, LL_rx=50),
    162: dict(ry=-70, rx=-70, T_rx=-30, RA_rx=60, LA_rx=60, RL_rx=60, LL_rx=-30),
    168: dict(ry=-100, rx=-60, T_rx=-30, RA_rx=60, LA_rx=60, RL_rx=60, LL_rx=-30),
    174: dict(ry=-80, rx=-20, T_rx=-50, RA_rx=60, LA_rx=60, RL_rx=70, LL_rx=40),
    180: dict(ry=-60, rx=-5, T_rx=-60, RA_rx=70, LA_rx=70, RL_rx=70, LL_rx=70),
    186: dict(ry=-70, rx=-5, T_rx=-30, RA_rx=40, LA_rx=40, RL_rx=30, LL_rx=-20),
    192: dict(ry=205, RA_rx=30, LA_rx=30, RL_rz=12, LL_rz=-12),
    196: dict(ry=180, RA_rx=30, RA_rz=10, LA_rx=30, LA_rz=-10, RL_rz=10, LL_rz=-10),
}
