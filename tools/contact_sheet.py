"""Assemble rendered frames into one labelled contact sheet (needs Pillow).

usage: python tools/contact_sheet.py out.png frame1.png frame2.png ... [--cols N]
"""

from __future__ import annotations

import re
import sys

from PIL import Image, ImageDraw

args = sys.argv[1:]
cols = 4
if "--cols" in args:
    i = args.index("--cols")
    cols = int(args[i + 1])
    del args[i : i + 2]
out, files = args[0], args[1:]
imgs = [Image.open(f).convert("RGB") for f in files]
w, h = imgs[0].size
scale = 0.62
tw, th = int(w * scale), int(h * scale)
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), "white")
d = ImageDraw.Draw(sheet)
for n, (img, f) in enumerate(zip(imgs, files)):
    x, y = (n % cols) * tw, (n // cols) * th
    sheet.paste(img.resize((tw, th)), (x, y))
    m = re.search(r"_(\d+)\.png$", f)
    d.text((x + 8, y + th - 18), f"frame {int(m.group(1)) if m else n}", fill="black")
sheet.save(out)
print(out, sheet.size)
