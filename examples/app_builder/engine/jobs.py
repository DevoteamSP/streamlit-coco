"""CoCo jobs + Copilot / Preview chrome flags for App Builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import streamlit as st

from engine.paths import PREVIEW_PORT
from engine.skills import skill_dirs_for

SESSION_KEY = "ab_coco"
GATE_KEY = "ab_coco_connected"
CONN_KEY = "ab_coco_connection"
JOB_KEY = "ab_coco_job"
KIND_KEY = "ab_coco_kind"
OPEN_KEY = "ab_copilot_open"
PREVIEW_KEY = "ab_preview_open"
PREVIEW_FULL_KEY = "ab_preview_full"

JobKind = Literal["build", "chat"]


def is_connected() -> bool:
    return bool(st.session_state.get(GATE_KEY) and st.session_state.get(CONN_KEY))


def connection_name() -> str | None:
    return st.session_state.get(CONN_KEY)


def is_copilot_open() -> bool:
    return bool(st.session_state.get(OPEN_KEY))


def is_preview_open() -> bool:
    return bool(st.session_state.get(PREVIEW_KEY))


def is_preview_full() -> bool:
    return is_preview_open() and bool(st.session_state.get(PREVIEW_FULL_KEY))


def set_copilot_open(open_: bool) -> None:
    st.session_state[OPEN_KEY] = bool(open_)


def set_preview_open(open_: bool) -> None:
    st.session_state[PREVIEW_KEY] = bool(open_)
    if not open_:
        st.session_state[PREVIEW_FULL_KEY] = False


def set_preview_full(full: bool) -> None:
    st.session_state[PREVIEW_FULL_KEY] = bool(full) and is_preview_open()


def toggle_copilot() -> None:
    set_copilot_open(not is_copilot_open())


def toggle_preview() -> None:
    set_preview_open(not is_preview_open())


def get_job() -> dict[str, Any] | None:
    job = st.session_state.get(JOB_KEY)
    return job if isinstance(job, dict) else None


def set_job(job: dict[str, Any]) -> None:
    st.session_state[JOB_KEY] = job


def clear_job() -> None:
    st.session_state.pop(JOB_KEY, None)


def queue_job(kind: JobKind, *, prompt: str, label: str, cwd: Path) -> None:
    st.session_state[JOB_KEY] = {
        "kind": kind,
        "prompt": prompt,
        "cwd": str(cwd),
        "label": label,
        "status": "queued",
        "expect_structured": False,
    }
    set_copilot_open(True)


def queue_build(prompt: str, cwd: Path) -> None:
    queue_job("build", prompt=prompt, label="Build Streamlit app", cwd=cwd)


def queue_fix(traceback: str, app_dir: Path) -> None:
    import streamlit_coco as st_coco

    queue_job(
        "build",
        prompt=st_coco.default_fix_prompt(traceback, app_dir),
        label="Fix Streamlit app",
        cwd=app_dir,
    )


def skill_dirs(guidelines_skill: str | None) -> list[str]:
    """Always mount ``types/shared`` when present; add the type folder next."""
    return skill_dirs_for(guidelines_skill)


def session_options(*, cwd: str | Path, guidelines_skill: str | None = None) -> Any:
    import streamlit_coco as st_coco

    work = Path(cwd).resolve()
    work.mkdir(parents=True, exist_ok=True)
    return st_coco.CocoOptions(
        connection=connection_name(),
        cwd=str(work),
        allowed_tools=["Read", "Glob", "Grep", "Write", "Edit"],
        require_approval_for=["Write", "Edit"],
        output_schema=None,
        max_turns=40,
        extra_sdk_options={"add_dirs": skill_dirs(guidelines_skill)},
    )


def preview_port() -> int:
    return PREVIEW_PORT


def is_coco_cooking() -> tuple[bool, str]:
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
