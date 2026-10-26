"""Send Build / demo scaffold to Ask CoCo from Brief or Studio."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.brief import answers_complete, slug_dir
from engine.generate import build_prompt
from engine.jobs import set_preview_open
from engine.scaffold import copy_fixture, write_demo_scaffold
from engine.state import answers, persist_brief, selected_type, slug
from streamlit_coco.window import get_window

BUILD_KEY = "ab_build"  # the key of the request, read back in app.py when it is finished
FIX_KEY = "ab_fix"


def missing_required() -> list[str]:
    app_type = selected_type()
    if app_type is None:
        return ["type"]
    return answers_complete(app_type, answers())


def start_coco_build(*, regenerate: bool, values: dict[str, Any] | None = None) -> None:
    app_type = selected_type()
    current = slug()
    if app_type is None or not current:
        return
    persist_brief(values)
    dest = slug_dir(current)
    copy_fixture(app_type, dest)
    persist_brief(values)
    set_preview_open(True)
    # Ask CoCo opens and shows the request (it waits for the connection if there is none).
    get_window().ask(
        "Regenerate this app" if regenerate else "Build this app",
        build_prompt(app_type, regenerate=regenerate),
        key=BUILD_KEY,
    )


def start_fix(traceback: str, app_dir) -> None:
    from streamlit_coco import default_fix_prompt

    set_preview_open(True)
    get_window().ask("Fix the preview", default_fix_prompt(traceback, app_dir), key=FIX_KEY)


def start_demo_scaffold() -> None:
    app_type = selected_type()
    current = slug()
    if app_type is None or not current:
        return
    persist_brief()
    write_demo_scaffold(app_type, current)
    set_preview_open(True)
    st.toast("Wrote demo scaffold · open Preview")
    st.rerun()
