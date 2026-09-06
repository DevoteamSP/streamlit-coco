"""Library — resume project cards and type cards to start a new project."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

import streamlit as st
from engine.brief import (
    USER_BRIEF_KEY,
    app_exists,
    filled_app_name,
    list_saved_briefs,
    load_filled,
)
from engine.catalog import (
    AppType,
    catalog_topics,
    filter_by_topics,
    get_type,
    load_catalog,
)
from engine.state import forget_app, go, resume, start_app

_GRID = 6
_T = TypeVar("_T")


def _chunk(items: list[_T], size: int) -> list[list[_T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _updated_label(payload: dict[str, Any] | None, folder: Path) -> str:
    raw = (payload or {}).get("updated_at")
    when: datetime | None = None
    if isinstance(raw, str) and raw.strip():
        try:
            when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            when = None
    if when is None:
        when = datetime.fromtimestamp(folder.stat().st_mtime, tz=timezone.utc)
    local = when.astimezone()
    return f"{local:%b} {local.day}, {local.year}"


def _delete_popover(slug_name: str, label: str, *, key: str) -> None:
    with st.popover("Delete", icon=":material/delete:"):
        st.caption(f"Removes **{label}** (`{slug_name}`). This cannot be undone.")
        if st.button("Delete this app", type="primary", icon=":material/delete:", key=key):
            forget_app(slug_name)
            st.toast(f"Deleted `{slug_name}`")
            st.rerun()


def _saved_cards() -> list[tuple[Path, dict[str, Any] | None, AppType]]:
    cards: list[tuple[Path, dict[str, Any] | None, AppType]] = []
    for folder in list_saved_briefs():
        payload = load_filled(folder.name)
        app_type = get_type((payload or {}).get("type_id") or folder.name)
        if app_type is None:
            continue
        cards.append((folder, payload, app_type))
    return cards


def _filter_saved(
    cards: list[tuple[Path, dict[str, Any] | None, AppType]],
    selected: list[str] | None,
) -> list[tuple[Path, dict[str, Any] | None, AppType]]:
    if not selected:
        return cards
    wanted = set(selected)
    return [card for card in cards if wanted.intersection(card[2].topics)]


def _resume_section(
    cards: list[tuple[Path, dict[str, Any] | None, AppType]],
) -> None:
    if not cards:
        return

    st.subheader("Resume")
    st.caption("Open a saved project and pick up the brief.")
    for row in _chunk(cards, _GRID):
        cols = st.columns(_GRID, gap="small")
        for col, (folder, payload, app_type) in zip(cols, row):
            name = filled_app_name(payload, fallback=folder.name)
            answers = (payload or {}).get("answers") or {}
            owner = str(answers.get(USER_BRIEF_KEY) or "").strip()
            with col.container(border=True, height="stretch"):
                with st.container(height="stretch"):
                    st.markdown(f"**{app_type.material_icon} {name}**")
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.badge(app_type.name)
                        st.badge(app_type.grounding_label)
                    st.caption(f"Updated {_updated_label(payload, folder)}")
                    if owner:
                        snippet = owner if len(owner) <= 96 else owner[:93] + "…"
                        st.caption(snippet)
                    if app_exists(folder.name):
                        st.badge(
                            "App ready",
                            icon=":material/check_circle:",
                            color="green",
                        )
                    else:
                        st.badge(
                            "Brief only",
                            icon=":material/edit_note:",
                            color="orange",
                        )
                with st.container(horizontal=True):
                    if st.button(
                        "Open",
                        type="primary",
                        icon=":material/play_arrow:",
                        key=f"ab_resume_{folder.name}",
                    ):
                        resume(folder.name, app_type)
                        go("Brief")
                    _delete_popover(
                        folder.name,
                        name,
                        key=f"ab_resume_del_{folder.name}",
                    )


def run() -> None:
    types = load_catalog()
    topics = catalog_topics(types)
    picked = st.pills(
        "Topics",
        topics,
        selection_mode="multi",
        key="ab_topic_pills",
        help="Leave empty to show every saved app and type. Local = no Snowflake connection.",
    )
    selected = list(picked) if picked else None
    types = filter_by_topics(types, selected)
    _resume_section(_filter_saved(_saved_cards(), selected))

    st.subheader("Create a new project")
    if not types:
        st.info("No types for those topics. Clear the pills to see the full library.")
        return

    for row in _chunk(list(types), _GRID):
        cols = st.columns(_GRID, gap="small")
        for col, app_type in zip(cols, row):
            with col.container(border=True, height="stretch"):
                with st.container(height="stretch"):
                    st.markdown(f"**{app_type.material_icon} {app_type.name}**")
                    st.badge(app_type.grounding_label)
                    st.caption("For: " + (", ".join(app_type.users) or "—"))
                    if app_type.topics:
                        st.caption(" · ".join(app_type.topics))
                    if app_type.screenshot is not None:
                        st.image(str(app_type.screenshot), width="stretch")
                    if app_type.coming_soon:
                        st.badge("Coming soon", color="gray")
                    if not app_type.needs_snowflake:
                        st.badge("No Snowflake", color="green")
                    elif app_type.demo_fixture:
                        st.badge("Demo pack", color="blue")
                    if app_type.coming_soon:
                        st.caption("Not selectable for Build yet.")
                if not app_type.coming_soon:
                    with st.popover(
                        "Create a new app",
                        icon=":material/add:",
                        type="primary",
                        width="stretch",
                    ):
                        with st.form(f"ab_create_{app_type.id}"):
                            name = st.text_input(
                                "App name",
                                placeholder=f"e.g. Q3 {app_type.name}",
                            )
                            created = st.form_submit_button(
                                "Create",
                                type="primary",
                                icon=":material/add:",
                            )
                        if created:
                            try:
                                start_app(app_type, str(name or ""))
                                go("Brief")
                            except ValueError as exc:
                                st.error(str(exc))


run()
