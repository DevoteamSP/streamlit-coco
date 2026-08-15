"""Copilot rail public surface."""

from __future__ import annotations

import streamlit_coco as st_coco
from streamlit_coco.rail import FILTER_LAST, FILTER_SHORT, LAST_MESSAGES_N, PREVIEW_CHARS_N


def test_copilot_rail_exports() -> None:
    assert "copilot_rail" in st_coco.__all__
    assert "transcript_view_pills" in st_coco.__all__
    assert callable(st_coco.copilot_rail)
    assert callable(st_coco.transcript_view_pills)


def test_transcript_filter_constants() -> None:
    assert LAST_MESSAGES_N == 8
    assert PREVIEW_CHARS_N == 200
    assert FILTER_LAST == "Last messages"
    assert FILTER_SHORT == "First 200 characters"


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
