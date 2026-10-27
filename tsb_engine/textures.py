"""Procedural VFX textures baked to Roblox flipbook sheets (numpy + Pillow, no Blender needed).

Roblox ``ParticleEmitter`` flipbooks: ``FlipbookLayout`` Grid2x2 / Grid4x4 / Grid8x8, square power-of-two
texture (1024 x 1024 is the safe size), ``FlipbookFramerate`` up to 30. The frame order inside the sheet is
**not documented** in the sources we found: bake the numbered test sheet (``numbered_sheet``), look at it in
Studio, and flip ``ROW_MAJOR_TOP_FIRST`` below if it plays backwards.

Algorithms (written here; the ideas come from the surveyed sources, see docs/research/github-survey.md):
starburst = angular lobes with radial falloff (Godot Shaders "starburst" CC0 formula), lightning = midpoint
displacement, smoke = fBm + domain warp + dissolve threshold, flipbook packing = grid paste + RGB bleed
(bgivenb/blender-spritesheet, CC0, for the cell/flip logic).
"""

from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROW_MAJOR_TOP_FIRST = True  # frame 0 = top-left, then left to right, top to bottom (unverified in Roblox)

Frames = list[np.ndarray]  # each (n, n, 4) float32, straight (non-premultiplied) RGBA in 0..1


# ------------------------------------------------------------------ helpers
def _coords(n: int) -> tuple[np.ndarray, np.ndarray]:
    ax = (np.arange(n, dtype=np.float32) + 0.5) / n * 2 - 1
    x, y = np.meshgrid(ax, -ax)
    return x, y


def _smoothstep(a: float | np.ndarray, b: float | np.ndarray, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def _ramp(v: np.ndarray, stops: list[tuple[float, tuple[float, float, float]]]) -> np.ndarray:
    """Colour ramp: v in 0..1 -> RGB through (position, colour) stops."""
    pos = [p for p, _ in stops]
    out = np.zeros(v.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(v, pos, [col[c] for _, col in stops])
    return out


def _rgba(rgb: np.ndarray, a: np.ndarray) -> np.ndarray:
    return np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]], axis=-1).astype(np.float32)


def value_noise(n: int, cells: int, seed: int) -> np.ndarray:
    """Smooth value noise on an n x n grid with ``cells`` lattice cells (cosine interpolation)."""
    rng = np.random.default_rng(seed)
    g = rng.random((cells + 2, cells + 2)).astype(np.float32)
    t = np.linspace(0, cells, n, endpoint=False, dtype=np.float32)
    i = t.astype(int)
    f = t - i
    f = (1 - np.cos(f * math.pi)) / 2
    a = g[i][:, i] * (1 - f)[None, :] * (1 - f)[:, None]
    # bilinear with smoothed weights
    ix = i[None, :]
    iy = i[:, None]
    fx = f[None, :]
    fy = f[:, None]
    v00, v10 = g[iy, ix], g[iy, ix + 1]
    v01, v11 = g[iy + 1, ix], g[iy + 1, ix + 1]
    del a
    return (v00 * (1 - fx) + v10 * fx) * (1 - fy) + (v01 * (1 - fx) + v11 * fx) * fy


