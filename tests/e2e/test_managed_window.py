"""E2E: the window on the managed agent (a scripted stand-in for Snowflake's client, no login).

What is proven in a browser: the first screen does not claim to read project files of this
computer; a command that asks says it runs in the Snowflake sandbox, and only Allow lets it go;
every decision lands in the audit log; an attached file goes to the stage and the agent is told its
sandbox path (never the local one), with no copy left in the working folder.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

WAIT = 20_000
FIELD = "textbox"


@pytest.fixture
def managed(page, managed_url: str):
    page.goto(managed_url, wait_until="domcontentloaded")
    page.get_by_role("button", name="Ask CoCo").first.click(timeout=30_000)
    page.get_by_role(FIELD, name="Ask CoCo").wait_for(timeout=WAIT)  # connected on its own
    page.wait_for_timeout(1_000)
    return page


def say(page, text: str) -> None:
    field = page.get_by_role(FIELD, name="Ask CoCo")
    field.fill(text)
    field.press("Enter")


def audit(managed_workspace: Path) -> list[dict]:
    path = managed_workspace.parent / "managed-audit.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_the_first_screen_does_not_claim_to_read_project_files(managed) -> None:
    page = managed
    page.get_by_text("Snowflake sandbox").first.wait_for(timeout=WAIT)
    assert "project files" not in page.get_by_role("dialog").first.inner_text()


def test_a_message_gets_an_answer(managed) -> None:
    say(managed, "hello there")
    managed.get_by_text("Echo: hello there").first.wait_for(timeout=WAIT)


def test_a_command_asks_in_the_sandbox_and_runs_only_after_allow(
    managed, managed_workspace: Path
) -> None:
    page = managed
    say(page, "run a risky command")
    page.get_by_role("button", name="Allow", exact=True).wait_for(timeout=WAIT)
    card = page.get_by_role("dialog").first.inner_text()
    assert "Snowflake sandbox" in card
    assert managed_workspace.name not in card  # no local folder in the "Where" line
    assert "The command ran" not in card
    page.get_by_role("button", name="Allow", exact=True).click()
    page.get_by_text("The command ran.").first.wait_for(timeout=WAIT)
    page.get_by_role("button", name="Send", exact=True).wait_for(timeout=WAIT)
    rows = [r for r in audit(managed_workspace) if r["tool"] == "Bash"]
    allowed = [r for r in rows if r["decision"] == "allowed"]
    assert allowed and allowed[-1]["who"] == "e2e"
    assert "rm -rf /workspace/build" in json.dumps(allowed[-1]["evidence"])
    done = [
        r for r in rows if r["decision"] == "outcome" and r["tool_id"] == allowed[-1]["tool_id"]
    ]
    assert [r["outcome"] for r in done] == ["succeeded"]  # the result came back: it ran


def test_a_declined_command_is_not_run_and_is_logged(managed, managed_workspace: Path) -> None:
    page = managed
    say(page, "run a risky command")
    page.get_by_role("button", name="Decline").click(timeout=WAIT)
    page.get_by_text("Not run.").first.wait_for(timeout=WAIT)
    assert [r["decision"] for r in audit(managed_workspace)][-1] == "declined"


def test_an_attached_file_goes_to_the_stage_not_the_folder(
    managed, managed_workspace: Path, tmp_path: Path
) -> None:
    page = managed
    sample = tmp_path / "sales_e2e.csv"
    sample.write_text("x,y\n3,4\n", encoding="utf-8")
    page.locator("section.cc input[type=file]").set_input_files(str(sample))
    page.get_by_text("sales_e2e.csv").first.wait_for(timeout=WAIT)
    say(page, "what is in the file")
    page.get_by_text("/uploads/", exact=False).first.wait_for(timeout=WAIT)
    thread = page.get_by_role("log").first.inner_text()
    assert "sales_e2e.csv" in thread
    assert str(managed_workspace) not in thread
    assert not list(managed_workspace.glob("_coco_uploads/**/*.csv"))
