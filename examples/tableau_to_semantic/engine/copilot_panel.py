"""Tableau adapter around the generic ``st_coco.copilot_rail``."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine import state
from engine.coco_jobs import (
    CONN_KEY,
    GATE_KEY,
    SCHEMA_KIND_KEY,
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
from engine.extract import accept_structured, load_schema
from engine.paths import OUT_DIR, WORKSPACE_DIR


def render_coco_cooking_indicator() -> None:
    cooking, label = is_coco_cooking()
    if not cooking:
        return
    msg = "CoCo is cooking…"
    if label:
        msg = f"CoCo is cooking… · {label}"
    st.status(msg, state="running", expanded=False)


def _apply_structured_output(kind: str, data: dict[str, Any]) -> None:
    schema_name = {
        "estate": "estate_map.schema.json",
        "kpi": "kpi_inventory.schema.json",
        "access": "access_rules.schema.json",
    }.get(kind)
    if not schema_name:
        return
    schema = load_schema(schema_name)
    setters = {
        "estate": state.set_estate,
        "kpi": state.set_metrics,
        "access": state.set_access,
    }
    ok, errors = accept_structured(data, schema=schema, on_ok=setters[kind])
    clear_job()
    if ok:
        st.toast(f"Stored · {kind}")
        st.rerun()
    st.error("Payload failed schema validation:")
    for err in errors[:12]:
        st.caption(f"- {err}")
    with st.expander("Raw payload"):
        st.json(data)


def _on_job_finished(job: dict[str, Any]) -> None:
    if get_job() is None:
        return
    kind = job.get("kind")
    clear_job()
    if kind in {"generate", "streamlit", "chat"}:
        return
    st.session_state["tts_coco_job_missed_output"] = job.get("label") or kind or "Job"


def _fail_stale_job(session: Any) -> None:
    job = get_job()
    if not job:
        return
    from streamlit_coco.rail import sent_job_is_complete

    saw = bool(st.session_state.get("tts_coco_job_saw_running"))
    if sent_job_is_complete(session, job, saw_running=saw):
        _on_job_finished(job)


def _connections() -> list[str]:
    names = list_connections()
    try:
        secret = st.secrets.get("snowflake_connection")
    except Exception:  # noqa: BLE001
        secret = None
    if secret and secret not in names:
        names = [str(secret), *names]
    return names


def render_copilot_rail() -> None:
    import streamlit_coco as st_coco
    from streamlit_coco.rail import copilot_rail

    job = get_job()
    if job:
        kind = str(job.get("kind") or "chat")
    else:
        kind = str(st.session_state.get(SCHEMA_KIND_KEY) or "chat")
    if kind not in {"estate", "kpi", "access", "generate", "streamlit", "chat"}:
        kind = "chat"
    job_cwd = (job or {}).get("cwd") or str(
        OUT_DIR if kind in {"generate", "streamlit"} else WORKSPACE_DIR
    )
    opts = session_options(kind=kind, cwd=job_cwd)  # type: ignore[arg-type]

    session = None
    if is_connected():
        if st.session_state.get(SCHEMA_KIND_KEY) != kind:
            session = st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
            st.session_state[SCHEMA_KIND_KEY] = kind
        else:
            session = st_coco.get_or_create_session(opts, key=SESSION_KEY)
            if not session.is_ready and not session.is_connecting:
                session.start()
        _fail_stale_job(session)
        job = get_job()

    def _on_connect(chosen: str) -> None:
        st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
        st.session_state[CONN_KEY] = chosen
        st.session_state[GATE_KEY] = True
        st.session_state[SCHEMA_KIND_KEY] = "access"

    def _on_disconnect() -> None:
        try:
            st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
        except Exception:  # noqa: BLE001
            st.session_state[GATE_KEY] = False
        st.session_state.pop(CONN_KEY, None)
        st.session_state.pop(SCHEMA_KIND_KEY, None)
        clear_job()

    def _on_structured(data: dict, result: st_coco.CocoChatResult) -> None:  # noqa: ARG001
        active = get_job()
        if not active or active.get("kind") not in {"estate", "kpi", "access"}:
            return
        _apply_structured_output(str(active["kind"]), data if isinstance(data, dict) else {})

    def _on_clear() -> None:
        st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
        st.session_state[SCHEMA_KIND_KEY] = kind
        clear_job()
        st.toast("Chat cleared")

    write_job = bool(job and job.get("kind") in {"generate", "streamlit"})
    placeholder = "Ask about the workbooks…"
    if job and write_job:
        placeholder = "Approve Writes, or ask a follow-up…"
    elif job:
        placeholder = "Waiting for structured output…"

    missed = st.session_state.pop("tts_coco_job_missed_output", None)
    if missed:
        st.warning(
            f"**{missed}** finished without structured output. "
            "Check the Copilot transcript, then retry."
        )

    copilot_rail(
        session,
        title="Copilot",
        key_prefix="tts_coco",
        connected=is_connected(),
        connections=_connections(),
        connection_name=connection_name(),
        on_connect=_on_connect,
        on_disconnect=_on_disconnect,
        connect_caption="CoCo CLI auth — workbooks live in the agent workspace.",
        on_close=lambda: set_copilot_open(False),
        on_clear=_on_clear if session is not None else None,
        job=job,
        job_hint=("Approve Write / Edit — Copilot shows the unified diff." if write_job else None),
        on_cancel_job=clear_job,
        on_job_sent=set_job,
        on_job_finished=_on_job_finished,
        on_structured_output=_on_structured,
        show_copy=False,
        show_transcript_filters=True,
        status_caption=(
            f"cwd · `{job_cwd}` · status · `{session.status.value}`" if session else None
        ),
        input_placeholder=placeholder,
    )
