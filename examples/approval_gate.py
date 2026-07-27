"""Example emphasizing approval gates for destructive tools."""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo Approval Gate", layout="wide")
st.title("CoCo approval gate")

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

result = st_coco.chat(session=session, key="coco_chat", height=580)

if result.pending_approval:
    st.warning(f"Awaiting approval for `{result.pending_approval['tool_name']}`")
