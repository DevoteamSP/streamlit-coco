"""Product Backlog Desk â€” multipage Streamlit demo for streamlit-coco."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from utils.skill_desk import mount, render_skill_picker  # noqa: E402

st.set_page_config(
    page_title="Product Backlog Desk",
    page_icon=":material/view_kanban:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

page = st.navigation(
    [
        st.Page("app_pages/board.py", title="Board", icon=":material/dashboard:"),
        st.Page("app_pages/epic.py", title="Epic", icon=":material/account_tree:"),
        st.Page("app_pages/ticket.py", title="Ticket", icon=":material/confirmation_number:"),
        st.Page("app_pages/release.py", title="Release", icon=":material/new_releases:"),
    ],
    position="top",
)


def _chrome() -> None:
    """Full-width page title and the skill picker."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        render_skill_picker()
    st.caption("Product Backlog Desk · streamlit-coco demo (file-backed, no SQL)")


_chrome()
mount()
with st.container(border=True):
    page.run()
