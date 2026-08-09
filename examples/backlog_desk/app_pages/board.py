"""Board — KPIs and filterable ticket table."""

from __future__ import annotations

import streamlit as st
from utils.backlog import STATUSES, filter_tickets, tickets_as_rows
from utils.ui import get_backlog, open_epic, open_ticket

backlog = get_backlog()
kpis = backlog.kpis()

with st.container(horizontal=True):
    st.metric("Open", kpis["open"], border=True)
    st.metric("In progress", kpis["in_progress"], border=True)
    st.metric("Blocked", kpis["blocked"], border=True)
    st.metric("Done", kpis["done"], border=True)
    st.metric("Points open", kpis["points_open"], border=True)

epic_options = ["all", *[e.id for e in backlog.epics]]
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    query = st.text_input("Search", placeholder="T-042 or title…", label_visibility="collapsed")
with c2:
    status = st.selectbox("Status", ["all", *STATUSES], label_visibility="collapsed")
with c3:
    priority = st.selectbox(
        "Priority",
        ["all", "critical", "high", "medium", "low"],
        label_visibility="collapsed",
    )
with c4:
    epic_id = st.selectbox("Epic", epic_options, label_visibility="collapsed")

tickets = filter_tickets(
    backlog,
    status=status,
    priority=priority,
    epic_id=epic_id,
    query=query or "",
)

st.caption(f"{len(tickets)} ticket(s)")

if not tickets:
    st.info("No tickets match these filters.", icon=":material/info:")
else:
    rows = tickets_as_rows(tickets)
    event = st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "epic": st.column_config.TextColumn("Epic", width="small"),
            "points": st.column_config.NumberColumn("Pts", width="small"),
        },
        key="board_table",
    )
    selected = event.selection.rows if event and event.selection else []
    if selected:
        ticket = tickets[selected[0]]
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"**Selected** `{ticket.id}` — {ticket.title}")
            if st.button("Open ticket", icon=":material/open_in_new:", type="primary"):
                open_ticket(ticket.id)
            if ticket.epic_id and st.button("Open epic", icon=":material/account_tree:"):
                open_epic(ticket.epic_id)

with st.expander("Epics", expanded=False):
    for epic in backlog.epics:
        kids = backlog.tickets_for_epic(epic.id)
        done = sum(1 for t in kids if t.status == "done")
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(
                f"**{epic.id}** · {epic.title} · `{epic.status}` · "
                f"{done}/{len(kids)} done · release `{epic.target_release}`"
            )
            if st.button("View", key=f"epic_btn_{epic.id}", icon=":material/arrow_forward:"):
                open_epic(epic.id)
