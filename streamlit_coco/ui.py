"""Native Streamlit UI for CoCo sessions (no custom component input)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import streamlit as st

from streamlit_coco.ask_user import (
    build_answers_payload,
    choice_labels_with_other,
    extract_questions,
    is_ask_user_question,
    is_other_choice,
    option_is_free_form,
    resolve_selected_labels,
)
from streamlit_coco.debug import is_debug_mode
from streamlit_coco.display import render_output_field, render_session_status, render_transcript
from streamlit_coco.errors import CocoError
from streamlit_coco.permissions import PendingApproval, approve_pending, deny_pending
from streamlit_coco.session import CocoChatResult, CocoRunStatus, CocoSession
from streamlit_coco.text_renderer import TextRenderer
from streamlit_coco.tool_cards import render_approval_preview
from streamlit_coco.tool_extract import extract_plan
from streamlit_coco.tool_names import ToolFamily, family_label, is_exit_plan_mode, tool_family

StructuredOutputCallback = Callable[[dict[str, Any], CocoChatResult], None]


def send_prompt(session: CocoSession, prompt: str) -> None:
    """Queue a user prompt on the CoCo session."""
    text = prompt.strip()
    if not text:
        return
    try:
        session.send(text)
    except CocoError as exc:
        st.error(str(exc))


def request_input(
    question: str,
    *,
    key: str = "coco_input",
    default: str = "",
    schema: list[dict[str, Any]] | dict[str, Any] | None = None,
    submit_label: str = "Submit",
    cancel_label: str | None = "Cancel",
) -> str | dict[str, Any] | None:
    """App-owned clarification form between turns (not a CoCo tool channel).

    Mid-turn agent questions use AskUserQuestion via ``panel()`` / approvals.
    Use this helper for wizard steps, gates, or multi-field follow-ups the app owns.

    Parameters
    ----------
    question:
        Prompt shown above the form.
    schema:
        Optional field list (or single field dict). Each field may include
        ``name``, ``label``, ``type`` (``text`` / ``textarea`` / ``number`` /
        ``select``), ``default``, ``options`` (for select), and ``required``.
    Returns
    -------
    ``None`` until the user submits. Then a ``str`` (no schema) or ``dict`` of
    field values (with schema). Cancel returns ``None`` and clears the form.
    """
    st.markdown(question)
    fields = _normalize_input_schema(schema)
    submitted_key = f"{key}__submitted"
    cancelled_key = f"{key}__cancelled"

    if st.session_state.pop(cancelled_key, False):
        return None

    if fields:
        with st.form(key=f"{key}__form", clear_on_submit=True):
            values: dict[str, Any] = {}
            for index, field in enumerate(fields):
                name = str(field.get("name") or f"field_{index}")
                label = str(field.get("label") or name)
                field_type = str(field.get("type") or "text").lower()
                field_default = field.get("default", default if index == 0 else "")
                widget_key = f"{key}__{name}"

                if field_type in {"textarea", "text_area"}:
                    values[name] = st.text_area(
                        label,
                        value=str(field_default or ""),
                        key=widget_key,
                    )
                elif field_type == "number":
                    values[name] = st.text_input(
                        label,
                        value=str(field_default or ""),
                        key=widget_key,
                    )
                elif field_type == "select":
                    options = [str(opt) for opt in (field.get("options") or [])]
                    values[name] = st.selectbox(
                        label,
                        options=options or [""],
                        index=0,
                        key=widget_key,
                    )
                else:
                    values[name] = st.text_input(
                        label,
                        value=str(field_default or ""),
                        key=widget_key,
                    )

            cols = st.columns(2 if cancel_label else 1)
            with cols[0]:
                submitted = st.form_submit_button(submit_label, type="primary", width="stretch")
            cancelled = False
            if cancel_label and len(cols) > 1:
                with cols[1]:
                    cancelled = st.form_submit_button(cancel_label, width="stretch")

        if cancelled:
            st.session_state[cancelled_key] = True
            st.rerun()
        if not submitted:
            return None

        cleaned: dict[str, Any] = {}
        for field in fields:
            name = str(field.get("name") or "")
            raw = values.get(name)
            text = str(raw or "").strip()
            required = bool(field.get("required", True))
            if required and not text:
                st.warning(f"Please fill in **{field.get('label') or name}**.")
                return None
            cleaned[name] = text
        st.session_state[submitted_key] = cleaned
        return cleaned

    with st.form(key=f"{key}__form", clear_on_submit=True):
        answer = st.text_input(
            "Your answer",
            value=default,
            key=f"{key}__text",
            label_visibility="collapsed",
        )
        cols = st.columns(2 if cancel_label else 1)
        with cols[0]:
            submitted = st.form_submit_button(submit_label, type="primary", width="stretch")
        cancelled = False
        if cancel_label and len(cols) > 1:
            with cols[1]:
                cancelled = st.form_submit_button(cancel_label, width="stretch")

    if cancelled:
        st.session_state[cancelled_key] = True
        st.rerun()
    if not submitted:
        return None
    text = answer.strip()
    if not text:
        st.warning("Please enter an answer.")
        return None
    return text


def _normalize_input_schema(
    schema: list[dict[str, Any]] | dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if schema is None:
        return []
    if isinstance(schema, dict):
        return [schema]
    return [field for field in schema if isinstance(field, dict)]


def render_plan_banner(
    session: CocoSession,
    *,
    key_prefix: str = "coco",
    execute_prompt: str = "Execute the approved plan.",
    plan_state_key: str | None = "coco_plan_mode",
) -> bool:
    """Show plan-mode banner with an Execute CTA. Returns True when rendered."""
    if session.options.permission_mode != "plan":
        return False

    pending = session.permission_manager.active_pending()
    if pending is not None and is_exit_plan_mode(pending.tool_name):
        # ExitPlanMode UI owns the approval — avoid a duplicate Execute button.
        return False

    with st.container(border=True):
        st.markdown("**Plan mode** — CoCo is planning; edits wait until you execute.")
        cols = st.columns([3, 1])
        with cols[1]:
            if st.button(
                "Execute plan",
                key=f"{key_prefix}_execute_plan",
                type="primary",
                width="stretch",
            ):
                try:
                    session.execute_plan(prompt=execute_prompt)
                except CocoError as exc:
                    st.error(str(exc))
                if plan_state_key is not None and plan_state_key in st.session_state:
                    st.session_state[plan_state_key] = False
                st.rerun()
    return True


def render_ask_user_question(
    session: CocoSession,
    pending: PendingApproval,
    *,
    key_prefix: str = "coco",
) -> bool:
    """Render interactive controls for an AskUserQuestion permission request."""
    questions = extract_questions(pending.tool_input)
    if not questions:
        st.warning("CoCo asked a question, but no options were provided.")
        if st.button("Dismiss", key=f"{key_prefix}_ask_dismiss_{pending.request_id}"):
            deny_pending(session, pending.request_id, reason="No questions provided")
            st.rerun()
        return True

    st.info("CoCo needs your input to continue.")
    answers: dict[str, str] = {}
    complete = True

    for index, question in enumerate(questions):
        question_text = str(question.get("question") or "").strip()
        header = str(question.get("header") or "").strip() or f"Question {index + 1}"
        options = [opt for opt in (question.get("options") or []) if isinstance(opt, dict)]
        multi = bool(question.get("multiSelect") or question.get("multi_select"))
        key_base = f"{key_prefix}_ask_{pending.request_id}_{index}"
        answer_key = question_text or header

        st.markdown(f"**{header}**")
        if question_text:
            st.markdown(question_text)

        if not options:
            free_text = st.text_input("Your answer", key=f"{key_base}_text")
            if free_text.strip():
                answers[answer_key] = free_text.strip()
            else:
                complete = False
            continue

        display_labels = choice_labels_with_other(options)
        if multi:
            selected = st.multiselect(
                "Select one or more options",
                options=display_labels,
                key=f"{key_base}_multi",
                label_visibility="collapsed",
            )
            labels = resolve_selected_labels(options, selected)
            if not labels:
                complete = False
                continue

            free_parts: list[str] = []
            needs_other = any(is_other_choice(label) for label in labels)
            other_text = ""
            if needs_other:
                other_text = st.text_input(
                    "Other — please specify",
                    key=f"{key_base}_other",
                    placeholder="Type your answer…",
                ).strip()
                if not other_text:
                    complete = False

            for label in labels:
                if is_other_choice(label):
                    if other_text:
                        free_parts.append(other_text)
                    continue
                option = next(
                    (opt for opt in options if str(opt.get("label") or "") == label),
                    None,
                )
                if option is not None and option_is_free_form(option):
                    custom = st.text_input(
                        f"Details for {label}",
                        key=f"{key_base}_free_{label}",
                    ).strip()
                    free_parts.append(custom or label)
                else:
                    free_parts.append(label)

            if free_parts:
                answers[answer_key] = ", ".join(free_parts)
            else:
                complete = False
        else:
            selected = st.radio(
                "Select an option",
                options=display_labels,
                key=f"{key_base}_radio",
                label_visibility="collapsed",
            )
            labels = resolve_selected_labels(options, selected)
            if not labels:
                complete = False
                continue

            label = labels[0]
            if is_other_choice(label):
                other_text = st.text_input(
                    "Other — please specify",
                    key=f"{key_base}_other",
                    placeholder="Type your answer…",
                ).strip()
                if other_text:
                    answers[answer_key] = other_text
                else:
                    complete = False
                continue

            option = next((opt for opt in options if str(opt.get("label") or "") == label), None)
            if option is not None and option_is_free_form(option):
                custom = st.text_input(
                    "Add details",
                    key=f"{key_base}_free",
                ).strip()
                answers[answer_key] = custom or label
            else:
                answers[answer_key] = label

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Submit answers",
            key=f"{key_prefix}_ask_submit_{pending.request_id}",
            type="primary",
            width="stretch",
            disabled=not complete,
        ):
            approve_pending(
                session,
                pending.request_id,
                updated_input=build_answers_payload(questions, answers),
            )
            st.rerun()
    with col2:
        if st.button(
            "Cancel",
            key=f"{key_prefix}_ask_cancel_{pending.request_id}",
            width="stretch",
        ):
            deny_pending(session, pending.request_id, reason="User cancelled")
            st.rerun()

    return True


def render_exit_plan(
    session: CocoSession,
    pending: PendingApproval,
    *,
    key_prefix: str = "coco",
) -> bool:
    """Render plan-mode exit approval (ExitPlanMode)."""
    st.warning("Approve this plan to leave plan mode and continue.")
    plan = extract_plan(pending.tool_input)
    question = ""
    if isinstance(pending.tool_input, dict):
        raw = pending.tool_input.get("question")
        if isinstance(raw, str):
            question = raw.strip()
    if question:
        st.markdown(question)
    if plan:
        with st.container(border=True):
            st.markdown(plan)
    else:
        st.caption("No plan text was provided.")

    reason = st.text_input(
        "Rejection feedback (optional)",
        key=f"{key_prefix}_plan_reason_{pending.request_id}",
        placeholder="Tell CoCo what to revise…",
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Approve plan",
            key=f"{key_prefix}_plan_approve_{pending.request_id}",
            type="primary",
            width="stretch",
        ):
            approve_pending(
                session,
                pending.request_id,
                updated_input={"message": "Plan approved."},
            )
            st.rerun()
    with col2:
        if st.button(
            "Reject plan",
            key=f"{key_prefix}_plan_deny_{pending.request_id}",
            width="stretch",
        ):
            deny_pending(
                session,
                pending.request_id,
                reason=reason.strip() or "Plan rejected by user",
            )
            st.rerun()
    return True


def render_approvals(
    session: CocoSession,
    *,
    key_prefix: str = "coco",
    show_tool_input: bool | None = None,
) -> bool:
    """Render native approval controls when a tool is awaiting confirmation.

    Raw tool payloads appear only in CoCo debug mode (or when
    ``show_tool_input=True``). AskUserQuestion and ExitPlanMode use dedicated UIs.
    """
    pending = session.permission_manager.active_pending()
    if pending is None:
        return False

    if is_ask_user_question(pending.tool_name):
        return render_ask_user_question(session, pending, key_prefix=key_prefix)

    if is_exit_plan_mode(pending.tool_name):
        return render_exit_plan(session, pending, key_prefix=key_prefix)

    family = tool_family(pending.tool_name)
    label = family_label(family, pending.tool_name)
    st.warning(f"CoCo wants to run **{label}** — approve or deny to continue.")
    render_approval_preview(pending.tool_name, pending.tool_input)

    reveal_input = is_debug_mode() if show_tool_input is None else show_tool_input
    if reveal_input:
        with st.expander("Raw tool payload", expanded=False):
            st.json(pending.tool_input)

    show_always = family not in {ToolFamily.ASK_USER, ToolFamily.EXIT_PLAN}
    cols = st.columns(3 if show_always else 2)
    with cols[0]:
        if st.button(
            "Approve once",
            key=f"{key_prefix}_approve_{pending.request_id}",
            type="primary",
            width="stretch",
        ):
            approve_pending(session, pending.request_id)
            st.rerun()
    if show_always:
        with cols[1]:
            if st.button(
                f"Always allow {label}",
                key=f"{key_prefix}_always_{pending.request_id}",
                width="stretch",
            ):
                approve_pending(session, pending.request_id, always=True)
                st.rerun()
        with cols[2]:
            if st.button(
                "Deny",
                key=f"{key_prefix}_deny_{pending.request_id}",
                width="stretch",
            ):
                deny_pending(session, pending.request_id, reason="Denied by user")
                st.rerun()
    else:
        with cols[1]:
            if st.button(
                "Deny",
                key=f"{key_prefix}_deny_{pending.request_id}",
                width="stretch",
            ):
                deny_pending(session, pending.request_id, reason="Denied by user")
                st.rerun()

    return True


def panel(
    session: CocoSession,
    *,
    output_label: str | None = "CoCo output",
    output_mode: str = "transcript",
    show_tool_details: bool = True,
    show_thinking: bool = False,
    show_approvals: bool = True,
    show_stop: bool = True,
    show_status: bool = True,
    show_plan_banner: bool = True,
    warm_up: bool = False,
    status_expanded: str = "auto",
    approval_key_prefix: str = "coco",
    use_fragment: bool = True,
    run_every: float | None = 0.25,
    text_renderer: TextRenderer = None,
    show_copy: bool = True,
    max_messages: int | None = None,
    preview_chars: int | None = None,
    on_structured_output: StructuredOutputCallback | None = None,
    structured_output_container: Any | None = None,
) -> CocoChatResult:
    """Render CoCo output and controls with native Streamlit widgets.

    Parameters
    ----------
    show_status:
        Show a ``st.status`` / caption strip for connect and turn progress.
    warm_up:
        Start connecting the SDK client as soon as the panel mounts (before the
        first prompt). Pair with fragment polling so the UI shows "Starting CoCo…".
    status_expanded:
        ``\"auto\"`` expands while busy, ``\"always\"`` / ``\"never\"`` force the state.
    text_renderer:
        How to render assistant/user text: ``None`` / ``\"markdown\"`` (default),
        ``\"write\"``, ``\"text\"``, ``\"caption\"``, ``\"code\"``, or a callable.
        Default markdown mode highlights fenced code blocks via ``st.code``.
    show_copy:
        Show clipboard controls on assistant messages and tool cards.
    max_messages:
        Optional transcript window size; shows **Load earlier** when truncated.
    preview_chars:
        Optional cap on user/assistant text length in the transcript.
    """

    session.set_show_structured_inline(
        on_structured_output is None and structured_output_container is None
    )

    if warm_up and session.status == CocoRunStatus.IDLE:
        session.start()

    def _render_output(*, include_approvals: bool = True) -> CocoChatResult:
        connecting = session.is_connecting

        if show_status:
            render_session_status(session, expanded=status_expanded)

        if show_plan_banner and not connecting:
            render_plan_banner(session, key_prefix=approval_key_prefix)

        # During connect, the status card already includes a soft skeleton —
        # skip the empty transcript so the UI doesn't flash two panels.
        if output_label is not None and not connecting:
            with st.container(border=True):
                if output_mode == "field":
                    render_output_field(
                        session,
                        label=output_label,
                        show_tool_details=show_tool_details,
                        text_renderer=text_renderer,
                        show_copy=show_copy,
                    )
                else:
                    render_transcript(
                        session,
                        show_tool_details=show_tool_details,
                        show_thinking=show_thinking,
                        hide_active_approval=include_approvals and show_approvals,
                        text_renderer=text_renderer,
                        show_copy=show_copy,
                        max_messages=max_messages,
                        preview_chars=preview_chars,
                    )

        if include_approvals and show_approvals and not connecting:
            render_approvals(session, key_prefix=approval_key_prefix)

        if show_stop and session.needs_polling and not connecting:
            if st.button("Stop CoCo", key=f"{approval_key_prefix}_stop", type="secondary"):
                session.cancel()
                st.rerun()

        result = session.chat_result()
        if not connecting:
            _maybe_render_structured_output(
                session=session,
                result=result,
                callback=on_structured_output,
                container=structured_output_container,
            )
        return result

    if not use_fragment:
        return _render_output()

    fragment_kwargs: dict[str, Any] = {}
    poll_seconds = run_every
    pending = session.permission_manager.active_pending() is not None
    if poll_seconds is None and (session.needs_polling or output_label is not None):
        poll_seconds = 0.25
    # Pause auto-polling while waiting for approval so buttons stay clickable.
    if poll_seconds is not None and not pending:
        fragment_kwargs["run_every"] = timedelta(seconds=poll_seconds)
    polling_active = "run_every" in fragment_kwargs

    @st.fragment(**fragment_kwargs)
    def _output_fragment() -> CocoChatResult:
        if polling_active and session.permission_manager.active_pending() is not None:
            # run_every was enabled before the worker blocked on can_use_tool;
            # rerun the full script so approvals render without polling.
            st.rerun()

        boot_key = f"_coco_was_connecting_{session.key or id(session)}"
        if session.is_connecting:
            st.session_state[boot_key] = True
        elif st.session_state.pop(boot_key, False):
            # chat_input lives outside this fragment — refresh so it re-enables.
            st.rerun()

        return _render_output(include_approvals=True)

    return _output_fragment()


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
