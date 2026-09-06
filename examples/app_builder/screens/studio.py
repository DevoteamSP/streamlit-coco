"""Studio — summary, regenerate, then Copilot | Preview in the chrome."""

from __future__ import annotations

import streamlit as st
from engine.actions import missing_required, start_coco_build, start_demo_scaffold
from engine.brief import app_exists
from engine.jobs import set_copilot_open, set_preview_open
from engine.state import answers, app_name, go, selected_type, slug


def run() -> None:
    app_type = selected_type()
    current = slug()
    if app_type is None or not current:
        st.info("Create an app from the Library and fill its brief first.")
        if st.button("Go to Library", icon=":material/apps:"):
            go("Library")
        return

    title = app_name() or app_type.name
    st.markdown(
        f"**{title}** · {app_type.material_icon} {app_type.name} · `{current}`"
    )
    missing = missing_required()
    if missing:
        by_id = {q.id: q.prompt.rstrip(" ?") for q in app_type.questions}
        labels = ", ".join(by_id.get(mid, mid) for mid in missing)
        st.warning(f"Brief is incomplete: {labels}")
        if st.button("Back to brief", icon=":material/edit_note:"):
            go("Brief")
        return

    vals = answers()
    chips = [f"`{key}` {vals[key]}" for key in list(vals)[:4] if vals.get(key)]
    if chips:
        st.caption(" · ".join(str(c) for c in chips))

    exists = app_exists(current)
    st.caption(
        "Ready to preview" if exists else "Not written yet — build from the brief, or Open Copilot."
    )

    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button(
            "Build this app" if not exists else "Regenerate with CoCo",
            type="primary",
            icon=":material/psychology:",
            key="ab_studio_coco",
        ):
            start_coco_build(regenerate=exists)
        if app_type.demo_fixture and st.button(
            "Try a local demo",
            icon=":material/handyman:",
            key="ab_studio_demo",
        ):
            start_demo_scaffold()
        if st.button("Edit brief", icon=":material/edit_note:", key="ab_studio_brief"):
            go("Brief")
        if st.button("Open Copilot", icon=":material/psychology:", key="ab_studio_copilot"):
            set_copilot_open(True)
            st.rerun()
        if exists and st.button("Open Preview", icon=":material/preview:", key="ab_studio_preview"):
            set_preview_open(True)
            st.rerun()


run()
