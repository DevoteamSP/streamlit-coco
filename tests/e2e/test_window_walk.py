"""E2E: a walk of the default window on the scripted agent, launcher to new conversation."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

WAIT = 20_000


def test_walk_of_the_default_window(default_window, ask, workspace: Path) -> None:
    page = default_window
    # Connect, send, steps
    ask.connect()
    ask.say("reads please")
    page.get_by_text("Read README.md").first.wait_for(state="attached", timeout=WAIT)  # in a fold
    page.get_by_text("I read the file").first.wait_for(timeout=WAIT)

    # A request allowed: the file is written only after Allow
    ask.say("write a note")
    allow = page.get_by_role("button", name="Allow", exact=True)
    allow.wait_for(timeout=WAIT)
    assert not (workspace / "coco_note.md").exists()
    allow.click()
    page.get_by_text("Allowed by you").first.wait_for(timeout=WAIT)
    assert (workspace / "coco_note.md").exists()

    # A request declined: the command is never run
    ask.say("unlisted")
    page.get_by_role("button", name="Decline").click(timeout=WAIT)
    page.get_by_text("Declined").first.wait_for(timeout=WAIT)
    page.get_by_role("button", name="Send", exact=True).wait_for(timeout=WAIT)  # the turn is over

    # Queue, take back, stop
    ask.say("slow read")
    page.get_by_role("button", name="Stop").wait_for(timeout=WAIT)
    ask.say("queued thought")
    page.get_by_text("Queued").first.wait_for(timeout=WAIT)
    page.get_by_role("button", name="Take back").first.click()
    expect(page.get_by_role("textbox", name="Ask CoCo")).to_have_value("queued thought")
    page.get_by_role("button", name="Stop").click()
    page.get_by_role("button", name="Send", exact=True).wait_for(timeout=WAIT)

    # A new conversation
    ask.menu("New conversation")
    page.get_by_role("button", name="Start new conversation").click()
    page.get_by_text("What can CoCo do for you?").wait_for(timeout=WAIT)
