"""Modelled VFX for the Blender renderer: the meshes and the textures a Roblox VFX artist builds, made procedurally.

Roblox VFX are not drawn shapes, they are textured meshes lit by the scene: a hatched dome, curved wind blades spiralling out, a four-point star sprite that always faces
the lens, translucent wind bands, a streaked light pillar. This module builds exactly those objects (emissive, alpha-masked, no shadow, they also light the ground and
the characters) and animates them from the ``{"type": "mesh", "kind": ...}`` entries of the cinematic's fx list.

kinds: ``star`` (billboard), ``dome`` (hatched hemisphere), ``blades`` (spiral crescents), ``wind`` (translucent band ring), ``pillar`` (streaked cylinder).
All positions are engine coordinates; the caller passes the engine -> Blender rotation ``C3``.
"""

from __future__ import annotations

import math

import bmesh
import bpy
import mathutils
import numpy as np


def _hex(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def _lin(c: np.ndarray) -> np.ndarray:
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _image(name: str, rgba: np.ndarray) -> bpy.types.Image:
    """``rgba`` is H x W x 4 float, row 0 = bottom (Blender's convention); colours are given in sRGB."""
    h, w = rgba.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.update()
    img.pack()
    return img


# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# textures

def tex_star(tint: str, n: int = 512) -> np.ndarray:
    """Four-point anamorphic star: white-hot core, tinted halo, two long hair-thin spikes and two short diagonal ones."""
    y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    r = np.hypot(x, y)
    core = np.exp(-(r / 0.055) ** 2) * 1.25
    halo = 0.62 * np.exp(-(r / 0.20) ** 1.3)
    spike = lambda a, b, w, L: np.exp(-np.abs(b) / w) * np.exp(-(np.abs(a) / L) ** 1.25)
    sp = spike(x, y, 0.014, 0.62) + spike(y, x, 0.014, 0.62)
    d1, d2 = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
    sp += 0.4 * (spike(d1, d2, 0.016, 0.26) + spike(d2, d1, 0.016, 0.26))
    inten = np.clip(core + halo + sp, 0, 1) * np.clip(1 - (r / 0.98) ** 4, 0, 1)
    tint_c = _hex(tint)
    mix = (inten ** 1.6)[..., None]
    rgb = tint_c * (1 - mix) + 1.0 * mix
    return np.dstack([rgb, inten]).astype(np.float32)


def _stripes(w: int, h: int, count: int, seed: int, wmin: float, wmax: float, lmin: float = 0.35) -> np.ndarray:
    """Hair-like streaks along the vertical axis (row 0 = base): each one has its own width, brightness and length."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, 1, w, endpoint=False)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    out = np.zeros((h, w), np.float32)
    for _ in range(count):
        x0, wd, amp, L = rng.random(), rng.uniform(wmin, wmax), rng.uniform(0.35, 1.0), rng.uniform(lmin, 1.0)
        dx = np.minimum(np.abs(xs - x0), 1 - np.abs(xs - x0))
        out += amp * np.exp(-(dx / wd) ** 2) * np.clip(1 - ys / L, 0, 1) ** 0.8
    return np.clip(out, 0, 1)


def tex_streaks(tint: str, w: int = 1024, h: int = 256, seed: int = 1, count: int = 130, wmin: float = 0.0012, wmax: float = 0.006,
                floor: float = 0.16, base_fade: float = 0.0) -> np.ndarray:
    """Streak texture for domes and pillars: bright thin lines from the base up, fading, hot white at their roots (``floor`` = the soft body behind the lines)."""
    s = _stripes(w, h, count, seed, wmin, wmax)
    ys = np.linspace(0, 1, h)[:, None]
    base = floor * np.clip(1 - ys, 0, 1) ** 1.2
    inten = np.clip(s * 1.1 + base, 0, 1)
    if base_fade > 0:
        inten = inten * np.clip(ys / base_fade, 0, 1) ** 1.5
    mix = (inten ** 1.5)[..., None]
    rgb = _hex(tint) * (1 - mix) + 1.0 * mix
    return np.dstack([np.broadcast_to(rgb, (h, w, 3)), inten]).astype(np.float32)


def tex_blade(tint: str, edge: str, w: int = 128, h: int = 512, seed: int = 3) -> np.ndarray:
    """A wind blade seen flat: bright thin core, wide soft edge in the second colour, long streaks along its length, a tail that fades out."""
    rng = np.random.default_rng(seed)
    u = np.linspace(-1, 1, w)[None, :]
    v = np.linspace(0, 1, h)[:, None]                       # 0 = tail, 1 = head
    core = np.exp(-(u / 0.16) ** 2)
    soft = 0.55 * np.exp(-(u / 0.55) ** 2)
    lines = np.zeros((1, w), np.float32)
    for _ in range(26):
        lines += rng.uniform(0.3, 1) * np.exp(-((u - rng.uniform(-0.9, 0.9)) / rng.uniform(0.012, 0.04)) ** 2)
    lines = np.clip(lines, 0, 1)
    along = np.clip(v / 0.7, 0, 1) ** 1.2 * np.clip((1 - v) / 0.06 + 0.0, 0, 1)
    inten = np.clip((core + soft * 0.75) * (0.62 + 0.38 * lines) * along, 0, 1)
    m = np.clip(core * along, 0, 1)[..., None]
    rgb = _hex(edge) * (1 - m ** 0.8) + _hex(tint) * (m ** 0.8)
    rgb = rgb * (1 - m ** 2) + 1.0 * (m ** 2)
    return np.dstack([np.broadcast_to(rgb, (h, w, 3)), inten]).astype(np.float32)


def tex_band(tint: str, w: int = 1024, h: int = 128, seed: int = 5) -> np.ndarray:
    """Translucent wind band: soft across, broken into long arcs along its length by random gaps, with fine streaks."""
    rng = np.random.default_rng(seed)
    v = np.linspace(-1, 1, h)[:, None]
    across = np.clip(1 - np.abs(v) ** 2.2, 0, 1)
    xs = np.linspace(0, 1, w, endpoint=False)[None, :]
    gate = np.zeros((1, w), np.float32)
    for _ in range(5):
        c, L = rng.random(), rng.uniform(0.12, 0.3)
        d = np.minimum(np.abs(xs - c), 1 - np.abs(xs - c))
        gate += np.clip(1 - (d / L) ** 2, 0, 1)
    gate = np.clip(gate, 0, 1)
    fine = 0.65 + 0.35 * np.clip(sum(np.exp(-((v - rng.uniform(-0.9, 0.9)) / 0.03) ** 2) * rng.uniform(0.4, 1) for _ in range(18)), 0, 1)
    inten = np.clip(across * gate * fine, 0, 1)
    rgb = _hex(tint) * (1 - inten[..., None] ** 2) + 1.0 * inten[..., None] ** 2
    return np.dstack([rgb, inten]).astype(np.float32)


def _box_blur(a: np.ndarray, r: int) -> np.ndarray:
    """Separable box blur (numpy only: the Blender python has no cv2)."""
    k = 2 * r + 1
    out = a
    for ax in (0, 1):
        c = np.cumsum(np.pad(out, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode="edge"), axis=ax)
        sl = [slice(None)] * 2
        hi, lo = list(sl), list(sl)
        hi[ax], lo[ax] = slice(k, None), slice(0, -k)
        out = (c[tuple(hi)] - c[tuple(lo)]) / k
    return out


def tex_cracks(tint: str, edge: str, n: int = 1024, seed: int = 2, branches: int = 16) -> np.ndarray:
    """Floor cracks seen from above: thin branching fissures from the centre, hot white in the middle of each line, a violet/magenta glow around it."""
    rng = np.random.default_rng(seed)
    mask = np.zeros((n, n), np.float32)
    c = n / 2.0

    def stamp(x, y, v=1.0):
        xi, yi = int(x), int(y)
        if 1 <= xi < n - 1 and 1 <= yi < n - 1:
            mask[yi - 1:yi + 2, xi - 1:xi + 2] = np.maximum(mask[yi - 1:yi + 2, xi - 1:xi + 2], v)

    def walk(x, y, ang, length, depth):
        step = 4.0
        for i in range(int(length / step)):
            ang += rng.uniform(-0.28, 0.28)
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            stamp(x, y)
            if depth < 2 and rng.random() < 0.05:
                walk(x, y, ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0), length * rng.uniform(0.25, 0.5), depth + 1)

    for i in range(branches):
        a0 = 2 * math.pi * i / branches + rng.uniform(-0.15, 0.15)
        walk(c + math.cos(a0) * 10, c + math.sin(a0) * 10, a0, rng.uniform(0.35, 0.92) * c, 0)
    core = _box_blur(mask, 1) * 2.0
    glow = 0.9 * _box_blur(mask, 3) + 0.5 * _box_blur(mask, 9) + 0.3 * _box_blur(mask, 24)
    r = np.hypot(*np.mgrid[-1:1:n * 1j, -1:1:n * 1j])
    inten = np.clip(core + glow * 2.0, 0, 1) * np.clip(1 - (r / 0.98) ** 6, 0, 1)
    m = np.clip(core, 0, 1)[..., None]
    rgb = _hex(edge) * (1 - m) + _hex(tint) * (m * 0.5) + 1.0 * (m ** 2) * 0.9
    return np.dstack([np.clip(rgb, 0, 1), inten]).astype(np.float32)


def tex_scorch(n: int = 512, seed: int = 4) -> np.ndarray:
    """A burnt, ragged disc: black in the middle, fading out (alpha only, the colour is black)."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    rag = 1.0 + 0.12 * sum(rng.uniform(0.3, 1.0) * np.sin(ang * k + rng.uniform(0, 6.28)) for k in (3, 5, 8, 13)) / 2.0
    a = np.clip(1.0 - (r / (0.78 * rag)) ** 2.5, 0, 1) ** 0.8
    return np.dstack([np.zeros((n, n, 3), np.float32), a.astype(np.float32) * 0.92])


# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# meshes

def _mesh_obj(name: str, verts, faces, uvs) -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="uv")
    for li, loop in enumerate(me.loops):
        uv.data[li].uv = uvs[loop.vertex_index]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.visible_shadow = False
    return ob


