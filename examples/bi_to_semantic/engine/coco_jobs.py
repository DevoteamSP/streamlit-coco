"""CoCo jobs for bi_to_semantic, through the Ask CoCo window, + Preview chrome flags.

Screens only queue a job (`queue_job`). The next run sets the window up for the job's kind (its
folder, rights and answer schema, see `engine.coco_window`) and sends it with `coco.ask`.
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

PENDING_KEY = "tts_coco_pending"  # the job a screen queued, until the next run sends it
KIND_KEY = "tts_coco_kind"  # the kind the window is set up for
SESSION_KIND_KEY = "tts_coco_session_kind"  # the kind the running session was started for
PREVIEW_KEY = "tts_preview_open"
PREVIEW_FULL_KEY = "tts_preview_full"

JobKind = Literal["estate", "kpi", "access", "generate", "streamlit", "chat"]
STRUCTURED = ("estate", "kpi", "access")  # jobs answered with data (the session's output_schema)
WRITES = ("generate", "streamlit")  # jobs that write files, under approval


def cwd_for(kind: str) -> Path:
    return OUT_DIR if kind in WRITES else WORKSPACE_DIR


def current_kind() -> str:
    return str(st.session_state.get(KIND_KEY) or "chat")


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


def queue_job(kind: JobKind, *, prompt: str, label: str) -> None:
    """Queue work for the window. Reruns the page: the window must be set up for `kind` (folder,
    rights, schema) before it is asked, and that happens at the top of the next run."""
    st.session_state[PENDING_KEY] = {"kind": kind, "prompt": prompt, "label": label}
    st.session_state[KIND_KEY] = kind
    st.rerun()


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
    from streamlit_coco import default_fix_prompt

    queue_job("streamlit", prompt=default_fix_prompt(traceback, app_dir), label="Fix Streamlit app")
