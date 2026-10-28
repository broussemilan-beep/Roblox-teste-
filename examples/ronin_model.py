"""An original character built from real meshes: the "Ronin" (spiky hair, goggles, katana, harness, bracers, pauldron).

It is *inspired by the silhouette traits observed in the second reference* (docs/research/reference-analysis-2.md: spiky black hair, goggles on the
forehead, a katana across the back, dark torso with orange-brown sleeves, light shoe trim, a rounded-cylinder dummy head) but every shape is made
here from the ``tsb_engine.modeling`` kit; nothing is copied from any game asset. Each mesh is modelled in the local frame of the R6 part it is glued to.

``python examples/ronin_model.py out_dir`` writes one OBJ+MTL per accessory and prints triangle counts (Roblox MeshPart limit: see modeling.py).
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tsb_engine import modeling as M  # noqa: E402
from tsb_engine.secondary import Attach, Outfit, Rigid, Strand  # noqa: E402

INK = "#101014"
STEEL = "#cfd6de"
STEEL_DK = "#8d98a4"
LACQUER = "#17171c"
WRAP = "#3a2a22"
GOLD = "#8a7a4c"
SLEEVE = "#5a3523"
SLEEVE_DK = "#3a2216"
CREAM = "#7a766c"
LENS = "#c9e6f2"
STRAP = "#2a2a31"
HAIR = "#0a0a0d"

RONIN_COLORS = {"Head": "#e9c9a5", "Torso": INK, "Left Arm": SLEEVE, "Right Arm": SLEEVE, "Left Leg": INK, "Right Leg": INK}


def _aim(mesh: M.Mesh, direction, pos) -> M.Mesh:
    """Rotate a +Y-pointing mesh so it points along ``direction`` (any length), then move it to ``pos``."""
    import numpy as np

    d = np.array(direction, float)
    d /= np.linalg.norm(d)
    y = np.array([0.0, 1.0, 0.0])
    ax = np.cross(y, d)
    s, c = np.linalg.norm(ax), float(y @ d)
    if s < 1e-9:
        rot = np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        ax /= s
        k = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        rot = np.eye(3) + k * s + k @ k * (1 - c)
    return mesh.transform(rot=rot, pos=pos)


# ------------------------------------------------------------------ head
def hair(seed: int = 7) -> M.Mesh:
    """A skull cap plus ~45 conical spikes: crown spikes sweep back, fringe spikes fall to the front, nape spikes hang down the back."""
    rng = random.Random(seed)
    parts = [M.bevel_box((2.12, 0.34, 1.12), 0.12, HAIR, "cap").translate(0, 0.42, 0.02)]
    parts.append(M.bevel_box((2.12, 0.9, 0.34), 0.12, HAIR, "nape").translate(0, 0.02, 0.5))
    # crown: rows from front to back; each spike leans backwards and outwards from the middle
    for row, z in enumerate([-0.35, -0.1, 0.15, 0.4]):
        for x in [-0.85, -0.5, -0.17, 0.17, 0.5, 0.85]:
            x += rng.uniform(-0.07, 0.07)
            h = rng.uniform(0.55, 0.95) + 0.08 * row
            d = (x * 0.35, 1.0, 0.55 + 0.35 * row + rng.uniform(-0.1, 0.1))
            parts.append(_aim(M.cone(rng.uniform(0.17, 0.24), h, 6, HAIR, "s"), d, (x, 0.55, z)))
    # fringe: short spikes over the forehead, pointing forward-down so the goggles sit under them
    for x in [-0.8, -0.4, 0.0, 0.4, 0.8]:
        parts.append(_aim(M.cone(0.15, rng.uniform(0.38, 0.5), 5, HAIR, "f"), (x * 0.2, -0.5, -1.0), (x + rng.uniform(-0.05, 0.05), 0.42, -0.52)))
    # nape: spikes going down and back
    for x in [-0.85, -0.5, -0.17, 0.17, 0.5, 0.85]:
        for y in [0.15, -0.2]:
            parts.append(_aim(M.cone(0.18, rng.uniform(0.5, 0.8), 6, HAIR, "n"), (x * 0.3, -0.45, 1.0), (x, y, 0.62)))
    return M.merge(parts, "ronin_hair")


def goggles() -> M.Mesh:
    """Strap around the head and two round lenses with metal rims, pushed up on the forehead."""
    y = 0.45
    parts = [M.bevel_box((2.1, 0.15, 1.1), 0.05, STRAP, "strap").translate(0, y, 0)]
    for sx in (-1, 1):
        lens = M.cylinder(0.21, 0.1, 14, LENS, "lens").rotate(90, 0, 0).translate(0.5 * sx, y, -0.58)
        rim = M.torus(0.21, 0.05, 14, 6, STEEL_DK, "rim").rotate(90, 0, 0).translate(0.5 * sx, y, -0.56)
        parts += [lens, rim]
    parts.append(M.bevel_box((0.3, 0.08, 0.1), 0.03, STEEL_DK, "bridge").translate(0, y, -0.58))
    return M.merge(parts, "ronin_goggles")


# ------------------------------------------------------------------ katana
def katana(sheathed: bool = True, handle: bool = True) -> M.Mesh:
    """Origin at the guard (tsuba), handle toward -Y (0.95 long), blade toward +Y (2.5 long) with a curved sori and a pointed tip.
    Sheathed: a lacquered saya covers the blade."""
    n = 14
    parts: list[M.Mesh] = []
    if handle:  # handle (tsuka): wrapped cylinder with diamond ito bands, guard, collar
        parts.append(M.cylinder(0.075, 0.95, 8, WRAP, "tsuka").translate(0, -0.475, 0))
        for k in range(5):
            parts.append(M.cylinder(0.088, 0.045, 8, STRAP, "ito").translate(0, -0.15 - 0.17 * k, 0))
        parts.append(M.cylinder(0.1, 0.07, 8, GOLD, "kashira").translate(0, -0.97, 0))
        parts.append(M.cylinder(0.3, 0.04, 14, GOLD, "tsuba").translate(0, 0.0, 0))  # round guard
        parts.append(M.cylinder(0.11, 0.1, 8, GOLD, "habaki").translate(0, 0.07, 0))
    length, sori = 2.5, 0.07
    path = [(sori * math.sin(math.pi * i / n) ** 2 * 0 + 0.0, 0.1 + length * i / n, -sori * math.sin(math.pi * i / n)) for i in range(n + 1)]
    path = [(0.0, y, z * 0.9) for _, y, z in path]
    if sheathed:
        sec = [(-0.075, -0.1), (0.075, -0.1), (0.075, 0.1), (-0.075, 0.1)]
        sc = [1.0] * n + [0.9]
        parts.append(M.sweep(sec, path, sc, LACQUER, "saya"))
        parts.append(M.bevel_box((0.22, 0.12, 0.22), 0.04, GOLD, "koiguchi").translate(0, 0.14, 0))
        parts.append(M.bevel_box((0.19, 0.2, 0.19), 0.04, GOLD, "kojiri").translate(0, 0.1 + length, path[-1][2]))
    else:
        sec = [(0.0, -0.105), (0.03, -0.07), (0.03, 0.105), (-0.03, 0.105), (-0.03, -0.07)]  # thickness x, width y: edge at -y, spine at +y
        sc = [1.0] * (n - 2) + [0.8, 0.45, 0.06]
        parts.append(M.sweep(sec, path, sc, STEEL, "blade"))
        parts.append(M.sweep([(0.0, 0.0), (0.012, 0.0), (0.012, 0.03), (0.0, 0.03)], [(0, 0.1, 0.0), (0, 0.1 + length * 0.85, path[int(n * 0.85)][2] * 0.9)], None, STEEL_DK, "hamon") if False else M.Mesh())
    return M.merge([p for p in parts if len(p.f)], "ronin_katana" + ("_saya" if sheathed else "_drawn") + ("" if handle else "_empty"))


# ------------------------------------------------------------------ body
def harness() -> M.Mesh:
    """Chest strap crossing the torso, belt with buckle, two pouches and a short scarf collar (torso local frame)."""
    parts = [
        M.bevel_box((2.1, 0.3, 1.12), 0.07, STRAP, "belt").translate(0, -0.78, 0),
        M.bevel_box((0.34, 0.26, 0.1), 0.03, GOLD, "buckle").translate(0, -0.78, -0.58),
        M.bevel_box((0.5, 0.42, 0.34), 0.07, WRAP, "pouch").translate(0.78, -0.88, -0.45),
        M.bevel_box((0.5, 0.42, 0.34), 0.07, WRAP, "pouch2").translate(-0.78, -0.88, -0.45),
        M.bevel_box((2.1, 0.36, 1.12), 0.1, CREAM, "scarf").translate(0, 0.86, 0),
    ]
    # diagonal chest strap, front and back (a flat band wrapped around the torso: two sloped boxes)
    for z in (-0.53, 0.53):
        band = M.bevel_box((0.26, 2.15, 0.07), 0.025, STRAP, "band").rotate(0, 0, 38).translate(0.1, 0.0, z)
        parts.append(band)
    return M.merge(parts, "ronin_harness")


def pauldron() -> M.Mesh:
    """Layered shoulder guard on the arm's top (arm local frame: shoulder at +Y 1.0)."""
    dome = M.sphere(0.72, 14, 8, LACQUER, "dome").scale(1.0, 0.55, 1.0).translate(0, 0.98, 0)
    plates = [M.bevel_box((1.22 - 0.1 * i, 0.15, 1.22 - 0.1 * i), 0.06, LACQUER if i % 2 == 0 else SLEEVE_DK, "p").translate(0, 0.78 - 0.16 * i, 0) for i in range(3)]
    trim = M.torus(0.6, 0.04, 16, 6, GOLD, "trim").translate(0, 0.9, 0)
    return M.merge([dome, trim] + plates, "ronin_pauldron")


