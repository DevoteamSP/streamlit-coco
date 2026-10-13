"""Files into the agent's working folder: attached in the window's field, or by the page's uploader.

Attached files are saved under ``_coco_uploads/`` in the folder; the page's ``cwd_uploader`` writes
under ``_uploads/``. Both are the folder CoCo works in.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo cwd upload", layout="wide")
st.title("CoCo — file upload into `cwd`")
st.caption("Attach files in the window's field or use the sidebar uploader.")

WORKSPACE = Path("cwd_upload_workspace").resolve()  # next to where you run the example
WORKSPACE.mkdir(parents=True, exist_ok=True)

with st.sidebar:
    st.markdown(f"`cwd` · `{WORKSPACE}`")
    st_coco.cwd_uploader(str(WORKSPACE), overwrite="replace", key="cwd_upload_sidebar")

st_coco.ask_coco(
    WORKSPACE,
    features=st_coco.Features(
        attachments=st_coco.Attachments(accept=[".csv", ".md", ".txt", ".json", ".sql", ".py"])
    ),
)
