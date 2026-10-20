"""BI → Semantic — streamlit-coco example (Welcome + screens 1–6).

Reads Tableau workbooks and/or Power BI reports, surfaces KPI and access-rule
drift, arbitrates with the human, then Writes a semantic view + row access
policy under approval.

Copilot and Preview can open together (preview | Copilot) so a failing
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
    connection_name,
    get_job,
    is_connected,
    is_copilot_open,
    is_preview_full,
    is_preview_open,
    is_rail_open,
    set_copilot_open,
    toggle_copilot,
    toggle_preview,
)
from engine.coco_window import mount_window  # noqa: E402
from engine.copilot_panel import (  # noqa: E402
    render_coco_cooking_indicator,
    render_copilot_rail,
)
from engine.paths import WORKSPACE_DIR  # noqa: E402
from engine.preview_panel import render_preview_rail  # noqa: E402

from streamlit_coco.rail import (  # noqa: E402
    ask_coco_switch,
    ask_restore,
    present_ask,
    rail_minimized,
)

st.set_page_config(
    page_title="BI → Semantic",
    page_icon=":material/account_tree:",
    layout="wide",
    initial_sidebar_state="expanded",
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


def _chrome() -> bool:
    copilot_on = is_copilot_open()
    preview_on = is_preview_open()
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title(f"{page.icon} {page.title}")
        if st.button(
            "Close Copilot" if copilot_on else "Copilot",
            icon=":material/close:" if copilot_on else ":material/psychology:",
            type="secondary" if copilot_on else "primary",
            key="bts_toggle_copilot_header",
        ):
            toggle_copilot()
            st.rerun()
        if page.title != "Welcome" and st.button(
            "Close Preview" if preview_on else "Preview",
            icon=":material/close:" if preview_on else ":material/preview:",
            type="secondary" if preview_on else "primary",
            key="bts_toggle_preview_header",
        ):
            toggle_preview()
            st.rerun()
    show_ask = ask_coco_switch("tts_ask_coco")
    if page.title == "Welcome":
        st.caption(
            "BI → Semantic · Tableau and Power BI · Open Copilot once — later "
            "screens reuse that session."
        )
    else:
        st.caption(
            "BI → Semantic · Tableau and Power BI · Copilot and Preview can sit "
            "side by side — screens queue jobs, they do not open new agents."
        )
    restored = state.hydrated_files()
    if restored:
        st.caption("Restored from disk · " + ", ".join(f"`{n}`" for n in restored))
    render_coco_cooking_indicator()
    return show_ask


show_ask = _chrome()

# Keep the Copilot rail open while a structured job is queued/running.
if get_job() and not is_copilot_open():
    set_copilot_open(True)

present_ask(
    show_ask,
    "tts_coco",
    lambda: mount_window(
        connection=connection_name() if is_connected() else None,
        on_rail=ask_restore("tts_coco"),
    ),
)

_preview_ok = page.title != "Welcome"
_minimized = show_ask and rail_minimized("tts_coco")
_layout_copilot = is_copilot_open() and not _minimized

if _layout_copilot and _preview_ok and is_preview_open():
    preview_col, rail = resizable_columns(
        [1.15, 1],
        min_width=280,
        key="bts_fix_split",
    )
    with preview_col:
        with st.container(border=True):
            render_preview_rail()
    with rail:
        with st.container(border=True):
            render_copilot_rail(ask=show_ask)
elif _preview_ok and is_preview_open() and (is_preview_full() or _minimized):
    with st.container(border=True):
        render_preview_rail()
elif _layout_copilot or (_preview_ok and is_rail_open() and not _minimized):
    # Rail FIRST: if a page stops early, Copilot still streams.
    main, rail = resizable_columns(
        [1.15, 1],
        min_width=280,
        key="bts_rail_split",
    )
    with rail:
        with st.container(border=True):
            if _layout_copilot:
                render_copilot_rail(ask=show_ask)
            else:
                render_preview_rail()
    with main:
        page.run()
else:
    page.run()
