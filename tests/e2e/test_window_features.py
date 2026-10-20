"""E2E: the window's code block, display switch, attachments and the page's own uploader."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

WAIT = 20_000


def test_code_block_has_its_own_copy(window, ask) -> None:
    page = window
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    ask.connect()
    ask.say("codeblock please")
    page.get_by_role("button", name="Copy code").first.click(timeout=WAIT)
    assert "select customer" in page.evaluate("navigator.clipboard.readText()")
    assert page.get_by_role("button", name="Copy answer").count() >= 1


def test_latest_exchange_only(window, ask) -> None:
    page = window
    ask.connect()
    for text in ("first question", "second question", "third question"):
        ask.say(text)
        page.get_by_text(f"You wrote: {text}").wait_for(timeout=WAIT)
    assert "first question" in ask.thread()
    ask.menu("Latest exchange only")
    page.wait_for_function(
        "() => ![...document.querySelectorAll('[role=log]')]"
        ".some(l => l.innerText.includes('first question'))",
        timeout=WAIT,
    )
    assert "third question" in ask.thread()


def test_attached_file_lands_in_the_folder(window, ask, workspace: Path, tmp_path: Path) -> None:
    page = window
    ask.connect()
    sample = tmp_path / "attached_e2e.csv"
    sample.write_text("x,y\n3,4\n", encoding="utf-8")
    page.locator("section.cc input[type=file]").set_input_files(str(sample))
    page.get_by_text("attached_e2e.csv").first.wait_for(timeout=WAIT)
    ask.say("what is in the file")
    for _ in range(40):  # the file is saved when the message is sent
        if list(workspace.glob("_coco_uploads/*/attached_e2e.csv")):
            break
        page.wait_for_timeout(500)
    assert list(workspace.glob("_coco_uploads/*/attached_e2e.csv"))


def test_page_cwd_uploader(window, workspace: Path, tmp_path: Path) -> None:
    sample = tmp_path / "e2e_sample.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")
    window.set_input_files('section[data-testid="stSidebar"] input[type="file"]', str(sample))
    window.get_by_text("Saved", exact=False).first.wait_for(timeout=WAIT)
    assert (workspace / "_uploads" / "e2e_sample.csv").read_text() == "a,b\n1,2\n"
