"""Render a scene of the engine with Blender (Cycles, CPU) through the ``bpy`` module: real lighting, shadows, materials, depth haze, motion blur.

Only the *3D layer* is made here (floor, sky, bodies, accessory meshes, props, debris, lights, camera). The graphic effects (speed shell, needles, ink,
particles, screen punctuation) are drawn by the 2D viewer and composited on top by ``tools/composite.py``: see ``tools/render_film.py`` for the whole chain.

usage (needs ``pip install bpy``, Python 3.13, in its own venv):
    python tools/render_blender.py SCENE OUT_DIR [--frames a:b] [--samples 20] [--width 737] [--still N]

Conventions: the engine is Y-up with -Z forward; Blender is Z-up. Every engine point (x, y, z) becomes (x, -z, y) in Blender (a pure rotation),
so meshes keep their engine-local coordinates and only the object matrices are converted. One stud = one Blender unit.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402
import mathutils  # noqa: E402
import numpy as np  # noqa: E402

from examples.scenes import SCENES  # noqa: E402
from tsb_engine import modeling as M  # noqa: E402
from tsb_engine.scene import export_viewer_data  # noqa: E402

C3 = mathutils.Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # engine -> blender (rotation)
C4 = C3.to_4x4()
STEEL, GOLD, GLASS = {"#cfd6de", "#8d98a4"}, {"#b9a064"}, {"#c9e6f2"}


def lin(hexcol: str) -> tuple[float, float, float, float]:
    h = hexcol.lstrip("#")
    return tuple((int(h[i : i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4)) + (1.0,)


_MATS: dict = {}


def material(hexcol: str, rough: float = 0.7, metal: float = 0.0, emit: float = 0.0):
    if hexcol in STEEL:
        rough, metal = 0.28, 0.85
    elif hexcol in GOLD:
        rough, metal = 0.35, 0.8
    elif hexcol in GLASS:
        rough, metal = 0.08, 0.0
    key = (hexcol, rough, metal, emit)
    if key not in _MATS:
        m = bpy.data.materials.new(f"m_{hexcol}_{len(_MATS)}")
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = lin(hexcol)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emit:
            bsdf.inputs["Emission Color"].default_value = lin(hexcol)
            bsdf.inputs["Emission Strength"].default_value = emit
        _MATS[key] = m
    return _MATS[key]


def obj_from_mesh(name: str, mesh: M.Mesh, smooth_angle: float | None = 40.0, rough: float = 0.7):
    me = bpy.data.meshes.new(name)
    me.from_pydata(mesh.v.tolist(), [], mesh.f.tolist())
    me.update()
    for col in mesh.materials:
        me.materials.append(material(col, rough))
    me.polygons.foreach_set("material_index", mesh.mat.astype(np.int32).tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if smooth_angle is not None:
        for p in me.polygons:
            p.use_smooth = True
        if hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return ob


def mat4(t12) -> mathutils.Matrix:
    r = t12
    return C4 @ mathutils.Matrix(((r[0], r[1], r[2], r[9]), (r[3], r[4], r[5], r[10]), (r[6], r[7], r[8], r[11]), (0, 0, 0, 1)))


class Keyer:
    """Keyframes an object's pose each frame (quaternions kept on the same hemisphere so interpolation never takes the long way round)."""

    def __init__(self):
        self.last: dict = {}

    def key(self, ob, m: mathutils.Matrix, frame: int):
        loc, rot, _ = m.decompose()
        ob.rotation_mode = "QUATERNION"
        prev = self.last.get(ob.name)
        if prev is not None and prev.dot(rot) < 0:
            rot = mathutils.Quaternion((-rot.w, -rot.x, -rot.y, -rot.z))
        self.last[ob.name] = rot
        ob.location, ob.rotation_quaternion = loc, rot
        ob.keyframe_insert("location", frame=frame)
        ob.keyframe_insert("rotation_quaternion", frame=frame)


