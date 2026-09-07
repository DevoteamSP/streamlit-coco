"""Copilot rail public surface."""

from __future__ import annotations

import streamlit_coco as st_coco
from streamlit_coco.rail import (
    DISPLAY_CONFIG_ICON,
    FILTER_LAST,
    FILTER_SHORT,
    LAST_MESSAGES_N,
    PREVIEW_CHARS_N,
    apply_example_question_draft,
    example_draft_key,
    example_questions_visible,
    normalize_example_questions,
    resolve_transcript_view,
)


def test_copilot_rail_exports() -> None:
    assert "copilot_rail" in st_coco.__all__
    assert "transcript_display_config" in st_coco.__all__
    assert "transcript_view_pills" in st_coco.__all__
    assert callable(st_coco.copilot_rail)
    assert callable(st_coco.transcript_display_config)
    assert callable(st_coco.transcript_view_pills)


def test_transcript_filter_constants() -> None:
    assert LAST_MESSAGES_N == 8
    assert PREVIEW_CHARS_N == 200
    assert FILTER_LAST == "Last messages"
    assert FILTER_SHORT == "First n characters"
    assert DISPLAY_CONFIG_ICON == ":material/display_settings:"


def test_resolve_transcript_view_both_on() -> None:
    max_messages, chars = resolve_transcript_view(
        [FILTER_LAST, FILTER_SHORT],
        last_n=12,
        preview_chars=80,
    )
    assert max_messages == 12
    assert chars == 80


def test_resolve_transcript_view_pills_off() -> None:
    max_messages, chars = resolve_transcript_view(
        [],
        last_n=12,
        preview_chars=80,
    )
    assert max_messages is None
    assert chars is None


def test_ellipsize_middle_keeps_short_text() -> None:
    from streamlit_coco.rail import ellipsize_middle

    assert ellipsize_middle("short") == "short"
    assert ellipsize_middle("a" * 100) == "a" * 100


def test_ellipsize_middle_inserts_ellipsis() -> None:
    from streamlit_coco.rail import PATH_DISPLAY_LIMIT, ellipsize_middle

    path = "/Users/laurentletourmy/dev2/streamlit-coco-dev/examples/workspaces/" + (
        "bi_to_semantic_and_then_some_extra_directory_name"
    )
    assert len(path) > PATH_DISPLAY_LIMIT
    out = ellipsize_middle(path)
    assert len(out) == PATH_DISPLAY_LIMIT
    assert "..." in out
    assert out.startswith(path[:4])
    assert out.endswith(path[-10:])


def test_session_progress_text_running() -> None:
    from streamlit_coco.display import session_progress_text
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoRunStatus, CocoSession

    session = CocoSession(options=CocoOptions(), key="progress-running")
    session.status = CocoRunStatus.RUNNING
    assert session_progress_text(session) == "Working · thinking…"


def test_sent_job_is_complete_after_completed() -> None:
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.rail import sent_job_is_complete
    from streamlit_coco.session import CocoRunStatus, CocoSession

    session = CocoSession(options=CocoOptions(), key="job-done")
    session.status = CocoRunStatus.COMPLETED
    job = {"status": "sent", "kind": "streamlit"}
    assert sent_job_is_complete(session, job, saw_running=False) is True


def test_sent_job_is_complete_not_ready_before_run() -> None:
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.rail import sent_job_is_complete
    from streamlit_coco.session import CocoRunStatus, CocoSession

    session = CocoSession(options=CocoOptions(), key="job-ready")
    session.status = CocoRunStatus.READY
    job = {"status": "sent", "kind": "streamlit"}
    assert sent_job_is_complete(session, job, saw_running=False) is False
    assert sent_job_is_complete(session, job, saw_running=True) is True


def test_session_progress_text_idle() -> None:
    from streamlit_coco.display import session_progress_text
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoSession

    session = CocoSession(options=CocoOptions(), key="progress-idle")
    assert session_progress_text(session) is None


def test_shorten_backtick_paths() -> None:
    from streamlit_coco.rail import _shorten_backtick_paths

    long_path = "x" * 120
    caption = f"cwd · `{long_path}` · status · `ready`"
    out = _shorten_backtick_paths(caption)
    assert "`ready`" in out
    assert "..." in out
    assert long_path not in out


def test_normalize_example_questions() -> None:
    assert normalize_example_questions(None) == []
    assert normalize_example_questions([]) == []
    assert normalize_example_questions(
        [
            {"title": "List files", "question": "What is in cwd?"},
            {"title": "  ", "question": "skip me"},
            {"title": "No question"},
            ("Hover me", "Send this"),
            "bare-string",
        ]
    ) == [
        ("List files", "What is in cwd?", False),
        ("Hover me", "Send this", False),
    ]


def test_normalize_example_questions_deferred_default() -> None:
    assert normalize_example_questions(
        [{"title": "List files", "question": "What is in cwd?"}],
        deferred=True,
    ) == [("List files", "What is in cwd?", True)]


def test_normalize_example_questions_per_item_deferred() -> None:
    assert normalize_example_questions(
        [
            {"title": "Fill me", "question": "Edit then send", "deferred": True},
            {"title": "Run me", "question": "Send now", "deferred": False},
            ("Tuple fill", "From a pair", True),
        ],
        deferred=False,
    ) == [
        ("Fill me", "Edit then send", True),
        ("Run me", "Send now", False),
        ("Tuple fill", "From a pair", True),
    ]


def test_apply_example_question_draft() -> None:
    state: dict[str, object] = {
        example_draft_key("coco_rail"): "  List the files  ",
    }
    assert (
        apply_example_question_draft(state, "coco_rail", input_key="coco_rail_input")
        == "List the files"
    )
    assert state["coco_rail_input"] == "List the files"
    assert example_draft_key("coco_rail") not in state
    assert apply_example_question_draft(state, "coco_rail", input_key="coco_rail_input") is None


def test_example_questions_visible_after_connect() -> None:
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoSession

    session = CocoSession(options=CocoOptions(), key="examples-empty")
    items = [{"title": "List files", "question": "What is in cwd?"}]
    assert (
        example_questions_visible(session, items, connected=True, job=None) is True
    )
    assert (
        example_questions_visible(session, items, connected=False, job=None) is False
    )
    assert example_questions_visible(None, items, connected=True, job=None) is False
    assert (
        example_questions_visible(session, items, connected=True, job={"status": "queued"})
        is False
    )


def test_example_questions_hidden_while_turn_in_progress() -> None:
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoSession

    session = CocoSession(options=CocoOptions(), key="examples-pending")
    items = [{"title": "List files", "question": "What is in cwd?"}]
    session._turn_in_progress = True
    assert (
        example_questions_visible(session, items, connected=True, job=None) is False
    )


def test_example_questions_hidden_after_user_turn() -> None:
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoSession

    session = CocoSession(options=CocoOptions(), key="examples-used")
    session.transcript.append({"role": "user", "content": "hello"})
    items = [{"title": "List files", "question": "What is in cwd?"}]
    assert (
        example_questions_visible(session, items, connected=True, job=None) is False
    )
