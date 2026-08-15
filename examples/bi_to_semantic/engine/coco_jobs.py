"""Shared CoCo connection + generation jobs for bi_to_semantic.

Screens only queue a job. Copilot and Preview can be open together.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import streamlit as st

from engine.extract import (
    ESTATE_MAP_PROMPT,
    KPI_INVENTORY_PROMPT,
    access_rules_prompt,
    load_schema,
)
from engine.paths import OUT_DIR, WORKSPACE_DIR

SESSION_KEY = "tts_coco"
GATE_KEY = "tts_coco_connected"
CONN_KEY = "tts_coco_connection"
JOB_KEY = "tts_coco_job"
SCHEMA_KIND_KEY = "tts_coco_schema_kind"
OPEN_KEY = "tts_copilot_open"
RAIL_KEY = "tts_rail"
PREVIEW_KEY = "tts_preview_open"
PREVIEW_FULL_KEY = "tts_preview_full"

JobKind = Literal["estate", "kpi", "access", "generate", "streamlit", "chat"]


def list_connections() -> list[str]:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    cfg = Path.home() / ".snowflake" / "connections.toml"
    if not cfg.is_file():
        return []
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    return sorted(data.keys())


def is_connected() -> bool:
    return bool(st.session_state.get(GATE_KEY) and st.session_state.get(CONN_KEY))


def connection_name() -> str | None:
    return st.session_state.get(CONN_KEY)


def is_copilot_open() -> bool:
    return bool(st.session_state.get(OPEN_KEY))


def is_preview_open() -> bool:
    return bool(st.session_state.get(PREVIEW_KEY))


def is_rail_open() -> bool:
    return is_copilot_open() or is_preview_open()


def rail_panel() -> str | None:
    copilot = is_copilot_open()
    preview = is_preview_open()
    if copilot and preview:
        st.session_state[RAIL_KEY] = "both"
        return "both"
    if copilot:
        st.session_state[RAIL_KEY] = "copilot"
        return "copilot"
    if preview:
        st.session_state[RAIL_KEY] = "preview"
        return "preview"
    st.session_state[RAIL_KEY] = None
    return None


def _sync_rail_key() -> None:
    rail_panel()


def set_rail(panel: str | None) -> None:
    if panel == "both":
        st.session_state[OPEN_KEY] = True
        st.session_state[PREVIEW_KEY] = True
    elif panel == "copilot":
        st.session_state[OPEN_KEY] = True
    elif panel == "preview":
        st.session_state[PREVIEW_KEY] = True
    else:
        st.session_state[OPEN_KEY] = False
        st.session_state[PREVIEW_KEY] = False
        st.session_state[PREVIEW_FULL_KEY] = False
    _sync_rail_key()


def is_preview_full() -> bool:
    return is_preview_open() and bool(st.session_state.get(PREVIEW_FULL_KEY))


def set_preview_full(full: bool) -> None:
    st.session_state[PREVIEW_FULL_KEY] = bool(full) and is_preview_open()


def set_copilot_open(open_: bool) -> None:
    st.session_state[OPEN_KEY] = bool(open_)
    _sync_rail_key()


def set_preview_open(open_: bool) -> None:
    st.session_state[PREVIEW_KEY] = bool(open_)
    if not open_:
        st.session_state[PREVIEW_FULL_KEY] = False
    _sync_rail_key()


def toggle_copilot() -> None:
    set_copilot_open(not is_copilot_open())


def toggle_preview() -> None:
    set_preview_open(not is_preview_open())


def open_copilot_for_job() -> None:
    set_copilot_open(True)


def get_job() -> dict[str, Any] | None:
    job = st.session_state.get(JOB_KEY)
    return job if isinstance(job, dict) else None


def set_job(job: dict[str, Any]) -> None:
    st.session_state[JOB_KEY] = job


def clear_job() -> None:
    st.session_state.pop(JOB_KEY, None)


def queue_job(kind: JobKind, *, prompt: str, label: str) -> None:
    """Queue work for the shared Copilot rail (pages never mount their own panel)."""
    cwd = str(OUT_DIR if kind in {"generate", "streamlit"} else WORKSPACE_DIR)
    st.session_state[JOB_KEY] = {
        "kind": kind,
        "prompt": prompt,
        "cwd": cwd,
        "label": label,
        "status": "queued",
        "expect_structured": kind not in {"generate", "streamlit", "chat"},
    }
    # Do not force a session rebuild here — the Copilot rail resets only when
    # SCHEMA_KIND_KEY != kind (cwd / output_schema actually change). Same-kind
    # jobs (e.g. re-click Compare access rules) just send the prompt.
    open_copilot_for_job()


def queue_estate_map() -> None:
    queue_job("estate", prompt=ESTATE_MAP_PROMPT, label="Map the estate")


def queue_kpi_inventory() -> None:
    queue_job("kpi", prompt=KPI_INVENTORY_PROMPT, label="Inventory KPIs")


def queue_access_rules() -> None:
    queue_job("access", prompt=access_rules_prompt(), label="Compare access rules")


def queue_generate(prompt: str) -> None:
    queue_job("generate", prompt=prompt, label="Write semantic artifacts")


def queue_streamlit_app(prompt: str) -> None:
    queue_job("streamlit", prompt=prompt, label="Write Streamlit app")


def queue_fix_streamlit(traceback: str, app_dir: Path) -> None:
    import streamlit_coco as st_coco

    queue_job(
        "streamlit",
        prompt=st_coco.default_fix_prompt(traceback, app_dir),
        label="Fix Streamlit app",
    )


def session_options(*, kind: JobKind, cwd: str | Path | None = None) -> Any:
    import streamlit_coco as st_coco

    if kind in {"generate", "streamlit"}:
        work = Path(cwd).resolve() if cwd else OUT_DIR
        return st_coco.CocoOptions(
            connection=connection_name(),
            cwd=str(work),
            allowed_tools=["Read", "Glob", "Grep", "Write", "Edit"],
            require_approval_for=["Write", "Edit"],
            output_schema=None,
            max_turns=40,
        )

    work = Path(cwd).resolve() if cwd else WORKSPACE_DIR
    schema_file = {
        "estate": "estate_map.schema.json",
        "kpi": "kpi_inventory.schema.json",
        "access": "access_rules.schema.json",
    }.get(kind)
    schema = load_schema(schema_file) if schema_file else None
    # Mount out/ so agents can Read prior step JSON (estate/KPI) while cwd stays
    # on the BI source workspace.
    return st_coco.CocoOptions(
        connection=connection_name(),
        cwd=str(work),
        allowed_tools=["Read", "Glob", "Grep"],
        require_approval_for=[],
        output_schema=schema,
        max_turns=40,
        extra_sdk_options={"add_dirs": [str(OUT_DIR.resolve())]},
    )


def is_coco_cooking() -> tuple[bool, str]:
    """Return ``(cooking, label)`` when CoCo is connecting, thinking, or on a job."""
    job = get_job()
    label = ""
    if job:
        label = str(job.get("label") or job.get("kind") or "job")
    try:
        import streamlit_coco as st_coco
        from streamlit_coco import CocoRunStatus

        session = st_coco.get_session(SESSION_KEY)
    except Exception:  # noqa: BLE001
        session = None

    if job and (job.get("status") or "queued") == "queued":
        return True, label
    if session is None:
        if job and (job.get("status") or "") == "sent":
            return True, label
        return False, ""
    if session.is_connecting:
        return True, label or "connecting"
    if session.is_running:
        return True, label or "thinking"
    if session.status == CocoRunStatus.AWAITING_USER:
        return True, label or "waiting for approval"
    return False, ""
