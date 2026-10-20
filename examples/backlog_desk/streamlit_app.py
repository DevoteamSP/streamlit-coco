"""Product Backlog Desk — multipage Streamlit demo for streamlit-coco."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from utils.copilot_panel import (  # noqa: E402
    CONN_KEY,
    GATE_KEY,
    is_copilot_open,
    render_copilot_rail,
    toggle_copilot,
)
from utils.skill_desk import mount  # noqa: E402

from streamlit_coco.rail import (  # noqa: E402
    ask_coco_switch,
    ask_restore,
    present_ask,
    rail_minimized,
)

st.set_page_config(
    page_title="Product Backlog Desk",
    page_icon=":material/view_kanban:",
    layout="wide",
    initial_sidebar_state="expanded",
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


def _chrome() -> bool:
    """Full-width page title — sits above the content / Copilot split."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        # Open only — close via the Copilot rail Close button.
        if not is_copilot_open() and st.button(
            "Copilot",
            icon=":material/psychology:",
            type="primary",
            key="bd_toggle_copilot_header",
        ):
            toggle_copilot()
            st.rerun()
    show_ask = ask_coco_switch("bd_ask_coco")
    st.caption("Product Backlog Desk · streamlit-coco demo (file-backed, no SQL)")
    return show_ask


show_ask = _chrome()
profile = st.session_state.get(CONN_KEY) if st.session_state.get(GATE_KEY) else None
present_ask(
    show_ask,
    "bd_coco",
    lambda: mount(connection=profile, on_rail=ask_restore("bd_coco")),
)

_minimized = show_ask and rail_minimized("bd_coco")
if is_copilot_open() and not _minimized:
    # Rail starts below title/subtitle so panes share the same content baseline.
    main, rail = st.columns([1.15, 1], gap="large")
    with main:
        with st.container(border=True):
            page.run()
    with rail:
        with st.container(border=True):
            render_copilot_rail(ask=show_ask)
else:
    with st.container(border=True):
        page.run()
