"""The 0.1.9 helpers behind the chat family, kept as they were tested in 0.1.9.

The chat family is the default UI. These tests pin the modules it is built on
(``ask_user``, ``sql_tool``, ``tool_extract``, ``tool_cards``, ``debug``).
"""

from __future__ import annotations

import asyncio

import pytest

from streamlit_coco.permissions import PermissionManager, build_can_use_tool


def test_is_debug_mode_env_and_session_state(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit_coco.debug import is_debug_mode

    monkeypatch.delenv("STREAMLIT_COCO_DEBUG", raising=False)
    monkeypatch.delenv("COCO_DEBUG", raising=False)
    assert is_debug_mode(session_state={}) is False
    assert is_debug_mode(session_state={"coco_debug": True}) is True

    monkeypatch.setenv("STREAMLIT_COCO_DEBUG", "1")
    assert is_debug_mode(session_state={}) is True


def test_is_ask_user_question_name_variants() -> None:
    from streamlit_coco.ask_user import is_ask_user_question

    assert is_ask_user_question("AskUserQuestion")
    assert is_ask_user_question("ask_user_question")
    assert is_ask_user_question("ask-user-question")
    assert not is_ask_user_question("Write")


def test_choice_labels_with_other() -> None:
    from streamlit_coco.ask_user import OTHER_OPTION_LABEL, choice_labels_with_other

    options = [
        {"label": "A — Comments only", "description": "docs"},
        {"label": "B — Rename helpers", "description": "rename"},
    ]
    labels = choice_labels_with_other(options)
    assert labels[-1] == OTHER_OPTION_LABEL
    assert len(labels) == 3

    with_other = [
        *options,
        {"label": "Other", "description": "custom", "freeForm": True},
    ]
    assert OTHER_OPTION_LABEL not in choice_labels_with_other(with_other)
    assert choice_labels_with_other(with_other)[-1].startswith("Other")


def test_grep_match_lines_skips_summary_header() -> None:
    from streamlit_coco.tool_cards import _grep_match_lines

    text = "Grepped: 'TODO|FIXME'\n/tmp/a.py:1: # TODO fix\n/tmp/b.py:2: FIXME later\n"
    assert _grep_match_lines(text) == [
        "/tmp/a.py:1: # TODO fix",
        "/tmp/b.py:2: FIXME later",
    ]


def test_choice_labels_moves_something_else_last() -> None:
    from streamlit_coco.ask_user import choice_labels_with_other

    options = [
        {"label": "Markdown", "description": "Plain-text formatted report"},
        {"label": "CSV", "description": "Comma-separated values"},
        {"label": "HTML", "description": "Web page formatted report"},
        {
            "label": "Something else",
            "description": "Type your own feedback",
            "freeForm": True,
        },
        {
            "label": "I need clarification, let's chat about this",
            "description": "Submit current answers and discuss",
        },
        {"label": "Next", "description": "Move to the next question"},
    ]
    labels = choice_labels_with_other(options)
    assert [label.split(" — ")[0] for label in labels] == [
        "Markdown",
        "CSV",
        "HTML",
        "I need clarification, let's chat about this",
        "Next",
        "Something else",
    ]
    assert labels[-1].startswith("Something else")


def test_sql_tool_helpers() -> None:
    from streamlit_coco.sql_tool import (
        extract_sql_text,
        is_sql_tool,
        parse_sql_result_table,
    )
    from streamlit_coco.tool_names import ToolFamily, is_exit_plan_mode, tool_family

    assert is_sql_tool("SQL")
    assert is_sql_tool("sql_execute")
    assert is_sql_tool("SqlExecute")
    assert not is_sql_tool("Bash")
    assert tool_family("Read") == ToolFamily.READ
    assert tool_family("mcp__foo") == ToolFamily.GENERIC
    assert is_exit_plan_mode("ExitPlanMode")

    assert extract_sql_text({"query": "SELECT 1"}) == "SELECT 1"
    assert extract_sql_text({"command": "SHOW TABLES"}) == "SHOW TABLES"
    assert extract_sql_text({"input": {"sql": "SELECT 2"}}) == "SELECT 2"

    rows, text, total = parse_sql_result_table(
        [{"NAME": "A"}, {"NAME": "B"}],
    )
    assert rows == [{"NAME": "A"}, {"NAME": "B"}]
    assert text is None
    assert total == 2

    rows, text, total = parse_sql_result_table(
        '{"rows": [{"X": 1}], "row_count": 1}',
    )
    assert rows == [{"X": 1}]
    assert total == 1

    rows, text, total = parse_sql_result_table("plain failure")
    assert rows is None
    assert text == "plain failure"


def test_tool_extract_path_and_edit() -> None:
    from streamlit_coco.tool_extract import (
        extract_old_new,
        extract_path,
        language_for_path,
        unified_diff,
    )

    assert extract_path({"file_path": "a.py"}) == "a.py"
    assert language_for_path("x.sql") == "sql"
    assert extract_old_new({"old_string": "a", "new_string": "b"}) == ("a", "b")
    diff = unified_diff("hello\n", "hello\nworld\n", path="a.txt")
    assert "--- a/a.txt" in diff
    assert "+++ b/a.txt" in diff
    assert "+world" in diff


@pytest.mark.asyncio
async def test_ask_user_question_requires_answers() -> None:
    from streamlit_coco.ask_user import build_answers_payload

    manager = PermissionManager(approval_timeout_seconds=2.0)
    can_use_tool = build_can_use_tool(manager, [], auto_allow_tools=["Read"])
    questions = [
        {
            "header": "Scope",
            "question": "Which refactor?",
            "multiSelect": False,
            "options": [
                {"label": "A — Comments only", "description": "docs only"},
                {"label": "B — Rename helpers", "description": "rename"},
            ],
        }
    ]

    async def answer_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        assert pending.tool_name == "AskUserQuestion"
        manager.resolve(
            pending.request_id,
            approved=True,
            updated_input=build_answers_payload(
                questions,
                {"Which refactor?": "A — Comments only"},
            ),
        )

    task = asyncio.create_task(answer_later())
    result = await can_use_tool(
        "AskUserQuestion",
        {"questions": questions},
        None,
    )
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"
    assert result.updated_input is not None
    assert result.updated_input["answers"]["Which refactor?"] == "A — Comments only"
