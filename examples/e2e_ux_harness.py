"""CoCo-free Streamlit harness for the Playwright tests (``make e2e``).

The window on the scripted agent (the tests set ``STREAMLIT_COCO_AGENT=mock``: no Snowflake login)
and the page's own ``cwd_uploader``. ``?mode=default`` draws the default window; any other mode
draws it with attachments and the display switches on.
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

if st.query_params.get("mode") == "default":
    st_coco.ask_coco(WORKSPACE)
else:
    st_coco.ask_coco(
        WORKSPACE,
        features=st_coco.Features(
            attachments=st_coco.Attachments(accept=[".csv", ".md", ".txt"]),
            display=("latest", "shorten"),
        ),
    )
