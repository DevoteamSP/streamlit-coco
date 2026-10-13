# ruff: noqa: E501
"""Ask CoCo, the window on fixtures, with no server: one HTML file to open in a browser and to screenshot.

    python -m streamlit_coco.testing.harness f38_question_choice f48 [--out FILE] [--width 460] [--height 780] [--rem 14.4] [--shot FILE.png]

Writes one HTML file (its path is printed) that mounts the real window (static/coco/coco.js, the feature parts of
static/coco/parts/ and coco.css, exactly what streamlit_coco.assets serves) on the named fixtures of
streamlit_coco.testing.fixtures, side by side, each in its own frame, the window open (CLOSED fixtures: the launcher), at
--rem pixels to the rem (14.4 is a 1440 px screen). Nothing of a host is around it: no tokens, no font file, the window's own
defaults (CSS variables of coco.css, Montserrat from the package). A name may be a frame number: f38 or 38. After the window is
mounted the fixture's TYPING and UI, then its GESTURES, are played on it as a user would (clicks, typing, attaching), so the
page shows the state the sheet's frame shows. `labels_` and `theme` of page() play what a host passes to ask_coco.

It needs no Streamlit and no server. The window talks to nobody: an action it sends is recorded in the frame's
`window.__actions` and acknowledged. Open the file with Playwright (installed Edge channel), wait for `window.__cocoReady`,
screenshot `iframe` n, read `frames[n].__actions` / `frames[n].__log`. --shot does that for the whole page.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from streamlit_coco import assets, labels  # noqa: E402
from streamlit_coco.testing import fixtures as fx  # noqa: E402

WIDE = 1010  # a fixture that opens the wider view needs the room
# what the window's own state needs before the sheet's frame is reached (the fixture's UI dict, see coco_ui_fixtures.py)
UI_GESTURES = {"menu": [["press", "CoCo menu"]], "confirm": None}


def resolve(name: str) -> str:
    if name in fx.VIEWS:
        return name
    match = re.fullmatch(r"f?(\d+)", name)
    found = [key for key in fx.VIEWS if match and re.match(rf"f{int(match.group(1))}_", key)]
    if len(found) != 1:
        close = [key for key in fx.VIEWS if name.lower() in key.lower()][:8]
        raise SystemExit(
            f"No fixture '{name}'."
            + (
                f" Did you mean: {', '.join(close)}?"
                if close
                else " Names are the keys of VIEWS in streamlit_coco/testing/fixtures.py."
            )
        )
    return found[0]


def gestures(name: str) -> list[list]:
    steps: list[list] = []
    ui = fx.UI.get(name, {})
    if ui.get("menu"):
        steps.append(["press", "CoCo menu"])
    if ui.get("confirm"):
        steps += [
            ["press", "CoCo menu"],
            ["press", "Disconnect" if ui["confirm"] == "disc" else "New conversation"],
        ]
    return steps + [list(step) for step in fx.GESTURES.get(name, [])]


def bundle() -> str:
    """The window as a classic script: the module's two exports become globals, nothing else changes."""
    code = assets.js()
    for old, new in (
        ("export function renderMarkdown", "function renderMarkdown"),
        ("export default function", "window.__cocoMount = function"),
    ):
        assert code.count(old) == 1, old
        code = code.replace(old, new)
    return code + "\n;"


FRAME_JS = r"""
const norm = (t) => String(t || '').replace(/\s+/g, ' ').trim();
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
window.__actions = []; window.__log = [];
(async () => {
  const host = document.getElementById('host'), shadow = host.attachShadow({ mode: 'open' });
  shadow.innerHTML = '<style>' + SHEET + '</style><div class="coco-root"></div>';
  const data = { view: VIEW, ack: 0, open_token: CLOSED ? 0 : 1, sess: 'harness', spark: SPARK, labels: HOST_LABELS, theme: HOST_THEME, features: {}, exclude: [] };
  const trigger = (key, action) => {   // the Cockpit's answer: the action is recorded and acknowledged, the view stays the fixture
    if (action && action.a !== 'poll') window.__actions.push(action);
    setTimeout(() => window.__cocoMount({ data: { ...data, ack: action ? action.seq : 0 }, parentElement: shadow, setTriggerValue: trigger }), 0);
  };
  window.__cocoMount({ data, parentElement: shadow, setTriggerValue: trigger });
  await wait(120);
  const q = (s, n = 0) => shadow.querySelectorAll(s)[n];
  const field = () => q('.fld textarea');
  if (TYPING && field()) { field().value = TYPING; field().dispatchEvent(new Event('input', { bubbles: true })); }
  window.focus();   // the frame is played as the one the user is in, once: a later focus move would close a menu
  for (const [kind, a, b, c] of GESTURES) {
    try {
      if (kind === 'press') {
        const all = [...shadow.querySelectorAll('button, label, summary, [role=menuitem], [role=menuitemcheckbox], [role=option], [role=radio], a')].filter((e) => !e.closest('[hidden]'));
        const exact = all.filter((e) => norm(e.textContent) === a || e.getAttribute('aria-label') === a);
        const hit = (exact.length ? exact : all.filter((e) => norm(e.textContent).startsWith(a) || (e.getAttribute('aria-label') || '').startsWith(a)))[b || 0];
        if (!hit) window.__log.push('press: nothing named ' + JSON.stringify(a)); else hit.click();
      } else if (kind === 'type') {
        const e = q(a, c || 0);
        if (!e) window.__log.push('type: no ' + a); else { e.focus(); e.value = b; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }
      } else if (kind === 'attach') {
        const input = q('input[type=file]');
        if (!input) { window.__log.push('attach: no file input'); } else {
          const dt = new DataTransfer();
          a.forEach(([name, size]) => { const f = new File(['x'], name); Object.defineProperty(f, 'size', { value: size }); dt.items.add(f); });
          input.files = dt.files; input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      } else if (kind === 'dragover') {
        const dt = new DataTransfer(); dt.items.add(new File(['x'], 'a.csv'));
        ['dragenter', 'dragover'].forEach((t) => (q('.cc') || host).dispatchEvent(new DragEvent(t, { bubbles: true, cancelable: true, dataTransfer: dt })));
      }
    } catch (e) { window.__log.push(kind + ': ' + e.message); }
    await wait(220);   // a click paints, and a menu or a panel moves focus on the next frame
  }
  await document.fonts.ready;
  await wait(150);
  window.__ready = true;
})();
"""


