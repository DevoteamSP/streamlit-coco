"""App Builder — streamlit-coco example.

Library of app types → filled brief (form + user sketches) → CoCo (the Ask CoCo
window) writes a Streamlit app under approval → Preview with Fix with CoCo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from streamlit_extras.resizable_columns import resizable_columns

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from engine import state  # noqa: E402
from engine.brief import slug_dir  # noqa: E402
from engine.coco_window import mount_window, render_brief_expander  # noqa: E402
from engine.jobs import (  # noqa: E402
    is_preview_full,
    is_preview_open,
    job_finished,
    toggle_preview,
)
from engine.paths import WORKSPACE_DIR  # noqa: E402
from engine.preview_panel import render_preview_rail  # noqa: E402

st.set_page_config(
    page_title="App Builder",
    page_icon=":material/web:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

state.ensure_defaults()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
if state.slug():
    st.session_state["ab_slug_path"] = str(slug_dir(state.slug()))

_WELCOME = st.Page(
    "screens/welcome.py",
    title="Welcome",
    icon=":material/waving_hand:",
    default=True,
)
_LIBRARY = st.Page("screens/library.py", title="Library", icon=":material/apps:")
_BRIEF = st.Page("screens/brief.py", title="Brief", icon=":material/edit_note:")
_STUDIO = st.Page("screens/studio.py", title="Studio", icon=":material/web:")
_ADMIN = st.Page("screens/admin.py", title="Admin", icon=":material/settings:")

page = st.navigation(
    [_WELCOME, _LIBRARY, _BRIEF, _STUDIO, _ADMIN],
    position="top",
)

_ON_WELCOME = page.title == "Welcome"
_ON_ADMIN = page.title == "Admin"


def _chrome() -> None:
    preview_on = is_preview_open()
    app_type = state.selected_type()

    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        current_app = state.app_name()
        if current_app and not _ON_ADMIN:
            st.badge(current_app, color="blue")
        elif app_type and not _ON_ADMIN:
            st.badge(app_type.name, color="blue")
        show_preview = not _ON_WELCOME and not _ON_ADMIN
        if show_preview and st.button(
            "Close Preview" if preview_on else "Open Preview",
            icon=":material/close:" if preview_on else ":material/preview:",
            type="secondary" if preview_on else "primary",
            key="ab_toggle_preview",
        ):
            toggle_preview()
            st.rerun()

    if _ON_WELCOME:
        st.caption(
            "App Builder · pick a type, fill its brief, CoCo writes the app. "
            "Connect CoCo once from the launcher — later screens reuse that session."
        )
    elif _ON_ADMIN:
        st.caption("App Builder · add, edit, or delete the types that appear in the Library.")
    else:
        st.caption(
            "App Builder · Open Preview sits beside the page, CoCo floats above it. "
            "Screens queue jobs; they do not open a new agent."
        )


_chrome()
mount_window()
if job_finished():  # a build or a fix just finished: the preview starts on its own
    st.session_state["ab_preview_auto_run"] = True

_preview_ok = not _ON_WELCOME and not _ON_ADMIN

if _preview_ok and is_preview_open() and is_preview_full():
    with st.container(border=True):
        render_preview_rail()
elif _preview_ok and is_preview_open():
    main, rail = resizable_columns(
        [1.15, 1],
        min_width=280,
        key="ab_rail_split",
    )
    with rail:
        with st.container(border=True):
            render_brief_expander()
            render_preview_rail()
    with main:
        page.run()
else:
    page.run()
