"""Tableau → Semantic — streamlit-coco example (screens 1–6).

Reads Tableau workbooks, surfaces KPI and access-rule drift, arbitrates with
the human, then Writes a semantic view + row access policy under approval.

One shared right rail: Copilot (CoCo session) or Preview (generated app).
Screens only queue jobs — they do not open new agents.
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
from engine.coco_jobs import (  # noqa: E402
    get_job,
    is_copilot_open,
    is_preview_full,
    is_preview_open,
    is_rail_open,
    set_copilot_open,
    toggle_copilot,
    toggle_preview,
)
from engine.copilot_panel import (  # noqa: E402
    render_coco_cooking_indicator,
    render_copilot_rail,
)
from engine.paths import WORKSPACE_DIR  # noqa: E402
from engine.preview_panel import render_preview_rail  # noqa: E402

st.set_page_config(
    page_title="Tableau → Semantic",
    page_icon=":material/account_tree:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

state.ensure_defaults()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

page = st.navigation(
    [
        st.Page("screens/load.py", title="1 · Load", icon=":material/upload_file:"),
        st.Page("screens/estate_map.py", title="2 · Estate map", icon=":material/hub:"),
        st.Page("screens/kpi_inventory.py", title="3 · KPIs", icon=":material/speed:"),
        st.Page(
            "screens/access_rules.py",
            title="4 · Access rules",
            icon=":material/policy:",
        ),
        st.Page(
            "screens/arbitration.py",
            title="5 · Arbitration",
            icon=":material/gavel:",
        ),
        st.Page(
            "screens/generate.py",
            title="6 · Generate",
            icon=":material/deployed_code:",
        ),
    ],
    position="top",
)


def _chrome() -> None:
    copilot_on = is_copilot_open()
    preview_on = is_preview_open()
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        if st.button(
            "Close Copilot" if copilot_on else "Copilot",
            icon=":material/close:" if copilot_on else ":material/psychology:",
            type="secondary" if copilot_on else "primary",
            key="tts_toggle_copilot_header",
        ):
            toggle_copilot()
            st.rerun()
        if st.button(
            "Close Preview" if preview_on else "Preview",
            icon=":material/close:" if preview_on else ":material/preview:",
            type="secondary" if preview_on else "primary",
            key="tts_toggle_preview_header",
        ):
            toggle_preview()
            st.rerun()
    st.caption(
        "Tableau → Semantic · Copilot and Preview share the right panel — "
        "screens queue jobs, they do not open new agents."
    )
    restored = state.hydrated_files()
    if restored:
        st.caption("Restored from disk · " + ", ".join(f"`{n}`" for n in restored))
    render_coco_cooking_indicator()


_chrome()

# Keep the Copilot rail open while a structured job is queued/running.
if get_job() and not is_copilot_open():
    set_copilot_open(True)

if is_preview_open() and is_preview_full():
    with st.container(border=True):
        render_preview_rail()
elif is_rail_open():
    # Rail FIRST: if a page stops early, Copilot still streams.
    main, rail = resizable_columns(
        [1.15, 1],
        min_width=280,
        key="tts_rail_split",
    )
    with rail:
        with st.container(border=True):
            if is_copilot_open():
                render_copilot_rail()
            else:
                render_preview_rail()
    with main:
        with st.container(border=True):
            page.run()
else:
    with st.container(border=True):
        page.run()
