"""Right-rail preview of the generated Streamlit consumer app."""

from __future__ import annotations

import streamlit as st

from engine.coco_jobs import PREVIEW_FULL_KEY, set_preview_full, set_preview_open
from engine.paths import OUT_DIR
from engine.preview_server import (
    DEFAULT_PORT,
    preview_running,
    preview_url,
    start_preview,
    stop_preview,
)
from engine.streamlit_app_gen import (
    APP_DIRNAME_COCO,
    app_dir,
    generated_app_exists,
    list_generated_files,
    load_app_spec,
    render_inline_preview,
)

PREVIEW_VARIANT_KEY = "tts_preview_variant"
LAUNCH_KEY = "tts_launch_pills"
BUILD_MODE_KEY = "tts_build_mode"
BUILD_MODE_STORE = "tts_build_mode__persist"


def _store_key(base: str) -> str:
    return f"{base}__persist"


def _seed(base: str, default):
    store = _store_key(base)
    st.session_state.setdefault(store, default)
    if base not in st.session_state:
        st.session_state[base] = st.session_state[store]
    return base


def _variant_from_build_mode() -> str:
    mode = st.session_state.get(BUILD_MODE_KEY)
    if mode not in {"python", "coco"}:
        mode = st.session_state.get(BUILD_MODE_STORE)
    if mode not in {"python", "coco"}:
        for key in ("tts_build_mode__rail", "tts_build_mode__full"):
            val = st.session_state.get(key)
            if val in {"python", "coco"}:
                mode = val
                break
    variant = "coco" if mode == "coco" else "deterministic"
    st.session_state[PREVIEW_VARIANT_KEY] = variant
    return variant


def render_preview_rail() -> None:
    top = st.container(horizontal=True, vertical_alignment="center")
    with top:
        st.subheader("Preview")
        if "tts_preview_full_pill" not in st.session_state:
            st.session_state["tts_preview_full_pill"] = (
                ["full"] if st.session_state.get(PREVIEW_FULL_KEY) else []
            )
        picked = st.pills(
            "Width",
            ["full"],
            format_func=lambda _: "Full width",
            selection_mode="multi",
            key="tts_preview_full_pill",
            label_visibility="collapsed",
        )
        full = "full" in (picked or [])
        if full != bool(st.session_state.get(PREVIEW_FULL_KEY)):
            set_preview_full(full)
            st.rerun()
        if st.button("Close", key="tts_preview_close", icon=":material/close:"):
            set_preview_open(False)
            st.rerun()

    variant = _variant_from_build_mode()
    dest = app_dir(OUT_DIR, variant=variant)
    exists = generated_app_exists(OUT_DIR, variant=variant)
    running = preview_running()

    launch_key = _seed(LAUNCH_KEY, "disconnected")
    launch_mode = st.pills(
        "Mode",
        ["disconnected", "live"],
        format_func=lambda m: "Disconnected" if m == "disconnected" else "Live",
        key=launch_key,
        persist_state="session",
    )
    if launch_mode:
        st.session_state[_store_key(LAUNCH_KEY)] = launch_mode

    with st.container(horizontal=True):
        if st.button(
            "Run",
            icon=":material/play_arrow:",
            key="tts_preview_start",
            disabled=not exists,
        ):
            try:
                url = start_preview(dest, port=DEFAULT_PORT, mode=launch_mode or "disconnected")
                st.toast(f"Preview · {url}")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
        if st.button(
            "Stop",
            icon=":material/stop:",
            key="tts_preview_stop",
            disabled=not running,
        ):
            stop_preview(dest)
            st.rerun()
        url = preview_url()
        if running and url:
            st.link_button("Open", url, icon=":material/open_in_new:", type="primary")

    if running:
        st.caption(f"Running · {preview_url()} · `{dest.name}`")
        iframe_h = 860 if st.session_state.get(PREVIEW_FULL_KEY) else 720
        st.iframe(preview_url() or "", height=iframe_h)
        return
    if exists:
        st.caption(f"On disk · `{dest}`")
    else:
        st.caption("Build with python or generate with CoCo, then run.")
        return

    spec = load_app_spec(OUT_DIR, variant=variant)
    if variant == "coco":
        written = list_generated_files(dest)
        if written:
            st.caption(f"CoCo wrote `{APP_DIRNAME_COCO}/`")
            st.code("\n".join(written), language="text")
        else:
            st.caption("Run the CoCo app to preview its UI.")
        return

    if spec:
        render_inline_preview(spec, mode=launch_mode or "disconnected")
