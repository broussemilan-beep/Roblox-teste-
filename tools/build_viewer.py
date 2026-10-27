"""Build a self-contained HTML viewer for a scene: ``python tools/build_viewer.py``.

Writes ``viewer/output/<scene>.html`` (data inlined, no external requests).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.scenes import SCENES  # noqa: E402
from tsb_engine.scene import export_viewer_data  # noqa: E402


def to_artifact(html: str) -> str:
    """Strip the document wrapper: the Artifact host adds its own skeleton."""
    import re

    html = re.sub(r"<!doctype html>\s*", "", html, flags=re.I)
    html = re.sub(r"</?(html|head|body)[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r'<meta charset="utf-8">\s*', "", html)
    html = re.sub(r'<meta name="viewport"[^>]*>\s*', "", html)
    return html.replace(
        "</title>", '</title>\n<meta name="claude:viewport-fit-sides" content="cover">', 1
    )


def build(name: str) -> Path:
    scene = SCENES[name]()
    template = (ROOT / "viewer" / "viewer.template.html").read_text(encoding="utf-8")
    data = json.dumps(export_viewer_data(scene), separators=(",", ":"))
    out = ROOT / "viewer" / "output" / f"{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = template.replace("/*__DATA__*/null", data)
    out.write_text(html, encoding="utf-8")
    out.with_suffix(".artifact.html").write_text(to_artifact(html), encoding="utf-8")
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCENES)
    for n in names:
        path = build(n)
        print(f"{n}: {path} ({path.stat().st_size // 1024} KiB)")
