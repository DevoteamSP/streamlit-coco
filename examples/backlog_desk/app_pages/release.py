"""Release notes page."""

from __future__ import annotations

import streamlit as st
from utils.ui import get_backlog, open_copilot, open_ticket, priority_badge, status_badge

backlog = get_backlog()
versions = [r.version for r in backlog.releases]
if not versions:
    st.warning("No releases in `data/releases/`.")
    st.stop()

default = st.session_state.get("selected_release")
if default not in versions:
    default = versions[0]

version = st.selectbox(
    "Release",
    versions,
    index=versions.index(default),
    key="release_select",
)
st.session_state["selected_release"] = version
release = backlog.release(version)
assert release is not None

with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown(f"### {release.title}")
    color = "green" if release.status == "published" else "orange"
    st.badge(release.status, color=color)
    if release.date:
        st.caption(f"Date · `{release.date}`")

if st.button(
    "Draft / refresh notes with Copilot",
    icon=":material/edit_note:",
    type="primary",
):
    open_copilot(skill="draft-release-notes", auto_run=True)

tickets = backlog.tickets_for_release(version)
st.markdown(f"**{len(tickets)} ticket(s) in scope**")
for t in tickets:
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f"`{t.id}` · {t.title}")
        status_badge(t.status)
        priority_badge(t.priority)
        if st.button("Open", key=f"rel_t_{t.id}", icon=":material/open_in_new:"):
            open_ticket(t.id)

st.divider()
st.markdown(release.body)
