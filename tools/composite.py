"""Assemble the film: Blender 3D layer + the viewer's transparent fx layers + the full-picture punctuation (negative / black-and-white impact frames).

usage: python tools/composite.py SCENE BLENDER_DIR LAYERS_DIR OUT_DIR [first last]

Per frame, in order: Blender frame (``b_NNNN.png``) -> light bloom + grain -> world-space fx layer (``world_NNNN.png``) -> the picture-wide effects that read
what is underneath (``negative``, ``bw``: they must see the 3D layer and the world fx) -> the screen overlays (``screen_NNNN.png``: diagonals, edge lines,
vignette, flashes, plain black/white frames).
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.scenes import SCENES  # noqa: E402
from tsb_engine.scene import export_viewer_data  # noqa: E402


def over(base: np.ndarray, layer_path: Path) -> np.ndarray:
    im = cv2.imread(str(layer_path), cv2.IMREAD_UNCHANGED)
    if im is None:
        return base
    im = cv2.resize(im, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    a = im[..., 3:4]
    return base * (1 - a) + im[..., :3] * a


def bloom(img: np.ndarray, thr: float = 0.62, gain: float = 0.55) -> np.ndarray:
    hi = np.clip(img - thr, 0, 1)
    out = img.copy()
    for k, w in ((9, 0.5), (31, 0.35), (81, 0.2)):
        out += cv2.GaussianBlur(hi, (0, 0), k / 3) * gain * w * 3
    return np.clip(out, 0, 1)


def negative(img: np.ndarray, sf: dict) -> np.ndarray:
    x = 1.0 - img
    hsv = cv2.cvtColor(x.astype(np.float32), cv2.COLOR_BGR2HSV)
    hsv[..., 0] = (hsv[..., 0] + sf.get("hue", 150)) % 360
    hsv[..., 1] = np.clip(hsv[..., 1] * sf.get("sat", 1.7), 0, 1)
    x = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    x = (x - 0.5) * sf.get("contrast", 1.15) + 0.5
    return np.clip(x * sf.get("bright", 1.6), 0, 1)


def bw(img: np.ndarray, sf: dict, f: int) -> np.ndarray:
    h, w = img.shape[:2]
    g = cv2.cvtColor(img.astype(np.float32), cv2.COLOR_BGR2GRAY)
    br, ct = sf.get("bright", 1.25), sf.get("contrast", 14)
    if sf.get("bfirst"):
        g = np.clip(g * br, 0, 1)
        g = np.clip((g - 0.5) * ct + 0.5, 0, 1)
    else:
        g = np.clip((g - 0.5) * ct + 0.5, 0, 1)
        g = np.clip(g * br, 0, 1)
    out = np.dstack([g, g, g])
    if sf.get("multiply"):
        hx = sf["multiply"].lstrip("#")
        rgb = [int(hx[i : i + 2], 16) / 255.0 for i in (4, 2, 0)]  # BGR
        out = out * np.array(rgb, np.float32)
    rng = np.random.RandomState((sf.get("seed", 1) * 97 + f * 17) % (2**31))
    fx, fy = (sf.get("focus") or (0.5, 0.5))
    cx, cy = fx * w, fy * h
    dark = sf.get("dark", False)
    shard_col = (1, 1, 1) if dark else (0, 0, 0)
    for _ in range(sf.get("shards", 16)):
        a = rng.rand() * 2 * np.pi
        r0 = h * (0.18 + rng.rand() * 0.5)
        ln = h * (0.25 + rng.rand() * 0.8)
        wd = h * (0.02 + rng.rand() * 0.07)
        pts = np.array(
            [
                [cx + np.cos(a) * r0, cy + np.sin(a) * r0],
                [cx + np.cos(a + wd / r0) * (r0 + ln * 0.4), cy + np.sin(a + wd / r0) * (r0 + ln * 0.4)],
                [cx + np.cos(a) * (r0 + ln), cy + np.sin(a) * (r0 + ln)],
                [cx + np.cos(a - wd / r0) * (r0 + ln * 0.3), cy + np.sin(a - wd / r0) * (r0 + ln * 0.3)],
            ],
            np.int32,
        )
        cv2.fillConvexPoly(out, pts, shard_col, cv2.LINE_AA)
    for i in range(sf.get("prisms", 0)):
        a = rng.rand() * 2 * np.pi
        r = h * (0.05 + rng.rand() * 0.32)
        ww = h * (0.03 + rng.rand() * 0.07)
        hh = ww * (0.5 + rng.rand() * 1.4)
        rot = rng.rand() * np.pi
        col = (74 / 255, 226 / 255, 255 / 255) if i % 4 == 3 else (255 / 255, 242 / 255, 0.0)  # BGR: yellow / cyan
        c, s = np.cos(rot), np.sin(rot)
        px, py = cx + np.cos(a) * r * 1.3, cy + np.sin(a) * r
        pts = np.array([[px + c * dx - s * dy, py + s * dx + c * dy] for dx, dy in ((-ww / 2, -hh / 2), (ww / 2, -hh / 2), (ww / 2, hh / 2), (-ww / 2, hh / 2))], np.int32)
        cv2.fillConvexPoly(out, pts, col, cv2.LINE_AA)
    return out


def main():
    scene, bdir, ldir, odir = sys.argv[1:5]
    D = export_viewer_data(SCENES[scene]())
    n = D["nFrames"]
    first = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    last = int(sys.argv[6]) if len(sys.argv) > 6 else n - 1
    fxs = D["cine"]["screen"]["fx"]
    Path(odir).mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(4)
    for f in range(first, last + 1):
        b = cv2.imread(str(Path(bdir) / f"b_{f:04d}.png"))
        if b is None:
            print("missing blender frame", f)
            continue
        img = b.astype(np.float32) / 255.0
        img = bloom(img)
        img = over(img, Path(ldir) / f"world_{f:04d}.png")
        for sf in fxs:
            if sf["t0"] <= f < sf["t0"] + sf["dur"]:
                if sf["kind"] == "negative":
                    img = negative(img, sf)
                elif sf["kind"] == "bw":
                    img = bw(img, sf, f)
        img = over(img, Path(ldir) / f"screen_{f:04d}.png")
        img = np.clip(img + rng.normal(0, 0.012, img.shape).astype(np.float32), 0, 1)
        cv2.imwrite(str(Path(odir) / f"f_{f:04d}.png"), (img * 255).astype(np.uint8))
    print("composited", first, last)


if __name__ == "__main__":
    main()
