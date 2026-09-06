"""Preview column for the generated App Builder child app."""

from __future__ import annotations

import streamlit as st

from engine.brief import APP_FILE, app_exists, slug_dir
from engine.jobs import (
    is_connected,
    is_copilot_open,
    preview_port,
    queue_fix,
    set_copilot_open,
    set_preview_full,
    set_preview_open,
)
from engine.state import slug
from streamlit_coco.app_preview import preview_running, start_app_preview
from streamlit_coco.viewer import app_viewer


def render_preview_rail() -> None:
    current = slug()
    dest = slug_dir(current) if current else None
    if dest is None:
        st.caption("Pick a type and build an app to preview it.")
        return

    iframe_h = 860 if st.session_state.get("ab_preview_full") else 520
    if is_copilot_open():
        iframe_h = 480

    script = dest / APP_FILE
    if (
        st.session_state.get("ab_preview_auto_run")
        and script.is_file()
        and not preview_running(dest)
    ):
        st.session_state["ab_preview_auto_run"] = False
        try:
            started = start_app_preview(
                dest,
                port=preview_port(),
                env={"APPB_DATA_MODE": "disconnected"},
            )
            st.toast(f"Preview · {started}")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
    elif st.session_state.get("ab_preview_auto_run") and preview_running(dest):
        st.session_state["ab_preview_auto_run"] = False

    def _on_fix(trace: str) -> None:
        set_copilot_open(True)
        set_preview_open(True)
        if not is_connected():
            st.session_state["ab_coco_connect_hint"] = True
            st.rerun()
        queue_fix(trace, dest)
        st.toast("Queued · fix the preview")

    def _title_extra() -> None:
        if "ab_preview_full_pill" not in st.session_state:
            st.session_state["ab_preview_full_pill"] = (
                ["full"] if st.session_state.get("ab_preview_full") else []
            )
        picked = st.pills(
            "Width",
            ["full"],
            format_func=lambda _: "Full width",
            selection_mode="multi",
            key="ab_preview_full_pill",
            label_visibility="collapsed",
        )
        full = "full" in (picked or [])
        if full != bool(st.session_state.get("ab_preview_full")):
            set_preview_full(full)
            st.rerun()

    app_viewer(
        dest,
        key="ab_app_viewer",
        port=preview_port(),
        env={"APPB_DATA_MODE": "disconnected"},
        iframe_height=iframe_h,
        on_fix=_on_fix,
        on_close=lambda: set_preview_open(False),
        title_extra=_title_extra,
    )
    if not app_exists(current):
        st.caption(f"No `{APP_FILE}` yet — Build from the brief, then Run.")
