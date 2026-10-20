"""Ask CoCo for App Builder: the window, its rights, and the App brief form beside the preview."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from engine.actions import start_coco_build
from engine.brief import app_exists
from engine.brief_form import RAIL_NS, collect_form_answers, render_answers_form
from engine.jobs import skill_dirs
from engine.paths import TYPES_DIR, WORKSPACE_DIR
from engine.state import (
    RAIL_BRIEF_OPEN_KEY,
    answers,
    apply_brief_answers,
    selected_type,
    slug,
)
from streamlit_coco import CocoOptions, policy
from streamlit_coco.features import Features
from streamlit_coco.window import ask_coco

EXAMPLE_QUESTIONS = [
    {
        "title": "List the files",
        "text": (
            "List the files in this folder and say what each one is for. "
            "Do not write or edit files."
        ),
    },
    {
        "title": "Explain the brief",
        "text": (
            "Read BRIEF.md if it exists and summarize what this app should do, "
            "what it allows, and what it must not do. Do not write or edit files."
        ),
    },
    {
        "title": "Suggest a change",
        "text": (
            "If streamlit_app.py exists, read it and suggest one concrete UX "
            "improvement. Do not write or edit files unless I ask."
        ),
    },
]


def _rail_answers():
    app_type = selected_type()
    if app_type is None:
        return None
    return collect_form_answers(app_type, answers(), key_ns=RAIL_NS)


def mount_window(connection: str | None = None, on_rail=None):
    """The floating window, on the current app folder (the workspace before one is picked)."""
    cwd = st.session_state.get("ab_slug_path") or WORKSPACE_DIR
    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    app_type = selected_type()
    # Read when a session starts; the folder changes with the app, which starts a new one.
    options = st.session_state.setdefault("ab_coco_options", CocoOptions(max_turns=40))
    options.extra_sdk_options = {
        "add_dirs": skill_dirs(app_type.guidelines_skill if app_type else None)
    }
    return ask_coco(
        cwd,
        policy=policy.FolderPolicy(cwd, also_read=[TYPES_DIR]),
        features=Features(copy=False, display=("latest", "shorten")),
        prompts=EXAMPLE_QUESTIONS,
        labels={"window.field.placeholder": "Ask CoCo about this app…"},
        options=options,
        connection=connection,
        on_rail=on_rail,
    )


def render_brief_expander() -> None:
    """The owner brief and its answers, editable beside the preview: Save, or Save & regenerate."""
    current = slug()
    app_type = selected_type()
    if not current or app_type is None:
        return
    with st.expander(
        "App brief",
        expanded=bool(st.session_state.get(RAIL_BRIEF_OPEN_KEY)),
        icon=":material/edit_note:",
        type="compact",
    ):
        st.caption(
            "CoCo reads `BRIEF.md`. Edit the owner brief and answers, then save or regenerate."
        )
        render_answers_form(app_type, answers(), key_ns=RAIL_NS, compact=True)
        with st.container(horizontal=True, vertical_alignment="center"):
            save = st.button("Save", icon=":material/save:", key="ab_rail_brief_save")
            regen = st.button(
                "Save & regenerate",
                type="primary",
                icon=":material/psychology:",
                key="ab_rail_brief_regen",
                help="Save BRIEF.md and ask CoCo to rewrite the app.",
            )
        values = _rail_answers() if save or regen else None
        if values is not None:
            apply_brief_answers(values)
            if regen:
                start_coco_build(regenerate=app_exists(current), values=values)
            else:
                st.toast("Saved brief")
