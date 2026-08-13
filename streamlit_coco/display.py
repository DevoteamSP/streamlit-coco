"""Native Streamlit rendering for CoCo transcripts and streaming output."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from streamlit_coco.clipboard import render_copy_button
from streamlit_coco.rich_text import preview_text, split_markdown_fences, window_transcript
from streamlit_coco.session import CocoRunStatus, CocoSession
from streamlit_coco.text_renderer import TextRenderer, resolve_text_renderer
from streamlit_coco.tool_cards import render_tool_card


def _render_skeleton(height: int = 96) -> None:
    """Loading placeholder; ``st.skeleton`` requires Streamlit >= 1.59."""
    skeleton = getattr(st, "skeleton", None)
    if callable(skeleton):
        skeleton(height=height)
        return
    st.empty().markdown(
        (
            f'<div style="height:{height}px;'
            "background:linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);"
            'background-size:200% 100%;border-radius:8px;opacity:0.7;"></div>'
        ),
        unsafe_allow_html=True,
    )


def get_latest_assistant_text(session: CocoSession) -> str:
    """Return the current assistant reply text (including partial stream)."""
    text = ""
    for item in session.get_transcript_snapshot():
        if item.get("kind") == "text" and item.get("role") == "assistant":
            text = str(item.get("content") or "")
    return text


def _uses_rich_markdown(text_renderer: TextRenderer) -> bool:
    if text_renderer is None:
        return True
    if isinstance(text_renderer, str):
        key = text_renderer.strip().lower()
        if key.startswith("st."):
            key = key[3:]
        return key in {"markdown", ""}
    return False


def render_message_body(
    text: str,
    *,
    text_renderer: TextRenderer = None,
    streaming_suffix: str = "",
) -> None:
    """Render user/assistant text with optional fenced-code highlighting."""
    body = text + streaming_suffix
    if not _uses_rich_markdown(text_renderer):
        resolve_text_renderer(text_renderer)(body)
        return

    segments = split_markdown_fences(body)
    # Streaming cursor lives in the last prose segment when present.
    for segment in segments:
        if segment.kind == "code":
            st.code(segment.text, language=segment.language or "text")
        else:
            st.markdown(segment.text)


def _transcript_extra_key(session: CocoSession) -> str:
    return f"_coco_transcript_extra_{session.key or id(session)}"


def render_transcript(
    session: CocoSession,
    container: Any | None = None,
    *,
    show_tool_details: bool = True,
    show_thinking: bool = False,
    show_streaming_cursor: bool = True,
    hide_active_approval: bool = False,
    text_renderer: TextRenderer = None,
    show_copy: bool = True,
    max_messages: int | None = None,
    preview_chars: int | None = None,
) -> None:
    """Render the conversation into a Streamlit container or the current context.

    Parameters
    ----------
    show_copy:
        Show a clipboard control on assistant messages and completed tool cards.
    max_messages:
        When set, show only the newest N transcript items plus any extra loaded
        via the **Load earlier** control.
    preview_chars:
        When set, show only the first N characters of user/assistant text.
    """
    full_transcript = session.get_transcript_snapshot()
    extra_key = _transcript_extra_key(session)
    extra = int(st.session_state.get(extra_key, 0) or 0)
    transcript, hidden = window_transcript(
        full_transcript,
        max_messages=max_messages,
        extra=extra,
    )
    is_streaming = session.status == CocoRunStatus.RUNNING and session.needs_polling
    active_pending = session.permission_manager.active_pending()
    active_approval_id = active_pending.request_id if active_pending else None

    def _render() -> None:
        if not full_transcript:
            st.caption("CoCo responses will appear here.")
            return

        if hidden > 0:
            st.caption(f"{hidden} earlier message{'s' if hidden != 1 else ''} hidden")
            step = max_messages or 20
            if st.button(
                "Load earlier",
                key=f"{extra_key}_load",
                type="secondary",
            ):
                st.session_state[extra_key] = extra + step
                st.rerun()

        last_assistant_idx = -1
        for idx, item in enumerate(transcript):
            if item.get("role") == "assistant" and item.get("kind") == "text":
                last_assistant_idx = idx

        for idx, item in enumerate(transcript):
            role = item.get("role")
            kind = item.get("kind")
            item_id = str(item.get("id") or idx)

            if role == "user":
                visible, clipped = preview_text(str(item.get("content") or ""), limit=preview_chars)
                with st.chat_message("user"):
                    render_message_body(visible, text_renderer=text_renderer)
                    if clipped:
                        st.caption(f"First {preview_chars} characters")
                continue

            if kind == "text":
                content = str(item.get("content") or "")
                streaming = (
                    show_streaming_cursor and is_streaming and idx == last_assistant_idx and content
                )
                visible, clipped = preview_text(content, limit=None if streaming else preview_chars)
                with st.chat_message("assistant"):
                    render_message_body(
                        visible,
                        text_renderer=text_renderer,
                        streaming_suffix=" ▍" if streaming else "",
                    )
                    if clipped:
                        st.caption(f"First {preview_chars} characters")
                    if show_copy and content and not streaming:
                        render_copy_button(
                            content,
                            key=f"coco_copy_asst_{item_id}",
                            label="Copy",
                        )
                continue

            if kind == "tool":
                render_tool_card(
                    item,
                    show_tool_details=show_tool_details,
                    show_copy=show_copy,
                )
                continue

            if kind == "structured_output":
                with st.container(border=True):
                    st.markdown("**Structured output**")
                    payload = item.get("content")
                    st.json(payload)
                    if show_copy and payload is not None:
                        render_copy_button(
                            json.dumps(payload, indent=2, default=str),
                            key=f"coco_copy_struct_{item_id}",
                            label="Copy JSON",
                        )
                continue

            if kind == "approval":
                if hide_active_approval and item.get("id") == active_approval_id:
                    continue
                status = item.get("status") or "pending"
                st.caption(f"Approval for `{item.get('tool_name')}` — **{status}**")
                continue

        if session.last_error:
            st.error(session.last_error)

        if is_streaming and last_assistant_idx < 0:
            with st.chat_message("assistant"):
                render_message_body(
                    "_CoCo is thinking…_",
                    text_renderer=text_renderer,
                    streaming_suffix=" ▍",
                )

    if container is None:
        _render()
    else:
        with container:
            _render()


def _status_model_label(session: CocoSession) -> str:
    info = session.init_info or {}
    return str(info.get("model") or session.options.model or "auto")


def _status_connection_label(session: CocoSession) -> str:
    info = session.init_info or {}
    return str(info.get("connection") or session.options.connection or "default")


def _latest_tool_activity(session: CocoSession) -> dict[str, Any] | None:
    tools = [item for item in session.get_transcript_snapshot() if item.get("kind") == "tool"]
    if not tools:
        return None
    return tools[-1]


def session_progress_text(session: CocoSession) -> str | None:
    """Short busy label for a compact badge (or ``None`` when idle)."""
    if session.is_connecting:
        return "Starting CoCo"
    pending = session.permission_manager.active_pending()
    if pending is not None:
        name = pending.tool_name or "input"
        return f"Needs input · {name}"
    if session.status == CocoRunStatus.RUNNING:
        tool = _latest_tool_activity(session)
        if tool and tool.get("status") == "running":
            return f"Working · {tool.get('name')}"
        return "Working · thinking…"
    return None


def render_progress_badge(session: CocoSession | None) -> None:
    """Inline busy badge for the Copilot rail header. No-op when idle."""
    if session is None:
        return
    text = session_progress_text(session)
    if not text:
        return
    color = "orange" if text.startswith("Needs input") else "blue"
    icon = ":material/touch_app:" if text.startswith("Needs input") else ":material/pending:"
    st.badge(text, icon=icon, color=color)
    if session.status == CocoRunStatus.RUNNING:
        st.badge(_status_model_label(session), color="gray")


def render_session_status(
    session: CocoSession,
    *,
    expanded: str = "auto",
) -> None:
    """Render connect / turn progress without remounting ``st.status`` each poll."""
    connecting = session.is_connecting
    pending = session.permission_manager.active_pending()
    busy = session.needs_polling or pending is not None

    if expanded == "always":
        show_details = True
    elif expanded == "never":
        show_details = False
    else:
        show_details = connecting or busy

    if connecting:
        with st.container(border=True):
            st.markdown("**Starting CoCo**")
            st.caption("Connecting CLI · initializing session…")
            _render_skeleton(72)
        return

    if pending is not None:
        st.badge(
            f"Needs input · {pending.tool_name}",
            icon=":material/touch_app:",
            color="orange",
        )
        if show_details:
            st.caption("Approve, deny, or answer to continue.")
        return

    if session.status == CocoRunStatus.RUNNING:
        text = session_progress_text(session) or "Working · thinking…"
        st.badge(text, icon=":material/pending:", color="blue")
        if show_details:
            st.caption(
                f"`{_status_model_label(session)}` · `{_status_connection_label(session)}`"
            )
        return

    if session.status in {CocoRunStatus.READY, CocoRunStatus.COMPLETED, CocoRunStatus.IDLE}:
        st.caption(
            f":material/check_circle: CoCo ready · `{_status_model_label(session)}` · "
            f"`{_status_connection_label(session)}`"
        )
        if session.status == CocoRunStatus.ERROR and session.last_error:
            st.error(session.last_error)
        return

    if session.status == CocoRunStatus.ERROR and session.last_error:
        st.error(session.last_error)


def render_output_field(
    session: CocoSession,
    container: Any | None = None,
    *,
    label: str = "CoCo output",
    show_tool_details: bool = False,
    text_renderer: TextRenderer = None,
    show_copy: bool = True,
) -> None:
    """Render a focused output panel with the latest assistant response."""
    text = get_latest_assistant_text(session)
    is_streaming = session.status == CocoRunStatus.RUNNING and session.needs_polling
    suffix = " ▍" if is_streaming and text else ""

    def _render() -> None:
        st.subheader(label)
        st.caption(f"Status: **{session.status.value}** · revision {session.get_revision()}")

        if text:
            render_message_body(text, text_renderer=text_renderer, streaming_suffix=suffix)
            if show_copy and not is_streaming:
                render_copy_button(text, key="coco_copy_field_latest", label="Copy")
        elif is_streaming:
            render_message_body(
                "_CoCo is thinking…_",
                text_renderer=text_renderer,
                streaming_suffix=" ▍",
            )
        else:
            st.info("Send a message using the CoCo input below.")

        if session.last_error:
            st.error(session.last_error)

        if session.structured_output is not None:
            st.json(session.structured_output)

        if show_tool_details:
            tools = [
                item for item in session.get_transcript_snapshot() if item.get("kind") == "tool"
            ]
            for tool in tools:
                render_tool_card(tool, show_tool_details=True, show_copy=show_copy)

    if container is None:
        _render()
    else:
        with container:
            _render()
