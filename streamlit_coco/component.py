"""Streamlit Custom Component v2 mount helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from functools import lru_cache
from importlib import resources
from typing import Any

import streamlit as st

from streamlit_coco.bridge import build_component_data
from streamlit_coco.display import render_output_field, render_transcript
from streamlit_coco.errors import CocoError
from streamlit_coco.options import CocoOptions
from streamlit_coco.permissions import approve_pending, deny_pending
from streamlit_coco.session import CocoChatResult, CocoSession
from streamlit_coco.ui import request_input as request_input

StructuredOutputCallback = Callable[[dict[str, Any], CocoChatResult], None]


def _fragment_poll_seconds(
    session: CocoSession,
    run_every: float | None,
    *,
    default_when: bool,
) -> float | None:
    """Seconds for ``@st.fragment(run_every=…)``, or ``None`` to pause polling.

    Pauses while a HITL approval is pending so Approve / Deny buttons stay
    clickable (parity with ``panel()``).
    """
    if session.permission_manager.active_pending() is not None:
        return None
    if run_every is not None:
        return run_every
    if default_when:
        return 0.25
    return None


@lru_cache
def _load_asset(name: str) -> str:
    return resources.files("streamlit_coco.frontend").joinpath(name).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _get_component():
    """Register the CCv2 component once (CCv2 skill: never re-register on each mount)."""
    if not hasattr(st.components, "v2"):
        raise RuntimeError(
            "streamlit-coco requires Streamlit >= 1.53 with Custom Components v2. "
            f"Installed version: {st.__version__}"
        )
    # isolate_styles=True (explicit): shadow-root CSS so component styles do not
    # leak into the host app (CCv2 skill default; document intent in chat-ccv2.md).
    return st.components.v2.component(
        "streamlit_coco",
        html=_load_asset("index.html"),
        css=_load_asset("style.css"),
        js=_load_asset("main.js"),
        isolate_styles=True,
    )


def chat(
    *,
    session: CocoSession | None = None,
    options: CocoOptions | None = None,
    key: str = "coco_chat",
    height: int = 600,
    show_tool_details: bool = True,
    show_thinking: bool = False,
    placeholder: str = "Ask CoCo about your data…",
    use_fragment: bool = True,
    run_every: float | None = None,
    output_container: Any | None = None,
    output_label: str | None = None,
    output_mode: str = "transcript",
    show_transcript_in_component: bool | None = None,
    on_structured_output: StructuredOutputCallback | None = None,
    structured_output_container: Any | None = None,
    on_event: Callable[..., None] | None = None,
    on_submit_change: Callable[..., None] | None = None,
    on_approval_change: Callable[..., None] | None = None,
    on_cancel_change: Callable[..., None] | None = None,
) -> CocoChatResult:
    """Render the CoCo chat component and return the latest chat result."""
    session = _resolve_session(session=session, options=options, key=key)

    if show_transcript_in_component is None:
        show_transcript_in_component = output_container is None and output_label is None

    session.set_show_structured_inline(
        show_transcript_in_component
        and on_structured_output is None
        and structured_output_container is None
    )

    if on_event is not None:
        session.add_event_listener(on_event)

    def _render_panel() -> CocoChatResult:
        return _render_chat_panel(
            session=session,
            key=key,
            height=height,
            show_tool_details=show_tool_details,
            show_thinking=show_thinking,
            placeholder=placeholder,
            output_container=output_container,
            output_label=output_label,
            output_mode=output_mode,
            show_transcript_in_component=show_transcript_in_component,
            on_structured_output=on_structured_output,
            structured_output_container=structured_output_container,
            on_submit_change=on_submit_change,
            on_approval_change=on_approval_change,
            on_cancel_change=on_cancel_change,
        )

    if use_fragment:
        poll_seconds = _fragment_poll_seconds(
            session,
            run_every,
            default_when=session.needs_polling
            or output_container is not None
            or output_label is not None,
        )
        fragment_kwargs: dict[str, Any] = {}
        if poll_seconds is not None:
            fragment_kwargs["run_every"] = timedelta(seconds=poll_seconds)
        polling_active = poll_seconds is not None

        @st.fragment(**fragment_kwargs)
        def _fragment_panel() -> CocoChatResult:
            if polling_active and session.permission_manager.active_pending() is not None:
                st.rerun()
            return _render_panel()

        return _fragment_panel()

    return _render_panel()


def _resolve_session(
    *,
    session: CocoSession | None,
    options: CocoOptions | None,
    key: str,
) -> CocoSession:
    if session is not None:
        return session

    state_key = f"_coco_session_{key}"
    existing = st.session_state.get(state_key)
    if existing is not None:
        resolved = existing
    else:
        resolved = CocoSession(options=options or CocoOptions(), key=state_key)
        st.session_state[state_key] = resolved

    if options is not None and hasattr(resolved, "options"):
        new_hash = options.options_hash()
        old_hash = st.session_state.get(f"{state_key}_options_hash")
        if old_hash is not None and old_hash != new_hash:
            resolved.reset()
        st.session_state[f"{state_key}_options_hash"] = new_hash
        resolved.options = options

    return resolved


def _render_chat_panel(
    *,
    session: CocoSession,
    key: str,
    height: int,
    show_tool_details: bool,
    show_thinking: bool,
    placeholder: str,
    output_container: Any | None,
    output_label: str | None,
    output_mode: str,
    show_transcript_in_component: bool,
    on_structured_output: StructuredOutputCallback | None,
    structured_output_container: Any | None,
    on_submit_change: Callable[..., None] | None,
    on_approval_change: Callable[..., None] | None,
    on_cancel_change: Callable[..., None] | None,
) -> CocoChatResult:
    target_output = output_container
    if target_output is None and output_label is not None:
        target_output = st.container(border=True)

    if target_output is not None:
        if output_mode == "field":
            render_output_field(
                session,
                target_output,
                label=output_label or "CoCo output",
                show_tool_details=show_tool_details,
            )
        else:
            render_transcript(
                session,
                target_output,
                show_tool_details=show_tool_details,
                show_thinking=show_thinking,
            )

    component = _get_component()
    show_structured_inline = (
        show_transcript_in_component
        and on_structured_output is None
        and structured_output_container is None
    )
    component_height = 160 if target_output is not None else height

    def handle_submit() -> None:
        component_state = st.session_state.get(key, {})
        payload = component_state.get("submit_prompt")
        if isinstance(payload, dict) and payload.get("text"):
            try:
                session.send(str(payload["text"]))
            except CocoError as exc:
                st.error(str(exc))
        if on_submit_change is not None:
            on_submit_change()

    def handle_approve() -> None:
        component_state = st.session_state.get(key, {})
        payload = component_state.get("approve_tool")
        if isinstance(payload, dict) and payload.get("request_id"):
            approve_pending(
                session,
                str(payload["request_id"]),
                always=bool(payload.get("always")),
            )
        if on_approval_change is not None:
            on_approval_change()

    def handle_deny() -> None:
        component_state = st.session_state.get(key, {})
        payload = component_state.get("deny_tool")
        if isinstance(payload, dict) and payload.get("request_id"):
            deny_pending(
                session,
                str(payload["request_id"]),
                reason=str(payload.get("reason") or "Denied by user"),
            )
        if on_approval_change is not None:
            on_approval_change()

    def handle_cancel() -> None:
        session.cancel()
        if on_cancel_change is not None:
            on_cancel_change()

    def handle_execute_plan() -> None:
        component_state = st.session_state.get(key, {})
        payload = component_state.get("execute_plan")
        prompt = "Execute the approved plan."
        if isinstance(payload, dict) and payload.get("prompt"):
            prompt = str(payload["prompt"])
        try:
            session.execute_plan(prompt=prompt)
        except CocoError as exc:
            st.error(str(exc))
        if "coco_plan_mode" in st.session_state:
            st.session_state["coco_plan_mode"] = False

    data = build_component_data(
        session,
        placeholder=placeholder,
        show_tool_details=show_tool_details,
        show_thinking=show_thinking,
        show_structured_inline=show_structured_inline,
        height=component_height,
        include_transcript=show_transcript_in_component,
    )

    # Triggers: submit_prompt, approve_tool, deny_tool, cancel_run, execute_plan.
    # No provide_input channel (dropped — use AskUserQuestion / panel() HITL).
    component(
        key=key,
        data=data,
        height=component_height,
        on_submit_prompt_change=handle_submit,
        on_approve_tool_change=handle_approve,
        on_deny_tool_change=handle_deny,
        on_cancel_run_change=handle_cancel,
        on_execute_plan_change=handle_execute_plan,
    )

    result = session.chat_result()
    _maybe_render_structured_output(
        session=session,
        result=result,
        callback=on_structured_output,
        container=structured_output_container,
    )
    return result


def _maybe_render_structured_output(
    *,
    session: CocoSession,
    result: CocoChatResult,
    callback: StructuredOutputCallback | None,
    container: Any | None,
) -> None:
    if result.structured_output is None:
        return

    rendered_key = f"_coco_structured_rendered_{session.key or id(session)}"
    event_id = result.last_result.id if result.last_result else None
    if event_id is not None and st.session_state.get(rendered_key) == event_id:
        return

    payload = result.structured_output
    if not isinstance(payload, dict):
        payload = {"value": payload}

    if callback is not None:
        callback(payload, result)
    elif container is not None:
        with container:
            st.json(payload)
    else:
        return

    if event_id is not None:
        st.session_state[rendered_key] = event_id