def bracer() -> M.Mesh:
    """Forearm guard and wrapped wrist (arm local frame, hand end at -Y 1.0)."""
    return M.merge([
        M.bevel_box((1.14, 0.7, 1.14), 0.1, LACQUER, "guard").translate(0, -0.45, 0),
        M.bevel_box((1.18, 0.1, 1.18), 0.04, GOLD, "rim").translate(0, -0.08, 0),
        M.bevel_box((1.12, 0.22, 1.12), 0.06, CREAM, "wrap").translate(0, -0.88, 0),
    ], "ronin_bracer")


def shin() -> M.Mesh:
    """Shin guard, ankle wrap and a pale shoe trim (leg local frame, foot end at -Y 1.0)."""
    return M.merge([
        M.bevel_box((1.1, 0.78, 1.14), 0.1, LACQUER, "greave").translate(0, -0.32, 0),
        M.bevel_box((1.1, 0.2, 1.1), 0.05, CREAM, "wrap").translate(0, -0.75, 0),
        M.bevel_box((1.12, 0.14, 1.14), 0.05, CREAM, "sole").translate(0, -0.93, 0),
        M.bevel_box((1.1, 0.26, 0.34), 0.06, CREAM, "toe").translate(0, -0.78, -0.5),
    ], "ronin_shin")


