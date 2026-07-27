"""Tests for streamlit-coco core modules."""

from __future__ import annotations

import asyncio

import pytest

from streamlit_coco.messages import (
    CocoEvent,
    _extract_stream_delta,
    append_events_to_transcript,
    parse_ndjson_line,
    permission_request_event,
)
from streamlit_coco.options import CocoOptions
from streamlit_coco.permissions import PermissionManager, build_can_use_tool
from streamlit_coco.session import CocoRunStatus, CocoSession


def test_parse_assistant_ndjson() -> None:
    line = (
        '{"type":"assistant","message":{"content":['
        '{"type":"text","text":"Hello"},{"type":"tool_use","id":"t1","name":"Read","input":{"path":"."}}'
        "]}}"
    )
    events = parse_ndjson_line(line)
    assert len(events) == 2
    assert events[0].type == "assistant_text"
    assert events[0].text == "Hello"
    assert events[1].type == "tool_use"
    assert events[1].name == "Read"


def test_parse_result_ndjson() -> None:
    line = '{"type":"result","subtype":"success","duration_ms":100,"structured_output":{"ok":true}}'
    events = parse_ndjson_line(line)
    assert events[0].type == "result"
    assert events[0].structured_output == {"ok": True}


def test_parse_user_tool_result_ndjson() -> None:
    line = (
        '{"type":"user","message":{"content":['
        '{"type":"tool_result","tool_use_id":"t1","content":"a.py\\nb.py","is_error":false}'
        "]}}"
    )
    events = parse_ndjson_line(line)
    assert len(events) == 1
    assert events[0].type == "tool_result"
    assert events[0].tool_use_id == "t1"
    assert events[0].content == "a.py\nb.py"


def test_tool_result_marks_card_completed() -> None:
    transcript: list[dict] = []
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="tool_use", tool_use_id="t1", name="Grep", input={"pattern": "TODO"})],
    )
    assert transcript[0]["status"] == "running"
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="tool_result", tool_use_id="t1", content="prompts.json:1", is_error=False)],
    )
    assert transcript[0]["status"] == "completed"
    assert transcript[0]["result"] == "prompts.json:1"


def test_result_clears_stale_running_tool_captions() -> None:
    """After the turn completes, never leave Grep stuck on 'Searching content…'."""
    transcript: list[dict] = []
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="tool_use", tool_use_id="t1", name="Grep", input={"pattern": "TODO"})],
    )
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="assistant_text", text="Only 4 matches found.")],
    )
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="result", subtype="success", is_error=False)],
    )
    assert transcript[0]["kind"] == "tool"
    assert transcript[0]["status"] == "completed"


def test_append_transcript_merges_text() -> None:
    transcript: list[dict] = []
    append_events_to_transcript(transcript, [CocoEvent(type="assistant_text", text="Hi ")])
    append_events_to_transcript(transcript, [CocoEvent(type="assistant_text", text="there")])
    assert transcript == [
        {"id": transcript[0]["id"], "role": "assistant", "kind": "text", "content": "Hi there"}
    ]


def test_append_transcript_skips_full_text_snapshots_after_stream() -> None:
    """Stream deltas + AssistantMessage + ResultMessage must not triple the reply."""
    transcript: list[dict] = []
    reply = "What are you working on today?"
    append_events_to_transcript(
        transcript,
        [
            CocoEvent(type="stream_event", delta="What are you "),
            CocoEvent(type="stream_event", delta="working on today?"),
        ],
    )
    append_events_to_transcript(transcript, [CocoEvent(type="assistant_text", text=reply)])
    append_events_to_transcript(transcript, [CocoEvent(type="assistant_text", text=reply)])
    assert len(transcript) == 1
    assert transcript[0]["content"] == reply


def test_append_transcript_replaces_partial_with_final_snapshot() -> None:
    transcript: list[dict] = []
    append_events_to_transcript(transcript, [CocoEvent(type="stream_event", delta="What are you")])
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="assistant_text", text="What are you working on today?")],
    )
    assert transcript[0]["content"] == "What are you working on today?"


def test_append_structured_output_inline() -> None:
    transcript: list[dict] = []
    append_events_to_transcript(
        transcript,
        [CocoEvent(type="result", structured_output={"features": []})],
        show_structured_inline=True,
    )
    assert transcript[-1]["kind"] == "structured_output"


def test_options_hash_stable() -> None:
    a = CocoOptions(connection="prod", cwd=".", model="claude-sonnet-4-6")
    b = CocoOptions(connection="prod", cwd=".", model="claude-sonnet-4-6")
    assert a.options_hash() == b.options_hash()