def mesh_dome(nu: int = 64, nv: int = 20):
    verts, uvs, faces = [], [], []
    for j in range(nv + 1):
        th = (math.pi / 2) * j / nv
        for i in range(nu + 1):
            ph = 2 * math.pi * i / nu
            verts.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th) * 0.9))
            uvs.append((i / nu, 1.0 - j / nv))          # v = 0 on the rim (the streaks' bright roots), 1 at the apex
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return verts, faces, uvs


def mesh_pillar(nu: int = 48, nv: int = 8):
    verts, uvs, faces = [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            ph = 2 * math.pi * i / nu
            verts.append((math.cos(ph), math.sin(ph), j / nv))
            uvs.append((i / nu, j / nv))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return verts, faces, uvs


def mesh_wind(nu: int = 96):
    """Annulus of unit outer radius; the band is the ring between 0.78 and 1.0, with a slight lift so it reads as a swirl, not a flat disc."""
    verts, uvs, faces = [], [], []
    for k, (rad, v) in enumerate(((0.78, 0.0), (0.89, 0.5), (1.0, 1.0))):
        for i in range(nu + 1):
            ph = 2 * math.pi * i / nu
            verts.append((rad * math.cos(ph), rad * math.sin(ph), 0.04 * math.sin(ph * 3 + k)))
            uvs.append((i / nu, v))
    for k in range(2):
        for i in range(nu):
            a = k * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return verts, faces, uvs


def mesh_blade(sweep: float, rise: float, wmax: float, n: int = 40, tilt: float = 0.5):
    """A crescent ribbon spiralling outward: unit-radius frame, pointed at both ends (width ~ sin), tilted out of the ground plane by ``tilt``."""
    verts, uvs, faces = [], [], []
    for j in range(n + 1):
        t = j / n
        ang = sweep * t
        rho = 0.28 + 0.72 * t ** 0.85
        z = rise * t
        wd = wmax * math.sin(math.pi * min(1.0, 0.04 + t * 0.96)) ** 0.8
        rad = np.array((math.cos(ang), math.sin(ang), 0.0))
        up = np.array((0.0, 0.0, 1.0))
        cross = rad * math.cos(tilt) + up * math.sin(tilt)
        c = rad * rho + up * z
        for s, u in ((-1, 0.0), (1, 1.0)):
            p = c + cross * wd * s * 0.5
            verts.append(tuple(p))
            uvs.append((u, t))
    for j in range(n):
        a = j * 2
        faces.append((a, a + 1, a + 3, a + 2))
    return verts, faces, uvs


# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# material

def fx_material(name: str, img: bpy.types.Image, strength: float, fresnel: float = 0.0, base: float = 0.0, center: float = 0.0):
    """Emission masked by the texture's alpha. ``A`` (a Value node) is the animated brightness: it scales both the emission and the opacity."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.interpolation = "Linear"
    tx.extension = "EXTEND"
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "uv"
    A = nt.nodes.new("ShaderNodeValue")
    A.outputs[0].default_value = 0.0
    smul = nt.nodes.new("ShaderNodeMath")
    smul.operation = "MULTIPLY"
    smul.inputs[1].default_value = strength
    amin = nt.nodes.new("ShaderNodeMath")
    amin.operation = "MINIMUM"
    amin.inputs[1].default_value = 1.0
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    nt.links.new(uv.outputs["UV"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(A.outputs[0], smul.inputs[0])
    nt.links.new(smul.outputs[0], em.inputs["Strength"])
    nt.links.new(A.outputs[0], amin.inputs[0])
    nt.links.new(tx.outputs["Alpha"], fac.inputs[0])
    nt.links.new(amin.outputs[0], fac.inputs[1])
    last = fac.outputs[0]
    if center > 0:                                                  # the edges of a cylinder fade out: a soft beam, not a plastic tube
        lw2 = nt.nodes.new("ShaderNodeLayerWeight")
        lw2.inputs["Blend"].default_value = 0.5
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(lw2.outputs["Facing"], inv.inputs[1])
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = center
        nt.links.new(inv.outputs[0], pw.inputs[0])
        cm = nt.nodes.new("ShaderNodeMath")
        cm.operation = "MULTIPLY"
        nt.links.new(last, cm.inputs[0])
        nt.links.new(pw.outputs[0], cm.inputs[1])
        last = cm.outputs[0]
    if fresnel > 0 or base > 0:                                    # a bright, see-through rim (domes): alpha += fresnel * k + base
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.3
        fk = nt.nodes.new("ShaderNodeMath")
        fk.operation = "MULTIPLY_ADD"
        fk.inputs[1].default_value = fresnel
        fk.inputs[2].default_value = base
        nt.links.new(lw.outputs["Facing"], fk.inputs[0])
        fadd = nt.nodes.new("ShaderNodeMath")
        fadd.operation = "ADD"
        fadd.use_clamp = True
        nt.links.new(fac.outputs[0], fadd.inputs[0])
        fmul = nt.nodes.new("ShaderNodeMath")
        fmul.operation = "MULTIPLY"
        nt.links.new(fk.outputs[0], fmul.inputs[0])
        nt.links.new(amin.outputs[0], fmul.inputs[1])
        nt.links.new(fmul.outputs[0], fadd.inputs[1])
        last = fadd.outputs[0]
    nt.links.new(last, mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat, A


def crater_material(name: str, img, strength: float):
    """Emissive cracks that spread outward: ``A`` = brightness, ``R`` = reveal radius (0..1 of the decal)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.extension = "EXTEND"
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "uv"
    A = nt.nodes.new("ShaderNodeValue")
    R = nt.nodes.new("ShaderNodeValue")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    d2 = nt.nodes.new("ShaderNodeMath")
    d2.operation = "MULTIPLY"
    d2.inputs[1].default_value = 2.0
    rv = nt.nodes.new("ShaderNodeMath")
    rv.operation = "SUBTRACT"
    rv2 = nt.nodes.new("ShaderNodeMath")
    rv2.operation = "MULTIPLY"
    rv2.inputs[1].default_value = 14.0
    rv2.use_clamp = True
    sm = nt.nodes.new("ShaderNodeMath")
    sm.operation = "MULTIPLY"
    sm.inputs[1].default_value = strength
    am = nt.nodes.new("ShaderNodeMath")
    am.operation = "MINIMUM"
    am.inputs[1].default_value = 1.0
    f1 = nt.nodes.new("ShaderNodeMath")
    f1.operation = "MULTIPLY"
    f2 = nt.nodes.new("ShaderNodeMath")
    f2.operation = "MULTIPLY"
    L = nt.links.new
    L(uv.outputs["UV"], tx.inputs["Vector"])
    L(uv.outputs["UV"], sub.inputs[0])
    L(sub.outputs[0], ln.inputs[0])
    L(ln.outputs["Value"], d2.inputs[0])
    L(R.outputs[0], rv.inputs[0])
    L(d2.outputs[0], rv.inputs[1])
    L(rv.outputs[0], rv2.inputs[0])
    L(tx.outputs["Color"], em.inputs["Color"])
    L(A.outputs[0], sm.inputs[0])
    L(sm.outputs[0], em.inputs["Strength"])
    L(A.outputs[0], am.inputs[0])
    L(tx.outputs["Alpha"], f1.inputs[0])
    L(rv2.outputs[0], f1.inputs[1])
    L(f1.outputs[0], f2.inputs[0])
    L(am.outputs[0], f2.inputs[1])
    L(f2.outputs[0], mix.inputs["Fac"])
    L(tr.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    return mat, A, R


def scorch_material(img):
    mat = bpy.data.materials.new("fx_scorch")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    bs = nt.nodes.new("ShaderNodeBsdfDiffuse")
    bs.inputs["Color"].default_value = (0.012, 0.01, 0.016, 1)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "uv"
    A = nt.nodes.new("ShaderNodeValue")
    am = nt.nodes.new("ShaderNodeMath")
    am.operation = "MULTIPLY"
    nt.links.new(uv.outputs["UV"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Alpha"], am.inputs[0])
    nt.links.new(A.outputs[0], am.inputs[1])
    nt.links.new(am.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bs.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat, A


def smoke_material(color, seed: int, emit: float = 0.0):
    """A volume (no surface): noise density inside a unit sphere, soft towards its edge, scaled by the animated ``A``."""
    mat = bpy.data.materials.new("fx_smoke")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*[float(v) for v in _lin(_hex(color))], 1.0)
    vol.inputs["Emission Strength"].default_value = emit
    vol.inputs["Emission Color"].default_value = (0.5, 0.2, 0.9, 1.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (seed * 3.7, seed * 1.9, seed * 5.3)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.4
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.62
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.36
    mr.inputs["From Max"].default_value = 0.72
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    fo = nt.nodes.new("ShaderNodeMapRange")
    fo.inputs["From Min"].default_value = 0.25
    fo.inputs["From Max"].default_value = 0.98
    fo.inputs["To Min"].default_value = 1.0
    fo.inputs["To Max"].default_value = 0.0
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    A = nt.nodes.new("ShaderNodeValue")
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    L = nt.links.new
    L(tc.outputs["Object"], mp.inputs["Vector"])
    L(mp.outputs[0], nz.inputs["Vector"])
    L(nz.outputs["Fac"], mr.inputs["Value"])
    L(tc.outputs["Object"], ln.inputs[0])
    L(ln.outputs["Value"], fo.inputs["Value"])
    L(mr.outputs["Result"], m1.inputs[0])
    L(fo.outputs["Result"], m1.inputs[1])
    L(m1.outputs[0], m2.inputs[0])
    L(A.outputs[0], m2.inputs[1])
    L(m2.outputs[0], vol.inputs["Density"])
    L(vol.outputs["Volume"], out.inputs["Volume"])
    return mat, A


# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# one animated instance per fx entry

def _ease_out(u: float, p: float = 3.0) -> float:
    return 1 - (1 - min(1.0, max(0.0, u))) ** p


class Fx:
    def __init__(self, e: dict, C3: mathutils.Matrix, cam: bpy.types.Object):
        self.e = e
        self.t0, self.dur = e["t0"], e["dur"]
        self.kind = e["kind"]
        c = mathutils.Vector(e["c"])
        self.pos = C3 @ c
        self.cam = cam
        self.objs: list[tuple[bpy.types.Object, bpy.types.Node, float]] = []     # (object, brightness node, brightness weight)
        self._R: dict = {}
        k = self.kind
        tint, edge = e.get("color", "#ff9a1f"), e.get("edge", e.get("color", "#ff5a00"))
        seed = int(e.get("seed", 1))
        if k == "star":
            img = _image("star", tex_star(tint))
            mat, A = fx_material("fx_star", img, e.get("strength", 5.0))
            ob = _mesh_obj("fx_star", [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
            ob.data.materials.append(mat)
            con = ob.constraints.new("COPY_ROTATION")
            con.target = cam
            self.objs.append((ob, A, 1.0))
        elif k == "dome":
            img = _image("dome", tex_streaks(tint, seed=seed, count=320, wmin=0.0006, wmax=0.0028, floor=0.22))
            mat, A = fx_material("fx_dome", img, e.get("strength", 4.0), fresnel=e.get("rim", 0.55), base=e.get("fill", 0.10))
            v, f, uv = mesh_dome()
            ob = _mesh_obj("fx_dome", v, f, uv)
            ob.data.materials.append(mat)
            self.objs.append((ob, A, 1.0))
        elif k == "pillar":
            img = _image("pillar", tex_streaks(tint, seed=seed, count=200, wmin=0.0012, wmax=0.007, floor=0.34, base_fade=0.05))
            for wmul, bright in ((1.0, 0.7), (0.38, 1.0)):
                mat, A = fx_material("fx_pillar", img, e.get("strength", 4.0) * bright, center=1.6)
                v, f, uv = mesh_pillar()
                ob = _mesh_obj("fx_pillar", v, f, uv)
                ob.data.materials.append(mat)
                self.objs.append((ob, A, wmul))
        elif k == "wind":
            img = _image("wind", tex_band(tint, seed=seed))
            mat, A = fx_material("fx_wind", img, e.get("strength", 2.2))
            v, f, uv = mesh_wind()
            ob = _mesh_obj("fx_wind", v, f, uv)
            ob.data.materials.append(mat)
            self.objs.append((ob, A, 1.0))
        elif k == "blades":
            img = _image("blade", tex_blade(tint, edge, seed=seed))
            n = int(e.get("n", 7))
            mat, A = fx_material("fx_blades", img, e.get("strength", 4.5))
            for i in range(n):
                rng = np.random.default_rng(seed * 100 + i)
                v, f, uv = mesh_blade(sweep=rng.uniform(1.6, 2.6), rise=e.get("rise", 0.35) * rng.uniform(0.6, 1.4), wmax=rng.uniform(0.2, 0.34) * e.get("width", 1.0),
                                      tilt=rng.uniform(0.15, 0.7))
                ob = _mesh_obj("fx_blade", v, f, uv)
                ob.data.materials.append(mat)
                ob.rotation_mode = "XYZ"
                ob["phase"] = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
                ob["sz"] = rng.uniform(0.5, 1.45)
                self.objs.append((ob, A, 1.0))
        elif k == "crater":
            img = _image("cracks", tex_cracks(tint, edge, seed=seed, branches=int(e.get("branches", 16))))
            mat, A, R = crater_material("fx_cracks", img, e.get("strength", 6.0))
            ob = _mesh_obj("fx_cracks", [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
            ob.data.materials.append(mat)
            self._R[ob.name] = R
            self.objs.append((ob, A, 1.0))
            simg = _image("scorch", tex_scorch(seed=seed))
            smat, SA = scorch_material(simg)
            so = _mesh_obj("fx_scorch", [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
            so.data.materials.append(smat)
            so["scorch"] = 1
            self.objs.append((so, SA, 1.0))
        elif k == "smoke":
            sc = bpy.context.scene
            sc.cycles.volume_step_rate = 2.5
            sc.cycles.volume_max_steps = 40
            n = int(e.get("n", 6))
            for i in range(n):
                rng = np.random.default_rng(seed * 100 + i)
                bm = bmesh.new()
                bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
                me = bpy.data.meshes.new("fx_puff")
                bm.to_mesh(me)
                bm.free()
                ob = bpy.data.objects.new("fx_puff", me)
                bpy.context.scene.collection.objects.link(ob)
                ob.visible_shadow = True
                mat, A = smoke_material(e.get("color", "#9aa4c0"), seed * 13 + i, emit=e.get("emit", 0.0))
                ob.data.materials.append(mat)
                a_ = rng.uniform(0, 2 * math.pi)
                rr = e.get("spread", 2.0) * math.sqrt(rng.uniform())
                ob["off"] = (math.cos(a_) * rr, math.sin(a_) * rr, rng.uniform(0.0, e.get("lift0", 0.5)))
                ob["sz"] = rng.uniform(0.55, 1.25)
                ob["delay"] = rng.uniform(0.0, 0.25)
                self.objs.append((ob, A, 1.0))
        for ob, _, _ in self.objs:
            ob.hide_render = True

    def dim_at(self, f: int) -> float:
        """Stops of exposure the picture is darkened by at frame ``f`` so the light reads (a bright arena washes an additive glow out)."""
        d = self.e.get("dim", 0.0)
        u = (f - self.t0) / max(1, self.dur)
        if d <= 0 or not 0.0 <= u <= 1.0:
            return 0.0
        return d * min(1.0, u / 0.06) * (1 - u) ** 1.3

    # --------------------------------------------------------------------------------------------------------------------------------------
    def key(self, f: int):
        e, u = self.e, (f - self.t0) / max(1, self.dur)
        live = 0.0 <= u <= 1.0
        for ob, A, w in self.objs:
            ob.hide_render = not live
            ob.keyframe_insert("hide_render", frame=f)
            if not live:
                continue
            k = self.kind
            r0, r1 = e.get("r0", 1.0), e.get("r1", e.get("r0", 1.0))
            grow = r0 + (r1 - r0) * _ease_out(u, e.get("ease", 3.0))
            a_peak = e.get("a", 1.0)
            fade_in = min(1.0, u / max(1e-3, e.get("in", 0.06)))
            fade = fade_in * (1 - u) ** e.get("fade", 1.2) if k != "pillar" else fade_in * (1 - u) ** 0.8
            a = a_peak * fade
            loc = self.pos.copy()
            rot = list(e.get("rot", (0.0, 0.0, 0.0)))
            sc = [grow, grow, grow]
            if k == "star":
                sc = [grow, grow, 1.0]
            elif k == "dome":
                sc = [grow, grow, grow * e.get("height", 1.0)]
            elif k == "pillar":
                H = e.get("height", 12.0)
                sc = [grow * w, grow * w, H * _ease_out(u * 3.0, 3.0) + 0.01]
            elif k == "wind":
                rot[2] += e.get("spin", 0.25) * (f - self.t0)
                loc.z += e.get("lift", 0.0) * u
            elif k == "blades":
                spin = e.get("spin", 0.5) * (1 - (1 - u) ** 2) * 3.0
                rot[2] += ob["phase"] + spin
                loc.z += e.get("lift", 0.0) * u
                sc = [grow * ob["sz"]] * 3
            elif k == "crater":
                loc.z += 0.04 if "scorch" not in ob else 0.02
                sc = [grow, grow, 1.0]
                if "scorch" in ob:
                    a = a_peak * min(1.0, u / 0.05) * (1 - max(0.0, (u - 0.85) / 0.15))
                else:
                    Rn = self._R[ob.name]
                    Rn.outputs[0].default_value = min(1.0, 1.4 * _ease_out(u * 5.0, 2.2))
                    Rn.outputs[0].keyframe_insert("default_value", frame=f)
                    a = a_peak * min(1.0, u / 0.03) * (1 - max(0.0, (u - 0.5) / 0.5) ** 1.5)
            elif k == "smoke":
                ud = max(0.0, (u - ob["delay"]) / (1 - ob["delay"]))
                if ud <= 0.0:
                    ob.hide_render = True
                    ob.keyframe_insert("hide_render", frame=f)
                    continue
                g = r0 + (r1 - r0) * _ease_out(ud, e.get("ease", 2.2))
                sc = [g * ob["sz"]] * 3
                off = ob["off"]
                loc = loc + mathutils.Vector((off[0] * (0.5 + ud), off[1] * (0.5 + ud), off[2] + e.get("rise", 1.2) * ud))
                a = e.get("a", 1.0) * min(1.0, ud / 0.12) * (1 - ud) ** e.get("fade", 1.1)
            ob.location = loc
            ob.scale = sc
            ob.rotation_mode = "ZYX"
            ob.rotation_euler = (rot[0], rot[1], rot[2])
            for p in ("location", "scale", "rotation_euler"):
                ob.keyframe_insert(p, frame=f)
            A.outputs[0].default_value = a
            A.outputs[0].keyframe_insert("default_value", frame=f)


def make(e: dict, C3: mathutils.Matrix, cam: bpy.types.Object) -> Fx:
    return Fx(e, C3, cam)
