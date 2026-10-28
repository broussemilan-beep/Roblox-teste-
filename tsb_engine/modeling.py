"""Real 3D modelling for the preview and for Roblox MeshParts: procedural triangle meshes with materials and OBJ export.

The R6 body is six blocks; what makes a character recognisable are its *accessories* (hair, goggles, a sword, a belt, shoulder pads) and
those are real meshes in Roblox (MeshPart / Accessory with a ``Handle``). This module builds them from a small kit of operations - the same
ones used in Blender's modifier stack - without any dependency but numpy:

* primitives: ``bevel_box`` (rounded box), ``cylinder``, ``cone``, ``sphere``, ``torus``, ``lathe`` (revolve a profile), ``sweep`` (extrude a
  cross-section along a path with taper), ``prism`` (extrude a 2D polygon);
* ``Mesh`` operations: ``translate / rotate / scale / transform``, ``merge``, ``recolor`` (material id), normals, bounds, triangle count;
* ``to_obj`` + ``to_mtl``: Wavefront OBJ with one material per colour, ready to import in Blender or Studio (Studio's *3D Importer*).

Conventions follow the engine: +Y up, the character faces -Z, units are studs (R6: torso 2x2x1). Parts are modelled **in the local frame of the
part they attach to** (origin at the part's centre) so an attachment is ``(part, mesh)`` with no extra offset.

Roblox limits (``unverified`` in this sandbox, taken from public documentation): a MeshPart is limited to about 10 000 triangles and 20 000 vertices
(older limit; check the current documentation before uploading); ``Mesh.stats()`` reports both numbers so a model can be checked.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

Vec = tuple[float, float, float]


@dataclass
class Mesh:
    """Triangles only (quads are split on creation). ``mat[i]`` indexes ``materials`` for face ``i``."""

    v: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    f: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), dtype=np.int32))
    mat: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int32))
    materials: list[str] = field(default_factory=list)  # hex colours
    name: str = "mesh"

    # ---- construction helpers
    @staticmethod
    def from_quads(v, quads, color: str, name: str = "mesh") -> "Mesh":
        f = []
        for q in quads:
            if len(q) == 3:
                f.append(q)
            else:
                f.append((q[0], q[1], q[2]))
                f.append((q[0], q[2], q[3]))
        f = np.array(f, dtype=np.int32).reshape(-1, 3)
        return Mesh(np.array(v, float).reshape(-1, 3), f, np.zeros(len(f), np.int32), [color], name)

    def copy(self) -> "Mesh":
        return Mesh(self.v.copy(), self.f.copy(), self.mat.copy(), list(self.materials), self.name)

    # ---- transforms (return new meshes, so primitives can be reused)
    def transform(self, rot=None, pos=(0, 0, 0), scale=(1, 1, 1)) -> "Mesh":
        m = self.copy()
        m.v = m.v * np.array(scale, float)
        if rot is not None:
            m.v = m.v @ np.array(rot, float).T
        m.v = m.v + np.array(pos, float)
        if np.prod(scale) < 0:  # mirrored: keep the faces facing outwards
            m.f = m.f[:, ::-1].copy()
        return m

    def translate(self, x=0.0, y=0.0, z=0.0) -> "Mesh":
        return self.transform(pos=(x, y, z))

    def scale(self, sx=1.0, sy=None, sz=None) -> "Mesh":
        return self.transform(scale=(sx, sx if sy is None else sy, sx if sz is None else sz))

    def rotate(self, rx=0.0, ry=0.0, rz=0.0) -> "Mesh":
        """Degrees, applied X then Y then Z (the engine's ``euler`` order)."""
        return self.transform(rot=_euler(rx, ry, rz))

    def recolor(self, color: str) -> "Mesh":
        m = self.copy()
        m.materials = [color]
        m.mat = np.zeros(len(m.f), np.int32)
        return m

    # ---- analysis
    def normals(self) -> np.ndarray:
        a, b, c = (self.v[self.f[:, k]] for k in range(3))
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        return n / np.where(ln > 1e-12, ln, 1.0)

    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return self.v.min(0), self.v.max(0)

    def stats(self) -> dict:
        lo, hi = self.bounds() if len(self.v) else (np.zeros(3), np.zeros(3))
        return {"name": self.name, "triangles": int(len(self.f)), "vertices": int(len(self.v)), "materials": len(self.materials),
                "size": [round(float(x), 3) for x in (hi - lo)],
                "roblox_ok": bool(len(self.f) <= 10000 and len(self.v) <= 20000)}

    def volume(self) -> float:
        """Signed volume (positive for outward-facing closed meshes)."""
        a, b, c = (self.v[self.f[:, k]] for k in range(3))
        return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def merge(meshes: list[Mesh], name: str = "merged") -> Mesh:
    """Concatenate meshes, de-duplicating materials by colour."""
    verts, faces, mats, materials = [], [], [], []
    off = 0
    for m in meshes:
        verts.append(m.v)
        faces.append(m.f + off)
        remap = []
        for col in m.materials:
            if col not in materials:
                materials.append(col)
            remap.append(materials.index(col))
        mats.append(np.array(remap, np.int32)[m.mat] if len(m.mat) else np.zeros(0, np.int32))
        off += len(m.v)
    return Mesh(np.concatenate(verts) if verts else np.zeros((0, 3)), np.concatenate(faces) if faces else np.zeros((0, 3), np.int32),
                np.concatenate(mats) if mats else np.zeros(0, np.int32), materials, name)


def _euler(rx: float, ry: float, rz: float) -> np.ndarray:
    def rot_x(a):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    def rot_y(a):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

    def rot_z(a):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    return rot_x(rx) @ rot_y(ry) @ rot_z(rz)


# ------------------------------------------------------------------ primitives
def lathe(profile: list[tuple[float, float]], segments: int = 16, color: str = "#888888", name: str = "lathe", closed_top: bool = True) -> Mesh:
    """Revolve a profile [(radius, y), ...] around the Y axis. Radius 0 at an end closes it to a point."""
    pr = np.array(profile, float)
    n = len(pr)
    verts, quads = [], []
    for j, (r, y) in enumerate(pr):
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((r * math.cos(a), y, r * math.sin(a)))
    for j in range(n - 1):
        for i in range(segments):
            i2 = (i + 1) % segments
            a, b = j * segments + i, j * segments + i2
            c, d = (j + 1) * segments + i2, (j + 1) * segments + i
            if pr[j][0] < 1e-9 and pr[j + 1][0] < 1e-9:
                continue
            quads.append((a, d, c, b) if pr[j][0] >= 1e-9 or pr[j + 1][0] >= 1e-9 else (a, d, c, b))
    # the winding above faces outwards for profiles that go bottom -> top
    m = Mesh.from_quads(verts, [q for q in quads], color, name)
    # drop degenerate triangles produced at radius-0 rings
    a, b, c = (m.v[m.f[:, k]] for k in range(3))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    keep = area > 1e-10
    m.f, m.mat = m.f[keep], m.mat[keep]
    return m


def cylinder(radius: float = 0.5, height: float = 1.0, segments: int = 16, color: str = "#888888", name: str = "cylinder", caps: bool = True) -> Mesh:
    prof = [(0.0, -height / 2), (radius, -height / 2), (radius, height / 2), (0.0, height / 2)] if caps else [(radius, -height / 2), (radius, height / 2)]
    return lathe(prof, segments, color, name)


def cone(radius: float = 0.5, height: float = 1.0, segments: int = 12, color: str = "#888888", name: str = "cone") -> Mesh:
    """Base at y = 0, tip at y = height."""
    return lathe([(0.0, 0.0), (radius, 0.0), (0.0, height)], segments, color, name)


def sphere(radius: float = 0.5, segments: int = 16, rings: int = 10, color: str = "#888888", name: str = "sphere") -> Mesh:
    prof = [(radius * math.sin(math.pi * k / rings), -radius * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    return lathe(prof, segments, color, name)


def torus(major: float = 0.5, minor: float = 0.1, segments: int = 24, sides: int = 8, color: str = "#888888", name: str = "torus") -> Mesh:
    """A ring in the XZ plane (axis Y)."""
    verts, quads = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for j in range(sides):
            b = 2 * math.pi * j / sides
            r = major + minor * math.cos(b)
            verts.append((r * math.cos(a), minor * math.sin(b), r * math.sin(a)))
    for i in range(segments):
        i2 = (i + 1) % segments
        for j in range(sides):
            j2 = (j + 1) % sides
            quads.append((i * sides + j, i * sides + j2, i2 * sides + j2, i2 * sides + j))
    m = Mesh.from_quads(verts, quads, color, name)
    if m.volume() < 0:
        m.f = m.f[:, ::-1].copy()
    return m


def bevel_box(size: Vec = (1, 1, 1), bevel: float = 0.08, color: str = "#888888", name: str = "box", steps: int = 1) -> Mesh:
    """A box with rounded edges and corners (``bevel`` studs), built as a superellipsoid-like sphere-swept cube."""
    sx, sy, sz = (s / 2 for s in size)
    bv = min(bevel, sx, sy, sz)
    n = 4 * steps + 1
    # a unit cube surface subdivided n x n per face, pushed onto a rounded cube by clamping to the inner box then offsetting by bv along the normal
    verts, quads = [], []
    inner = np.array([sx - bv, sy - bv, sz - bv])
    idx = {}

    def vert(p):
        key = tuple(np.round(p, 6))
        if key not in idx:
            idx[key] = len(verts)
            verts.append(p)
        return idx[key]

    t = np.linspace(-1.0, 1.0, n)
    for axis in range(3):
        for sign in (-1, 1):
            u_axis, v_axis = [a for a in range(3) if a != axis]
            grid = {}
            for i, a in enumerate(t):
                for j, b in enumerate(t):
                    p = np.zeros(3)
                    p[axis] = sign
                    p[u_axis] = a
                    p[v_axis] = b
                    q = np.clip(p * np.array([sx, sy, sz]), -inner, inner)  # nearest point on the inner box
                    d = p * np.array([sx, sy, sz]) - q
                    ln = np.linalg.norm(d)
                    d = d / ln * bv if ln > 1e-9 else np.zeros(3)
                    if ln <= 1e-9:
                        d = np.zeros(3)
                        d[axis] = sign * bv
                    grid[(i, j)] = vert(q + d)
            for i in range(n - 1):
                for j in range(n - 1):
                    quad = (grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)])
                    if len({*quad}) < 3:
                        continue
                    quads.append(quad)
    m = Mesh.from_quads(verts, quads, color, name)
    # the six faces are generated with different handedness: orient every triangle away from the centre (valid because a rounded box is convex)
    a, b, c = (m.v[m.f[:, k]] for k in range(3))
    n = np.cross(b - a, c - a)
    out = np.einsum("ij,ij->i", n, (a + b + c) / 3.0) < 0
    m.f[out] = m.f[out][:, ::-1]
    a, b, c = (m.v[m.f[:, k]] for k in range(3))
    keep = np.linalg.norm(np.cross(b - a, c - a), axis=1) > 1e-10
    m.f, m.mat = m.f[keep], m.mat[keep]
    return m


def prism(polygon: list[tuple[float, float]], depth: float = 1.0, color: str = "#888888", name: str = "prism") -> Mesh:
    """Extrude a convex-or-star-shaped 2D polygon (x, y) along Z (centred), caps fanned from the centroid."""
    poly = np.array(polygon, float)
    cx, cy = poly.mean(0)
    n = len(poly)
    verts = [(x, y, -depth / 2) for x, y in poly] + [(x, y, depth / 2) for x, y in poly] + [(cx, cy, -depth / 2), (cx, cy, depth / 2)]
    quads = []
    for i in range(n):
        j = (i + 1) % n
        quads.append((i, j, n + j, n + i))
        quads.append((2 * n, j, i))
        quads.append((2 * n + 1, n + i, n + j))
    m = Mesh.from_quads(verts, quads, color, name)
    if m.volume() < 0:
        m.f = m.f[:, ::-1].copy()
    return m


def sweep(section: list[tuple[float, float]], path: list[Vec], scales: list[float] | None = None, color: str = "#888888", name: str = "sweep",
          caps: bool = True, twist: float = 0.0) -> Mesh:
    """Extrude a closed 2D cross-section (x, y) along a 3D path with per-point scale (taper). Good for blades, tails, scarves, spikes."""
    sec = np.array(section, float)
    pts = np.array(path, float)
    m_, k = len(pts), len(sec)
    scales = scales or [1.0] * m_
    verts, quads = [], []
    prev_n = None
    for i in range(m_):
        t = pts[min(i + 1, m_ - 1)] - pts[max(i - 1, 0)]
        t = t / (np.linalg.norm(t) or 1.0)
        ref = np.array([0.0, 1.0, 0.0]) if abs(t[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        if prev_n is not None:  # parallel transport: keep the frame from flipping
            ref = prev_n
        b = np.cross(t, ref)
        b = b / (np.linalg.norm(b) or 1.0)
        nrm = np.cross(b, t)
        prev_n = nrm
        ang = math.radians(twist * i / max(1, m_ - 1))
        for sx, sy in sec:
            x, y = sx * math.cos(ang) - sy * math.sin(ang), sx * math.sin(ang) + sy * math.cos(ang)
            verts.append(tuple(pts[i] + (b * x + nrm * y) * scales[i]))
    for i in range(m_ - 1):
        for j in range(k):
            j2 = (j + 1) % k
            quads.append((i * k + j, (i + 1) * k + j, (i + 1) * k + j2, i * k + j2))
    if caps:
        c0 = len(verts)
        verts.append(tuple(pts[0]))
        verts.append(tuple(pts[-1]))
        for j in range(k):
            j2 = (j + 1) % k
            quads.append((c0, j2, j))
            quads.append((c0 + 1, (m_ - 1) * k + j, (m_ - 1) * k + j2))
    m = Mesh.from_quads(verts, quads, color, name)
    if m.volume() < 0:
        m.f = m.f[:, ::-1].copy()
    a, b2, c = (m.v[m.f[:, kk]] for kk in range(3))
    keep = np.linalg.norm(np.cross(b2 - a, c - a), axis=1) > 1e-10
    m.f, m.mat = m.f[keep], m.mat[keep]
    return m


def ngon(r: float, n: int = 8) -> list[tuple[float, float]]:
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ------------------------------------------------------------------ export
def to_obj(mesh: Mesh, mtl_name: str | None = None, smooth: bool = True) -> str:
    """Wavefront OBJ text (with vertex normals when ``smooth``) grouped by material."""
    lines = ["# generated by tsb_engine.modeling", f"o {mesh.name}"]
    if mtl_name:
        lines.append(f"mtllib {mtl_name}")
    for x, y, z in mesh.v:
        lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    if smooth:
        vn = np.zeros_like(mesh.v)
        fn = mesh.normals()
        for k in range(3):
            np.add.at(vn, mesh.f[:, k], fn)
        ln = np.linalg.norm(vn, axis=1, keepdims=True)
        vn = vn / np.where(ln > 1e-12, ln, 1.0)
        for x, y, z in vn:
            lines.append(f"vn {x:.4f} {y:.4f} {z:.4f}")
    for mi, col in enumerate(mesh.materials):
        sel = np.nonzero(mesh.mat == mi)[0]
        if not len(sel):
            continue
        lines.append(f"usemtl m{mi}_{col.lstrip('#')}")
        for fi in sel:
            a, b, c = (int(i) + 1 for i in mesh.f[fi])
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c}" if smooth else f"f {a} {b} {c}")
    return "\n".join(lines) + "\n"


def to_mtl(mesh: Mesh) -> str:
    out = []
    for mi, col in enumerate(mesh.materials):
        r, g, b = (int(col.lstrip("#")[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        out += [f"newmtl m{mi}_{col.lstrip('#')}", f"Kd {r:.4f} {g:.4f} {b:.4f}", "Ka 0 0 0", "Ks 0.05 0.05 0.05", "Ns 20", "d 1", ""]
    return "\n".join(out)


def parse_obj(text: str) -> Mesh:
    """Read back what ``to_obj`` writes (vertices, triangle faces, materials by colour): used to verify exports."""
    v, f, mat, materials, cur = [], [], [], [], 0
    for ln in text.splitlines():
        p = ln.split()
        if not p:
            continue
        if p[0] == "v":
            v.append([float(x) for x in p[1:4]])
        elif p[0] == "usemtl":
            col = "#" + p[1].split("_", 1)[1]
            if col not in materials:
                materials.append(col)
            cur = materials.index(col)
        elif p[0] == "f":
            f.append([int(x.split("/")[0]) - 1 for x in p[1:4]])
            mat.append(cur)
    return Mesh(np.array(v), np.array(f, np.int32), np.array(mat, np.int32), materials, "parsed")
