"""Shared UI helpers for Backlog Desk pages."""

from __future__ import annotations

import streamlit as st

from utils.backlog import (
    PRIORITY_BADGE,
    STATUS_BADGE,
    Backlog,
    backlog_mtime_key,
    load_backlog,
)


@st.cache_data(ttl="30s")
def cached_backlog(_mtime: tuple[float, ...]) -> Backlog:
    return load_backlog()


def get_backlog() -> Backlog:
    return cached_backlog(backlog_mtime_key())


def status_badge(status: str) -> None:
    color, label = STATUS_BADGE.get(status, ("gray", status))
    st.badge(label, color=color)


def priority_badge(priority: str) -> None:
    color, label = PRIORITY_BADGE.get(priority, ("gray", priority))
    st.badge(label, color=color)


def open_ticket(ticket_id: str) -> None:
    st.session_state["selected_ticket"] = ticket_id
    st.switch_page("app_pages/ticket.py")


def open_epic(epic_id: str) -> None:
    st.session_state["selected_epic"] = epic_id
    st.switch_page("app_pages/epic.py")


def open_release(version: str) -> None:
    st.session_state["selected_release"] = version
    st.switch_page("app_pages/release.py")


def open_copilot(
    *,
    ticket_id: str | None = None,
    skill: str | None = None,
    auto_run: bool = False,
) -> None:
    """Open the right-rail Copilot (stay on the current page)."""
    from utils.copilot_panel import set_copilot_open

    if ticket_id:
        st.session_state["selected_ticket"] = ticket_id
    if skill:
        st.session_state["pending_skill"] = skill
        if auto_run:
            st.session_state["auto_run_skill"] = True
    set_copilot_open(True)
