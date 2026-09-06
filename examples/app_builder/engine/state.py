"""Session state for App Builder."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.brief import delete_filled, load_filled, save_filled, slugify, unique_slug
from engine.catalog import AppType, get_type

TYPE_KEY = "ab_type_id"
SLUG_KEY = "ab_slug"
APP_NAME_KEY = "ab_app_name"
ANSWERS_KEY = "ab_answers"

JOURNEY = {
    "Welcome": "screens/welcome.py",
    "Library": "screens/library.py",
    "Brief": "screens/brief.py",
    "Studio": "screens/studio.py",
    "Admin": "screens/admin.py",
}


def ensure_defaults() -> None:
    st.session_state.setdefault(TYPE_KEY, None)
    st.session_state.setdefault(SLUG_KEY, None)
    st.session_state.setdefault(APP_NAME_KEY, None)
    st.session_state.setdefault(ANSWERS_KEY, {})


def selected_type_id() -> str | None:
    value = st.session_state.get(TYPE_KEY)
    return str(value) if value else None


def selected_type() -> AppType | None:
    type_id = selected_type_id()
    return get_type(type_id) if type_id else None


def slug() -> str | None:
    value = st.session_state.get(SLUG_KEY)
    return str(value) if value else None


def app_name() -> str | None:
    value = st.session_state.get(APP_NAME_KEY)
    return str(value) if value else None


def set_app_name(name: str) -> None:
    clean = str(name or "").strip()
    if clean:
        st.session_state[APP_NAME_KEY] = clean


def answers() -> dict[str, Any]:
    raw = st.session_state.get(ANSWERS_KEY)
    return dict(raw) if isinstance(raw, dict) else {}


def set_answers(values: dict[str, Any]) -> None:
    st.session_state[ANSWERS_KEY] = dict(values)


def start_app(app_type: AppType, name: str) -> str:
    clean = name.strip()
    if not clean:
        raise ValueError("Give the app a name.")
    slug_name = unique_slug(slugify(clean))
    st.session_state[TYPE_KEY] = app_type.id
    st.session_state[SLUG_KEY] = slug_name
    st.session_state[APP_NAME_KEY] = clean
    st.session_state[ANSWERS_KEY] = {}
    save_filled(slug_name, app_type, {}, app_name=clean)
    return slug_name


def persist_brief(values: dict[str, Any] | None = None) -> None:
    app_type = selected_type()
    current = slug()
    if app_type is None or not current:
        return
    payload = dict(values) if values is not None else answers()
    if values is not None:
        set_answers(payload)
    save_filled(current, app_type, payload, app_name=app_name())


ANSWERS_OVERRIDE_KEY = "ab_answers_override"
RAIL_BRIEF_OPEN_KEY = "ab_rail_brief_open"


def apply_brief_answers(values: dict[str, Any]) -> None:
    """Write the filled brief into session answers and persist ``BRIEF.md``."""
    persist_brief(values)
    st.session_state[ANSWERS_OVERRIDE_KEY] = dict(values)
    st.session_state[RAIL_BRIEF_OPEN_KEY] = True


def new_app() -> None:
    st.session_state[TYPE_KEY] = None
    st.session_state[SLUG_KEY] = None
    st.session_state[APP_NAME_KEY] = None
    st.session_state[ANSWERS_KEY] = {}


def forget_app(slug_name: str) -> None:
    delete_filled(slug_name)
    if slug() == slug_name:
        new_app()


def go(title: str) -> None:
    st.switch_page(JOURNEY.get(title, title))


def resume(slug_name: str, app_type: AppType) -> None:
    saved = load_filled(slug_name)
    st.session_state[TYPE_KEY] = app_type.id
    st.session_state[SLUG_KEY] = slug_name
    st.session_state[APP_NAME_KEY] = str((saved or {}).get("app_name") or slug_name)
    st.session_state[ANSWERS_KEY] = dict((saved or {}).get("answers") or {})
