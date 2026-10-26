"""Managed chat: Ask CoCo on Snowflake's managed coding agent, no `cortex` program (experimental).

The agent runs in Snowflake (a sandbox, with the workspace you mount), not on this computer. You
log in with a profile of ~/.snowflake; the Snowflake connector reads its secrets and the Cortex
Agent SDK gets the session token. Run it with `make managed`.

What differs from the other examples: no working folder (the agent cannot read this repository),
a role you choose (the agent has the rights of that role), and Snowflake decides which commands ask
before they run: a harmless one (`echo hello`) runs unasked, one that writes asks.
"""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.diagnostics import (
    default_snowflake_connection_name,
    list_snowflake_connections,
)
from streamlit_coco.policy import FolderPolicy
from streamlit_coco.window import request_open

KEY = "managed"
STARTERS = [
    {"title": "Say hello", "text": "Reply with one short sentence saying hello. Use no tool."},
    {
        "title": "Run a command",
        "text": "Run the shell command `echo hello` and tell me what it printed.",
    },
    {
        "title": "Write a file",
        "text": "Create /tmp/coco_probe.txt containing the word probe, using the shell.",
    },
]

st.set_page_config(page_title="CoCo managed agent", page_icon=":material/cloud:", layout="wide")
st.title(":material/cloud: CoCo, managed by Snowflake")
st.caption("streamlit-coco · managed coding agent (experimental) · no local CLI")
st.info(
    "The agent runs in Snowflake's sandbox, with the rights of the role you pick below: give it "
    "the least that works. Snowflake asks before a command it rates risky; a command it rates "
    "harmless runs without asking. Every request that does ask waits for your Allow or Decline.",
    icon=":material/info:",
)

with st.sidebar:
    st.subheader("Connection")
    names = list_snowflake_connections()
    if not names:
        st.error("No Snowflake profile in ~/.snowflake. Add one to connections.toml.")
        st.stop()
    default = default_snowflake_connection_name("config.toml")  # the user's own default, if any
    profile = st.selectbox(
        "Profile",
        names,
        index=names.index(default) if default in names else None,
        placeholder="Pick the account to log in to",
    )
    role = st.text_input(
        "Role",
        value="PUBLIC",
        help="The agent works with the rights of this role. Empty: the profile's own role.",
    )
    mount = st.text_input(
        "Workspace to mount (optional)",
        placeholder="DB.SCHEMA.WORKSPACE or USER$ME.PUBLIC.DEFAULT$",
        help="Mounted at /workspace; the agent can read and write it, each write asking first.",
    )
    if st.button("Connect", type="primary", icon=":material/link:", disabled=profile is None):
        old = st.session_state.pop(KEY + "_options", None)
        if old is not None and old.connection is not None:
            old.connection.close()
        try:
            with st.spinner(f"Logging in with {profile}…"):
                st.session_state[KEY + "_options"] = st_coco.options_from_connection(
                    profile,
                    role=role.strip() or None,
                    workspace_mounts=(
                        [{"name": mount.strip(), "mount_path": "/workspace"}]
                        if mount.strip()
                        else []
                    ),
                )
            st.session_state[KEY + "_open"] = True
        except Exception as error:  # noqa: BLE001 - the page says why, whatever it was
            st.error(f"Could not log in: {error}")

options = st.session_state.get(KEY + "_options")
if options is None:
    st.write("Pick a profile and a role, then **Connect**. The chat opens when you are logged in.")
    st.stop()

st.success(f"Logged in with `{options.label}`. The chat is the button at the bottom right.")
if st.session_state.pop(KEY + "_open", False):
    request_open(KEY)  # before the mount: it opens the window of that mount, once
st_coco.ask_coco(
    ".",
    key=KEY,
    agent=st_coco.managed_agent(options),
    connection=options.label,
    policy=FolderPolicy(".", words=st_coco.SANDBOX_WORDS, where=st_coco.SANDBOX_WHERE),
    prompts=STARTERS,
    labels={"window.field.placeholder": "Ask the managed agent…"},
)
