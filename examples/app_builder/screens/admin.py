"""Admin — view, add, edit, and delete app types."""

from __future__ import annotations

from typing import Any

import streamlit as st
from engine.catalog import (
    GROUNDING_KINDS,
    AppType,
    delete_type,
    load_catalog,
    load_type_raw,
    new_type_template,
    save_type_raw,
)
from engine.paths import APP_ROOT
from engine.skills import (
    SHARED_SKILL_ID,
    read_skill_md,
    skill_md_path,
    write_skill_md,
)
from streamlit_extras.resizable_columns import resizable_columns

_NEW = "— New type —"
_PICK = "ab_admin_pick"
_Q_KINDS = ("text", "list", "enum", "semantic_view", "tables")
_MATERIAL_ICONS = (
    "apps",
    "speed",
    "table_chart",
    "verified",
    "record_voice_over",
    "edit_note",
    "menu_book",
    "dashboard",
    "analytics",
    "insights",
    "monitoring",
    "query_stats",
    "stacked_bar_chart",
    "pie_chart",
    "scatter_plot",
    "show_chart",
    "bar_chart",
    "description",
    "article",
    "folder",
    "upload_file",
    "download",
    "cloud",
    "database",
    "storage",
    "view_list",
    "checklist",
    "fact_check",
    "chat",
    "forum",
    "call",
    "transcribe",
    "mic",
    "headset_mic",
    "calendar_month",
    "event",
    "schedule",
    "task",
    "assignment",
    "group",
    "person",
    "support_agent",
    "handshake",
    "lock",
    "security",
    "policy",
    "language",
    "public",
    "link",
    "travel_explore",
    "image",
    "photo_library",
    "slideshow",
    "web",
    "code",
    "terminal",
    "bug_report",
    "psychology",
    "smart_toy",
    "lightbulb",
    "school",
    "auto_stories",
    "library_books",
    "mail",
    "inbox",
    "notifications",
    "campaign",
    "payments",
    "account_balance",
    "trending_up",
    "savings",
    "map",
    "location_on",
    "home",
    "storefront",
    "settings",
    "tune",
    "build",
    "favorite",
    "star",
    "bookmark",
    "label",
    "category",
    "newspaper",
    "history",
    "timeline",
    "science",
    "biotech",
    "bolt",
    "eco",
    "water_drop",
)


def _lines(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _field_key(pick: str, name: str) -> str:
    return f"ab_admin_{pick}_{name}"


def _normalize_icon(value: str) -> str:
    name = value.strip().strip(":")
    if name.startswith("material/"):
        name = name.split("/", 1)[1]
    return name.replace(" ", "_") or "apps"


def _icon_key(pick: str) -> str:
    return f"ab_admin_icon_{pick}"


def _load_icon(pick: str, fallback: str) -> str:
    key = _icon_key(pick)
    if key not in st.session_state:
        st.session_state[key] = _normalize_icon(fallback)
    return str(st.session_state[key])


def _set_icon(pick: str, name: str) -> None:
    st.session_state[_icon_key(pick)] = _normalize_icon(name)


def _render_icon_picker(pick: str, fallback: str) -> str:
    current = _load_icon(pick, fallback)
    st.markdown("Icon")
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f"### :material/{current}:")
        st.caption(f"`{current}`")
        with st.popover("Choose icon", icon=f":material/{current}:"):
            query = str(
                st.text_input(
                    "Search",
                    key=f"ab_icon_q_{pick}",
                    placeholder="voice, chart, book…",
                )
                or ""
            ).strip().lower()
            typed_key = f"ab_icon_typed_{pick}"
            if typed_key not in st.session_state:
                st.session_state[typed_key] = current
            typed = st.text_input("Or type a Material name", key=typed_key)
            if st.button(
                "Use this name",
                icon=":material/check:",
                key=f"ab_icon_use_{pick}",
            ):
                _set_icon(pick, str(typed or current))
                st.rerun()
            names = [
                name
                for name in _MATERIAL_ICONS
                if not query or query in name or query in name.replace("_", " ")
            ]
            if query:
                extra = _normalize_icon(query)
                if extra not in names:
                    names = [extra, *names]
            if not names:
                st.caption("No match. Type a Material name above.")
            else:
                with st.container(height=280):
                    for start in range(0, min(len(names), 48), 4):
                        cols = st.columns(4)
                        for col, name in zip(
                            cols, names[start : start + 4], strict=False
                        ):
                            with col:
                                if st.button(
                                    f":material/{name}:",
                                    help=name,
                                    width="stretch",
                                    key=f"ab_icon_btn_{pick}_{name}",
                                ):
                                    _set_icon(pick, name)
                                    st.rerun()
    return current


