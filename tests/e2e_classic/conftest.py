"""Playwright fixtures: the 0.1.9 chat family's helpers on a CoCo-free harness.

These browser tests are the ones 0.1.9 shipped (copy and highlight, transcript windowing,
uploads into ``cwd``). They run next to ``tests/e2e`` (the window) and have their own
harness, ``harness.py``, so the window's harness can change without touching them.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness.py"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict, playwright) -> dict:
    """Use the installed Edge when Playwright's Chromium is not installed."""
    if not Path(playwright.chromium.executable_path).exists():
        return {**browser_type_launch_args, "channel": "msedge"}
    return browser_type_launch_args


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(url: str, *, timeout: float = 60.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                if 200 <= resp.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_err = exc
            time.sleep(0.4)
    raise RuntimeError(f"Streamlit harness did not become ready at {url}: {last_err}")


@pytest.fixture(scope="session")
def base_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    workspace = tmp_path_factory.mktemp("coco_e2e_classic") / "work"
    workspace.mkdir()
    port = _free_port()
    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    env.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    env["COCO_E2E_WORKSPACE"] = str(workspace)
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(HARNESS),
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(workspace.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_http(url)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def harness_page(page, base_url: str):
    """Open harness and click Start."""
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.goto(base_url, wait_until="domcontentloaded")
    page.get_by_role("button", name="Start harness").click()
    page.get_by_text("Harness ready", exact=True).wait_for(timeout=30_000)
    page.locator('[data-testid="e2e-harness-ready"]').wait_for(state="attached", timeout=5_000)
    return page
