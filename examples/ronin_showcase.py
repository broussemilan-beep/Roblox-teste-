"""Model check: the Ronin and the mannequin seen close, from three sides, standing / crouched / blade drawn.

Frames 0-119 front close-up, 120-239 three-quarter orbit, 240-359 crouch with the katana drawn and the dummy in the foreground.
This is a *modelling* scene (to look at the meshes), not an animation.
"""

from __future__ import annotations

from tsb_engine.authoring import K, P, tp
from tsb_engine.cinematic import Cinematic, orbit
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene

from .ronin_model import RONIN_COLORS, dummy_outfit, ronin_outfit

DUMMY_COLORS = {"Head": "#f1ead8", "Torso": "#e6dfcc", "Left Arm": "#f1ead8", "Right Arm": "#f1ead8", "Left Leg": "#cfc8b6", "Right Leg": "#cfc8b6"}


def build() -> Scene:
    hero = Character("ronin", Animation("ronin", fps=60, archetype="cinematic"), colors=RONIN_COLORS, outfit=ronin_outfit(drawn=True), face="std")
    dummy = Character("dummy", Animation("dummy", fps=60, archetype="cinematic"), base_pos=(-4.5, 0, -1.0), base_yaw=160.0, colors=DUMMY_COLORS, outfit=dummy_outfit(), hide=("Head",))
    a = hero.anim
    K(a, 0, "linear", R=P((0, 0, 0), (0, 0, 0)), T=tp(0, 0, 0), RA=P((0, 0, 6)), LA=P((0, 0, -6)))
    K(a, 239, "sine_inout", R=P((0, 0, 0), (0, 0, 0)), T=tp(0, 0, 0), RA=P((0, 0, 6)), LA=P((0, 0, -6)))
    K(a, 300, "sine_inout", R=P((0, 0, 0), (0, -0.9, 0)), T=tp(0.6, -14, 0), H=P((16, 0, 0)), RA=P((95, 0, 6)), LA=P((30, 0, -22)), RL=P((55, 0, 4)), LL=P((60, 0, -4)))
    K(a, 359, "sine_inout", R=P((0, 0, 0), (0, -0.9, 0)), T=tp(0.6, -14, 0), H=P((16, 0, 0)), RA=P((95, 0, 6)), LA=P((30, 0, -22)), RL=P((55, 0, 4)), LL=P((60, 0, -4)))
    b = dummy.anim
    K(b, 0, "linear", R=P((0, 0, 0), (0, 0, 0)))
    K(b, 359, "linear", R=P((0, 0, 0), (0, 0, 0)))
    cine = Cinematic(360)
    cine.sky_color, cine.floor_color = "#8f9cab", "#8c9098"
    cine.shot(0, 119, orbit((0, 3.6, 0), 10.0, 180, 180, 4.2, 4.2, 0.0, fov=32))
    cine.shot(120, 239, orbit((0, 3.3, 0), 10.0, 150, 330, 4.6, 3.4, 0.0, fov=34))
    cine.shot(240, 359, orbit((0, 2.4, -0.5), 9.0, 140, 215, 3.0, 3.0, 0.0, fov=34))
    return Scene("Ronin — modèle", [hero, dummy], cine=cine)
