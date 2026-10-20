"""Capture the release screenshots of the window on the scripted agent (no Snowflake login).

usage: .venv/bin/python scripts/capture_release_screens.py [out_dir] [shot ...]
       (needs the e2e extra: `uv run --extra e2e python scripts/capture_release_screens.py`)

shots: hero minimize simple (all three by default). `out_dir` defaults to
doc/releases/<version>/screenshots (the version of pyproject.toml). The files are the ones
doc/releases/<version>/screenshots/README.md lists: hero.png, 01-minimize.png, 02-simple-chat.png.

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
_SHOT_NAMES = {"hero", "minimize", "simple"}
OUT = (
    Path(_ARGS.pop(0)).resolve()
    if _ARGS and _ARGS[0] not in _SHOT_NAMES
    else REPO / "doc" / "releases" / (_VERSION.group(1) if _VERSION else "next") / "screenshots"
)
SHOTS = _ARGS or ["hero", "minimize", "simple"]
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


def serve(script: str) -> tuple[subprocess.Popen, str]:
    port = free_port()
    env = {
        **os.environ,
        "HOME": str(HOME),
        "PATH": f"{HOME / '.local' / 'bin'}{os.pathsep}{os.environ['PATH']}",
        "STREAMLIT_COCO_AGENT": "mock",
        "STREAMLIT_COCO_MOCK_PROFILES": "demo",
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        "STREAMLIT_SERVER_HEADLESS": "true",
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
        modern, modern_url = serve("examples/modern_chat/app.py")
        procs.append(modern)
        simple, simple_url = serve("examples/chat_app.py")
        procs.append(simple)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:  # noqa: BLE001
                browser = p.chromium.launch(channel="msedge")
            ctx = browser.new_context(viewport=WIDE, device_scale_factor=2, color_scheme="light")
            page = ctx.new_page()

            if "hero" in SHOTS:
                both(page, modern_url)
                open_window(page)
                connect(page)
                say(page, "What is the git status of this folder?")
                page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=20_000)
                settle(page)
                page.screenshot(path=str(OUT / "hero.png"))

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
