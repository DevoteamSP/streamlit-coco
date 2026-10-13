"""Build standalone consultation pages without changing the original canvas files."""

from __future__ import annotations

import json
import re
from pathlib import Path


def build() -> None:
    design = Path(__file__).resolve().parent
    source = design / "canvas" / "project"
    output = design / "preview"
    output.mkdir(exist_ok=True)
    manifest = json.loads((source / "canvas.json").read_text(encoding="utf-8"))
    for name in manifest["order"]:
        page = (source / name).read_text(encoding="utf-8")
        page = re.sub(r'<script\b[^>]*src="\./support\.js"[^>]*></script>\s*', "", page)
        page = re.sub(
            r'<script\b[^>]*type="text/x-dc"[^>]*>.*?</script>', "", page, flags=re.DOTALL
        )
        page = re.sub(
            r'href="(cockpit(?:22)?\.css|coco22\.css)"', r'href="../canvas/project/\1"', page
        )
        # Cockpit navigation only illustrates the host; those mockups are not in this canvas.
        page = re.sub(
            r'href="([^"]+\.dc\.html)"', r'aria-disabled="true" data-mockup-target="\1"', page
        )
        (output / name).write_text(page, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