def _q_store_key(pick: str) -> str:
    return f"ab_admin_qs_{pick}"


def _load_questions(pick: str, fallback: list[Any]) -> list[dict[str, Any]]:
    key = _q_store_key(pick)
    if key not in st.session_state:
        st.session_state[key] = [dict(item) for item in fallback if isinstance(item, dict)]
    return list(st.session_state[key])


def _store_questions(pick: str, questions: list[dict[str, Any]]) -> None:
    st.session_state[_q_store_key(pick)] = questions


def _question_from_fields(
    qid: str,
    prompt: str,
    kind: str,
    required: bool,
    options: str,
    help_text: str,
    infer: str,
) -> dict[str, Any]:
    qid = qid.strip()
    prompt = prompt.strip()
    if not qid or not prompt:
        raise ValueError("Each question needs an id and a prompt.")
    payload: dict[str, Any] = {
        "id": qid,
        "prompt": prompt,
        "kind": kind,
        "required": bool(required),
    }
    opts = _split_lines(options)
    if opts:
        payload["options"] = opts
    if help_text.strip():
        payload["help"] = help_text.strip()
    if infer.strip():
        payload["infer"] = infer.strip()
    return payload


def _persist_questions(pick: str, questions: list[dict[str, Any]]) -> None:
    if pick == _NEW:
        return
    raw = load_type_raw(pick)
    brief = dict(raw.get("brief") or {})
    brief["questions"] = questions
    raw["brief"] = brief
    save_type_raw(raw, previous_id=pick)


def _q_edit_key(pick: str) -> str:
    return f"ab_admin_q_edit_{pick}"


def _q_editing(pick: str) -> str | int | None:
    value = st.session_state.get(_q_edit_key(pick))
    if value == "add" or isinstance(value, int):
        return value
    return None


def _set_q_editing(pick: str, value: str | int | None) -> None:
    st.session_state[_q_edit_key(pick)] = value


def _question_fields(
    pick: str,
    suffix: str,
    question: dict[str, Any],
    *,
    disabled: bool = False,
) -> tuple[Any, ...]:
    kind = str(question.get("kind") or "text")
    kind_index = _Q_KINDS.index(kind) if kind in _Q_KINDS else 0
    id_col, kind_col, req_col = st.columns(3)
    with id_col:
        qid = st.text_input(
            "Id",
            value=str(question.get("id") or ""),
            disabled=disabled,
            key=f"{pick}_{suffix}_id",
        )
    with kind_col:
        kind_val = st.selectbox(
            "Kind",
            list(_Q_KINDS),
            index=kind_index,
            disabled=disabled,
            key=f"{pick}_{suffix}_kind",
        )
    with req_col:
        required = st.toggle(
            "Required",
            value=bool(question.get("required")),
            disabled=disabled,
            key=f"{pick}_{suffix}_req",
        )
    prompt = st.text_input(
        "Prompt",
        value=str(question.get("prompt") or ""),
        disabled=disabled,
        key=f"{pick}_{suffix}_prompt",
    )
    opt_col, help_col, infer_col = st.columns(3)
    with opt_col:
        options = st.text_area(
            "Options (one per line, for enum)",
            value=_lines(question.get("options")),
            height=70,
            disabled=disabled,
            key=f"{pick}_{suffix}_opts",
        )
    with help_col:
        help_text = st.text_input(
            "Help",
            value=str(question.get("help") or ""),
            disabled=disabled,
            key=f"{pick}_{suffix}_help",
        )
    with infer_col:
        infer = st.text_input(
            "Infer (optional)",
            value=str(question.get("infer") or ""),
            disabled=disabled,
            key=f"{pick}_{suffix}_infer",
        )
    return (
        str(qid or ""),
        str(prompt or ""),
        str(kind_val or "text"),
        bool(required),
        str(options or ""),
        str(help_text or ""),
        str(infer or ""),
    )


def _submit_question_form(
    pick: str,
    questions: list[dict[str, Any]],
    raw: tuple[Any, ...],
    *,
    index: int | None,
    saved: bool,
    cancelled: bool,
) -> None:
    if cancelled:
        _set_q_editing(pick, None)
        st.rerun()
    if not saved:
        return
    try:
        draft = _question_from_fields(*raw)
        next_qs = list(questions)
        if index is None:
            next_qs.append(draft)
        else:
            next_qs[index] = draft
        _store_questions(pick, next_qs)
        _persist_questions(pick, next_qs)
        _set_q_editing(pick, None)
        st.toast(f"Saved `{draft['id']}`")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))


