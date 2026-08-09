"""Right-rail Copilot (streamlit-coco) — not a separate navigation page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from utils.paths import APP_ROOT
from utils.skills import SKILLS, skill_by_name, skill_prompt
from utils.snowflake_connections import (
    default_connection_name,
    list_connection_sources,
    list_connections,
)
from utils.ui import get_backlog

SESSION_KEY = "backlog_desk_coco"
GATE_KEY = "backlog_desk_coco_connected"
CONN_KEY = "backlog_desk_coco_connection"
SOURCE_KEY = "backlog_desk_coco_source"
OPEN_KEY = "copilot_open"


def is_copilot_open() -> bool:
    return bool(st.session_state.get(OPEN_KEY))


def set_copilot_open(open_: bool) -> None:
    st.session_state[OPEN_KEY] = open_


def toggle_copilot() -> None:
    set_copilot_open(not is_copilot_open())


def _coco_options(connection: str) -> Any:
    import streamlit_coco as st_coco

    return st_coco.CocoOptions(
        connection=connection,
        cwd=str(APP_ROOT),
        allowed_tools=["Read", "Glob", "Grep", "Edit", "Write"],
        require_approval_for=["Edit", "Write"],
    )


def _render_connection_popover() -> None:
    """Snowflake / CoCo connection controls next to Close (not in the sidebar)."""
    try:
        import streamlit_coco as st_coco
    except ImportError:
        st.caption("Install streamlit-coco")
        return

    connected = bool(st.session_state.get(GATE_KEY))
    active = st.session_state.get(CONN_KEY)
    label = f"Connected · {active}" if connected and active else "Connection"
    icon = ":material/cloud_done:" if connected else ":material/link:"

    with st.popover(label, icon=icon, help="CoCo CLI auth (no SQL)"):
        st.caption("Auth for CoCo CLI only — backlog data is local JSON/Markdown.")
        sources = list_connection_sources()
        if not sources:
            st.warning("No `~/.snowflake/*.toml` found.")
            return

        if len(sources) > 1:
            source_labels = [s.label for s in sources]
            default_source = st.session_state.get(SOURCE_KEY, source_labels[0])
            if default_source not in source_labels:
                default_source = source_labels[0]
            chosen_label = st.segmented_control(
                "Config file",
                options=source_labels,
                default=default_source,
                key="bd_config_source",
            )
            source = next(s for s in sources if s.label == chosen_label)
        else:
            source = sources[0]
            st.caption(f"`~/.snowflake/{source.label}`")

        st.session_state[SOURCE_KEY] = source.label
        conn_names = list_connections(source)
        if not conn_names:
            st.warning(f"No connections in `{source.label}`.")
            return

        preferred = st.session_state.get(CONN_KEY) or default_connection_name(source)
        if preferred not in conn_names:
            preferred = conn_names[0]

        connection = st.selectbox(
            "Connection",
            conn_names,
            index=conn_names.index(preferred),
            key="bd_connection_select",
        )
        st.caption(f"cwd: `{APP_ROOT.name}`")

        env = st_coco.check_environment(connection=connection)
        if env.sdk_installed:
            st.badge(f"SDK {env.sdk_version or 'ok'}", color="green", icon=":material/check:")
        else:
            st.badge("SDK missing", color="red", icon=":material/error:")
        if env.cli_ok:
            st.badge(f"CLI {env.cli_version}", color="green", icon=":material/check:")
        else:
            st.badge("CLI missing", color="red", icon=":material/error:")

        needs_reconnect = connected and active != connection
        if not connected or needs_reconnect:
            disabled = not env.ready
            btn_label = "Reconnect" if needs_reconnect else "Connect"
            if st.button(
                btn_label,
                type="primary",
                icon=":material/link:",
                disabled=disabled,
                width="stretch",
                key="bd_connect",
            ):
                opts = _coco_options(connection)
                st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
                session = st_coco.CocoSession(options=opts, key=SESSION_KEY)
                session.start()
                st.session_state[SESSION_KEY] = session
                st.session_state[GATE_KEY] = True
                st.session_state[CONN_KEY] = connection
                set_copilot_open(True)
                st.rerun()
            if disabled:
                st.caption("Fix SDK / CLI before connecting.")
        else:
            st.badge(f"Connected · {active}", color="green", icon=":material/cloud_done:")
            if st.button(
                "Disconnect",
                icon=":material/link_off:",
                width="stretch",
                key="bd_disc",
            ):
                st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
                st.session_state.pop(CONN_KEY, None)
                st.rerun()


def render_copilot_rail() -> None:
    """Skills + transcript for the right column."""
    try:
        import streamlit_coco as st_coco
    except ImportError:
        st.info("Copilot needs **streamlit-coco** (`make install`).", icon=":material/info:")
        return

    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown("### :material/psychology: Copilot")
        _render_connection_popover()
        if st.button("Close", icon=":material/close:", key="bd_close_copilot"):
            set_copilot_open(False)
            st.rerun()

    if not st.session_state.get(GATE_KEY):
        st.info(
            "Open **Connection** (next to Close), pick a Snowflake profile, then **Connect**.",
            icon=":material/info:",
        )
        return

    connection = st.session_state.get(CONN_KEY)
    if not connection:
        st.warning("No active connection — use the Connection popover.")
        return

    opts = _coco_options(str(connection))
    session = st_coco.get_or_create_session(opts, key=SESSION_KEY)

    backlog = get_backlog()
    ticket_ids = [t.id for t in backlog.tickets]
    epic_ids = [e.id for e in backlog.epics]
    release_versions = [r.version for r in backlog.releases]

    skill_names = [s.name for s in SKILLS]
    skill_labels = {s.name: s.label for s in SKILLS}
    pending_skill = st.session_state.pop("pending_skill", None)
    if pending_skill in skill_names:
        st.session_state["bd_skill_pills"] = pending_skill
    default_skill = (
        pending_skill
        if pending_skill in skill_names
        else (st.session_state.get("bd_skill_pills") or skill_names[0])
    )
    if default_skill not in skill_names:
        default_skill = skill_names[0]

    selected_skill = st.pills(
        "Skill",
        options=skill_names,
        format_func=lambda n: skill_labels.get(n, n),
        selection_mode="single",
        default=default_skill,
        key="bd_skill_pills",
    )

    focus_ticket = st.session_state.get("selected_ticket")
    if focus_ticket not in ticket_ids and ticket_ids:
        focus_ticket = ticket_ids[0]
    ticket_options = ["(none)", *ticket_ids]

    epic_default = st.session_state.get("selected_epic")
    if epic_default not in epic_ids and epic_ids:
        epic_default = epic_ids[0]
    epic_options = ["(none)", *epic_ids]

    rel_default = st.session_state.get("selected_release")
    if rel_default not in release_versions and release_versions:
        rel_default = release_versions[0]
    rel_options = ["(none)", *release_versions]

    c_ticket, c_epic, c_release = st.columns(3)
    with c_ticket:
        ticket_id = st.selectbox(
            "Ticket",
            options=ticket_options,
            index=ticket_options.index(focus_ticket) if focus_ticket in ticket_ids else 0,
            key="bd_skill_ticket",
        )
    with c_epic:
        epic_id = st.selectbox(
            "Epic",
            options=epic_options,
            index=epic_options.index(epic_default) if epic_default in epic_ids else 0,
            key="bd_skill_epic",
        )
    with c_release:
        release = st.selectbox(
            "Release",
            options=rel_options,
            index=rel_options.index(rel_default) if rel_default in release_versions else 0,
            key="bd_skill_release",
        )

    skill = skill_by_name(selected_skill) if selected_skill else None
    prompt = ""
    if skill:
        st.caption(skill.description)
        prompt = skill_prompt(
            skill,
            ticket_id=None if ticket_id == "(none)" else ticket_id,
            epic_id=None if epic_id == "(none)" else epic_id,
            release=None if release == "(none)" else release,
        )
        with st.expander("Prompt preview", expanded=False):
            st.code(prompt, language=None)

    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption(f"Status · `{session.status.value}`")
        run = st.button(
            "Run skill",
            type="primary",
            icon=":material/play_arrow:",
            key="bd_run_skill",
            disabled=not skill,
        )
        if st.button("Clear", icon=":material/delete:", key="bd_coco_clear"):
            st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
            st.toast("Chat cleared")
            st.rerun()

    auto_run = bool(st.session_state.pop("auto_run_skill", False))
    if skill and prompt and (run or auto_run):
        if ticket_id != "(none)":
            st.session_state["selected_ticket"] = ticket_id
        if epic_id != "(none)":
            st.session_state["selected_epic"] = epic_id
        if release != "(none)":
            st.session_state["selected_release"] = release
        session.send(prompt)
        if not auto_run:
            st.toast(f"Queued `{skill.label}`")
        else:
            st.toast(f"Running `{skill.label}`")

    st_coco.panel(session=session, warm_up=True, show_status=True, run_every=0.25)
    st_coco.chat_input_bar(
        session,
        placeholder="Ask about tickets, epics, or release notes…",
        key="bd_chat_input",
    )
