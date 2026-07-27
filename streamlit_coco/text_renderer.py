"""Pluggable Streamlit text rendering for assistant / user content."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

TextRenderer = str | Callable[[str], Any] | None

_NAMED_RENDERERS: dict[str, Callable[[str], Any]] = {
    "markdown": st.markdown,
    "write": st.write,
    "text": st.text,
    "caption": st.caption,
    "code": st.code,
}


def resolve_text_renderer(text_renderer: TextRenderer = None) -> Callable[[str], Any]:
    """Resolve a named Streamlit API, callable, or default ``st.markdown``."""
    if text_renderer is None:
        return st.markdown
    if isinstance(text_renderer, str):
        key = text_renderer.strip().lower()
        if key.startswith("st."):
            key = key[3:]
        try:
            return _NAMED_RENDERERS[key]
        except KeyError as exc:
            known = ", ".join(sorted(_NAMED_RENDERERS))
            raise ValueError(
                f"Unknown text_renderer={text_renderer!r}. Use one of: {known}, or a callable."
            ) from exc
    if callable(text_renderer):
        return text_renderer
    raise TypeError(
        f"text_renderer must be a str name, callable, or None; got {type(text_renderer).__name__}"
    )
