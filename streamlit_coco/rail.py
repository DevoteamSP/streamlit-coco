"""Generic Copilot right-rail — connection, queued jobs, transcript filters.

App-agnostic: callers own session lifecycle, job dicts, and structured-output
handlers. This module only renders the rail chrome + ``panel()`` + chat input.

Named ``rail.py`` so ``st_coco.copilot_rail`` is the function, not this module.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import streamlit as st

from streamlit_coco.display import render_progress_badge
from streamlit_coco.session import CocoChatResult, CocoRunStatus, CocoSession
from streamlit_coco.ui import panel

LAST_MESSAGES_N = 8
PREVIEW_CHARS_N = 200
FILTER_LAST = "Last messages"
FILTER_SHORT = "First 200 characters"
PATH_DISPLAY_LIMIT = 100


def ellipsize_middle(text: str, limit: int = PATH_DISPLAY_LIMIT) -> str:
    """Shorten ``text`` with ``...`` in the middle, keeping the suffix."""
    if len(text) <= limit:
        return text
    inner = limit - 3
    if inner < 8:
        return text[: max(0, limit - 3)] + "..."
    head = max(4, inner // 3)
    tail = inner - head
    return f"{text[:head]}...{text[-tail:]}"


def _shorten_backtick_paths(caption: str, limit: int = PATH_DISPLAY_LIMIT) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"`{ellipsize_middle(match.group(1), limit)}`"

    return re.sub(r"`([^`]+)`", repl, caption)


def sent_job_is_complete(
    session: CocoSession | None,
    job: Mapping[str, Any] | None,
    *,
    saw_running: bool,
) -> bool:
    """True when a sent job's CoCo turn has ended (not merely queued).

    ``READY`` right after ``send()`` is not complete — wait until the session
    has actually run, or landed on ``COMPLETED`` / ``ERROR`` / ``CANCELLED``.
    """
    if session is None or not job:
        return False
    if str(job.get("status") or "") != "sent":
        return False
    if session.is_running or session.is_connecting:
        return False
    if session.status in {
        CocoRunStatus.COMPLETED,
        CocoRunStatus.ERROR,
        CocoRunStatus.CANCELLED,
    }:
        return True
    return bool(saw_running) and session.status in {
        CocoRunStatus.READY,
        CocoRunStatus.IDLE,
        CocoRunStatus.COMPLETED,
    }


def transcript_view_pills(
    *,
    key: str = "coco_transcript_view",
    last_n: int = LAST_MESSAGES_N,
    preview_chars: int = PREVIEW_CHARS_N,
    default: Sequence[str] | None = None,
    label: str = "Transcript",
    label_visibility: str = "collapsed",
) -> tuple[int | None, int | None]:
    """Pills that compact a long CoCo transcript for a live demo.

    Returns ``(max_messages, preview_chars)`` suitable for ``panel()``.
    """
    options = [FILTER_LAST, FILTER_SHORT]
    picked = st.pills(
        label,
        options,
        selection_mode="multi",
        default=list(default) if default is not None else list(options),
        key=key,
        label_visibility=label_visibility,  # type: ignore[arg-type]
        width="content",
    )
    selected = set(picked or [])
    max_messages = last_n if FILTER_LAST in selected else None
    chars = preview_chars if FILTER_SHORT in selected else None
    return max_messages, chars


def copilot_rail(
    session: CocoSession | None,
    *,
    title: str = "Copilot",
    key_prefix: str = "coco_rail",
    connected: bool = True,
    connections: Sequence[str] | None = None,
    connection_name: str | None = None,
    on_connect: Callable[[str], None] | None = None,
    on_disconnect: Callable[[], None] | None = None,
    connect_caption: str = "",
    on_close: Callable[[], None] | None = None,
    on_clear: Callable[[], None] | None = None,
    job: Mapping[str, Any] | None = None,
    job_hint: str | None = None,
    on_cancel_job: Callable[[], None] | None = None,
    on_job_sent: Callable[[dict[str, Any]], None] | None = None,
    on_job_finished: Callable[[dict[str, Any]], None] | None = None,
    on_structured_output: Callable[[dict[str, Any], CocoChatResult], None] | None = None,
    show_copy: bool = False,
    show_transcript_filters: bool = True,
    last_messages: int = LAST_MESSAGES_N,
    preview_chars: int = PREVIEW_CHARS_N,
    show_status: bool = True,
    show_approvals: bool = True,
    run_every: float = 0.25,
    input_placeholder: str = "Ask CoCo…",
    status_caption: str | None = None,
    render_environment: Callable[..., Any] | None = None,
) -> None:
    """Render a Copilot column: connection, job, transcript, chat input.

    ``session`` may be ``None`` until the caller has connected. Queued jobs
    (``job["status"] == "queued"`` plus ``job["prompt"]``) are sent once the
    session is ready. When the turn ends, ``on_job_finished`` is called so the
    caller can drop the job (Cancel job / caption).
    """
    import streamlit_coco as st_coco

    top = st.container(horizontal=True, vertical_alignment="center")
    with top:
        st.subheader(title)
        if job and on_cancel_job is not None:
            if st.button(
                "Cancel job",
                key=f"{key_prefix}_cancel_job",
                icon=":material/cancel:",
            ):
                on_cancel_job()
                st.rerun()
        if on_close is not None and st.button(
            "Close",
            key=f"{key_prefix}_close",
            icon=":material/close:",
        ):
            on_close()
            st.rerun()

    saw_key = f"{key_prefix}_job_saw_running"

    @st.fragment(run_every=run_every)
    def _progress_badge() -> None:
        if session is not None and (session.is_running or session.is_connecting):
            st.session_state[saw_key] = True
        if show_status:
            render_progress_badge(session)
        if on_job_finished is not None and sent_job_is_complete(
            session, job, saw_running=bool(st.session_state.get(saw_key))
        ):
            st.session_state.pop(saw_key, None)
            finished = dict(job)
            finished["status"] = "finished"
            on_job_finished(finished)
            st.rerun()

    @st.fragment
    def _copilot_live() -> None:
        max_messages = None
        chars: int | None = None
        show_conn = on_connect is not None or on_disconnect is not None
        if show_conn or show_transcript_filters or session is not None:
            with st.container(horizontal=True, vertical_alignment="center"):
                if show_conn:
                    _render_connection(
                        connected=connected,
                        connection_name=connection_name,
                        connections=connections or [],
                        on_connect=on_connect,
                        on_disconnect=on_disconnect,
                        connect_caption=connect_caption,
                        key_prefix=key_prefix,
                        render_environment=render_environment or st_coco.render_environment_status,
                    )
                if show_transcript_filters:
                    max_messages, chars = transcript_view_pills(
                        key=f"{key_prefix}_transcript_view",
                        last_n=last_messages,
                        preview_chars=preview_chars,
                    )
                _progress_badge()
        else:
            _progress_badge()

        if job:
            status = str(job.get("status") or "queued")
            label = str(job.get("label") or job.get("kind") or "Job")
            hint = job_hint or (
                "Approve Write / Edit in the panel."
                if not job.get("expect_structured", True)
                else "Watch the stream — structured output is handled by the app."
            )
            st.caption(f"**{label}** · {status}. {hint}")

        if not connected or session is None:
            st.caption("Connect a Snowflake profile to start Copilot.")
            return

        if status_caption:
            st.caption(_shorten_backtick_paths(status_caption))

        if job and (job.get("status") or "") == "queued":
            prompt = str(job.get("prompt") or "")
            if prompt and session.is_ready and not session.is_running:
                session.send(prompt)
                sent = dict(job)
                sent["status"] = "sent"
                if on_job_sent is not None:
                    on_job_sent(sent)
                st.toast(f"{job.get('label') or 'Job'} started…")
            elif session.is_connecting:
                st.caption("Waiting for CoCo to finish connecting…")

        expect_structured = bool((job or {}).get("expect_structured", True))
        panel(
            session,
            warm_up=True,
            show_status=False,
            show_approvals=show_approvals,
            show_copy=show_copy,
            max_messages=max_messages,
            preview_chars=chars,
            run_every=run_every,
            on_structured_output=on_structured_output if job and expect_structured else None,
        )

    _copilot_live()

    if connected and session is not None:
        if on_clear is not None:
            with st.container(horizontal=True, vertical_alignment="center"):
                if st.button(
                    "Clear chat",
                    icon=":material/delete:",
                    key=f"{key_prefix}_clear",
                ):
                    on_clear()
                    st.rerun()
        st_coco.chat_input_bar(
            session,
            placeholder=input_placeholder,
            key=f"{key_prefix}_input",
        )


def _render_connection(
    *,
    connected: bool,
    connection_name: str | None,
    connections: Sequence[str],
    on_connect: Callable[[str], None] | None,
    on_disconnect: Callable[[], None] | None,
    connect_caption: str,
    key_prefix: str,
    render_environment: Callable[..., Any],
) -> None:
    import streamlit_coco as st_coco

    label = f"Connected · {connection_name}" if connected and connection_name else "Connection"
    with st.popover(
        label,
        icon=":material/cloud_done:" if connected else ":material/link:",
    ):
        if connect_caption:
            st.caption(connect_caption)
        names = list(connections)
        if not names:
            st.warning("No Snowflake connections available.")
            return
        preferred = connection_name if connection_name in names else names[0]
        chosen = st.selectbox(
            "Connection",
            names,
            index=names.index(preferred),
            key=f"{key_prefix}_conn_select",
        )
        env = st_coco.check_environment(connection=chosen)
        render_environment(env, stacked=True, show_title=False)
        if on_connect is not None and st.button(
            "Connect",
            type="primary",
            key=f"{key_prefix}_connect",
            disabled=not env.ready,
        ):
            on_connect(str(chosen))
            st.rerun()
        if (
            connected
            and on_disconnect is not None
            and st.button(
                "Disconnect",
                key=f"{key_prefix}_disconnect",
            )
        ):
            on_disconnect()
            st.rerun()
