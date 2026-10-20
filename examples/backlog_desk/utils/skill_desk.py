"""Ask CoCo for Product Backlog Desk: the window, its rights, and the skill picker (a page form)."""

from __future__ import annotations

import streamlit as st

from streamlit_coco import policy
from streamlit_coco.window import ask_coco, get_window
from utils.paths import APP_ROOT, DATA_DIR
from utils.skills import SKILLS, Skill, skill_by_name, skill_prompt
from utils.ui import get_backlog

PROMPTS = [
    {"title": "Summarize the sprint", "text": "Summarize the current sprint from data/tickets/."},
    {"title": "Which tickets are blocked?", "text": "Which tickets are blocked, and why?"},
    {"title": "Ask about a ticket…", "text": "About ticket ", "fill": True},
]


def mount(connection: str | None = None, on_rail=None) -> None:
    """The floating window. Reading `data/` is free; an Edit or Write asks each time, as it did."""
    ask_coco(
        APP_ROOT,
        policy=policy.FolderPolicy(APP_ROOT, scope=DATA_DIR),
        prompts=PROMPTS,
        labels={"window.field.placeholder": "Ask about tickets, epics, or release notes…"},
        connection=connection,
        on_rail=on_rail,
    )


def run_skill(
    skill: Skill,
    *,
    ticket_id: str | None = None,
    epic_id: str | None = None,
    release: str | None = None,
) -> None:
    """Send a skill to CoCo: the thread shows its label, CoCo gets the whole prompt."""
    for key, value in (
        ("selected_ticket", ticket_id),
        ("selected_epic", epic_id),
        ("selected_release", release),
    ):
        if value:
            st.session_state[key] = value
    prompt = skill_prompt(skill, ticket_id=ticket_id, epic_id=epic_id, release=release)
    get_window().ask(skill.label, prompt, key=skill.name)


def ask_skill(name: str, **focus: str | None) -> None:
    """A page button runs a named skill on the focus it gives."""
    skill = skill_by_name(name)
    if skill:
        run_skill(skill, **focus)


def _focus(label: str, options: list[str], current: str | None, key: str) -> str | None:
    choices = ["(none)", *options]
    index = choices.index(current) if current in options else 0
    picked = st.selectbox(label, choices, index=index, key=key)
    return None if picked == "(none)" else picked


def render_skill_picker() -> None:
    """The skill picker: the page's own form, whose prompt goes through `coco.ask`."""
    backlog = get_backlog()
    with st.popover("Run a skill", icon=":material/psychology:", type="primary"):
        names = [s.name for s in SKILLS]
        labels = {s.name: s.label for s in SKILLS}
        chosen = st.pills(
            "Skill",
            names,
            format_func=labels.get,
            selection_mode="single",
            default=names[0],
            key="bd_skill_pills",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            ticket = _focus(
                "Ticket",
                [t.id for t in backlog.tickets],
                st.session_state.get("selected_ticket"),
                "bd_skill_ticket",
            )
        with c2:
            epic = _focus(
                "Epic",
                [e.id for e in backlog.epics],
                st.session_state.get("selected_epic"),
                "bd_skill_epic",
            )
        with c3:
            release = _focus(
                "Release",
                [r.version for r in backlog.releases],
                st.session_state.get("selected_release"),
                "bd_skill_release",
            )
        skill = skill_by_name(chosen) if chosen else None
        if skill:
            st.caption(skill.description)
            prompt = skill_prompt(skill, ticket_id=ticket, epic_id=epic, release=release)
            with st.expander("Prompt preview", expanded=False):
                st.code(prompt, language=None)
        if st.button(
            "Run skill",
            type="primary",
            icon=":material/play_arrow:",
            key="bd_run_skill",
            disabled=not skill,
        ):
            run_skill(skill, ticket_id=ticket, epic_id=epic, release=release)
