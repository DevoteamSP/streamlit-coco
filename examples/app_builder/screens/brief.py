"""Brief — type story, drop data, confirm findings, optional sketches."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from engine.actions import start_coco_build, start_demo_scaffold
from engine.brief import (
    SKETCH_DIR,
    USER_BRIEF_KEY,
    answers_complete,
    list_sketches,
    partition_questions,
    slug_dir,
)
from engine.brief_form import (
    BRIEF_PAGE_NS,
    clear_form_widget_keys,
    collect_form_answers,
    render_question,
    render_user_brief,
    seed_form_widget_keys,
)
from engine.catalog import AppType
from engine.jobs import set_copilot_open
from engine.paths import FIXTURES_DIR
from engine.profile import EMPTY_PROFILE, DataProfile, profile_csv
from engine.state import (
    ANSWERS_OVERRIDE_KEY,
    answers,
    app_name,
    forget_app,
    go,
    persist_brief,
    selected_type,
    set_answers,
    set_app_name,
    slug,
)

_PROFILE_KEY = "ab_data_profile"
_PROFILE_SRC_KEY = "ab_data_profile_src"


def _fixture_path(demo: str) -> Path | None:
    exact = FIXTURES_DIR / demo
    if exact.is_file():
        return exact
    matches = sorted(FIXTURES_DIR.glob(f"{demo}.*"))
    return matches[0] if matches else None


def _ensure_profile(slug_name: str, grounding: str) -> DataProfile | None:
    src_map: dict[str, str] = st.session_state.setdefault(_PROFILE_SRC_KEY, {})
    prof_map: dict[str, DataProfile | None] = st.session_state.setdefault(_PROFILE_KEY, {})
    if src_map.get(slug_name) == grounding and slug_name in prof_map:
        return prof_map[slug_name]
    if not grounding.startswith("DEMO:"):
        src_map[slug_name] = grounding
        prof_map[slug_name] = None
        return None
    demo = grounding[5:]
    path = _fixture_path(demo)
    result = profile_csv(path) if path is not None else EMPTY_PROFILE
    src_map[slug_name] = grounding
    prof_map[slug_name] = result
    return result


def _missing_labels(app_type: AppType, missing: list[str]) -> str:
    by_id = {q.id: q for q in app_type.questions}
    labels = []
    for mid in missing:
        q = by_id.get(mid)
        labels.append(q.prompt.rstrip(" ?") if q else mid)
    return ", ".join(labels)


def _render_findings(profile: DataProfile | None, *, grounding: str) -> None:
    if grounding.startswith("DEMO:") and profile and profile.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{profile.row_count:,}", border=True)
        if profile.date_range:
            c2.metric("Period", f"{profile.date_range[0]} → {profile.date_range[1]}", border=True)
        else:
            c2.metric("Period", "No dates", border=True)
        c3.metric("Suggested grain", profile.grain or "—", border=True)
        st.caption("Uncheck or change anything that looks wrong. Your edit wins.")
        return
    if grounding and not grounding.startswith("DEMO:"):
        st.info("A named semantic view is not profiled yet. Fill the fields below yourself.")
        return
    st.caption("Confirm or type the answers below.")


def _bullet_list(title: str, items: tuple[str, ...]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("—")
        return
    for item in items:
        st.markdown(f"- {item}")


def _name_widget_key(slug_name: str) -> str:
    return f"ab_brief_app_name_{slug_name}"


def _sync_app_name(slug_name: str, fallback: str) -> str:
    key = _name_widget_key(slug_name)
    if key not in st.session_state:
        st.session_state[key] = app_name() or fallback
    raw = str(st.session_state.get(key) or "").strip()
    if raw:
        set_app_name(raw)
    else:
        st.session_state[key] = app_name() or fallback
    return key


def _render_actions(app_type: AppType, current: str, missing: list[str]) -> None:
    can_demo = bool(app_type.demo_fixture) and not missing
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button(
            "Build this app",
            type="primary",
            icon=":material/psychology:",
            disabled=bool(missing),
            key="ab_build_coco",
        ):
            start_coco_build(regenerate=False)
        if app_type.demo_fixture and st.button(
            "Try a local demo",
            icon=":material/handyman:",
            disabled=not can_demo,
            key="ab_build_demo",
        ):
            start_demo_scaffold()
        if st.button("Open Copilot", icon=":material/psychology:", key="ab_brief_copilot"):
            set_copilot_open(True)
            st.rerun()
        if st.button("Open Studio", icon=":material/web:", key="ab_to_studio"):
            go("Studio")
        with st.popover("Delete app", icon=":material/delete:"):
            st.caption(
                f"Removes **{app_name() or current}** (`{current}`). "
                "This cannot be undone."
            )
            if st.button(
                "Delete this app",
                type="primary",
                icon=":material/delete:",
                key="ab_brief_del_ok",
            ):
                forget_app(current)
                st.toast(f"Deleted `{current}`")
                go("Library")
    if missing:
        st.caption(f"To build, we still need: {_missing_labels(app_type, missing)}")


def _render_sketches(slug_name: str, dest: Path) -> None:
    st.markdown("**Sketches**")
    st.caption("Optional wireframe, whiteboard photo, or schema.")
    uploaded = st.file_uploader(
        "Sketches",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        key="ab_sketches",
        label_visibility="collapsed",
    )
    if uploaded:
        import streamlit_coco as st_coco

        dest.mkdir(parents=True, exist_ok=True)
        try:
            saved = st_coco.upload_to_cwd(
                dest,
                uploaded,
                subdir=SKETCH_DIR,
                overwrite="replace",
            )
            persist_brief()
            st.toast(f"Saved {len(saved)} sketch(es)")
        except st_coco.CwdUploadError as exc:
            st.error(str(exc))
    sketches = list_sketches(slug_name)
    if not sketches:
        return
    thumbs = st.columns(min(3, len(sketches)))
    for col, path in zip(thumbs, sketches):
        with col:
            try:
                st.image(str(path), caption=path.name, width="stretch")
            except Exception:  # noqa: BLE001
                st.caption(path.name)


def run() -> None:
    app_type = selected_type()
    if app_type is None:
        st.info("Create an app from the Library first.")
        if st.button("Go to Library", icon=":material/apps:", type="primary"):
            go("Library")
        return

    current = slug() or app_type.id
    dest = slug_dir(current)
    name_key = _sync_app_name(current, app_type.name)

    override = st.session_state.pop(ANSWERS_OVERRIDE_KEY, None)
    if override is not None:
        clear_form_widget_keys(current, app_type, key_ns=BRIEF_PAGE_NS)
        seed_form_widget_keys(override, app_type, key_ns=BRIEF_PAGE_NS, slug_name=current)
        values = dict(override)
        persist_brief(override)
    else:
        values = collect_form_answers(app_type, answers(), key_ns=BRIEF_PAGE_NS)
        set_answers(values)
        persist_brief()
    missing = answers_complete(app_type, values)
    _render_actions(app_type, current, missing)

    with st.container(border=True):
        ident, allows, will_not = st.columns([1.2, 1, 1], gap="medium")
        with ident:
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(f"**{app_type.name}**")
                st.badge(app_type.grounding_label)
                if not app_type.needs_snowflake:
                    st.badge("No Snowflake", color="green")
                elif app_type.demo_fixture:
                    st.badge("Demo pack", color="blue")
            st.caption("For " + ", ".join(app_type.users))
            st.write(app_type.brief_context)
        with allows:
            _bullet_list("Allows", app_type.enables)
        with will_not:
            _bullet_list("Will not", app_type.does_not)

    grounding_qs, found_qs, asked_qs = partition_questions(app_type.questions)

    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("**App name**")
            st.caption("Display name for this app. The folder on disk stays the same.")
            st.text_input("App name", key=name_key, label_visibility="collapsed")
        with st.container(border=True):
            st.markdown("**Your brief**")
            st.caption("What you want, what you do not want, who uses this.")
            values[USER_BRIEF_KEY] = render_user_brief(values, key_ns=BRIEF_PAGE_NS)
        with st.container(border=True):
            _render_sketches(current, dest)

    with right:
        with st.container(border=True):
            st.markdown("**Questions**")
            st.caption("What this type needs before we can build.")
            if not app_type.questions:
                st.caption("This type has no questions.")
            for question in grounding_qs:
                values[question.id] = render_question(
                    question, values, app_type, None, key_ns=BRIEF_PAGE_NS
                )

            profile: DataProfile | None = None
            grounding = ""
            for question in grounding_qs:
                if question.kind == "semantic_view":
                    grounding = str(values.get(question.id) or "")
                    profile = _ensure_profile(current, grounding)
                    break

            has_profile = bool(profile and profile.columns)
            named_view = bool(grounding) and not grounding.startswith("DEMO:")
            if found_qs or has_profile or named_view:
                _render_findings(profile, grounding=grounding)
                for question in found_qs:
                    values[question.id] = render_question(
                        question, values, app_type, profile, key_ns=BRIEF_PAGE_NS
                    )
            for question in asked_qs:
                values[question.id] = render_question(
                    question, values, app_type, profile, key_ns=BRIEF_PAGE_NS
                )

    if override is not None:
        persist_brief(override)
    else:
        set_answers(values)
        persist_brief()
    after = answers_complete(app_type, values)
    if after != missing:
        st.rerun()


run()
