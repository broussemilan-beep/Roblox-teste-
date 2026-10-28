"""Run-cycle check: the hero runs 36 studs along +X with the gait of ``tsb_engine.gait``; a side camera follows. Used to look at foot contact and silhouettes
and compared with the tracked run of the reference (images 284-299). ``python tools/build_viewer.py run_test``."""

from __future__ import annotations

from tsb_engine.authoring import rest_on_ground
from tsb_engine.cinematic import Cinematic, tracking
from tsb_engine.gait import add_air, run_keys, stride_speed
from tsb_engine.kinematics import apply
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from .ronin_model import RONIN_COLORS, ronin_outfit

N, PERIOD, AMP = 90, 12.0, 45.0


def build(period: float = PERIOD, amp: float = AMP, lean: float = 18.0, sword: bool = True) -> Scene:
    hero = Character("hero", Animation("hero", fps=30, archetype="cinematic"), colors=RONIN_COLORS, outfit=ronin_outfit(), face="std")
    v = stride_speed(amp, period)
    run_keys(hero.anim, 0, N - 1, lambda f: (v * f, 0.0, 270.0), period=period, amp=amp, lean=lean, sword_arm=sword)
    rest_on_ground(hero, range(N))
    add_air(hero, range(N), 0, period, 0.45)
    cine = Cinematic(N, fps=30)
    cine.sky_color, cine.floor_color = "#3d3b41", "#66646a"
    hp = lambda f: apply(hero.world_parts(int(f))["Torso"], (0, 0, 0))
    cine.shot(0, N - 1, tracking(hp, (0.0, 1.0, 12.0), look_dy=0.0, fov=34))
    return Scene("run test", [hero], fps=30, cine=cine)
