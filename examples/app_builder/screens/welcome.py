"""Welcome — who this is for and the three steps."""

from __future__ import annotations

import streamlit as st
from engine.state import go

_STEPS = (
    (
        ":material/apps:",
        "1 · Library",
        "Pick the kind of app you need. Each card says who it is for and what data it uses.",
        "Browse",
        "blue",
    ),
    (
        ":material/edit_note:",
        "2 · Brief",
        "Drop your file or pick the demo. We show what we found. "
        "You confirm, correct, and add the two things only you know.",
        "Confirm",
        "blue",
    ),
    (
        ":material/web:",
        "3 · Studio",
        "CoCo writes the app under your approval. Preview starts on its own. "
        "Talk to it to keep shaping it.",
        "Preview",
        "orange",
    ),
)


def run() -> None:
    st.markdown(
        "You never start from a blank `app.py`. You pick a type, fill its brief, "
        "and CoCo writes a Streamlit app you can preview and regenerate."
    )
    st.markdown(
        "This is an example of "
        "[streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) "
        "for business users — the people who own the question. "
        "It is not a BI migration (that is **BI → Semantic**) "
        "and not napkin-only generation."
    )

    if st.button(
        "Get started — browse types",
        type="primary",
        icon=":material/navigate_next:",
        key="ab_welcome_next",
    ):
        go("Library")

    st.subheader("What happens")
    cols = st.columns(3, gap="medium")
    for col, (icon, title, body, badge, color) in zip(cols, _STEPS):
        with col.container(border=True, height="stretch"):
            st.markdown(f"**{icon} {title}**")
            st.caption(body)
            st.badge(badge, color=color)

    st.subheader("How to use it")
    h1, h2 = st.columns(2, gap="medium")
    with h1.container(border=True, height="stretch"):
        st.markdown("**Open Copilot**")
        st.caption(
            "Connect once from the header. **Build this app** queues a Write. "
            "Approve the files in plain language; expand the diff if you want."
        )
    with h2.container(border=True, height="stretch"):
        st.markdown("**Open Preview**")
        st.caption(
            "Runs the generated app beside you. After a Write it starts on its own. "
            "**Fix with CoCo** sends the traceback back as a job. "
            "Demo packs work with no warehouse."
        )


run()
