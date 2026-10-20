"""render_output_field takes the window's handle and draws its latest answer."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest


def _page() -> None:
    import streamlit as st

    import streamlit_coco as st_coco
    from streamlit_coco.display import render_output_field

    coco = st_coco.ask_coco(".")
    coco.conversation.items.append({"kind": "answer", "id": "a1", "text": "Hello **there**"})
    render_output_field(coco, label="Output", text_renderer=lambda text: st.text(text.upper()))


def test_render_output_field_shows_latest_answer(monkeypatch) -> None:
    from streamlit_coco import window

    # each AppTest has its own component registry; a cached mount belongs to one
    window._component.cache_clear()
    monkeypatch.setenv("STREAMLIT_COCO_AGENT", "mock")
    app = AppTest.from_function(_page, default_timeout=30).run()
    assert not app.exception
    assert [t.value for t in app.subheader] == ["Output"]
    assert "HELLO **THERE**" in [t.value for t in app.text]