def _question_tab_labels(questions: list[dict[str, Any]]) -> list[str]:
    used: set[str] = set()
    labels: list[str] = []
    for index, question in enumerate(questions):
        qid = str(question.get("id") or "").strip() or f"q{index + 1}"
        label = qid
        n = 2
        while label in used:
            label = f"{qid}-{n}"
            n += 1
        used.add(label)
        labels.append(label)
    return labels


def _render_add_question(pick: str, questions: list[dict[str, Any]]) -> None:
    st.markdown("**New question**")
    with st.form(f"ab_q_add_{pick}"):
        raw = _question_fields(pick, "add", {"kind": "text", "required": True})
        with st.container(horizontal=True):
            saved = st.form_submit_button(
                "Save",
                type="primary",
                icon=":material/save:",
            )
            cancelled = st.form_submit_button(
                "Cancel",
                icon=":material/close:",
            )
    _submit_question_form(
        pick, questions, raw, index=None, saved=saved, cancelled=cancelled
    )


def _render_question_tab(
    pick: str,
    questions: list[dict[str, Any]],
    index: int,
    question: dict[str, Any],
    editing: str | int | None,
) -> None:
    if editing == index:
        with st.form(f"ab_q_form_{pick}_{index}"):
            raw = _question_fields(pick, f"e{index}", question)
            with st.container(horizontal=True):
                saved = st.form_submit_button(
                    "Save",
                    type="primary",
                    icon=":material/save:",
                )
                cancelled = st.form_submit_button(
                    "Cancel",
                    icon=":material/close:",
                )
        _submit_question_form(
            pick,
            questions,
            raw,
            index=index,
            saved=saved,
            cancelled=cancelled,
        )
        return
    _question_fields(pick, f"v{index}", question, disabled=True)
    with st.container(horizontal=True):
        if st.button(
            "Edit",
            icon=":material/edit:",
            key=f"ab_q_edit_{pick}_{index}",
        ):
            _set_q_editing(pick, index)
            st.rerun()
        if st.button(
            "Delete",
            icon=":material/delete:",
            key=f"ab_q_del_{pick}_{index}",
        ):
            next_qs = [item for i, item in enumerate(questions) if i != index]
            _store_questions(pick, next_qs)
            _persist_questions(pick, next_qs)
            if editing == index:
                _set_q_editing(pick, None)
            st.toast("Question deleted")
            st.rerun()


def _render_questions(pick: str, fallback: list[Any]) -> list[dict[str, Any]]:
    questions = _load_questions(pick, fallback)
    editing = _q_editing(pick)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown("**Questions**")
        if editing != "add":
            if st.button("Add question", icon=":material/add:", key=f"ab_q_add_btn_{pick}"):
                _set_q_editing(pick, "add")
                st.rerun()
    st.caption("These become Brief fields. Save writes this type’s `type.json`.")

    labels = _question_tab_labels(questions)
    if editing == "add":
        new_label = "New"
        tabs = st.tabs(
            [*labels, new_label],
            default=new_label,
            key=f"ab_admin_q_tabs_{pick}_add",
        )
        for index, (tab, question) in enumerate(
            zip(tabs[: len(questions)], questions, strict=True)
        ):
            with tab:
                _render_question_tab(pick, questions, index, question, editing)
        with tabs[-1]:
            _render_add_question(pick, questions)
        return questions

    if not questions:
        st.caption("No questions yet.")
        return questions

    default = (
        labels[editing]
        if isinstance(editing, int) and 0 <= editing < len(labels)
        else None
    )
    tabs = st.tabs(labels, default=default, key=f"ab_admin_q_tabs_{pick}")
    for index, (tab, question) in enumerate(zip(tabs, questions, strict=True)):
        with tab:
            _render_question_tab(pick, questions, index, question, editing)
    return questions


def _select(pick: str) -> None:
    st.session_state[_PICK] = pick
    st.rerun()


@st.dialog("Delete this type?")
def _confirm_delete(type_id: str) -> None:
    st.write(
        f"This removes `types/{type_id}/` from the example catalog. "
        "It cannot be undone."
    )
    if st.button("Delete type", type="primary", key="ab_admin_del_ok"):
        try:
            delete_type(type_id)
            st.session_state[_PICK] = _NEW
            st.toast(f"Deleted `{type_id}`")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def _new_card(*, selected: bool) -> None:
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown("**:material/add: New type**")
            if selected:
                st.badge("Editing", color="blue")
        st.caption("Create a catalog card. Save writes a new folder under `types/`.")
        if st.button(
            "Create",
            icon=":material/add:",
            type="primary" if selected else "secondary",
            width="stretch",
            key="ab_admin_new",
        ):
            _select(_NEW)


