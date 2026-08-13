#!/usr/bin/env python3
"""Render an SVG to PNG at 2x via headless Chromium (Playwright).

Usage:
    .venv/bin/python scripts/render_svg.py path/to/visual.svg [out.png] [--scale 2]

Used for marketing visuals in doc-dev/ — keeps the SVG as the source of truth.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _viewbox_size(svg: str) -> tuple[float, float]:
    match = re.search(r'viewBox\s*=\s*"([^"]+)"', svg)
    if not match:
        raise SystemExit("SVG has no viewBox; cannot infer size.")
    parts = [float(p) for p in match.group(1).replace(",", " ").split()]
    if len(parts) != 4:
        raise SystemExit(f"Unexpected viewBox: {match.group(1)!r}")
    return parts[2], parts[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("out", type=Path, nargs="?")
    parser.add_argument("--scale", type=float, default=2.0)
    args = parser.parse_args()

    svg_path = args.svg.resolve()
    out_path = (args.out or svg_path.with_suffix(".png")).resolve()
    svg = svg_path.read_text(encoding="utf-8")
    width, height = _viewbox_size(svg)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": int(width), "height": int(height)},
            device_scale_factor=args.scale,
        )
        # A standalone SVG document has no <head>/<body>, so inline it in HTML.
        page.set_content(
            "<style>html,body{margin:0;padding:0}"
            f"svg{{display:block;width:{width}px;height:{height}px}}</style>" + svg,
            wait_until="load",
        )
        page.screenshot(path=str(out_path))
        browser.close()

    print(f"{out_path} — {int(width * args.scale)}x{int(height * args.scale)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
