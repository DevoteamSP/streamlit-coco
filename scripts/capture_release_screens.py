"""Capture the release screenshots of the window on the scripted agent (no Snowflake login).

usage: .venv/bin/python scripts/capture_release_screens.py [out_dir] [shot ...]
       (needs the e2e extra: `uv run --extra e2e python scripts/capture_release_screens.py`)

shots: split full hint (the three of 0.2.2, by default) · hero minimize simple (those of 0.2.0) ·
managed (0.3.0: hero, 01-first-screen, 02-attach and 03-audit: the window on the managed agent) ·
shop (0.3.0: 04-shop-library: the Skills shop on its sample skills).
`out_dir` defaults to doc/releases/<version>/screenshots (the version of pyproject.toml). The files
are the ones doc/releases/<version>/screenshots/README.md lists. 0.2.2: hero.png (split),
01-full-page.png, 02-hint.png.

The servers run with a throw-away HOME (/tmp/coco_demo) that holds one dummy connection profile
and a link to the cortex program, so neither a real profile name nor the maintainer's path reaches a
picture. Only the window runs on the scripted agent: the Copilot column is shown not connected.
The window's theme font is named in examples/modern_chat/app.py, not "inherit" (see the roadmap).
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
_VERSION = re.search(r'^version = "([^"]+)"', (REPO / "pyproject.toml").read_text(), re.M)
_ARGS = sys.argv[1:]
_SHOT_NAMES = {"split", "full", "hint", "hero", "minimize", "simple", "managed", "shop"}
OUT = (
    Path(_ARGS.pop(0)).resolve()
    if _ARGS and _ARGS[0] not in _SHOT_NAMES
    else REPO / "doc" / "releases" / (_VERSION.group(1) if _VERSION else "next") / "screenshots"
)
SHOTS = _ARGS or ["split", "full", "hint"]
OUT.mkdir(parents=True, exist_ok=True)
WIDE = {"width": 1440, "height": 1000}
SIMPLE = {"width": 1440, "height": 900}
HOME = Path("/tmp/coco_demo")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def neutral_home() -> None:
    shutil.rmtree(HOME, ignore_errors=True)
    (HOME / ".snowflake").mkdir(parents=True)
    (HOME / ".snowflake" / "connections.toml").write_text(
        '[demo]\naccount = "example"\nuser = "demo"\n', encoding="utf-8"
    )
    (HOME / ".local" / "bin").mkdir(parents=True)
    real = shutil.which("cortex")
    if real:
        (HOME / ".local" / "bin" / "cortex").symlink_to(real)


def serve(script: str, **extra: str) -> tuple[subprocess.Popen, str]:
    port = free_port()
    env = {
        **os.environ,
        "HOME": str(HOME),
        "PATH": f"{HOME / '.local' / 'bin'}{os.pathsep}{os.environ['PATH']}",
        "STREAMLIT_COCO_AGENT": "mock",
        "STREAMLIT_COCO_MOCK_PROFILES": "demo",
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        "STREAMLIT_SERVER_HEADLESS": "true",
        **extra,
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            script,
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(150):
        try:
            urllib.request.urlopen(url, timeout=2)
            return proc, url
        except Exception:  # noqa: BLE001
            time.sleep(0.4)
    proc.kill()
    raise RuntimeError(f"{script} did not start")


def settle(page, ms: int = 900) -> None:
    page.wait_for_timeout(ms)


def open_window(page) -> None:
    page.get_by_role("button", name="Ask CoCo").first.click(timeout=30_000)


def connect(page) -> None:
    page.get_by_role("button", name=re.compile(r"^Connect demo")).click(timeout=30_000)
    page.get_by_role("textbox", name="Ask CoCo").wait_for()
    settle(page, 1_800)


def say(page, text: str) -> None:
    field = page.get_by_role("textbox", name="Ask CoCo")
    field.fill(text)
    field.press("Enter")


def both(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded")
    page.get_by_text("Both", exact=True).first.click(timeout=30_000)
    settle(page, 1500)


def ask_coco_page(page, url: str, *, split: bool) -> None:
    """modern_chat on its first surface (Ask CoCo), the window open and connected."""
    page.goto(url, wait_until="domcontentloaded")
    page.get_by_text("Split" if split else "Overlay", exact=True).first.click(timeout=30_000)
    settle(page, 1500)
    open_window(page)
    connect(page)


def audit_png(browser, path: Path, out: Path) -> None:
    """The audit file as a picture: its lines, as the application wrote them."""
    import html
    import json

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    body = "\n".join(html.escape(json.dumps(r, ensure_ascii=False)) for r in rows[-2:])
    page = browser.new_context(
        viewport={"width": 1000, "height": 330}, device_scale_factor=2
    ).new_page()
    page.set_content(
        "<body style='margin:0;background:#17181c;color:#e8e8ea;padding:28px;"
        "font:14px/1.6 ui-monospace,Menlo,monospace'>"
        "<div style='color:#8b8f99;margin-bottom:12px;font:600 13px system-ui'>"
        "logs/coco-audit.jsonl</div>"
        f"<pre style='margin:0;white-space:pre-wrap;word-break:break-all'>{body}</pre>"
    )
    page.screenshot(path=str(out))
    page.close()


def stitch(left: Path, right: Path, out: Path) -> None:
    from PIL import Image

    a, b = Image.open(left).convert("RGB"), Image.open(right).convert("RGB")
    half = (a.width // 2, a.height // 2)
    a, b = a.resize(half, Image.LANCZOS), b.resize(half, Image.LANCZOS)
    gap = 24
    sheet = Image.new("RGB", (a.width + gap + b.width, a.height), (205, 208, 214))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width + gap, 0))
    sheet.save(out, optimize=True)


def main() -> None:
    neutral_home()
    procs = []
    try:
        modern_url = simple_url = managed_url = shop_url = ""
        if {"split", "full", "hint", "hero", "minimize"} & set(SHOTS):
            modern, modern_url = serve("examples/modern_chat/app.py")
            procs.append(modern)
        if "simple" in SHOTS:
            simple, simple_url = serve("examples/chat_app.py")
            procs.append(simple)
        if "managed" in SHOTS:
            managed, managed_url = serve(
                "examples/e2e_managed_harness.py", COCO_E2E_WORKSPACE=str(HOME / "work")
            )
            procs.append(managed)
        if "shop" in SHOTS:
            shop, shop_url = serve("examples/skills_hub/app.py")
            procs.append(shop)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:  # noqa: BLE001
                browser = p.chromium.launch(channel="msedge")
            ctx = browser.new_context(viewport=WIDE, device_scale_factor=2, color_scheme="light")
            page = ctx.new_page()

            if {"split", "full", "hint"} & set(SHOTS):
                page.set_viewport_size(WIDE)
            if "split" in SHOTS:  # hero.png: the window attached to the right, the page beside it
                ask_coco_page(page, modern_url, split=True)
                say(page, "reads")
                page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=20_000)
                page.get_by_role("button", name="Attach to the right").click()
                page.get_by_text("Window place").first.wait_for(timeout=20_000)
                page.mouse.move(300, 900)  # no hint in the picture
                settle(page, 2000)
                page.screenshot(path=str(OUT / "hero.png"))

            if "full" in SHOTS:  # 01-full-page.png: the window on the whole page
                ask_coco_page(page, modern_url, split=False)
                say(page, "reads")
                page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=20_000)
                page.get_by_role("button", name="Full page").click()
                page.mouse.move(300, 900)
                settle(page, 1500)
                page.screenshot(path=str(OUT / "01-full-page.png"))

            if "hint" in SHOTS:  # 02-hint.png: the title bar, a hint under the pressed icon
                ask_coco_page(page, modern_url, split=False)
                page.get_by_role("button", name="Attach to the right").click()
                settle(page, 1500)
                page.get_by_role("button", name="Floating window").hover()
                page.wait_for_function(
                    "() => [...document.querySelectorAll('*')].some(e => e.shadowRoot && "
                    "[...e.shadowRoot.querySelectorAll('[data-a=layout]')].some(b => "
                    "getComputedStyle(b, '::after').visibility === 'visible'))",
                    timeout=5_000,
                )
                settle(page, 400)
                box = page.viewport_size
                page.screenshot(
                    path=str(OUT / "02-hint.png"),
                    clip={"x": box["width"] - 520, "y": 0, "width": 520, "height": 150},
                )

            if "hero" in SHOTS:
                both(page, modern_url)
                open_window(page)
                connect(page)
                say(page, "What is the git status of this folder?")
                page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=20_000)
                settle(page)
                page.screenshot(path=str(OUT / "hero.png"))

            if "managed" in SHOTS:  # 0.3.0: the window on the managed agent
                page.set_viewport_size(WIDE)
                window_box = {"x": 940, "y": 385, "width": 500, "height": 610}
                page.goto(managed_url, wait_until="domcontentloaded")
                open_window(page)
                page.get_by_role("textbox", name="Ask CoCo").wait_for(timeout=30_000)
                settle(page, 1500)
                page.screenshot(path=str(OUT / "01-first-screen.png"), clip=window_box)
                say(page, "run a risky command")  # hero.png: a command waits for Allow
                page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=20_000)
                page.mouse.move(300, 900)
                settle(page, 1200)
                page.screenshot(path=str(OUT / "hero.png"))
                page.get_by_role("button", name="Allow", exact=True).click()
                page.get_by_text("The command ran.").first.wait_for(timeout=20_000)
                settle(page, 800)
                audit_png(browser, HOME / "managed-audit.jsonl", OUT / "03-audit.png")

                page.goto(managed_url, wait_until="domcontentloaded")  # 02-attach.png
                open_window(page)
                page.get_by_role("textbox", name="Ask CoCo").wait_for(timeout=30_000)
                sample = HOME / "orders_q3.csv"
                sample.write_text("item,qty\nwidget,3\ngadget,4\n", encoding="utf-8")
                page.locator("section.cc input[type=file]").set_input_files(str(sample))
                page.get_by_text("orders_q3.csv").first.wait_for(timeout=20_000)
                say(page, "what is in the file")
                page.get_by_text("/uploads/", exact=False).first.wait_for(timeout=20_000)
                page.mouse.move(300, 900)
                settle(page, 1200)
                page.screenshot(path=str(OUT / "02-attach.png"), clip=window_box)

            if "shop" in SHOTS:  # the Skills shop on its sample skills, a scripted chat
                page.set_viewport_size(WIDE)
                page.goto(shop_url, wait_until="domcontentloaded")
                page.get_by_role("button", name="Open").first.wait_for(timeout=30_000)
                settle(page, 1200)
                page.screenshot(path=str(OUT / "04-shop-library.png"))

            if "minimize" in SHOTS:
                both(page, modern_url)
                page.locator("button:has-text('minimize')").first.click(timeout=30_000)
                page.get_by_text("Minimized").first.wait_for(timeout=30_000)  # the rerun is done
                connect(page)  # Minimize opened the window, not connected yet
                page.get_by_text("What can CoCo do for you?").wait_for(timeout=30_000)
                page.mouse.move(600, 900)  # no tooltip in the picture
                settle(page, 1500)
                page.screenshot(path=str(OUT / "01-minimize.png"))

            if "simple" in SHOTS:
                page2 = browser.new_context(
                    viewport=SIMPLE, device_scale_factor=2, color_scheme="light"
                ).new_page()
                page2.goto(simple_url, wait_until="domcontentloaded")
                page2.get_by_text("Ask CoCo", exact=True).first.wait_for(timeout=30_000)
                settle(page2, 1500)
                page2.screenshot(path=str(OUT / "_simple_off.png"))
                page2.get_by_text("On", exact=True).first.click(timeout=30_000)
                settle(page2, 2000)
                page2.screenshot(path=str(OUT / "_simple_on.png"))
                stitch(OUT / "_simple_off.png", OUT / "_simple_on.png", OUT / "02-simple-chat.png")
                (OUT / "_simple_off.png").unlink()
                (OUT / "_simple_on.png").unlink()
            browser.close()
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(HOME, ignore_errors=True)


main()
