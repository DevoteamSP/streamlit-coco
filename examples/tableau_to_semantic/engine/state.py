"""Session-state accessors and decision provenance for tableau_to_semantic."""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

# Must not collide with CoCo session keys (``tts_estate``, ``tts_access``, …)
# which ``get_or_create_session`` stores directly in ``st.session_state``.
PREFIX = "tts_data_"


def _key(name: str) -> str:
    return f"{PREFIX}{name}"


def ensure_defaults() -> None:
    defaults: dict[str, Any] = {
        "estate": None,
        "metrics": None,
        "access": None,
        "decisions": [],
        "cwd_ready": False,
        "generate_prompted": False,
    }
    for name, value in defaults.items():
        st.session_state.setdefault(_key(name), value)
    hydrate_from_disk()


def _as_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def get_estate() -> dict[str, Any] | None:
    return _as_dict(st.session_state.get(_key("estate")))


def set_estate(payload: dict[str, Any]) -> None:
    st.session_state[_key("estate")] = payload


def get_metrics() -> dict[str, Any] | None:
    return _as_dict(st.session_state.get(_key("metrics")))


def set_metrics(payload: dict[str, Any]) -> None:
    st.session_state[_key("metrics")] = payload


def get_access() -> dict[str, Any] | None:
    return _as_dict(st.session_state.get(_key("access")))


def set_access(payload: dict[str, Any]) -> None:
    st.session_state[_key("access")] = payload


def set_decisions(payload: list[dict[str, Any]]) -> None:
    st.session_state[_key("decisions")] = list(payload)


def get_decisions() -> list[dict[str, Any]]:
    return list(st.session_state.get(_key("decisions")) or [])


def hydrate_from_disk() -> list[str]:
    """Load ``out/*.json``, workspace workbooks, and a saved CoCo brief once per session."""
    flag = _key("hydrated")
    if st.session_state.get(flag):
        return list(st.session_state.get(_key("hydrated_files")) or [])

    from engine.extract import list_twb_files
    from engine.paths import OUT_DIR, WORKSPACE_DIR
    from engine.persist import load_payload, step_has_output

    restored: list[str] = []
    if get_estate() is None:
        payload = load_payload("estate")
        if step_has_output("estate", payload):
            set_estate(payload)
            restored.append("estate_map.json")
    if get_metrics() is None:
        payload = load_payload("kpi")
        if step_has_output("kpi", payload):
            set_metrics(payload)
            restored.append("kpi_inventory.json")
    if get_access() is None:
        payload = load_payload("access")
        if step_has_output("access", payload):
            set_access(payload)
            restored.append("access_rules.json")
    if not get_decisions():
        payload = load_payload("decisions")
        if step_has_output("decisions", payload):
            set_decisions(payload)
            restored.append("decisions.json")
    if list_twb_files(WORKSPACE_DIR):
        set_cwd_ready(True)

    brief = OUT_DIR / "streamlit_dash_coco" / "BRIEF.md"
    if brief.is_file() and brief.stat().st_size > 0:
        text = brief.read_text(encoding="utf-8")
        if text.strip():
            restored.append("streamlit_dash_coco/BRIEF.md")

    st.session_state[flag] = True
    st.session_state[_key("hydrated_files")] = restored
    return restored


def hydrated_files() -> list[str]:
    return list(st.session_state.get(_key("hydrated_files")) or [])


def add_decision(kind: str, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Record an arbitration decision; returns the stored record."""
    record = {
        "id": f"dec_{uuid.uuid4().hex[:10]}",
        "kind": kind,  # "metric" | "access_branch"
        "subject": subject,
        **payload,
    }
    decisions = get_decisions()
    decisions.append(record)
    st.session_state[_key("decisions")] = decisions
    return record


def clear_decisions() -> None:
    st.session_state[_key("decisions")] = []


def set_cwd_ready(ready: bool) -> None:
    st.session_state[_key("cwd_ready")] = ready


def is_cwd_ready() -> bool:
    return bool(st.session_state.get(_key("cwd_ready")))


def metric_decisions() -> list[dict[str, Any]]:
    return [d for d in get_decisions() if d.get("kind") == "metric"]


def access_decisions() -> list[dict[str, Any]]:
    return [d for d in get_decisions() if d.get("kind") == "access_branch"]


def decided_metric_names() -> set[str]:
    return {str(d.get("subject")) for d in metric_decisions()}


def decided_access_subjects() -> set[str]:
    return {str(d.get("subject")) for d in access_decisions()}
