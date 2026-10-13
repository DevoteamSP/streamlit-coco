"""Queue Build / demo scaffold from Brief or Studio."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.brief import answers_complete, slug_dir
from engine.generate import build_prompt
from engine.jobs import queue_build, set_preview_open
from engine.scaffold import copy_fixture, write_demo_scaffold
from engine.state import answers, persist_brief, selected_type, slug


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
    # Sent when CoCo is connected, shown as waiting until then; this reruns the page.
    set_preview_open(True)
    queue_build(build_prompt(app_type, regenerate=regenerate), dest)


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
