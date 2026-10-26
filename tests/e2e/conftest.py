"""Playwright fixtures: serve the UX harness on the scripted agent and open the window."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = REPO_ROOT / "examples" / "e2e_ux_harness.py"
MANAGED_HARNESS = REPO_ROOT / "examples" / "e2e_managed_harness.py"


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
def workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The agent's working folder, outside the repository."""
    folder = tmp_path_factory.mktemp("coco_e2e") / "work"
    folder.mkdir()
    (folder / "README.md").write_text("# Alpha\n\nTODO: scope\n", encoding="utf-8")
    return folder


def _serve(harness: Path, workspace: Path) -> Iterator[str]:
    port = _free_port()
    env = os.environ.copy()
    env.update(
        STREAMLIT_COCO_AGENT="mock",
        COCO_E2E_WORKSPACE=str(workspace),
        STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
        STREAMLIT_SERVER_HEADLESS="true",
    )
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(harness),
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(workspace.parent),  # not the repository
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


@pytest.fixture(scope="session")
def base_url(workspace: Path) -> Iterator[str]:
    yield from _serve(HARNESS, workspace)


@pytest.fixture(scope="session")
def managed_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The managed harness's working folder (it holds nothing the agent reads)."""
    folder = tmp_path_factory.mktemp("coco_e2e_managed") / "work"
    folder.mkdir()
    return folder


@pytest.fixture(scope="session")
def managed_url(managed_workspace: Path) -> Iterator[str]:
    yield from _serve(MANAGED_HARNESS, managed_workspace)


def _open(page, url: str):
    page.goto(url, wait_until="domcontentloaded")
    page.get_by_role("button", name="Ask CoCo").first.click(timeout=30_000)
    return page


@pytest.fixture
def window(page, base_url: str):
    """The window with attachments and display switches, open."""
    return _open(page, base_url)


@pytest.fixture
def default_window(page, base_url: str):
    """The default window (no features switched on), open."""
    return _open(page, f"{base_url}/?mode=default")


class Ask:
    """What a test does in the window."""

    def __init__(self, page) -> None:
        self.page = page

    def connect(self) -> None:
        self.page.get_by_role("button", name="Connect mock").click()
        self.page.get_by_role("textbox", name="Ask CoCo").wait_for()
        self.page.wait_for_timeout(1_500)  # the scripted connection settles

    def say(self, text: str) -> None:
        field = self.page.get_by_role("textbox", name="Ask CoCo")
        field.fill(text)
        field.press("Enter")  # Send is the Stop button while CoCo works

    def thread(self) -> str:
        return self.page.get_by_role("log").first.inner_text()

    def menu(self, item: str) -> None:
        self.page.get_by_role("button", name="CoCo menu").click()
        self.page.get_by_role("menuitem", name=item).or_(
            self.page.get_by_role("menuitemcheckbox", name=item)
        ).first.click()


@pytest.fixture
def ask(page) -> Ask:
    return Ask(page)
