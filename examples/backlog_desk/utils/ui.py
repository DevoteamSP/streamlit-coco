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
