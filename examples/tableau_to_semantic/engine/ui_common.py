"""Shared UI helpers for tableau_to_semantic screens."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from engine import state
from engine.extract import list_twb_files
from engine.paths import WORKSPACE_DIR


def optional_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def require_cwd_files() -> list[Path]:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    files = list_twb_files(WORKSPACE_DIR)
    if not files:
        st.warning("No `.twb` files in the workspace yet. Load them on the **Load** screen.")
        return []
    state.set_cwd_ready(True)
    return files
