"""Approval gate: what CoCo may do alone, what it must ask, and what it may be told once.

The policy decides. Reading inside the folder is free; ``git status`` is a listed command and also
free; a file change shows its exact text; SQL shows its exact statement; and the request offers a
standing permission, so "Do not ask again" lets the next step of its family run unasked.
Scripted words to try: ``status`` (listed command), ``unlisted`` (git push), ``edit``, ``write``,
``snowflake`` (with ``drop``: a statement).
"""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco import policy

st.set_page_config(page_title="CoCo Approval Gate", layout="wide")
st.title("CoCo approval gate")
st.info("Reading is free. Every change, command or statement asks first, with its exact text.")

status = policy.Command(
    "Look at what has changed", ("git", "status", "--short"), "The list of changed files"
)
st_coco.ask_coco(
    ".",
    policy=policy.FolderPolicy(
        ".",
        commands=[status, *policy.git_readonly(".")],
        changes="*.md",  # other files ask and are never offered a standing permission
        sql=True,
        standing=True,
    ),
)