def make_ground(far_color: str, floor: str, style: str = "film"):
    bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "ground"
    n = 1024
    tile = n // 2  # 16 studs per texture tile -> 2 big cells of 8 studs
    img = np.zeros((n, n, 4), np.float32)
    base = np.array(lin(floor), np.float32)
    img[:] = base
    if style == "studio":   # the Studio viewport: a plain baseplate with a faint big checker, no drawn grid
        cell = n // 4
        yy, xx = np.mgrid[0:n, 0:n]
        chk = (((yy // cell) + (xx // cell)) % 2).astype(np.float32)
        img[:] = base * (0.94 + 0.12 * chk)[..., None]
    else:
        fine, bold = np.array(lin("#6e6c76"), np.float32), np.array(lin("#908e9a"), np.float32)
        for k in range(0, n, tile // 2):  # an 8-stud grid (lines ~0.2 stud wide so they survive distance)
            img[max(0, k - 7) : k + 7, :] = fine
            img[:, max(0, k - 7) : k + 7] = fine
        for k in range(0, n, tile):  # a stronger line every 16 studs
            img[max(0, k - 12) : k + 12, :] = bold
            img[:, max(0, k - 12) : k + 12] = bold
    img[:, :, 3] = 1.0
    im = bpy.data.images.new("grid", n, n, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"  # must come BEFORE the pixels: changing it afterwards converts (and here zeroes) them
    im.pixels.foreach_set(img.ravel())
    m = bpy.data.materials.new("ground")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = nt.nodes["Material Output"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = "Cubic"
    tex.extension = "REPEAT"
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (4000 / 16, 4000 / 16, 1)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # depth haze: far away the floor melts into the horizon colour
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vl = nt.nodes.new("ShaderNodeVectorMath")
    vl.operation = "LENGTH"
    cam = nt.nodes.new("ShaderNodeCameraData")
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 60
    ramp.inputs["From Max"].default_value = 420
    nt.links.new(cam.outputs["View Distance"], ramp.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    # a Mix node has one A/B socket per data type: the colour ones are inputs 6 and 7, the colour result is output 2
    mix.inputs[7].default_value = lin(far_color)
    nt.links.new(ramp.outputs["Result"], mix.inputs[0])
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ob.data.materials.append(m)
    ob.is_shadow_catcher = False
    return ob


def make_world(sky_top: str, sky_horizon: str):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_WORLD":
            nt.nodes.remove(nd)
    out = nt.nodes["World Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.46
    ramp.color_ramp.elements[0].color = lin(sky_horizon)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = lin(sky_top)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def build(scene_name: str, frames: range, width: int, samples: int):
    sc = bpy.context.scene
    scene = SCENES[scene_name]()
    D = export_viewer_data(scene)
    CINE = D.get("cine")
    n = D["nFrames"]
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    sc.render.fps = D["fps"]
    sc.frame_start, sc.frame_end = frames.start, frames.stop - 1
    aspect = (CINE or {}).get("aspect", 16 / 9)
    sc.render.resolution_x = width
    sc.render.resolution_y = int(round(width / aspect))
    sc.render.resolution_percentage = 100
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.3
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"

    sky = (CINE or {}).get("skyColor", "#3d3b41")
    floor = (CINE or {}).get("floorColor", "#66646a")
    if (CINE or {}).get("look") == "studio":
        make_world("#7d8394", "#a4a9b7")
        make_ground("#a4a9b7", "#3d3e44", "studio")
    else:
        make_world("#1d1c21", "#4a484f")
        make_ground("#5c5a62", "#3c3a42")

    keyer = Keyer()
    # ---- characters
    SZ = D["sizes"]
    char_objs = []
    for ci, ch in enumerate(D["characters"]):
        objs = []
        for pi, part in enumerate(D["parts"]):
            if part in ch.get("hide", []):
                objs.append(None)
                continue
            if part == "Head" and ch.get("headShape") == "ball":
                box = M.sphere(0.5, 22, 14, ch["colors"][part], f"{ch['name']}_{part}").scale(1.0, 1.0, 1.0)
            else:
                box = M.bevel_box(tuple(SZ[part]), 0.02 if ch.get("faceColors") else 0.07, ch["colors"][part], f"{ch['name']}_{part}")
                if ch.get("faceColors"):
                    box = M.face_painted(box, ch["faceColors"])
            ob = obj_from_mesh(f"{ch['name']}_{part}", box, 35.0 if not ch.get("faceColors") else None, rough=0.62)
            objs.append(ob)
            if part == "Head" and ch.get("face", "std") in ("std", "smirk"):
                for fx_, (ex, ey, ew, eh) in enumerate([(-0.28, 0.12, 0.12, 0.17), (0.28, 0.12, 0.12, 0.17), (0.0, -0.2, 0.36, 0.05)]):
                    fo = obj_from_mesh(f"{ch['name']}_face{fx_}", M.bevel_box((ew, eh, 0.04), 0.01, "#101012", "face"), None, rough=0.9)
                    # a face piece rides on the head with a fixed offset in the head's (engine-local) frame
                    char_objs.append((ci, "face", fo, mathutils.Matrix.Translation((ex, ey, -0.51))))
        ex_objs = []
        for ex in ch.get("extras", []):
            shape = ex["shape"]
            if shape.startswith("mesh:"):
                mm = D["meshes"][shape[5:]]
                mesh = M.Mesh(np.array(mm["v"]).reshape(-1, 3), np.array(mm["f"], np.int32).reshape(-1, 3), np.array(mm["m"], np.int32), list(mm["cols"]), shape[5:])
                ob = obj_from_mesh(f"{ch['name']}_{ex['name']}", mesh, 38.0, rough=0.6)
            elif shape == "cyl":
                ob = obj_from_mesh(f"{ch['name']}_{ex['name']}", M.cylinder(0.5, 1.0, 20, ex["color"]).scale(*ex["size"]), 40.0)
            elif shape == "ell":
                ob = obj_from_mesh(f"{ch['name']}_{ex['name']}", M.sphere(0.5, 18, 10, ex["color"]).scale(*ex["size"]), 60.0)
            else:
                ob = obj_from_mesh(f"{ch['name']}_{ex['name']}", M.bevel_box(tuple(ex["size"]), 0.04, ex["color"]), 35.0)
            ex_objs.append(ob)
        char_objs.append((ci, "__parts__", objs, ex_objs))

    # ---- props + debris (static boxes with a visibility window / ballistic path)
    props = []
    debris = []
    if CINE:
        for p in CINE["props"]:
            ob = obj_from_mesh("prop", M.bevel_box(tuple(p["size"]), 0.03, p["color"]), 35.0)
            props.append((ob, p))
        for d in CINE["debris"]:
            ob = obj_from_mesh("debris", M.bevel_box(tuple(d["size"]), 0.05, d["color"]), 35.0, rough=0.8)
            arr = [None] * n
            p_, v_, w_ = list(d["p"]), list(d["v"]), [math.radians(x) for x in d["w"]]
            ang = [0.0, 0.0, 0.0]
            half = min(d["size"]) / 2
            for f in range(d["t0"], min(n, d["t0"] + d["life"])):
                arr[f] = (tuple(p_), tuple(ang))
                v_[1] -= d["g2"] if (d.get("tg") is not None and f >= d["tg"]) else d["g"]
                for k in range(3):
                    p_[k] += v_[k]
                    ang[k] += w_[k]
                if p_[1] < half:
                    p_[1] = half
                    v_[1] = -v_[1] * d["bounce"] if abs(v_[1]) > 0.06 else 0.0
                    for k in (0, 2):
                        v_[k] *= 0.8
                    w_ = [x * 0.7 for x in w_]
            debris.append((ob, arr))

    # ---- camera + key light + rim light
    cam_data = bpy.data.cameras.new("cam")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 24.0
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 2.4 if (CINE or {}).get('look') == 'studio' else 1.8
    sun_d.color = (1.0, 0.93, 0.86)
    sun_d.angle = math.radians(2.5)
    sun = bpy.data.objects.new("sun", sun_d)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(34), math.radians(0), math.radians(104)) if (CINE or {}).get('look') == 'studio' else (math.radians(52), math.radians(8), math.radians(-38))   # Studio: the sun is on the right, shadows fall left and a little toward the camera
    rim_d = bpy.data.lights.new("rim", "AREA")
    rim_d.energy = 800
    rim_d.color = (0.62, 0.74, 1.0)
    rim_d.size = 10
    rim = bpy.data.objects.new("rim", rim_d)
    sc.collection.objects.link(rim)

    def look_matrix(pos, forward, up_hint=(0, 1, 0)):
        f = mathutils.Vector(forward).normalized()
        r = f.cross(mathutils.Vector(up_hint)).normalized()
        u = r.cross(f)
        return r, u, f

    for f in frames:
        sc.frame_set(f)
        # characters
        for item in char_objs:
            ci = item[0]
            if item[1] == "__parts__":
                ch = D["characters"][ci]
                for pi, ob in enumerate(item[2]):
                    if ob is not None:
                        keyer.key(ob, mat4(ch["frames"][f][pi]), f)
                for ob, ex in zip(item[3], ch["extras"]):
                    keyer.key(ob, mat4(ex["frames"][f]), f)
            else:  # a face piece riding on the head
                ch = D["characters"][ci]
                keyer.key(item[2], mat4(ch["frames"][f][D["parts"].index("Head")]) @ item[3], f)
        for ob, p in props:
            vis = p["v"][0] <= f < p["v"][1]
            a = math.radians(p["yaw"])
            c, s = math.cos(a), math.sin(a)
            keyer.key(ob, mat4([c, 0, s, 0, 1, 0, -s, 0, c, *p["c"]]), f)
            ob.hide_render = not vis
            ob.keyframe_insert("hide_render", frame=f)
        for ob, arr in debris:
            e = arr[f]
            ob.hide_render = e is None
            ob.keyframe_insert("hide_render", frame=f)
            if e is not None:
                rx, ry, rz = e[1]
                eu = mathutils.Euler((rx, ry, rz), "XYZ").to_matrix().to_4x4()
                eu.translation = e[0]
                keyer.key(ob, C4 @ eu, f)
        # camera: engine basis -> blender
        c = CINE["camera"][f] if CINE else [8, 4, 10, 0, 3, 0, 40, 0]
        pos, tgt, fov, roll = mathutils.Vector(c[:3]), mathutils.Vector(c[3:6]), c[6], c[7]
        r, u, fw = look_matrix(pos, tgt - pos)
        if roll:
            cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
            r, u = r * cr + u * sr, u * cr - r * sr
        R = C3 @ r, C3 @ u, C3 @ (-fw)
        m = mathutils.Matrix.Identity(4)
        for i, v in enumerate(R):
            m[0][i], m[1][i], m[2][i] = v
        m.translation = C3 @ pos
        keyer.key(cam, m, f)
        cam_data.lens = 12.0 / math.tan(math.radians(fov) / 2)
        cam_data.keyframe_insert("lens", frame=f)
        # rim light behind the first character, opposite the camera
        t0 = D["characters"][0]["frames"][f][D["parts"].index("Torso")]
        focus = mathutils.Vector((t0[9], t0[10], t0[11]))
        away = (focus - pos)
        away.y = 0
        away = away.normalized() if away.length > 1e-6 else mathutils.Vector((0, 0, -1))
        rp = focus + away * 9 + mathutils.Vector((0, 6, 0))
        rf = (focus - rp).normalized()
        rr, ru, rff = look_matrix(rp, rf)
        lm = mathutils.Matrix.Identity(4)
        for i, v in enumerate((C3 @ rr, C3 @ ru, C3 @ (-rff))):
            lm[0][i], lm[1][i], lm[2][i] = v
        lm.translation = C3 @ rp
        keyer.key(rim, lm, f)
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("out")
    ap.add_argument("--frames", default="")
    ap.add_argument("--still", type=int, default=None)
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--width", type=int, default=737)
    a = ap.parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = SCENES[a.scene]()
    nfr = export_viewer_data(scene)["nFrames"]
    if a.still is not None:
        frames = range(max(0, a.still - 1), min(nfr, a.still + 2))
    elif a.frames:
        s, e = a.frames.split(":")
        frames = range(int(s), int(e) + 1)
    else:
        frames = range(nfr)
    D = build(a.scene, frames, a.width, a.samples)
    cuts = set()   # motion blur must not smear a cut: the interpolation between two shots is not a movement
    cams, tors = (D["cine"]["camera"] if D.get("cine") else []), [[ch["frames"][f][D["parts"].index("Torso")][9:12] for f in range(D["nFrames"])] for ch in D["characters"]]
    for f in range(1, D["nFrames"]):
        jump = max([math.dist(cams[f][:3], cams[f - 1][:3])] if cams else [0.0] + [math.dist(t[f], t[f - 1]) for t in tors])
        if cams:
            jump = max(jump, max(math.dist(t[f], t[f - 1]) for t in tors))
        if jump > 6.0:
            cuts.update((f - 1, f))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    if a.still is not None:
        sc.frame_set(a.still)
        sc.render.filepath = str(out / f"b_{a.still:04d}.png")
        bpy.ops.render.render(write_still=True)
    else:
        for f in frames:
            sc.frame_set(f)
            sc.render.use_motion_blur = f not in cuts
            sc.render.filepath = str(out / f"b_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("frame", f, flush=True)


if __name__ == "__main__":
    main()
