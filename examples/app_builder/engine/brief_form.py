"""Shared filled-brief widgets for the Brief page and Copilot rail."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.brief import USER_BRIEF_KEY
from engine.catalog import AppType, Question
from engine.profile import DataProfile
from engine.state import slug

BRIEF_PAGE_NS = "ab_q"
RAIL_NS = "ab_rail"


def widget_key(question_id: str, *, key_ns: str, slug_name: str | None = None) -> str:
    return f"{key_ns}_{slug_name or slug()}_{question_id}"


def extra_keys(base: str) -> tuple[str, ...]:
    return (base, f"{base}_mode", f"{base}_ms", f"{base}_named")


def clear_form_widget_keys(
    slug_name: str,
    app_type: AppType,
    *,
    key_ns: str,
) -> None:
    ids = [USER_BRIEF_KEY, *[question.id for question in app_type.questions]]
    for question_id in ids:
        for key in extra_keys(widget_key(question_id, key_ns=key_ns, slug_name=slug_name)):
            st.session_state.pop(key, None)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return any(str(item).strip() for item in value)
    return bool(value)


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _infer_value(profile: DataProfile | None, question: Question) -> Any:
    if not question.infer or profile is None:
        return None
    return getattr(profile, question.infer, None)


def _profile_candidates(profile: DataProfile | None, question: Question) -> list[str]:
    value = _infer_value(profile, question)
    if isinstance(value, tuple) and value:
        return [str(item) for item in value]
    return []


def render_user_brief(
    current: dict[str, Any],
    *,
    key_ns: str,
    compact: bool = False,
) -> str:
    key = widget_key(USER_BRIEF_KEY, key_ns=key_ns)
    if key not in st.session_state:
        st.session_state[key] = str(current.get(USER_BRIEF_KEY) or "")
    return st.text_area(
        "Your brief",
        key=key,
        height=100 if compact else 180,
        label_visibility="collapsed",
        placeholder=(
            "What you want this app to do, who it is for, and what it must never do."
        ),
        help="CoCo reads this with the type brief. Optional — this is how you steer generation.",
    )


def render_question(
    question: Question,
    current: dict[str, Any],
    app_type: AppType,
    profile: DataProfile | None,
    *,
    key_ns: str,
    compact: bool = False,
) -> Any:
    key = widget_key(question.id, key_ns=key_ns)
    help_text = question.help or None
    existing = current.get(question.id)
    inferred = _infer_value(profile, question)
    label = question.prompt + (" *" if question.required else "")
    text_height = 70 if compact else 90

    if question.kind == "enum":
        options = list(question.options)
        if not options:
            if key not in st.session_state:
                st.session_state[key] = str(existing or "")
            return st.text_input(label, key=key, help=help_text)
        if key not in st.session_state:
            if existing in options:
                st.session_state[key] = existing
            elif isinstance(inferred, str) and inferred in options:
                st.session_state[key] = inferred
            else:
                st.session_state[key] = options[0]
        if len(options) <= 5:
            picked = st.segmented_control(label, options, key=key, help=help_text)
            return picked if picked is not None else st.session_state.get(key) or options[0]
        return st.selectbox(label, options, key=key, help=help_text)

    candidates = _profile_candidates(profile, question)
    if question.infer and candidates and question.kind in {"list", "text"}:
        ms_key = f"{key}_ms"
        if ms_key not in st.session_state:
            prior = [item for item in _as_str_list(existing) if item in candidates]
            st.session_state[ms_key] = prior if _has_value(existing) and prior else list(candidates)
        return st.multiselect(label, options=candidates, key=ms_key, help=help_text)

    if question.kind == "list":
        if key not in st.session_state:
            if isinstance(existing, list):
                st.session_state[key] = "\n".join(str(item) for item in existing)
            else:
                st.session_state[key] = str(existing or "")
        raw = st.text_area(label, key=key, help=help_text, height=text_height)
        return [line.strip() for line in raw.splitlines() if line.strip()]

    if question.kind in {"semantic_view", "tables"}:
        demo = app_type.demo_fixture
        choices = ["Named"]
        if demo:
            choices = ["Demo pack", "Named"]
        stored = str(existing or "")
        default_mode = "Demo pack" if stored.startswith("DEMO:") or not stored else "Named"
        mode_key = f"{key}_mode"
        if mode_key not in st.session_state:
            st.session_state[mode_key] = default_mode if default_mode in choices else choices[0]
        mode = st.segmented_control(label, choices, key=mode_key, help=help_text)
        if mode is None:
            mode = st.session_state.get(mode_key) or choices[0]
        if mode == "Demo pack" and demo:
            st.caption(f"Using the **{demo}** sample — Preview works with no warehouse.")
            return f"DEMO:{demo}"
        named = stored[5:] if stored.startswith("DEMO:") else stored
        named_key = f"{key}_named"
        if named_key not in st.session_state:
            st.session_state[named_key] = named
        placeholder = (
            "ANALYTICS.PUBLIC.SV_SALES"
            if question.kind == "semantic_view"
            else "one table or file per line"
        )
        return st.text_input(
            "Name" if question.kind == "semantic_view" else "Tables / files",
            key=named_key,
            placeholder=placeholder,
        )

    if question.kind == "text":
        if key not in st.session_state:
            if isinstance(existing, (list, tuple)):
                st.session_state[key] = "\n".join(
                    str(item) for item in existing if str(item).strip()
                )
            else:
                st.session_state[key] = str(existing or "")
        return st.text_area(label, key=key, help=help_text, height=text_height)

    if key not in st.session_state:
        st.session_state[key] = str(existing or "")
    return st.text_input(label, key=key, help=help_text)


def _read_question_state(
    question: Question,
    key: str,
    fallback: Any,
    app_type: AppType,
) -> Any:
    if question.kind == "enum":
        picked = st.session_state.get(key, fallback)
        return picked if picked is not None else fallback
    ms_key = f"{key}_ms"
    if question.infer and ms_key in st.session_state:
        return st.session_state[ms_key]
    if question.kind == "list":
        raw = st.session_state.get(key, fallback)
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        return [line.strip() for line in str(raw or "").splitlines() if line.strip()]
    if question.kind in {"semantic_view", "tables"}:
        mode = st.session_state.get(f"{key}_mode")
        if mode == "Demo pack" and app_type.demo_fixture:
            return f"DEMO:{app_type.demo_fixture}"
        named = st.session_state.get(f"{key}_named")
        if named is not None:
            return named
        return fallback
    if question.kind == "text":
        raw = st.session_state.get(key, fallback)
        if isinstance(raw, (list, tuple)):
            return "\n".join(str(item) for item in raw if str(item).strip())
        return str(raw or "")
    if key in st.session_state:
        return st.session_state[key]
    return fallback


def collect_form_answers(
    app_type: AppType,
    current: dict[str, Any],
    *,
    key_ns: str,
) -> dict[str, Any]:
    """Read the current widget keys (authoritative on Save)."""
    values = dict(current)
    slug_name = slug()
    brief_key = widget_key(USER_BRIEF_KEY, key_ns=key_ns, slug_name=slug_name)
    if brief_key in st.session_state:
        values[USER_BRIEF_KEY] = str(st.session_state[brief_key] or "")
    for question in app_type.questions:
        key = widget_key(question.id, key_ns=key_ns, slug_name=slug_name)
        values[question.id] = _read_question_state(
            question, key, values.get(question.id), app_type
        )
    return values


def seed_form_widget_keys(
    values: dict[str, Any],
    app_type: AppType,
    *,
    key_ns: str,
    slug_name: str,
) -> None:
    """Force Brief-page widgets to match a saved answers dict."""
    brief_key = widget_key(USER_BRIEF_KEY, key_ns=key_ns, slug_name=slug_name)
    st.session_state[brief_key] = str(values.get(USER_BRIEF_KEY) or "")
    for question in app_type.questions:
        key = widget_key(question.id, key_ns=key_ns, slug_name=slug_name)
        raw = values.get(question.id)
        if question.kind == "list" and not isinstance(raw, str):
            st.session_state[key] = "\n".join(
                str(item) for item in (raw or []) if str(item).strip()
            )
        elif question.kind in {"semantic_view", "tables"}:
            stored = str(raw or "")
            demo = stored.startswith("DEMO:")
            st.session_state[f"{key}_mode"] = "Demo pack" if demo else "Named"
            st.session_state[f"{key}_named"] = stored[5:] if demo else stored
        else:
            st.session_state[key] = raw


def render_answers_form(
    app_type: AppType,
    current: dict[str, Any],
    *,
    key_ns: str,
    compact: bool = False,
    profile: DataProfile | None = None,
) -> dict[str, Any]:
    """Owner brief plus every type question. Returns the filled answers dict."""
    values = dict(current)
    st.markdown("**Your brief**")
    if not compact:
        st.caption("What you want, what you do not want, who uses this.")
    values[USER_BRIEF_KEY] = render_user_brief(values, key_ns=key_ns, compact=compact)
    if app_type.questions:
        st.markdown("**Questions**")
        if not compact:
            st.caption("What this type needs before we can build.")
        for question in app_type.questions:
            values[question.id] = render_question(
                question,
                values,
                app_type,
                profile,
                key_ns=key_ns,
                compact=compact,
            )
    return values
