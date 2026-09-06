"""Copilot rail adapter for App Builder."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.actions import start_coco_build
from engine.brief import app_exists
from engine.brief_form import RAIL_NS, collect_form_answers, render_answers_form
from engine.jobs import (
    CONN_KEY,
    GATE_KEY,
    KIND_KEY,
    SESSION_KEY,
    clear_job,
    connection_name,
    get_job,
    is_coco_cooking,
    is_connected,
    list_connections,
    session_options,
    set_copilot_open,
    set_job,
)
from engine.state import (
    RAIL_BRIEF_OPEN_KEY,
    answers,
    apply_brief_answers,
    selected_type,
    slug,
)

EXAMPLE_QUESTIONS = (
    {
        "title": "List the files",
        "question": (
            "List the files in this folder and say what each one is for. "
            "Do not write or edit files."
        ),
    },
    {
        "title": "Explain the brief",
        "question": (
            "Read BRIEF.md if it exists and summarize what this app should do, "
            "what it allows, and what it must not do. Do not write or edit files."
        ),
    },
    {
        "title": "Suggest a change",
        "question": (
            "If streamlit_app.py exists, read it and suggest one concrete UX "
            "improvement. Do not write or edit files unless I ask."
        ),
    },
)


def render_coco_cooking_indicator() -> None:
    cooking, label = is_coco_cooking()
    if not cooking:
        return
    msg = "CoCo is cooking…"
    if label:
        msg = f"CoCo is cooking… · {label}"
    st.status(msg, state="running", expanded=False)


def _connections() -> list[str]:
    names = list_connections()
    try:
        secret = st.secrets.get("snowflake_connection")
    except Exception:  # noqa: BLE001
        secret = None
    if secret and secret not in names:
        names = [str(secret), *names]
    return names


def _rail_answers():
    app_type = selected_type()
    if app_type is None:
        return None
    return collect_form_answers(app_type, answers(), key_ns=RAIL_NS)


def _on_save_rail_brief() -> None:
    values = _rail_answers()
    if values is None:
        return
    apply_brief_answers(values)
    st.toast("Saved brief")


def _on_save_and_regenerate() -> None:
    values = _rail_answers()
    if values is None:
        return
    apply_brief_answers(values)
    current = slug()
    start_coco_build(
        regenerate=bool(current and app_exists(current)),
        values=values,
    )


def render_brief_expander() -> None:
    current = slug()
    app_type = selected_type()
    if not current or app_type is None:
        return
    cooking, _label = is_coco_cooking()
    with st.expander(
        "App brief",
        expanded=bool(st.session_state.get(RAIL_BRIEF_OPEN_KEY)),
        icon=":material/edit_note:",
        type="compact",
    ):
        st.caption(
            "CoCo reads `BRIEF.md`. Edit the owner brief and answers, then save "
            "or regenerate."
        )
        render_answers_form(
            app_type,
            answers(),
            key_ns=RAIL_NS,
            compact=True,
        )
        with st.container(horizontal=True, vertical_alignment="center"):
            st.button(
                "Save",
                icon=":material/save:",
                key="ab_rail_brief_save",
                on_click=_on_save_rail_brief,
            )
            st.button(
                "Save & regenerate",
                type="primary",
                icon=":material/psychology:",
                key="ab_rail_brief_regen",
                disabled=cooking,
                help="Save BRIEF.md and ask CoCo to rewrite the app."
                if not cooking
                else "Wait for the current CoCo job to finish.",
                on_click=_on_save_and_regenerate,
            )


def render_copilot_rail() -> None:
    import streamlit_coco as st_coco

    job = get_job()
    app_type = selected_type()
    job_cwd = (job or {}).get("cwd") or str(st.session_state.get("ab_slug_path") or ".")
    opts = session_options(
        cwd=job_cwd,
        guidelines_skill=app_type.guidelines_skill if app_type else None,
    )

    session = None
    kind = str((job or {}).get("kind") or st.session_state.get(KIND_KEY) or "chat")
    if is_connected():
        if st.session_state.get(KIND_KEY) != kind or st.session_state.get("ab_cwd") != job_cwd:
            session = st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
            st.session_state[KIND_KEY] = kind
            st.session_state["ab_cwd"] = job_cwd
        else:
            session = st_coco.get_or_create_session(opts, key=SESSION_KEY)
            if not session.is_ready and not session.is_connecting:
                session.start()
        job = get_job()

    def _on_connect(chosen: str) -> None:
        st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
        st.session_state[CONN_KEY] = chosen
        st.session_state[GATE_KEY] = True
        st.session_state.pop("ab_coco_connect_hint", None)

    def _on_disconnect() -> None:
        try:
            st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
        except Exception:  # noqa: BLE001
            st.session_state[GATE_KEY] = False
        st.session_state.pop(CONN_KEY, None)
        st.session_state.pop(KIND_KEY, None)
        clear_job()

    def _on_job_finished(job: dict[str, Any]) -> None:
        if get_job() is None:
            return
        kind = str(job.get("kind") or "")
        clear_job()
        if kind == "build":
            st.session_state["ab_preview_auto_run"] = True
            st.rerun()

    def _on_clear() -> None:
        st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
        clear_job()
        st.toast("Chat cleared")

    write_job = bool(job and job.get("kind") == "build")
    if st.session_state.get("ab_coco_connect_hint") and not is_connected():
        st.info("Connect CoCo to build or fix the app.", icon=":material/link:")

    render_brief_expander()
    st_coco.copilot_rail(
        session,
        title="Copilot",
        key_prefix="ab_coco",
        connected=is_connected(),
        connections=_connections(),
        connection_name=connection_name(),
        on_connect=_on_connect,
        on_disconnect=_on_disconnect,
        connect_caption="CoCo CLI auth — generated files live in the app folder.",
        on_close=lambda: set_copilot_open(False),
        on_clear=_on_clear if session is not None else None,
        job=job,
        job_hint=(
            "Approve Write / Edit — CoCo will create or change your app files."
            if write_job
            else None
        ),
        on_cancel_job=clear_job,
        on_job_sent=set_job,
        on_job_finished=_on_job_finished,
        show_copy=False,
        show_transcript_filters=True,
        status_caption=(
            f"cwd · `{job_cwd}` · status · `{session.status.value}`" if session else None
        ),
        input_placeholder=(
            "Approve Writes, or ask to change the app…"
            if write_job
            else "Ask Copilot about this app…"
        ),
        example_questions=EXAMPLE_QUESTIONS,
    )