def fbm(n: int, base: int, octaves: int, seed: int, persistence: float = 0.5) -> np.ndarray:
    total = np.zeros((n, n), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise(n, base * 2**o, seed + o * 17)
        norm += amp
        amp *= persistence
    return total / norm


def _warp(field_fn, n: int, seed: int, strength: float) -> np.ndarray:
    """Domain-warped fBm: sample the field at positions displaced by two other noise fields."""
    qx, qy = fbm(n, 3, 3, seed + 100), fbm(n, 3, 3, seed + 200)
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    sx = np.clip(xs + (qx - 0.5) * strength * n, 0, n - 1).astype(int)
    sy = np.clip(ys + (qy - 0.5) * strength * n, 0, n - 1).astype(int)
    return field_fn()[sy, sx]


def _blur(img: Image.Image, r: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(r))


# ------------------------------------------------------------------ effects
def glow(n: int = 128, sharp: float = 6.0) -> Frames:
    """Soft round glow sprite (single frame): gaussian + hot core."""
    x, y = _coords(n)
    r2 = x * x + y * y
    a = np.exp(-r2 * sharp) * 0.85 + 0.6 / (1 + r2 * 60)
    return [_rgba(np.stack([np.ones_like(a)] * 3, -1), np.clip(a, 0, 1) * (r2 < 1))]


def starburst(n: int = 256, frames: int = 8, spikes: int = 8, seed: int = 1) -> Frames:
    """Hit star: thin angular lobes with exp falloff, popping out (overshoot) then fading."""
    x, y = _coords(n)
    r = np.sqrt(x * x + y * y) + 1e-6
    ang = np.arctan2(y, x)
    rng = random.Random(seed)
    dirs = [(k / spikes) * math.tau + rng.uniform(-0.25, 0.25) for k in range(spikes)]
    lens = [rng.uniform(0.55, 1.0) for _ in range(spikes)]
    out: Frames = []
    for f in range(frames):
        t = f / max(1, frames - 1)
        grow = 1 - (1 - min(1.0, t * 2.2)) ** 3
        scale = grow * (1.12 if t < 0.35 else 1.0)
        alpha = 1.0 if t < 0.3 else max(0.0, 1 - (t - 0.3) / 0.7)
        spike = np.zeros_like(r)
        for d, ln in zip(dirs, lens):
            da = np.abs(np.arctan2(np.sin(ang - d), np.cos(ang - d)))
            lobe = np.exp(-(da / (0.075 + 0.05 * (1 - r))) ** 2)
            spike = np.maximum(spike, lobe * np.exp(-r / (0.34 * ln * scale + 1e-3)))
        core = np.exp(-(r / (0.2 * scale + 0.02)) ** 2)
        v = np.clip(spike * 0.95 + core, 0, 1)
        rgb = _ramp(v, [(0.0, (1.0, 0.42, 0.08)), (0.45, (1.0, 0.8, 0.3)), (1.0, (1.0, 1.0, 0.95))])
        out.append(_rgba(rgb, np.clip(v * 1.15, 0, 1) * alpha * (r < 1.0)))
    return out


def impact_star(n: int = 256, frames: int = 8, points: int = 11, seed: int = 3) -> Frames:
    """Hard-edged comic/anime burst (jagged polygon + core), supersampled; pop, hold, fade."""
    rng = random.Random(seed)
    radii = [rng.uniform(0.6, 1.0) for _ in range(points)]
    ss = 4
    out: Frames = []
    for f in range(frames):
        t = f / max(1, frames - 1)
        grow = 1 - (1 - min(1.0, t * 2.6)) ** 3
        s = grow * (1.1 if t < 0.3 else 1.0) * 0.46
        alpha = 1.0 if t < 0.35 else max(0.0, 1 - (t - 0.35) / 0.65)
        img = Image.new("RGBA", (n * ss, n * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        c = n * ss / 2

        def star(scale: float, color: tuple[int, int, int, int], rot: float = 0.0) -> None:
            pts = []
            for i in range(points * 2):
                a = rot + i * math.pi / points
                rr = (radii[(i // 2) % points] if i % 2 == 0 else 0.26) * scale * n * ss
                pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
            d.polygon(pts, fill=color)

        star(s, (255, 150, 30, int(255 * alpha)))
        star(s * 0.64, (255, 245, 200, int(255 * alpha)), rot=0.12)
        r = max(1, int(s * 0.28 * n * ss))
        d.ellipse((c - r, c - r, c + r, c + r), fill=(255, 255, 255, int(255 * alpha)))
        img = img.resize((n, n), Image.LANCZOS)
        out.append(np.asarray(img, np.float32) / 255.0)
    return out


def slash(n: int = 256, frames: int = 8, sweep: tuple[float, float] = (-30.0, 150.0), seed: int = 2) -> Frames:
    """Crescent slash (lune = disc minus offset disc) wiped along its arc with a bright head and fading tail."""
    x, y = _coords(n)
    R = 0.92
    c1 = (0.0, 0.0)
    c2 = (0.0, -0.5)
    r1 = np.sqrt((x - c1[0]) ** 2 + (y - c1[1]) ** 2)
    r2 = np.sqrt((x - c2[0]) ** 2 + (y - c2[1]) ** 2)
    inside = _smoothstep(R + 0.01, R - 0.02, r1) * _smoothstep(R - 0.02, R + 0.02, r2)
    ang = np.degrees(np.arctan2(y, x))  # arc runs from sweep[0] to sweep[1]
    u = np.clip((ang - sweep[0]) / (sweep[1] - sweep[0]), 0, 1)
    out: Frames = []
    for f in range(frames):
        t = f / max(1, frames - 1)
        head = 1 - (1 - min(1.0, t * 1.5)) ** 2
        tail = max(0.0, (t - 0.25) / 0.75) ** 1.5
        vis = _smoothstep(head + 0.02, head - 0.1, u) * _smoothstep(tail - 0.05, tail + 0.1, u)
        edge = np.clip((u - tail) / (head - tail + 1e-3), 0, 1)
        v = np.clip(inside * vis, 0, 1)
        rgb = _ramp(edge * 0.8 + 0.2 * inside, [(0.0, (1.0, 0.55, 0.15)), (0.6, (1.0, 0.85, 0.5)), (1.0, (1.0, 1.0, 1.0))])
        out.append(_rgba(rgb, v))
    return out


def ring(n: int = 256, frames: int = 8, seed: int = 4) -> Frames:
    """Shockwave ring: gaussian annulus, radius ease-out, thinning, with angular ripples."""
    x, y = _coords(n)
    r = np.sqrt(x * x + y * y)
    ang = np.arctan2(y, x)
    rip = 0.8 + 0.2 * np.sin(ang * 9 + seed) * np.sin(ang * 5 - seed)
    out: Frames = []
    for f in range(frames):
        t = f / max(1, frames - 1)
        R = 0.15 + 0.8 * (1 - (1 - t) ** 3)
        w = 0.1 * (1 - t) + 0.015
        a = np.exp(-((r - R) / w) ** 2) * rip * (1 - t) ** 1.4
        core = np.exp(-((r - R) / (w * 0.35)) ** 2) * (1 - t)
        rgb = _ramp(np.clip(core, 0, 1), [(0.0, (1.0, 0.7, 0.35)), (1.0, (1.0, 1.0, 1.0))])
        out.append(_rgba(rgb, np.clip(a + core * 0.4, 0, 1)))
    return out


def _bolt_points(p0, p1, rng: random.Random, levels: int, jitter: float) -> list[tuple[float, float]]:
    pts = [p0, p1]
    amp = jitter
    for _ in range(levels):
        nxt = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1.0
            off = rng.uniform(-1, 1) * amp * ln
            nxt += [(mx - dy / ln * off, my + dx / ln * off), b]
        pts = nxt
        amp *= 0.55
    return pts


def lightning(n: int = 256, frames: int = 8, seed: int = 5) -> Frames:
    """Vertical lightning bolts: midpoint displacement + branches, 3-pass glow, re-rolled every frame."""
    out: Frames = []
    ss = 2
    for f in range(frames):
        rng = random.Random(seed * 1000 + f)
        S = n * ss
        base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        glowl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        main = _bolt_points((S * 0.5, S * 0.03), (S * 0.5 + rng.uniform(-0.1, 0.1) * S, S * 0.97), rng, 7, 0.3)
        branches = []
        for i in range(8, len(main) - 8, 14):
            if rng.random() < 0.55:
                a = main[i]
                end = (a[0] + rng.uniform(-0.3, 0.3) * S, a[1] + rng.uniform(0.08, 0.28) * S)
                branches.append(_bolt_points(a, end, rng, 5, 0.3))
        gd, bd = ImageDraw.Draw(glowl), ImageDraw.Draw(base)
        for path, w in [(main, 1.0)] + [(b, 0.55) for b in branches]:
            gd.line(path, fill=(255, 150, 40, 140), width=int(10 * w * ss))
            bd.line(path, fill=(255, 215, 120, 255), width=int(4 * w * ss))
            bd.line(path, fill=(255, 255, 255, 255), width=max(1, int(1.6 * w * ss)))
        comp = Image.alpha_composite(_blur(glowl, 5 * ss), _blur(base, 0.8))
        comp = Image.alpha_composite(comp, base)
        out.append(np.asarray(comp.resize((n, n), Image.LANCZOS), np.float32) / 255.0)
    return out


def smoke(n: int = 128, frames: int = 64, seed: int = 6, tones: int = 4) -> Frames:
    """Stylised billowing smoke puff: lumpy outline, upper-left light, posterised, eaten away by a noise dissolve."""
    x, y = _coords(n)
    r = np.sqrt(x * x + y * y)
    lump = fbm(n, 2, 4, seed)
    lump2 = fbm(n, 5, 4, seed + 9)
    rr = r / (0.62 + 0.5 * lump)
    light = 0.5 + (-x * 0.5 + y * 0.5) * 0.9 + (lump2 - 0.5) * 0.9
    out: Frames = []
    for f in range(frames):
        t = f / max(1, frames - 1)
        grow = 0.45 + 0.55 * (1 - (1 - min(1.0, t * 3.0)) ** 2)
        body = _smoothstep(grow, grow - 0.3, rr)
        td = max(0.0, (t - 0.35) / 0.65) * 1.15 - 0.05
        alive = _smoothstep(td, td + 0.18, lump2 + 0.15 * (1 - rr))
        a = body * alive * (1 - 0.45 * t)
        shade = np.clip(light, 0, 1)
        if tones:
            shade = np.round(shade * (tones - 1)) / (tones - 1)
        rgb = np.stack([0.34 + 0.56 * shade, 0.32 + 0.54 * shade, 0.31 + 0.52 * shade], -1)
        out.append(_rgba(rgb, a))
    return out


def fire(n: int = 128, frames: int = 32, seed: int = 7) -> Frames:
    """Stylised flame: fBm scrolled upwards, vertical gradient, fire colour ramp, posterised."""
    x, y = _coords(n)
    big = fbm(n * 2, 3, 5, seed)
    out: Frames = []
    for f in range(frames):
        t = f / frames  # looping
        shift = int(t * n)
        field = np.roll(big, shift, axis=0)[:n, :n]
        width = np.exp(-(x * 1.6) ** 2 * (1 + 1.5 * (y + 1) / 2))
        grad = _smoothstep(1.0, -0.6, y)
        v = np.clip(field * 1.3 * width * grad + width * grad * 0.2, 0, 1)
        v = np.round(v * 4) / 4
        rgb = _ramp(v, [(0.0, (0.6, 0.05, 0.0)), (0.35, (1.0, 0.3, 0.02)), (0.7, (1.0, 0.75, 0.2)), (1.0, (1.0, 1.0, 0.85))])
        out.append(_rgba(rgb, _smoothstep(0.12, 0.35, v)))
    return out


def speed_lines(n: int = 512, count: int = 90, seed: int = 8) -> Frames:
    """Radial speed lines with a clear centre (use on a screen-facing plane or a cylinder)."""
    rng = random.Random(seed)
    ss = 2
    S = n * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    for _ in range(count):
        a = rng.uniform(0, math.tau)
        r0, r1 = rng.uniform(0.3, 0.6) * S / 2, rng.uniform(0.75, 1.0) * S / 2
        w = rng.uniform(0.004, 0.012) * S
        ca, sa = math.cos(a), math.sin(a)
        pa, pb = c + ca * r0, c + sa * r0
        qa, qb = c + ca * r1, c + sa * r1
        d.polygon([(pa - sa * w * 0.1, pb + ca * w * 0.1), (pa + sa * w * 0.1, pb - ca * w * 0.1), (qa + sa * w, qb - ca * w), (qa - sa * w, qb + ca * w)],
                  fill=(255, 255, 255, rng.randint(120, 255)))
    return [np.asarray(img.resize((n, n), Image.LANCZOS), np.float32) / 255.0]


# ------------------------------------------------------------------ packing
def bleed_rgb(img: Image.Image, passes: int = 4) -> Image.Image:
    """Fill the RGB of transparent pixels with nearby colours so mip filtering leaves no dark/white fringe."""
    a = np.asarray(img, np.float32) / 255.0
    rgb, alpha = a[..., :3].copy(), a[..., 3]
    known = alpha > 0.02
    for _ in range(passes):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(alpha.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                k = np.roll(np.roll(known, dy, 0), dx, 1)
                acc += np.roll(np.roll(rgb * known[..., None], dy, 0), dx, 1) * k[..., None]
                cnt += k
        fill = (~known) & (cnt > 0)
        rgb[fill] = acc[fill] / cnt[fill][:, None]
        known = known | fill
    out = np.concatenate([rgb, alpha[..., None]], -1)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def pack_flipbook(frames: Frames, grid: int, size: int = 1024, pad: int = 4) -> Image.Image:
    """Paste frames into a ``grid`` x ``grid`` sheet of ``size`` px (cell = size // grid), transparent padding kept."""
    cell = size // grid
    if len(frames) > grid * grid:
        raise ValueError(f"{len(frames)} frames do not fit a {grid}x{grid} sheet")
    sheet = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        col, row = i % grid, i // grid
        if not ROW_MAJOR_TOP_FIRST:
            row = grid - 1 - row
        im = Image.fromarray((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").resize((cell - 2 * pad, cell - 2 * pad), Image.LANCZOS)
        tile = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        tile.paste(im, (pad, pad))
        sheet.paste(tile, (col * cell, row * cell))
    return bleed_rgb(sheet)


def numbered_sheet(grid: int, size: int = 1024) -> Image.Image:
    """Frame-number test sheet: load it as a flipbook in Studio to learn the real frame order."""
    cell = size // grid
    sheet = Image.new("RGBA", (size, size), (20, 20, 20, 255))
    d = ImageDraw.Draw(sheet)
    for i in range(grid * grid):
        col, row = i % grid, i // grid
        d.rectangle((col * cell + 2, row * cell + 2, (col + 1) * cell - 3, (row + 1) * cell - 3), outline=(255, 160, 40, 255), width=2)
        d.text((col * cell + cell // 3, row * cell + cell // 3), str(i), fill=(255, 255, 255, 255))
    return sheet


def preview(sheet: Image.Image, bg=(48, 52, 70)) -> Image.Image:
    back = Image.new("RGBA", sheet.size, bg + (255,))
    return Image.alpha_composite(back, sheet).convert("RGB")


# name -> (generator, kwargs, grid, framerate)
RECIPES = {
    "starburst": (starburst, dict(n=256, frames=8), 4, 24),
    "impact_star": (impact_star, dict(n=256, frames=8), 4, 24),
    "slash": (slash, dict(n=256, frames=8), 4, 24),
    "ring": (ring, dict(n=256, frames=8), 4, 24),
    "lightning": (lightning, dict(n=256, frames=8), 4, 20),
    "smoke": (smoke, dict(n=128, frames=64), 8, 15),
    "fire": (fire, dict(n=128, frames=32), 8, 24),
}


def bake_all(out_dir: str, names: list[str] | None = None) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name in names or list(RECIPES):
        gen, kw, grid, fps = RECIPES[name]
        sheet = pack_flipbook(gen(**kw), grid)
        path = os.path.join(out_dir, f"{name}_{grid}x{grid}_{fps}fps.png")
        sheet.save(path)
        preview(sheet).save(os.path.join(out_dir, f"{name}_preview.png"))
        written.append(path)
    for g in (4, 8):
        numbered_sheet(g).save(os.path.join(out_dir, f"order_test_{g}x{g}.png"))
    return written


if __name__ == "__main__":
    import sys

    for p in bake_all(sys.argv[1] if len(sys.argv) > 1 else "assets/flipbooks"):
        print(p)
