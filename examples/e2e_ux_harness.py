"""CoCo-free Streamlit harness for the Playwright tests (``make e2e``).

The window on the scripted agent (the tests set ``STREAMLIT_COCO_AGENT=mock``: no Snowflake login)
and the page's own ``cwd_uploader``. ``?mode=default`` draws the default window; ``?mode=fixed`` and
``?mode=dock_only`` switch its places off (``Features(dock=, full_page=)``); ``?mode=split`` splits
the screen; any other mode draws it with attachments and the display switches on.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo UX e2e harness", layout="wide")
st.title("CoCo UX e2e harness")
st.caption("Fixture app for Playwright. No live CoCo agent.")

WORKSPACE = Path(os.environ.get("COCO_E2E_WORKSPACE", "e2e_workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

with st.sidebar:
    st_coco.cwd_uploader(str(WORKSPACE), overwrite="replace", key="e2e_uploader")

mode = st.query_params.get("mode")
if mode == "default":
    st_coco.ask_coco(WORKSPACE)
elif mode == "fixed":  # the window cannot be moved
    st_coco.ask_coco(WORKSPACE, features=st_coco.Features(dock=False, full_page=False))
elif mode == "split":  # the page shares the screen with an attached window and is told its place
    st_coco.ask_coco(
        WORKSPACE,
        split=True,
        on_layout=lambda place: st.session_state.update(place=place),
    )
    st.caption(f"Window place: {st.session_state.get('place', 'closed')}")
elif mode == "dock_only":
    st_coco.ask_coco(WORKSPACE, features=st_coco.Features(full_page=False))
else:
    st_coco.ask_coco(
        WORKSPACE,
        features=st_coco.Features(
            attachments=st_coco.Attachments(accept=[".csv", ".md", ".txt"]),
            display=("latest", "shorten"),
        ),
    )