def ronin_outfit(with_sheath: bool = True, drawn: bool = False, draw: tuple[int, int] | None = None) -> Outfit:
    """``draw=(f0, f1)``: the katana is on his back until image ``f0``, then the empty sheath stays there and the blade is in his right hand until ``f1``."""
    items: list[object] = [
        Attach("hair", "Head", hair()),
        Attach("goggles", "Head", goggles()),
        Attach("harness", "Torso", harness()),
        Attach("pauldron_l", "Left Arm", pauldron()),
        Attach("bracer_l", "Left Arm", bracer()),
        Attach("bracer_r", "Right Arm", bracer()),
        Attach("shin_l", "Left Leg", shin()),
        Attach("shin_r", "Right Leg", shin()),
        Strand("scarf_tail", "Torso", (0.55, 0.9, 0.55), 4, 0.6, 0.62, 0.1, CREAM, rest_dir=(0.1, -1.0, 0.4), gravity=30, stiffness=3.5, drag=2.2, taper=0.9),
    ]
    back = ((0.5, 0.78, 0.7), (0.0, 0.0, 140.0))
    if draw is not None:
        items.append(Attach("katana", "Torso", katana(True), back[0], back[1], vis=(0, draw[0] - 1)))
        items.append(Attach("saya_empty", "Torso", katana(True, handle=False), back[0], back[1], vis=(draw[0], 10**6)))
        items.append(Attach("katana_hand", "Right Arm", katana(False), (0.0, -0.95, -0.15), (-90.0, 0.0, 0.0), vis=(draw[0], draw[1])))
        return Outfit(items)
    if with_sheath:
        items.append(Attach("katana", "Torso", katana(True), back[0], back[1]))
    if drawn:  # blade out, gripped in the right hand and pointing forward (arm local: hand end at -Y 1.0)
        items.append(Attach("katana_hand", "Right Arm", katana(False), (0.0, -0.95, -0.15), (-90.0, 0.0, 0.0)))
    return Outfit(items)


# ------------------------------------------------------------------ the dummy
def dummy_head() -> M.Mesh:
    """Rounded-cylinder head (a short capsule), like a mannequin: replaces the box head (set ``hide=("Head",)`` on the character)."""
    prof = [(0.0, -0.5), (0.34, -0.5), (0.5, -0.44), (0.58, -0.3), (0.6, 0.0), (0.58, 0.3), (0.5, 0.44), (0.34, 0.5), (0.0, 0.5)]
    return M.lathe(prof, 20, "#f1ead8", "dummy_head").scale(1.0, 1.0, 1.0)


def dummy_outfit() -> Outfit:
    return Outfit([Attach("head", "Head", dummy_head()), Attach("neck", "Torso", M.cylinder(0.32, 0.18, 12, "#d9d1be", "dummy_neck").translate(0, 1.05, 0))])


def export_all(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    stats = {}
    for mesh in list(ronin_outfit().meshes().values()) + [katana(False), dummy_head()]:
        (out / f"{mesh.name}.obj").write_text(M.to_obj(mesh, f"{mesh.name}.mtl"))
        (out / f"{mesh.name}.mtl").write_text(M.to_mtl(mesh))
        stats[mesh.name] = mesh.stats()
    return stats


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "viewer" / "output" / "ronin_obj"
    st = export_all(target)
    for k, v in st.items():
        print(f"{k:22s} {v['triangles']:6d} tris {v['vertices']:6d} verts  size {v['size']}  roblox_ok={v['roblox_ok']}")
    print("total triangles:", sum(v["triangles"] for v in st.values()))
