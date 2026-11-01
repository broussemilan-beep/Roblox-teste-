"""Render each modelled VFX kind alone on a dark ground (the way the reference showcases are shot) to judge its look.

usage: /tmp/bpyenv/bin/python tools/vfx_lab.py OUT_DIR [kind ...]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import mathutils  # noqa: E402

import vfx_mesh  # noqa: E402

C3 = mathutils.Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))

CASES = {
    "star": dict(kind="star", t0=0, dur=100, c=(0, 4.0, 0), r0=7.0, r1=7.0, color="#ff7a1a", a=1.0, strength=6.0, **{"in": 0.01, "fade": 0.3}),
    "dome": dict(kind="dome", t0=0, dur=100, c=(0, 0.0, 0), r0=5.0, r1=5.0, color="#ff9a1f", a=1.0, strength=5.0, rim=0.6, fill=0.12, height=0.9, **{"in": 0.01, "fade": 0.2}),
    "blades": dict(kind="blades", t0=0, dur=100, c=(0, 0.1, 0), r0=7.0, r1=7.0, color="#d9a0ff", edge="#7a2cff", a=1.0, strength=5.5, n=9, spin=0.1, **{"in": 0.01, "fade": 0.2}),
    "wind": dict(kind="wind", t0=0, dur=100, c=(0, 0.1, 0), r0=7.0, r1=7.0, color="#e8e8ff", a=1.0, strength=2.4, **{"in": 0.01, "fade": 0.2}),
    "pillar": dict(kind="pillar", t0=0, dur=100, c=(0, 0.0, 0), r0=1.2, r1=1.2, color="#ff3030", a=1.0, strength=5.0, height=14.0, **{"in": 0.01, "fade": 0.2}),
}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    kinds = sys.argv[2:] or list(CASES)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 800, 450
    sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.012, 0.012, 0.022, 1)
    bg.inputs[1].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=60)
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("g")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.07, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
    gnd.data.materials.append(gm)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 28
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (0, -13, 5.5)
    cam.rotation_euler = (math.radians(77), 0, 0)
    for k in kinds:
        e = dict(CASES[k])
        fx = vfx_mesh.make(e, C3, cam)
        sc.frame_set(30)
        fx.key(30)
        sc.frame_set(30)
        sc.render.filepath = str(out / f"{k}.png")
        bpy.ops.render.render(write_still=True)
        for ob, _, _ in fx.objs:
            ob.hide_render = True
            ob.hide_viewport = True
            ob.animation_data_clear()
        print("rendered", k)


main()
