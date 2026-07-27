"""Native Streamlit rendering for CoCo transcripts and streaming output."""

from __future__ import annotations

from typing import Any

import streamlit as st

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


def render_transcript(
    session: CocoSession,
    container: Any | None = None,
    *,
    show_tool_details: bool = True,
    show_thinking: bool = False,
    show_streaming_cursor: bool = True,
    hide_active_approval: bool = False,
    text_renderer: TextRenderer = None,
) -> None:
    """Render the conversation into a Streamlit container or the current context."""
    render_text = resolve_text_renderer(text_renderer)
    transcript = session.get_transcript_snapshot()
    is_streaming = session.status == CocoRunStatus.RUNNING and session.needs_polling
    active_pending = session.permission_manager.active_pending()
    active_approval_id = active_pending.request_id if active_pending else None

    def _render() -> None:
        if not transcript:
            st.caption("CoCo responses will appear here.")
            return

        last_assistant_idx = -1
        for idx, item in enumerate(transcript):
            if item.get("role") == "assistant" and item.get("kind") == "text":
                last_assistant_idx = idx

        for idx, item in enumerate(transcript):
            role = item.get("role")
            kind = item.get("kind")

            if role == "user":
                with st.chat_message("user"):
                    render_text(str(item.get("content") or ""))
                continue

            if kind == "text":
                content = str(item.get("content") or "")
                streaming = (
                    show_streaming_cursor and is_streaming and idx == last_assistant_idx and content
                )
                with st.chat_message("assistant"):
                    render_text(content + (" ▍" if streaming else ""))
                continue

            if kind == "tool":
                render_tool_card(item, show_tool_details=show_tool_details)
                continue

            if kind == "structured_output":
                with st.container(border=True):
                    st.markdown("**Structured output**")
                    st.json(item.get("content"))
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
                render_text("_CoCo is thinking…_ ▍")

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
        label = pending.tool_name
        with st.container(border=True):
            st.markdown(f"**Needs your input** · `{label}`")
            if show_details:
                st.caption("Approve, deny, or answer to continue.")
        return

    if session.status == CocoRunStatus.RUNNING:
        tool = _latest_tool_activity(session)
        with st.container(border=True):
            if tool and tool.get("status") == "running":
                st.markdown(f"**Working** · tool `{tool.get('name')}`")
            else:
                st.markdown("**Working** · thinking…")
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
) -> None:
    """Render a focused output panel with the latest assistant response."""
    render_text = resolve_text_renderer(text_renderer)
    text = get_latest_assistant_text(session)
    is_streaming = session.status == CocoRunStatus.RUNNING and session.needs_polling
    suffix = " ▍" if is_streaming and text else ""

    def _render() -> None:
        st.subheader(label)
        st.caption(f"Status: **{session.status.value}** · revision {session.get_revision()}")

        if text:
            render_text(text + suffix)
        elif is_streaming:
            render_text("_CoCo is thinking…_ ▍")
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
                render_tool_card(tool, show_tool_details=True)

    if container is None:
        _render()
    else:
        with container:
            _render()
