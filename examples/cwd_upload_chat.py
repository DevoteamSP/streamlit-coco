"""Demo: upload files into CoCo cwd via chat attachments + sidebar uploader."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.rail import (
    ask_coco_switch,
    ask_minimize,
    ask_restore,
    present_ask,
    rail_minimized,
)

st.set_page_config(page_title="CoCo cwd upload", layout="wide")
show_ask = ask_coco_switch("upload_ask_coco")
_chat_min = show_ask and rail_minimized("upload_coco")
with st.container(horizontal=True, vertical_alignment="center"):
    st.title("CoCo — file upload into `cwd`")
    if show_ask and not _chat_min:
        ask_minimize("upload_coco")
st.caption("Attach files in chat or use the sidebar uploader. Files land under `_uploads/`.")

if not hasattr(st_coco, "cwd_uploader"):
    st.error(
        "This process loaded an old `streamlit_coco` without `cwd_uploader` "
        f"(`{getattr(st_coco, '__file__', '?')}`). "
        "Stop other Streamlit servers and run `make cwd-upload` from `streamlit-coco-dev`."
    )
    st.stop()

WORKSPACE = Path(__file__).resolve().parent / "workspaces" / "cwd_upload"
WORKSPACE.mkdir(parents=True, exist_ok=True)

SESSION_KEY = "cwd_upload"
GATE_KEY = "cwd_upload_started"


def _optional_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


connection = _optional_secret("snowflake_connection")
present_ask(
    show_ask,
    "upload_coco",
    lambda: st_coco.ask_coco(
        WORKSPACE, connection=connection, on_rail=ask_restore("upload_coco")
    ),
)

opts = st_coco.CocoOptions(
    connection=connection,
    cwd=str(WORKSPACE),
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
)
env = st_coco.check_environment(connection=connection)

if not st_coco.render_start_gate(
    opts,
    session_key=SESSION_KEY,
    gate_key=GATE_KEY,
    env=env,
    title="Start CoCo with a local upload workspace",
):
    st.stop()

session = st_coco.get_or_create_session(opts, key=SESSION_KEY)

with st.sidebar:
    st.markdown(f"`cwd` · `{WORKSPACE}`")
    st_coco.cwd_uploader(session, overwrite="replace", key="cwd_upload_sidebar")
    if st.button("Reset session", width="stretch"):
        st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
        st.rerun()
    st_coco.render_environment_status(env, stacked=True, show_title=False)

if not _chat_min:
    st_coco.panel(session=session, warm_up=True, show_status=True, run_every=0.25)
    st_coco.chat_input_bar(
        session,
        placeholder="Ask about an uploaded file, or attach one…",
        accept_file="multiple",
        file_type=["csv", "md", "txt", "json", "sql", "py", "yaml", "yml"],
    )
