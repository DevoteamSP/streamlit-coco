"""Example emphasizing approval gates for destructive tools."""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.mini import window_connection
from streamlit_coco.rail import (
    ask_coco_switch,
    ask_minimize,
    ask_restore,
    present_ask,
    rail_minimized,
)

st.set_page_config(page_title="CoCo Approval Gate", layout="wide")
show_ask = ask_coco_switch("approval_ask_coco")
_chat_min = show_ask and rail_minimized("approval_coco")
with st.container(horizontal=True, vertical_alignment="center"):
    st.title("CoCo approval gate")
    if show_ask and not _chat_min:
        ask_minimize("approval_coco")

st.info("Write, Edit, and Bash tools require explicit approval before CoCo can run them.")

opts = st_coco.CocoOptions(
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep", "Edit", "Write", "Bash"],
    require_approval_for=["Edit", "Write", "Bash"],
    permission_mode="default",
)

session = st_coco.get_or_create_session(opts, key="approval_demo")
if not session.is_ready and not session.is_connecting:
    session.start()

present_ask(
    show_ask,
    "approval_coco",
    lambda: st_coco.ask_coco(
        ".",
        connection=window_connection(session),
        on_rail=ask_restore("approval_coco"),
    ),
)

result = None
if not _chat_min:
    result = st_coco.chat(session=session, key="coco_chat", height=580)

if result is not None and result.pending_approval:
    st.warning(f"Awaiting approval for `{result.pending_approval['tool_name']}`")
