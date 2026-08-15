"""Generic Streamlit app viewer column — child process, iframe, Fix with CoCo.

App-agnostic: callers own layout, Copilot session, and job queue. This module
renders chrome + iframe and calls ``on_fix(traceback)`` when asked.

Lives in ``viewer.py`` (not ``app_viewer.py``) so the lazy export
``st_coco.app_viewer`` is not shadowed by the submodule after import.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

import streamlit as st

from streamlit_coco.app_preview import (
    last_preview_exception,
    preview_log_tail,
    preview_running,
    preview_url,
    start_app_preview,
    stop_app_preview,
)


def app_viewer(
    app_dir: str | Path,
    *,
    key: str = "coco_app_viewer",
    port: int | None = None,
    address: str = "127.0.0.1",
    env: Mapping[str, str] | None = None,
    iframe_height: int = 520,
    show_fix: bool = True,
    on_fix: Callable[[str], None] | None = None,
    on_close: Callable[[], None] | None = None,
    title_extra: Callable[[], None] | None = None,
    title: str = "Preview",
    script_name: str = "streamlit_app.py",
) -> None:
    """Render a preview column: Run / Stop / Open / Fix, then an iframe.

    ``app_dir`` must contain ``script_name`` (default ``streamlit_app.py``).
    Do not point this at the host app. The child is another origin — Fix
    scrapes ``.preview.log``, it cannot read the iframe DOM.
    """
    dest = Path(app_dir)
    exists = (dest / script_name).is_file()
    running = preview_running(dest)
    url = preview_url(dest, address=address) if running else None
    err = last_preview_exception(dest) if running else None

    top = st.container(horizontal=True, vertical_alignment="center")
    with top:
        st.subheader(title)
        st.space("stretch")
        if title_extra is not None:
            title_extra()
        if on_close is not None and st.button(
            "Close",
            key=f"{key}_close",
            icon=":material/close:",
        ):
            on_close()
            st.rerun()

    with st.container(horizontal=True):
        if st.button(
            "Run",
            icon=":material/play_arrow:",
            key=f"{key}_start",
            disabled=not exists,
        ):
            try:
                started = start_app_preview(
                    dest,
                    port=port,
                    address=address,
                    env=dict(env) if env else None,
                    script_name=script_name,
                )
                st.toast(f"Preview · {started}")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
        if st.button(
            "Stop",
            icon=":material/stop:",
            key=f"{key}_stop",
            disabled=not running,
        ):
            stop_app_preview(dest)
            st.rerun()
        if running and url:
            st.link_button("Open", url, icon=":material/open_in_new:", type="primary")
        if show_fix:
            if st.button(
                "Fix with CoCo",
                icon=":material/build:",
                type="primary" if err else "secondary",
                key=f"{key}_fix",
                disabled=not exists,
            ):
                if on_fix is None:
                    st.toast("Wire on_fix= to queue a CoCo job.")
                else:
                    on_fix(_fix_payload(dest, err))
                    st.rerun()

    if running and url:
        st.caption(f"Running · {url} · `{dest.name}`")
        if err:
            with st.expander("Preview exception", expanded=True):
                st.code(err, language="text")
        st.iframe(url, height=iframe_height)
        return
    if exists:
        st.caption(f"On disk · `{dest}`")
        return
    st.caption(f"No `{script_name}` in `{dest}`.")


def _fix_payload(dest: Path, err: str | None) -> str:
    """Traceback or log tail for ``on_fix``. Host wraps with ``default_fix_prompt``."""
    return err or preview_log_tail(dest, n=40)


def collect_fix_text(app_dir: str | Path) -> str:
    """Traceback or log tail — same payload **Fix with CoCo** sends to ``on_fix``."""
    dest = Path(app_dir)
    err = last_preview_exception(dest)
    return _fix_payload(dest, err)
