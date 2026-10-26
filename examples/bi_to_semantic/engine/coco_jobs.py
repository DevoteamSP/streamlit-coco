"""Jobs a screen hands to Ask CoCo, and the Preview flags, for bi_to_semantic.

Screens only queue a job (`PENDING_KEY`); `coco_window.dispatch_pending` sends it to the window.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import streamlit as st

from engine.extract import (
    ESTATE_MAP_PROMPT,
    KPI_INVENTORY_PROMPT,
    access_rules_prompt,
)
from engine.paths import OUT_DIR, WORKSPACE_DIR

PENDING_KEY = "tts_coco_pending"
SESSION_KIND_KEY = "tts_coco_session_kind"
STRUCTURED = ("estate", "kpi", "access")
WRITES = ("generate", "streamlit")
PREVIEW_KEY = "tts_preview_open"
PREVIEW_FULL_KEY = "tts_preview_full"

JobKind = Literal["estate", "kpi", "access", "generate", "streamlit", "chat"]


def is_preview_open() -> bool:
    return bool(st.session_state.get(PREVIEW_KEY))


def is_preview_full() -> bool:
    return is_preview_open() and bool(st.session_state.get(PREVIEW_FULL_KEY))


def set_preview_full(full: bool) -> None:
    st.session_state[PREVIEW_FULL_KEY] = bool(full) and is_preview_open()


def set_preview_open(open_: bool) -> None:
    st.session_state[PREVIEW_KEY] = bool(open_)
    if not open_:
        st.session_state[PREVIEW_FULL_KEY] = False


def toggle_preview() -> None:
    set_preview_open(not is_preview_open())


def current_kind() -> str:
    """The job the window should be set up for, or ``chat`` when nothing is queued."""
    job = st.session_state.get(PENDING_KEY)
    if isinstance(job, dict) and job.get("kind"):
        return str(job["kind"])
    return str(st.session_state.get(SESSION_KIND_KEY) or "chat")


def cwd_for(kind: str) -> Path:
    """Generated apps live in ``out/``; reading the sources stays in the workspace."""
    return OUT_DIR if kind in WRITES else WORKSPACE_DIR


def queue_job(kind: JobKind, *, prompt: str, label: str) -> None:
    """Queue work for Ask CoCo; the next run of the app sends it (`dispatch_pending`)."""
    st.session_state[PENDING_KEY] = {"kind": kind, "prompt": prompt, "label": label}


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
