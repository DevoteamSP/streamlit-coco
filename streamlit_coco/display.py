"""``render_output_field``: the window's latest answer, shown in the page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_coco.text_renderer import TextRenderer, resolve_text_renderer


def _latest(coco: Any) -> str:
    conv = coco.conversation
    kept, conv.restore = conv.restore, None  # view() hands `restore` over once: not ours to take
    try:
        return coco.latest_answer
    finally:
        conv.restore = kept if conv.restore is None else conv.restore


def render_output_field(
    coco: Any,
    container: Any | None = None,
    *,
    label: str = "CoCo output",
    text_renderer: TextRenderer = None,
) -> None:
    """Show the latest answer of the window `coco` (``ask_coco`` / ``get_window``) in the page,
    drawn by `text_renderer` (default ``st.markdown``). It refreshes by itself while CoCo works."""
    render = resolve_text_renderer(text_renderer)
    busy = coco.conversation.busy

    @st.fragment(run_every=0.5 if busy else None)
    def _field() -> None:
        text = _latest(coco)
        with container if container is not None else st.container():
            st.subheader(label)
            if text:
                render(text)
            else:
                st.caption("The latest answer shows here." if not busy else "CoCo is working…")
        if busy and not coco.conversation.busy:
            st.rerun()  # leave the polling fragment once CoCo is done

    _field()
