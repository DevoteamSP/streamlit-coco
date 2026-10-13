"""``render_output_field``: the window's latest answer, shown in the page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_coco.text_renderer import TextRenderer, resolve_text_renderer


def render_output_field(
    coco: Any,
    container: Any | None = None,
    *,
    label: str = "CoCo output",
    text_renderer: TextRenderer = None,
) -> None:
    """Show the latest answer of the window `coco` (``ask_coco`` / ``get_window``) in the page,
    drawn by `text_renderer` (default ``st.markdown``). It looks again every second."""
    render = resolve_text_renderer(text_renderer)

    # The window is its own fragment, so the page does not rerun while CoCo answers: this one
    # looks again every second (ponytail: a fixed poll; a quiet window costs one cheap rerun).
    @st.fragment(run_every=1.0)
    def _field() -> None:
        text = coco.latest_answer
        with container if container is not None else st.container():
            st.subheader(label)
            if text:
                render(text)
            else:
                st.caption("The latest answer shows here.")

    _field()
