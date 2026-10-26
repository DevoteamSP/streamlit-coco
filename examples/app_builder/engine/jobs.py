"""Preview flags and skill folders for App Builder (the agent is Ask CoCo, see coco_window)."""

from __future__ import annotations

import streamlit as st

from engine.paths import PREVIEW_PORT
from engine.skills import skill_dirs_for

PREVIEW_KEY = "ab_preview_open"
PREVIEW_FULL_KEY = "ab_preview_full"


def is_preview_open() -> bool:
    return bool(st.session_state.get(PREVIEW_KEY))


def is_preview_full() -> bool:
    return is_preview_open() and bool(st.session_state.get(PREVIEW_FULL_KEY))


def set_preview_open(open_: bool) -> None:
    st.session_state[PREVIEW_KEY] = bool(open_)
    if not open_:
        st.session_state[PREVIEW_FULL_KEY] = False


def set_preview_full(full: bool) -> None:
    st.session_state[PREVIEW_FULL_KEY] = bool(full) and is_preview_open()


def toggle_preview() -> None:
    set_preview_open(not is_preview_open())


def skill_dirs(guidelines_skill: str | None) -> list[str]:
    """Always mount ``types/shared`` when present; add the type folder next."""
    return skill_dirs_for(guidelines_skill)


def preview_port() -> int:
    return PREVIEW_PORT