def _type_card(app: AppType, *, selected: bool) -> None:
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"**{app.material_icon} {app.name}**")
            st.badge(app.grounding_label)
            if selected:
                st.badge("Editing", color="blue")
        st.caption("For: " + (", ".join(app.users) or "—"))
        if app.topics:
            st.caption(" · ".join(app.topics))
        with st.container(horizontal=True, vertical_alignment="center"):
            if app.coming_soon:
                st.badge("Coming soon", color="gray")
            if not app.needs_snowflake:
                st.badge("No Snowflake", color="green")
            elif app.demo_fixture:
                st.badge("Demo pack", color="blue")
        with st.container(horizontal=True):
            if st.button(
                "Edit",
                icon=":material/edit:",
                type="primary" if selected else "secondary",
                width="stretch",
                key=f"ab_admin_edit_{app.id}",
            ):
                _select(app.id)
            if st.button(
                "Delete",
                icon=":material/delete:",
                width="stretch",
                key=f"ab_admin_del_{app.id}",
            ):
                _confirm_delete(app.id)


def _skill_area(skill_id: str, *, label: str, key: str, height: int = 280) -> str:
    path = skill_md_path(skill_id)
    if key not in st.session_state:
        st.session_state[key] = read_skill_md(skill_id)
    st.caption(f"`types/{skill_id}/SKILL.md`" + ("" if path.is_file() else " · new"))
    return str(
        st.text_area(
            label,
            height=height,
            key=key,
        )
        or ""
    )


def _save_skill(skill_id: str, body: str, *, widget_key: str) -> None:
    try:
        dest = write_skill_md(skill_id, body)
        st.session_state.pop(widget_key, None)
        st.toast(f"Saved `{dest.relative_to(APP_ROOT)}`")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))


def _render_skill_editors(pick: str, guidelines_skill: str) -> None:
    st.markdown("**Guidelines skills**")
    st.caption(
        "CoCo Reads these files on every Build. Shared applies to every type; "
        "the type skill adds layout and data rules."
    )
    shared_key = "ab_admin_skill_shared"
    shared_body = _skill_area(
        SHARED_SKILL_ID,
        label="Shared skill",
        key=shared_key,
    )
    if st.button(
        "Save shared skill",
        icon=":material/save:",
        key="ab_admin_skill_shared_save",
    ):
        _save_skill(SHARED_SKILL_ID, shared_body, widget_key=shared_key)

    type_id = "" if pick == _NEW else pick
    skill_id = (guidelines_skill or type_id).strip()
    if not skill_id:
        st.caption("Save the type first to edit its skill.")
        return
    type_key = f"ab_admin_skill_type_{skill_id}"
    type_body = _skill_area(
        skill_id,
        label="Type skill",
        key=type_key,
    )
    if st.button(
        "Save type skill",
        icon=":material/save:",
        key=f"ab_admin_skill_type_save_{skill_id}",
    ):
        _save_skill(skill_id, type_body, widget_key=type_key)


