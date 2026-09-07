"""Generic Copilot right-rail — connection, queued jobs, display config.

App-agnostic: callers own session lifecycle, job dicts, and structured-output
handlers. This module only renders the rail chrome + ``panel()`` + chat input.

Named ``rail.py`` so ``st_coco.copilot_rail`` is the function, not this module.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Any

import streamlit as st

from streamlit_coco.display import render_progress_badge
from streamlit_coco.session import CocoChatResult, CocoRunStatus, CocoSession
from streamlit_coco.ui import panel, send_prompt

LAST_MESSAGES_N = 8
LAST_MESSAGES_MIN = 1
LAST_MESSAGES_MAX = 50
PREVIEW_CHARS_N = 200
PREVIEW_CHARS_MIN = 40
PREVIEW_CHARS_MAX = 1000
PREVIEW_CHARS_STEP = 20
FILTER_LAST = "Last messages"
FILTER_SHORT = "First n characters"
PATH_DISPLAY_LIMIT = 100
DISPLAY_CONFIG_ICON = ":material/display_settings:"
EXAMPLE_DRAFT_KEY_SUFFIX = "_example_draft"


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


def resolve_transcript_view(
    selected: Sequence[str] | None,
    *,
    last_n: int,
    preview_chars: int,
) -> tuple[int | None, int | None]:
    """Map pill selection + slider values to ``panel()`` compactness args."""
    chosen = set(selected or [])
    max_messages = last_n if FILTER_LAST in chosen else None
    chars = preview_chars if FILTER_SHORT in chosen else None
    return max_messages, chars


def example_draft_key(key_prefix: str) -> str:
    """Session-state key that holds a deferred example prompt until chat input renders."""
    return f"{key_prefix}{EXAMPLE_DRAFT_KEY_SUFFIX}"


def apply_example_question_draft(
    state: MutableMapping[str, Any],
    key_prefix: str,
    *,
    input_key: str,
) -> str | None:
    """Move a deferred example prompt into the chat-input widget key.

    ``st.chat_input`` treats a session-state write as a field prefill, not a
    submit — the user still has to send.
    """
    draft = state.pop(example_draft_key(key_prefix), None)
    if not isinstance(draft, str):
        return None
    text = draft.strip()
    if not text:
        return None
    state[input_key] = text
    return text


def normalize_example_questions(
    items: Sequence[Mapping[str, Any] | Sequence[Any]] | None,
    *,
    deferred: bool = False,
) -> list[tuple[str, str, bool]]:
    """Return ``(title, question, deferred)`` triples, skipping empty items."""
    if not items:
        return []
    out: list[tuple[str, str, bool]] = []
    for raw in items:
        title = ""
        question = ""
        item_deferred = deferred
        if isinstance(raw, Mapping):
            title = str(raw.get("title") or "").strip()
            question = str(raw.get("question") or "").strip()
            if "deferred" in raw:
                item_deferred = bool(raw.get("deferred"))
        elif isinstance(raw, (str, bytes)):
            continue
        elif isinstance(raw, Sequence) and len(raw) >= 2:
            title = str(raw[0] or "").strip()
            question = str(raw[1] or "").strip()
            if len(raw) >= 3:
                item_deferred = bool(raw[2])
        if title and question:
            out.append((title, question, item_deferred))
    return out


def example_questions_visible(
    session: CocoSession | None,
    items: Sequence[Mapping[str, Any] | Sequence[Any]] | None,
    *,
    connected: bool,
    job: Mapping[str, Any] | None = None,
) -> bool:
    """True when starter buttons should render (connected, empty chat, no job)."""
    if not connected or session is None:
        return False
    if job:
        return False
    if session.is_running or getattr(session, "_turn_in_progress", False):
        return False
    if not normalize_example_questions(items):
        return False
    return not any(
        item.get("role") in {"user", "assistant"}
        for item in session.get_transcript_snapshot()
    )


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
    Prefer ``transcript_display_config()`` on the rail — this stays for apps
    that call ``panel()`` directly.
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
    return resolve_transcript_view(picked, last_n=last_n, preview_chars=preview_chars)


def transcript_display_config(
    *,
    key: str = "coco_transcript_display",
    last_n: int = LAST_MESSAGES_N,
    preview_chars: int = PREVIEW_CHARS_N,
    default: Sequence[str] | None = None,
) -> tuple[int | None, int | None]:
    """Icon-only Display config popover: pills plus last-N / first-n sliders.

    Widget changes rerun the enclosing fragment (the rail) while the popover
    stays open, so the transcript updates live.
    """
    last_key = f"{key}_last_n"
    chars_key = f"{key}_preview_chars"
    pills_key = f"{key}_pills"
    last_n = max(LAST_MESSAGES_MIN, min(LAST_MESSAGES_MAX, int(last_n)))
    preview_chars = max(PREVIEW_CHARS_MIN, min(PREVIEW_CHARS_MAX, int(preview_chars)))
    if last_key not in st.session_state:
        st.session_state[last_key] = last_n
    else:
        stored_last = int(st.session_state[last_key])
        if stored_last < LAST_MESSAGES_MIN or stored_last > LAST_MESSAGES_MAX:
            st.session_state[last_key] = max(
                LAST_MESSAGES_MIN, min(LAST_MESSAGES_MAX, stored_last)
            )
    if chars_key not in st.session_state:
        st.session_state[chars_key] = preview_chars
    else:
        stored_chars = int(st.session_state[chars_key])
        if stored_chars < PREVIEW_CHARS_MIN or stored_chars > PREVIEW_CHARS_MAX:
            st.session_state[chars_key] = max(
                PREVIEW_CHARS_MIN, min(PREVIEW_CHARS_MAX, stored_chars)
            )

    options = [FILTER_LAST, FILTER_SHORT]
    with st.popover(
        DISPLAY_CONFIG_ICON,
        help="Display config",
        type="tertiary",
        width="content",
        key=f"{key}_popover",
    ):
        picked = st.pills(
            "Transcript filters",
            options,
            selection_mode="multi",
            default=list(default) if default is not None else list(options),
            key=pills_key,
            label_visibility="collapsed",
            width="stretch",
        )
        selected = set(picked or [])
        last_n_val = st.slider(
            "Last messages",
            min_value=LAST_MESSAGES_MIN,
            max_value=LAST_MESSAGES_MAX,
            key=last_key,
            disabled=FILTER_LAST not in selected,
            width="stretch",
        )
        chars_val = st.slider(
            "First n characters",
            min_value=PREVIEW_CHARS_MIN,
            max_value=PREVIEW_CHARS_MAX,
            step=PREVIEW_CHARS_STEP,
            key=chars_key,
            disabled=FILTER_SHORT not in selected,
            width="stretch",
        )
    return resolve_transcript_view(selected, last_n=last_n_val, preview_chars=chars_val)


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
    example_questions: Sequence[Mapping[str, Any] | Sequence[Any]] | None = None,
    deferred: bool = False,
    render_environment: Callable[..., Any] | None = None,
) -> None:
    """Render a Copilot column: connection, job, transcript, chat input.

    ``session`` may be ``None`` until the caller has connected. Queued jobs
    (``job["status"] == "queued"`` plus ``job["prompt"]``) are sent once the
    session is ready. When the turn ends, ``on_job_finished`` is called so the
    caller can drop the job (Cancel job / caption).

    After Connect, ``example_questions`` (``title`` + ``question``) render as
    starter buttons on an empty transcript. Hover shows the question; click
    sends it unless ``deferred`` is true (or the item sets ``deferred``), in
    which case the question is copied into the chat input and not run. They
    hide once a user/assistant turn or a job is present.
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
                    max_messages, chars = transcript_display_config(
                        key=f"{key_prefix}_display",
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
        if example_questions_visible(
            session, example_questions, connected=True, job=job
        ):
            _render_example_questions(
                session,
                example_questions,
                key_prefix=key_prefix,
                deferred=deferred,
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
        input_key = f"{key_prefix}_input"
        apply_example_question_draft(st.session_state, key_prefix, input_key=input_key)
        st_coco.chat_input_bar(
            session,
            placeholder=input_placeholder,
            key=input_key,
        )


def _render_example_questions(
    session: CocoSession,
    items: Sequence[Mapping[str, Any] | Sequence[Any]] | None,
    *,
    key_prefix: str,
    deferred: bool = False,
) -> None:
    pairs = normalize_example_questions(items, deferred=deferred)
    if not pairs:
        return
    failed_boot = session.status == CocoRunStatus.ERROR and not session.is_ready
    disabled = session.is_running or failed_boot
    with st.container(horizontal=True, gap="small"):
        for index, (title, question, item_deferred) in enumerate(pairs):
            if st.button(
                title,
                key=f"{key_prefix}_example_{index}",
                help=question,
                type="tertiary",
                width="content",
                disabled=disabled,
            ):
                if item_deferred:
                    st.session_state[example_draft_key(key_prefix)] = question
                else:
                    send_prompt(session, question)
                st.rerun()


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
