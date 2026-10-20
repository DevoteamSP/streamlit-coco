"""Ask CoCo, the window before and after: the DOM of a fixture must not change unless meant.

    python -m streamlit_coco.testing.domdiff [--ref HEAD] [--only REGEX]
    python -m streamlit_coco.testing.domdiff --cockpit PATH/spec-first/cockpit [--only REGEX]

Needs Playwright and the installed Edge (no browser is downloaded). Prints `same <name>` or
`DIFF <name>` with the first difference; exit status 1 when anything differs.

Default mode: mounts the window as it was at --ref (coco.js and the parts of that commit) and as
it is now, on the fixtures that are not frames 38 to 86, plays their gestures and compares the DOM
of the window. What the seams add and leave empty (the slots .ag-top .ag-tk .ag-pan-host .ag-ftop
.ag-fleft), inline sizes, whitespace between tags and the first-session label are left out. A part
that changes an old frame's markup is a regression, not a feature.

--cockpit mode: the proof that moving the window into the package changed nothing. Every fixture
is rendered by the Cockpit's own harness (its coco.js, its tokens, its Montserrat) and by this
package's (defaults only), in two tabs of the same size. Compared: the DOM, the computed styles of
the launcher, the window, the request block and the composer (font family and size, colours,
radius, weight) and the size of those boxes. Left out: inline sizes, whitespace between tags.
The package's defaults name no host, so three sentences differ from the Cockpit's (COCKPIT_LABELS);
the package side passes the Cockpit's words through `labels=`, and those are the only allowed
differences: with them restored the result must be 0 differences.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from streamlit_coco import assets
from streamlit_coco.testing import fixtures as fx
from streamlit_coco.testing import harness

# The only sentences that differ between the package's defaults and the Cockpit's window: the
# defaults name no host. In --cockpit mode the package side passes the Cockpit's own words through
# `labels=`,
# which is what the Cockpit will do; every other difference is a failure.
COCKPIT_LABELS = {
    "window.offline": "No answer from the Cockpit yet. Trying again.",
    "window.first.not_installed_sub": "Ask whoever installs Cockpit for you to enable it.",
    "window.footer.package_missing": (
        "The assistant's package is not installed. Starting Cockpit with this command installs it:"
    ),
}
ROOT = Path(__file__).resolve().parents[2]
# states the playground added without a frame number: no "before" exists for them
ADDED = {"files_sending", "question_expired", "question_cancelled", "plan_expired"}
SLOTS = ".ag-top, .ag-tk, .ag-pan-host, .ag-ftop, .ag-fleft"
# compared besides the markup: the boxes a user sees first, and what a theme or a font would move
BOXES = (
    ".cl",
    ".cc",
    ".hd",
    ".rq",
    ".ag-ask",
    ".ag-q",
    ".fld",
    "textarea",
    ".msg.me",
    ".msg.md",
    ".b.k",
    ".emp .t",
)
PROPS = (
    "fontFamily",
    "fontSize",
    "fontWeight",
    "lineHeight",
    "color",
    "backgroundColor",
    "borderTopColor",
    "borderTopLeftRadius",
    "boxShadow",
    "letterSpacing",
)
DUMP = """([slots, boxes, props]) => [...document.querySelectorAll('iframe')].map((f) => {
  const shadow = f.contentDocument.getElementById('host').shadowRoot;
  const live = shadow.querySelector('.coco-root');
  const root = live.cloneNode(true);
  if (slots) root.querySelectorAll(slots).forEach((n) => n.remove());
  root.querySelectorAll('[style]').forEach((n) => n.removeAttribute('style'));
  const styles = {};
  for (const sel of boxes) {
    const n = [...live.querySelectorAll(sel)].find((e) => e.getClientRects().length);
    if (!n) continue;
    const cs = getComputedStyle(n), r = n.getBoundingClientRect();
    styles[sel] = Object.fromEntries(props.map((p) => [p, cs[p]]));
    styles[sel].box = [r.x, r.y, r.width, r.height].map((v) => v.toFixed(2)).join(' ');
  }
  return { html: root.innerHTML, cls: live.className, styles };
})"""


def tidy(html: str) -> str:
    return re.sub(r">\s+<", "><", html).replace('class="cl ex', 'class="cl')


def dump(page_html: str, browser, slots: str = "") -> list[dict]:
    page = Path(tempfile.mkdtemp(prefix="coco-domdiff-")) / "page.html"
    page.write_text(page_html, encoding="utf-8")
    tab = browser.new_page(viewport={"width": 1200, "height": 900})
    tab.goto(page.as_uri())
    tab.wait_for_function("window.__cocoReady === true", timeout=60000)
    tab.wait_for_timeout(500)
    result = tab.evaluate(DUMP, [slots, list(BOXES), list(PROPS)])
    tab.close()
    for item in result:
        item["html"] = tidy(item["html"])
    return result


def first_difference(before: dict, after: dict) -> str:
    a, b = before["html"], after["html"]
    if a != b:
        at = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        lo = max(0, at - 100)
        return f"\n  before: {a[lo : at + 150]}\n  after:  {b[lo : at + 150]}"
    if before["cls"] != after["cls"]:
        return f"\n  root class: {before['cls']!r} -> {after['cls']!r}"
    for sel in sorted(set(before["styles"]) | set(after["styles"])):
        x, y = before["styles"].get(sel), after["styles"].get(sel)
        if x != y:
            keys = [k for k in (x or {}) | (y or {}) if (x or {}).get(k) != (y or {}).get(k)]
            return f"\n  style of {sel}: " + "; ".join(
                f"{k}: {(x or {}).get(k)} -> {(y or {}).get(k)}" for k in keys
            )
    return ""


def ref_js(ref: str) -> str:
    """The window's script as it was at `ref` (coco.js, then the parts that existed)."""
    base = "streamlit_coco/static/coco"

    def show(path: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{ref}:{base}/{path}"],
            capture_output=True,
            encoding="utf-8",
        )
        return done.stdout if done.returncode == 0 else ""

    parts = [show(f"parts/{group}.js") for group in assets.GROUPS]
    return "\n".join(filter(None, [show("coco.js"), *parts])) + assets.fonts_js()