def _render_editor(pick: str, data: dict[str, Any], previous_id: str | None) -> None:
    brief = dict(data.get("brief") or {})
    kinds = list(GROUNDING_KINDS)
    kind = str(data.get("grounding_kind") or "tabular")
    kind_index = kinds.index(kind) if kind in kinds else 0
    questions = _load_questions(pick, list(brief.get("questions") or []))

    if pick == _NEW:
        st.info("Fill the id and name, then save. A new folder is created.")

    id_col, name_col, icon_col = st.columns(3)
    with id_col:
        type_id = st.text_input(
            "Id (folder name)",
            value=str(data.get("id") or ""),
            key=_field_key(pick, "id"),
        )
    with name_col:
        name = st.text_input(
            "Name",
            value=str(data.get("name") or ""),
            key=_field_key(pick, "name"),
        )
    with icon_col:
        icon = _render_icon_picker(pick, str(data.get("icon") or "apps"))

    with st.form("ab_admin_form"):
        ground_col, demo_col, skill_col = st.columns(3)
        with ground_col:
            grounding_kind = st.selectbox(
                "Grounding",
                kinds,
                index=kind_index,
                key=_field_key(pick, "grounding"),
            )
        with demo_col:
            demo_fixture = st.text_input(
                "Demo fixture",
                value=str(data.get("demo_fixture") or ""),
                key=_field_key(pick, "demo"),
            )
        with skill_col:
            guidelines_skill = st.text_input(
                "Guidelines skill folder",
                value=str(data.get("guidelines_skill") or ""),
                help=(
                    "Folder name under types/ (same as the type id). "
                    "Shared skill is always types/shared/."
                ),
                key=_field_key(pick, "skill"),
            )
        snow_col, soon_col, copilot_col = st.columns(3)
        with snow_col:
            needs_snowflake = st.toggle(
                "Needs Snowflake",
                value=bool(data.get("needs_snowflake")),
                key=_field_key(pick, "snow"),
            )
        with soon_col:
            coming_soon = st.toggle(
                "Coming soon",
                value=bool(data.get("coming_soon")),
                key=_field_key(pick, "soon"),
            )
        with copilot_col:
            ships_copilot = st.toggle(
                "Ships Copilot",
                value=bool(data.get("ships_copilot")),
                key=_field_key(pick, "copilot"),
            )
        user_col, topic_col, context_col = st.columns(3)
        with user_col:
            users = st.text_area(
                "Users (one per line)",
                value=_lines(data.get("users")),
                height=100,
                key=_field_key(pick, "users"),
            )
        with topic_col:
            topics = st.text_area(
                "Topics (one per line)",
                value=_lines(data.get("topics")),
                height=100,
                key=_field_key(pick, "topics"),
            )
        with context_col:
            context = st.text_area(
                "Context",
                value=str(brief.get("context") or ""),
                height=100,
                key=_field_key(pick, "context"),
            )
        allow_col, deny_col = st.columns(2)
        with allow_col:
            enables = st.text_area(
                "Allows (one per line)",
                value=_lines(brief.get("enables")),
                height=80,
                key=_field_key(pick, "enables"),
            )
        with deny_col:
            does_not = st.text_area(
                "Does not (one per line)",
                value=_lines(brief.get("does_not")),
                height=80,
                key=_field_key(pick, "does_not"),
            )
        saved = st.form_submit_button(
            "Save type",
            type="primary",
            icon=":material/save:",
        )

    _render_questions(pick, list(brief.get("questions") or []))
    _render_skill_editors(pick, str(data.get("guidelines_skill") or ""))

    if not saved:
        return
    try:
        payload = dict(data)
        payload.update(
            {
                "id": type_id.strip(),
                "name": name.strip() or type_id.strip(),
                "icon": icon.strip() or "apps",
                "users": _split_lines(users),
                "topics": _split_lines(topics),
                "grounding_kind": grounding_kind,
                "demo_fixture": demo_fixture.strip() or None,
                "guidelines_skill": guidelines_skill.strip() or None,
                "needs_snowflake": needs_snowflake,
                "coming_soon": coming_soon,
                "ships_copilot": ships_copilot,
                "brief": {
                    "context": context.strip(),
                    "enables": _split_lines(enables),
                    "does_not": _split_lines(does_not),
                    "questions": _load_questions(pick, questions),
                },
            }
        )
        save_type_raw(payload, previous_id=previous_id)
        st.session_state[_PICK] = payload["id"]
        if pick == _NEW:
            _store_questions(payload["id"], payload["brief"]["questions"])
        st.toast(f"Saved `{payload['id']}`")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))


def run() -> None:
    st.caption(
        "Cards on the left are the Library. Edit or delete on the card; "
        "the form on the right writes `types/<id>/type.json` and the "
        "guidelines skills CoCo Reads on Build."
    )

    types = load_catalog()
    ids = [item.id for item in types]
    if _PICK not in st.session_state:
        st.session_state[_PICK] = ids[0] if ids else _NEW
    pick = str(st.session_state[_PICK])
    if pick not in ids and pick != _NEW:
        pick = ids[0] if ids else _NEW
        st.session_state[_PICK] = pick

    left, right = resizable_columns(
        [1.15, 1.2],
        min_width=260,
        key="ab_admin_split",
    )
    with left:
        with st.container(border=True):
            st.markdown("**App types**")
            cards: list[AppType | None] = [None, *types]
            for start in range(0, len(cards), 2):
                col_a, col_b = st.columns(2)
                pair = cards[start : start + 2]
                for col, item in zip((col_a, col_b), pair, strict=False):
                    with col:
                        if item is None:
                            _new_card(selected=pick == _NEW)
                        else:
                            _type_card(item, selected=pick == item.id)

    with right:
        with st.container(border=True):
            if pick == _NEW:
                st.markdown("**New type**")
                data = new_type_template("new-type")
                previous_id = None
            else:
                data = load_type_raw(pick)
                previous_id = pick
                app = next((item for item in types if item.id == pick), None)
                if app:
                    st.markdown(f"**{app.material_icon} {app.name}** · `{app.id}`")
                else:
                    st.markdown(f"**Edit** · `{pick}`")
            _render_editor(pick, data, previous_id)


run()
