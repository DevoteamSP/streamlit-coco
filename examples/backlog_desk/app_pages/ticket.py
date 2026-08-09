"""Ticket detail page."""

from __future__ import annotations

import streamlit as st
from utils.paths import APP_ROOT
from utils.ui import get_backlog, open_copilot, open_epic, priority_badge, status_badge

backlog = get_backlog()
ticket_ids = [t.id for t in backlog.tickets]
if not ticket_ids:
    st.warning("No tickets in `data/tickets/`.")
    st.stop()

default = st.session_state.get("selected_ticket")
if default not in ticket_ids:
    default = ticket_ids[0]

ticket_id = st.selectbox(
    "Ticket",
    ticket_ids,
    index=ticket_ids.index(default),
    key="ticket_select",
)
st.session_state["selected_ticket"] = ticket_id
ticket = backlog.ticket(ticket_id)
assert ticket is not None
epic = backlog.epic(ticket.epic_id)

with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown(f"### {ticket.title}")
    status_badge(ticket.status)
    priority_badge(ticket.priority)
    st.badge(ticket.type, color="blue")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Points", ticket.points, border=True)
with c2:
    st.metric("Owner", ticket.owner, border=True)
with c3:
    st.metric("Epic", ticket.epic_id or "—", border=True)

st.markdown("**Description**")
st.write(ticket.description or "_No description_")

st.caption(f"File · `{ticket.path.relative_to(APP_ROOT)}`")

with st.container(horizontal=True):
    if epic and st.button("Open epic", icon=":material/account_tree:"):
        open_epic(epic.id)
    if st.button("Check DoD", icon=":material/checklist:", type="primary"):
        open_copilot(ticket_id=ticket.id, skill="check-dod", auto_run=True)
    if st.button("Propose update", icon=":material/edit:"):
        open_copilot(ticket_id=ticket.id, skill="propose-ticket-update", auto_run=True)
    if st.button("Ask Copilot", icon=":material/psychology:"):
        open_copilot(ticket_id=ticket.id)

with st.expander("Raw JSON", expanded=False):
    st.code(ticket.path.read_text(encoding="utf-8"), language="json")
