"""BI → Semantic — streamlit-coco example (Welcome + screens 1–6).

Reads Tableau workbooks and/or Power BI reports, surfaces KPI and access-rule
drift, arbitrates with the human, then Writes a semantic view + row access
policy under approval.

CoCo is the floating Ask CoCo window; Preview opens beside the page so a failing
generated app can be fixed in place. Screens only queue jobs.
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
    is_preview_full,
    is_preview_open,
    toggle_preview,
)
from engine.coco_window import collect_results, dispatch_pending, mount_window  # noqa: E402
from engine.paths import WORKSPACE_DIR  # noqa: E402
from engine.preview_panel import render_preview_rail  # noqa: E402

st.set_page_config(
    page_title="BI → Semantic",
    page_icon=":material/account_tree:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

state.ensure_defaults()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

page = st.navigation(
    [
        st.Page(
            "screens/welcome.py",
            title="Welcome",
            icon=":material/waving_hand:",
            default=True,
        ),
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
    preview_on = is_preview_open()
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        if page.title != "Welcome" and st.button(
            "Close Preview" if preview_on else "Preview",
            icon=":material/close:" if preview_on else ":material/preview:",
            type="secondary" if preview_on else "primary",
            key="bts_toggle_preview_header",
        ):
            toggle_preview()
            st.rerun()
    if page.title == "Welcome":
        st.caption(
            "BI → Semantic · Tableau and Power BI · Connect CoCo once from the "
            "launcher — later screens reuse that session."
        )
    else:
        st.caption(
            "BI → Semantic · Tableau and Power BI · Preview sits beside the page, CoCo "
            "floats above it — screens queue jobs, they do not open new agents."
        )
    restored = state.hydrated_files()
    if restored:
        st.caption("Restored from disk · " + ", ".join(f"`{n}`" for n in restored))


_chrome()
coco = mount_window()
dispatch_pending(coco)
collect_results(coco)

_preview_ok = page.title != "Welcome"

if _preview_ok and is_preview_open() and is_preview_full():
    with st.container(border=True):
        render_preview_rail()
elif _preview_ok and is_preview_open():
    # Preview FIRST: if a page stops early, the preview still renders.
    main, rail = resizable_columns(
        [1.15, 1],
        min_width=280,
        key="bts_rail_split",
    )
    with rail:
        with st.container(border=True):
            render_preview_rail()
    with main:
        page.run()
else:
    page.run()