@pytest.mark.asyncio
async def test_permission_manager_allow() -> None:
    manager = PermissionManager(approval_timeout_seconds=1.0)
    can_use_tool = build_can_use_tool(manager, ["Write"])

    async def approve_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        manager.resolve(pending.request_id, approved=True)

    task = asyncio.create_task(approve_later())
    result = await can_use_tool("Write", {"path": "x.sql"}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"


@pytest.mark.asyncio
async def test_permission_manager_deny() -> None:
    manager = PermissionManager(approval_timeout_seconds=1.0)
    can_use_tool = build_can_use_tool(manager, ["Bash"])

    async def deny_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        manager.resolve(pending.request_id, approved=False, reason="nope")

    task = asyncio.create_task(deny_later())
    result = await can_use_tool("Bash", {"command": "ls"}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultDeny"


def test_permission_request_event_shape() -> None:
    event = permission_request_event("req-1", "Edit", {"path": "a.py"})
    assert event.type == "permission_request"
    assert event.request_id == "req-1"


def test_coco_run_status_values() -> None:
    assert CocoRunStatus.AWAITING_USER.value == "awaiting_user"
    assert CocoRunStatus.CONNECTING.value == "connecting"
    assert CocoRunStatus.READY.value == "ready"


def test_session_needs_polling_while_connecting() -> None:
    session = CocoSession(options=CocoOptions(), key="connecting-poll")
    session.status = CocoRunStatus.CONNECTING
    assert session.needs_polling is True
    assert session.is_connecting is True
    assert session.is_ready is False


def test_session_captures_init_info() -> None:
    session = CocoSession(options=CocoOptions(), key="init-info")
    session._ingest_event(
        CocoEvent(
            type="system",
            subtype="init",
            metadata={"model": "claude-sonnet-4-6", "cwd": "/tmp"},
        )
    )
    assert session.init_info == {"model": "claude-sonnet-4-6", "cwd": "/tmp"}


def test_session_send_waits_for_worker_loop() -> None:
    session = CocoSession(options=CocoOptions(), key="loop-test")
    session.start()
    loop = session._ensure_loop()
    assert loop is not None
    assert session._prompt_queue is not None
    assert (
        session.status
        in {
            CocoRunStatus.CONNECTING,
            CocoRunStatus.READY,
            CocoRunStatus.ERROR,
        }
        or session.is_ready
    )
    session.send("hello")
    assert session.needs_polling is True
    session.close()
    session._wait_for_worker_stop(timeout=2.0)


def test_auto_allow_tools_excludes_approval_list() -> None:
    opts = CocoOptions(
        allowed_tools=["Read", "Glob", "Write"],
        require_approval_for=["Write", "Bash"],
    )
    assert opts.auto_allow_tools() == ["Read", "Glob"]


def test_to_sdk_options_omits_cli_allowed_tools_when_callback_set() -> None:
    opts = CocoOptions(allowed_tools=["Read", "Glob", "Grep"])

    async def _cb(*args: object) -> None:
        return None

    sdk = opts.to_sdk_options(can_use_tool=_cb)
    assert not sdk.allowed_tools
    assert opts.to_sdk_options().allowed_tools == ["Read", "Glob", "Grep"]


@pytest.mark.asyncio
async def test_permission_manager_wakes_from_main_thread() -> None:
    manager = PermissionManager(approval_timeout_seconds=2.0)
    can_use_tool = build_can_use_tool(manager, ["Write"])

    async def approve_from_main_thread() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        assert manager.resolve(pending.request_id, approved=True)

    task = asyncio.create_task(approve_from_main_thread())
    result = await can_use_tool("Write", {"path": "x.sql"}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"


@pytest.mark.asyncio
async def test_permission_tool_name_is_case_insensitive() -> None:
    manager = PermissionManager(approval_timeout_seconds=1.0)
    can_use_tool = build_can_use_tool(manager, ["Write"])

    async def approve_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        assert pending.tool_name == "write"
        manager.resolve(pending.request_id, approved=True)

    task = asyncio.create_task(approve_later())
    result = await can_use_tool("write", {}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"
    manager = PermissionManager(approval_timeout_seconds=1.0)
    can_use_tool = build_can_use_tool(manager, ["Write"])

    async def approve_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        assert pending.tool_name == "write"
        manager.resolve(pending.request_id, approved=True)

    task = asyncio.create_task(approve_later())
    result = await can_use_tool("write", {}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"


def test_extract_stream_delta_content_block() -> None:
    delta = _extract_stream_delta(
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        }
    )
    assert delta == "Hello"


def test_check_environment_smoke() -> None:
    from streamlit_coco.diagnostics import check_environment

    env = check_environment()
    assert env.connection_hint == "default"
    if env.snowflake_config_file:
        assert env.snowflake_config_display is not None
        assert "connections.toml" in env.snowflake_config_display or "config.toml" in (
            env.snowflake_config_display or ""
        )


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


def test_text_renderer_resolve_named() -> None:
    from streamlit_coco.text_renderer import resolve_text_renderer

    assert resolve_text_renderer(None) is not None
    assert resolve_text_renderer("markdown") is not None
    assert resolve_text_renderer("write") is not None
    assert callable(resolve_text_renderer(lambda text: text))

    with pytest.raises(ValueError, match="Unknown text_renderer"):
        resolve_text_renderer("nope")


def test_session_execute_plan_approves_exit_plan() -> None:
    session = CocoSession(options=CocoOptions(permission_mode="plan"), key="exec-plan")
    pending = session.permission_manager.create_request("ExitPlanMode", {"plan": "ship it"})
    session.execute_plan()
    resolved = session.permission_manager.get_pending(pending.request_id)
    assert resolved is not None
    assert resolved.decision == "allow"


def test_session_execute_plan_switches_mode() -> None:
    session = CocoSession(options=CocoOptions(permission_mode="plan"), key="exec-mode")
    session.execute_plan(prompt=None)
    assert session.options.permission_mode == "default"


@pytest.mark.asyncio
async def test_session_stream_yields_ingested_events() -> None:
    session = CocoSession(options=CocoOptions(), key="stream-test")

    async def produce() -> None:
        await asyncio.sleep(0.05)
        session._ingest_event(CocoEvent(type="assistant_text", text="hi"))
        session._ingest_event(CocoEvent(type="result", subtype="success"))

    task = asyncio.create_task(produce())
    events: list[str] = []
    async for event in session.stream():
        events.append(event.type)
        if event.type == "result":
            break
    await task
    assert events == ["assistant_text", "result"]


@pytest.mark.asyncio
async def test_session_run_waits_for_turn() -> None:
    session = CocoSession(options=CocoOptions(), key="run-test")

    async def finish_turn() -> None:
        await asyncio.sleep(0.05)
        # Mimic worker turn lifecycle without SDK.
        session._turn_in_progress = True
        session.status = CocoRunStatus.RUNNING
        await asyncio.sleep(0.05)
        session._ingest_event(CocoEvent(type="result", subtype="success"))
        session._turn_in_progress = False
        session.status = CocoRunStatus.COMPLETED

    # Bypass real worker: stub send to only flip the flag.
    session.send = lambda prompt: (
        setattr(session, "_turn_in_progress", True)
        or setattr(  # type: ignore[method-assign]
            session, "last_prompt", prompt
        )
    )
    task = asyncio.create_task(finish_turn())
    result = await session.run("hello", timeout=2.0)
    await task
    assert result.last_prompt == "hello"
    assert result.status == CocoRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_exit_plan_mode_requires_approval() -> None:
    manager = PermissionManager(approval_timeout_seconds=1.0)
    can_use_tool = build_can_use_tool(manager, [], auto_allow_tools=["ExitPlanMode"])

    async def approve_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        assert pending.tool_name == "ExitPlanMode"
        manager.resolve(
            pending.request_id,
            approved=True,
            updated_input={"message": "ok"},
        )

    task = asyncio.create_task(approve_later())
    result = await can_use_tool("ExitPlanMode", {"plan": "do stuff"}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultAllow"
    assert result.updated_input == {"message": "ok"}


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


@pytest.mark.asyncio
async def test_ask_user_question_not_auto_allowed() -> None:
    manager = PermissionManager(approval_timeout_seconds=1.0)
    # Even if somehow marked always-allowed, AskUserQuestion must still prompt.
    manager.always_allowed_tools.add("askuserquestion")
    can_use_tool = build_can_use_tool(manager, [], auto_allow_tools=["AskUserQuestion"])

    async def cancel_later() -> None:
        await asyncio.sleep(0.05)
        pending = manager.active_pending()
        assert pending is not None
        manager.resolve(pending.request_id, approved=False, reason="cancelled")

    task = asyncio.create_task(cancel_later())
    result = await can_use_tool("ask_user_question", {"questions": []}, None)
    await task
    assert result.__class__.__name__ == "PermissionResultDeny"
