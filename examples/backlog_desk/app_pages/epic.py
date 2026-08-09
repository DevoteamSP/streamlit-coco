"""Epic detail page."""

from __future__ import annotations

import streamlit as st
from utils.ui import get_backlog, open_copilot, open_ticket, priority_badge, status_badge

backlog = get_backlog()
epic_ids = [e.id for e in backlog.epics]
if not epic_ids:
    st.warning("No epics in `data/epics/`.")
    st.stop()

default = st.session_state.get("selected_epic")
if default not in epic_ids:
    default = epic_ids[0]

epic_id = st.selectbox("Epic", epic_ids, index=epic_ids.index(default), key="epic_select")
st.session_state["selected_epic"] = epic_id
epic = backlog.epic(epic_id)
assert epic is not None

with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown(f"### {epic.title}")
    status_badge(epic.status)
    st.badge(f"Release {epic.target_release}", color="violet")
    st.caption(f"Owner · `{epic.owner}`")

st.write(epic.summary or "_No summary_")

tickets = backlog.tickets_for_epic(epic.id)
done = sum(1 for t in tickets if t.status == "done")
points = sum(t.points for t in tickets)
points_done = sum(t.points for t in tickets if t.status == "done")

with st.container(horizontal=True):
    st.metric("Tickets", len(tickets), border=True)
    st.metric("Done", f"{done}/{len(tickets)}", border=True)
    st.metric("Points", f"{points_done}/{points}", border=True)

with st.container(horizontal=True):
    if st.button("Ask Copilot about this epic", icon=":material/psychology:", type="primary"):
        open_copilot(skill="summarize-sprint", auto_run=True)
    if st.button("Draft release notes", icon=":material/edit_note:"):
        st.session_state["selected_release"] = epic.target_release
        open_copilot(skill="draft-release-notes", auto_run=True)

st.subheader("Tickets")
for t in tickets:
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"**{t.id}** · {t.title}")
            status_badge(t.status)
            priority_badge(t.priority)
            st.caption(f"{t.points} pts · `{t.owner}`")
            if st.button("Open", key=f"open_{t.id}", icon=":material/open_in_new:"):
                open_ticket(t.id)
