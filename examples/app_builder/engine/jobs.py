"""CoCo jobs (through the Ask CoCo window) + Preview chrome flags for App Builder."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from engine.paths import PREVIEW_PORT
from engine.skills import skill_dirs_for
from streamlit_coco.window import get_window

PREVIEW_KEY = "ab_preview_open"
PREVIEW_FULL_KEY = "ab_preview_full"
# Job keys: `coco.ask(label, text, key=...)` then `coco.result(key)` once the job is finished.
BUILD_KEY = "build"
FIX_KEY = "fix"


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


def queue_build(prompt: str, cwd: Path) -> None:
    """Ask CoCo to write the app (the window's cwd is already this app folder)."""
    get_window().ask("Build Streamlit app", prompt, key=BUILD_KEY)


def queue_fix(traceback: str, app_dir: Path) -> None:
    from streamlit_coco import default_fix_prompt

    get_window().ask("Fix Streamlit app", default_fix_prompt(traceback, app_dir), key=FIX_KEY)


def job_finished() -> bool:
    """True once, when a build or a fix this session sent has finished (`coco.result`)."""
    coco = get_window()
    done = False
    for key in (BUILD_KEY, FIX_KEY):
        # Peek first: `result()` also stops the window from re-running the page on completion.
        if coco.conversation.result_for(key, take=False) is not None:
            done = bool(coco.result(key)) or done
    return done


def skill_dirs(guidelines_skill: str | None) -> list[str]:
    """Always mount ``types/shared`` when present; add the type folder next."""
    return skill_dirs_for(guidelines_skill)


def preview_port() -> int:
    return PREVIEW_PORT