def frame_info(name: str) -> dict:
    return {
        "name": name,
        "view": fx.VIEWS[name],
        "closed": name in fx.CLOSED,
        "typing": fx.TYPING.get(name, ""),
        "gestures": gestures(name),
        "wide": any(step[:2] == ["press", "Open larger"] for step in gestures(name)),
    }


def page(
    names: list[str],
    width: int,
    height: int,
    rem: float,
    labels_: dict | None = None,
    theme: dict | None = None,
) -> str:
    frames = [frame_info(name) for name in names]
    payload = json.dumps(
        {
            "frames": frames,
            "css": assets.css(),
            "code": bundle(),
            "spark": assets.spark(),
            "rem": rem,
            "width": width,
            "height": height,
            "wide": WIDE,
            "labels": labels.table(labels_),
            "theme": theme or {},
        },
        ensure_ascii=True,
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Ask CoCo, fixtures: {", ".join(names)}</title>
<style>body{{margin:0;padding:16px;background:#e9e7e1;font:13px system-ui,sans-serif;color:#333}} main{{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}}
figure{{margin:0}} figcaption{{margin:0 0 6px;font-weight:600}} iframe{{border:1px solid #bbb;background:#fff;display:block}}</style></head>
<body><main id="m"></main>
<script>
const P = {payload};
const main = document.getElementById('m');
let left = P.frames.length;
window.__cocoReady = false;
P.frames.forEach((f, i) => {{
  const fig = document.createElement('figure'), cap = document.createElement('figcaption'), fr = document.createElement('iframe');
  cap.textContent = f.name; fr.width = f.wide ? P.wide : P.width; fr.height = P.height; fr.title = f.name;
  const script = 'const VIEW = ' + JSON.stringify(f.view).replace(/<\\/script/gi, '<\\\\/script') + ', CLOSED = ' + JSON.stringify(f.closed) + ', TYPING = ' + JSON.stringify(f.typing)
    + ', GESTURES = ' + JSON.stringify(f.gestures) + ', SPARK = ' + JSON.stringify(P.spark) + ', SHEET = ' + JSON.stringify(P.css)
    + ', HOST_LABELS = ' + JSON.stringify(P.labels) + ', HOST_THEME = ' + JSON.stringify(P.theme) + ';\\n';
  fr.srcdoc = '<!doctype html><html><head><meta charset="utf-8"><style>' + 'html{{font-size:' + P.rem + 'px !important}}'
    + 'body{{margin:0;height:100vh;background:#F6F5F2}}</style></head><body><div id="host"></div>'
    + '<script>' + P.code.replace(/<\\/script/gi, '<\\\\/script') + '<\\/script><script>' + script.replace(/<\\/script/gi, '<\\\\/script') +{json.dumps(FRAME_JS)} + '<\\/script></body></html>';
  fig.append(cap, fr); main.append(fig);
}});
const poll = setInterval(() => {{
  const frames = [...document.querySelectorAll('iframe')];
  if (frames.every((f) => f.contentWindow && f.contentWindow.__ready)) {{ clearInterval(poll); window.__cocoReady = true; }}
}}, 100);
</script></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "names", nargs="+", help="fixture names (keys of VIEWS) or frame numbers (f38, 38)"
    )
    parser.add_argument("--out", help="the HTML file to write (default: a temporary file)")
    parser.add_argument(
        "--width", type=int, default=460, help="frame width in px (a window is 27 rem wide)"
    )
    parser.add_argument("--height", type=int, default=780)
    parser.add_argument(
        "--rem",
        type=float,
        default=14.4,
        help="pixels to the rem (the app: 14 at 1366 px wide, 14.4 at 1440)",
    )
    parser.add_argument(
        "--shot", help="also screenshot the page to this PNG with Playwright (the installed Edge)"
    )
    args = parser.parse_args(argv)
    names = [resolve(name) for name in args.names]
    out = (
        Path(args.out)
        if args.out
        else Path(tempfile.mkdtemp(prefix="coco-harness-")) / "harness.html"
    )
    out.write_text(page(names, args.width, args.height, args.rem), encoding="utf-8")
    print(out)
    if args.shot:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge")
            tab = browser.new_page(
                viewport={
                    "width": max(args.width * len(names) + 80, 900),
                    "height": args.height + 80,
                }
            )
            tab.goto(out.as_uri())
            tab.wait_for_function("window.__cocoReady === true", timeout=30000)
            tab.screenshot(path=args.shot, full_page=True)
            browser.close()
        print(args.shot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
