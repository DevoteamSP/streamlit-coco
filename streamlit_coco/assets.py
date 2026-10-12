"""Ask CoCo, the window's files: coco.js and coco.css, the feature parts in a fixed order, the font.

Pure Python (no Streamlit), so that the test harness (streamlit_coco.testing.harness) mounts
exactly what the app serves. A part is static/coco/parts/<group>.js and <group>.css; coco.js
documents what a part may register. The Montserrat files (static/fonts, OFL licence beside them)
are appended to the script as one constant: a shadow root does not register its own @font-face,
so the script adds the faces to the page's font set when the window starts. No request leaves
the browser.
"""

from __future__ import annotations

import base64
import json
import re
from functools import lru_cache
from pathlib import Path

STATIC = Path(__file__).resolve().parent / "static"
DIR = STATIC / "coco"
FONTS = STATIC / "fonts"
WEIGHTS = (400, 500, 600)
# The groups of the design sheet, in the order they are appended (an earlier decorator runs first)
GROUPS = ("questions", "plans", "standing", "data", "files", "page", "session")


def _join(core: str, folder: str) -> str:
    parts = [(DIR / "parts" / f"{group}.{folder}").read_text(encoding="utf-8") for group in GROUPS]
    return "\n".join([(DIR / core).read_text(encoding="utf-8"), *parts])


@lru_cache(maxsize=1)
def fonts_js() -> str:
    faces = {
        w: base64.b64encode((FONTS / f"Montserrat-{w}.ttf").read_bytes()).decode() for w in WEIGHTS
    }
    return f"\nconst COCO_FONTS = {json.dumps(faces)};\n"


def js(with_fonts: bool = True) -> str:
    return _join("coco.js", "js") + (fonts_js() if with_fonts else "")


def css() -> str:
    return _join("coco.css", "css")


@lru_cache(maxsize=1)
def spark() -> str:
    """The official mark's path, not redrawn."""
    found = re.search(r' d="([^"]+)"', (DIR / "coco-logo.svg").read_text(encoding="utf-8"))
    assert found, "coco-logo.svg has no path"
    return found.group(1)
