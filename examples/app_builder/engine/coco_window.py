"""Ask CoCo for App Builder: the window, its rights and suggested questions, and the App brief form
beside the preview."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from engine.actions import start_coco_build
from engine.brief import app_exists
from engine.brief_form import RAIL_NS, collect_form_answers, render_answers_form
from engine.jobs import skill_dirs
from engine.paths import TYPES_DIR, WORKSPACE_DIR
from engine.skills import SHARED_SKILL_ID, skill_md_path
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


def _no_edit(text: str) -> str:
    return f"{text} Do not write or edit files."


def page_prompts(page: str) -> list[dict[str, str]]:
    """The suggested questions of a screen (the window shows them in an empty conversation)."""
    app_type = selected_type()
    types = TYPES_DIR
    skill = (
        skill_md_path(app_type.guidelines_skill or SHARED_SKILL_ID) if app_type else None
    )
    if page == "Welcome":
        return [
            {
                "title": "What can I build?",
                "text": _no_edit(
                    f"Read the type.json of every folder under {types} and list each app "
                    "type: what it is for, who uses it, and whether it needs Snowflake."
                ),
            },
            {
                "title": "Which type fits me?",
                "text": _no_edit(
                    f"Ask me two or three questions about what I want to build, then pick "
                    f"the best of the app types under {types} and say why."
                ),
            },
            {
                "title": "How does a build work?",
                "text": _no_edit(
                    f"Read {types}/shared/SKILL.md and explain, in a few sentences, the "
                    "rules every generated app follows."
                ),
            },
        ]
    if page == "Library":
        return [
            {
                "title": "Compare the types",
                "text": _no_edit(
                    f"Read the type.json of every folder under {types} and compare the "
                    "types in a table: users, grounding, needs Snowflake, what it does not do."
                ),
            },
            {
                "title": "Works without Snowflake?",
                "text": _no_edit(
                    f"From the type.json files under {types}, which app types work with no "
                    "Snowflake account, and which demo data does each one ship?"
                ),
            },
            {
                "title": "What will I be asked?",
                "text": _no_edit(
                    f"For each app type under {types}, list the questions its brief asks, "
                    "so I can prepare my answers."
                ),
            },
        ]
    if page == "Brief":
        return [
            {
                "title": "Review my brief",
                "text": _no_edit(
                    "Read BRIEF.md if it exists. Say what is missing, vague or "
                    "contradictory before this app is built."
                ),
            },
            {
                "title": "Suggest answers",
                "text": _no_edit(
                    "Read BRIEF.md if it exists and propose an answer for each question "
                    "that is still empty, with a short reason."
                ),
            },
            {
                "title": "What it will not do",
                "text": _no_edit(
                    "Read BRIEF.md if it exists and list what this app allows and what "
                    "it must not do, in plain words."
                ),
            },
        ]
    if page == "Studio":
        guide = f" and {skill}" if skill else ""
        return [
            {
                "title": "Explain the app",
                "text": _no_edit(
                    "If streamlit_app.py exists, read it and explain what the app shows "
                    "and how a user moves through it."
                ),
            },
            {
                "title": "Suggest a change",
                "text": _no_edit(
                    "If streamlit_app.py exists, read it and suggest one concrete UX "
                    "improvement."
                ),
            },
            {
                "title": "Check the guidelines",
                "text": _no_edit(
                    f"Read streamlit_app.py{guide}, then list where the app departs from "
                    "the guidelines."
                ),
            },
        ]
    return [  # Admin
        {
            "title": "Review the types",
            "text": _no_edit(
                f"Read the type.json of every folder under {types} and flag unclear "
                "questions or missing allows and does-not rules."
            ),
        },
        {
            "title": "Check the guidelines",
            "text": _no_edit(
                f"Read {types}/shared/SKILL.md and say what is contradictory, missing or "
                "too vague for a generated app."
            ),
        },
        {
            "title": "Draft a new type",
            "text": _no_edit(
                f"Ask me what the new app type is for, then outline its type.json like "
                f"the ones under {types} (name, users, questions, does not)."
            ),
        },
    ]


def _rail_answers():
    app_type = selected_type()
    if app_type is None:
        return None
    return collect_form_answers(app_type, answers(), key_ns=RAIL_NS)


def mount_window(page: str, *, split: bool = False):
    """Ask CoCo, on the current app folder (the workspace before one is picked), with the
    suggested questions of the screen `page`."""
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
        prompts=page_prompts(page),
        labels={"window.field.placeholder": "Ask CoCo about this app…"},
        options=options,
        split=split,
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