def compare_with_ref(args, browser) -> int:
    old = ref_js(args.ref)
    names = [
        n
        for n in fx.VIEWS
        if not re.match(r"f\d+_", n) and n not in ADDED and re.search(args.only, n)
    ]
    bad = 0
    for start in range(0, len(names), 6):
        batch = names[start : start + 6]
        originals = harness.assets.js
        try:
            harness.assets.js = lambda *_a, **_k: old
            before = dump(harness.page(batch, 460, 780, 14.4), browser, SLOTS)
        finally:
            harness.assets.js = originals
        after = dump(harness.page(batch, 460, 780, 14.4), browser, SLOTS)
        for name, one, other in zip(batch, before, after):
            if one["html"] == other["html"]:
                print("same", name)
                continue
            bad += 1
            print("DIFF", name, first_difference(one, other))
    print(f"{len(names)} fixtures, {bad} differ")
    return bad


def compare_with_cockpit(args, browser) -> int:
    cockpit = Path(args.cockpit).resolve()
    sys.path[:0] = [str(cockpit), str(cockpit / "tests")]
    import coco_harness as theirs  # the Cockpit's own harness: its tokens, font, coco.js

    names = [n for n in fx.VIEWS if re.search(args.only, n)]
    bad = 0
    for start in range(0, len(names), 6):
        batch = names[start : start + 6]
        before = dump(theirs.page(batch, 460, 780, 14.4), browser)
        after = dump(harness.page(batch, 460, 780, 14.4, labels_=COCKPIT_LABELS), browser)
        for name, one, other in zip(batch, before, after):
            diff = first_difference(one, other)
            if not diff:
                print("same", name)
                continue
            bad += 1
            print("DIFF", name, diff)
    print(f"{len(names)} fixtures, {bad} differ")
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="HEAD", help="the commit whose window is the reference")
    parser.add_argument(
        "--only", default="", help="only the fixtures whose name matches this regular expression"
    )
    parser.add_argument(
        "--cockpit", help="the Cockpit's folder (spec-first/cockpit): compare with its own window"
    )
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge")
        try:
            bad = (compare_with_cockpit if args.cockpit else compare_with_ref)(args, browser)
        finally:
            browser.close()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
