"""Debug-mode helpers for streamlit-coco UI."""

from __future__ import annotations

import os
from typing import Any


def is_debug_mode(*, session_state: Any | None = None) -> bool:
    """Return True when CoCo debug UI should show tool request payloads.

    Enabled when any of:
    - env ``STREAMLIT_COCO_DEBUG`` or ``COCO_DEBUG`` is a truthy value
      (``1``, ``true``, ``yes``, ``on``)
    - ``st.session_state["coco_debug"]`` is truthy (if ``session_state`` provided
      or Streamlit is available)
    """
    for key in ("STREAMLIT_COCO_DEBUG", "COCO_DEBUG"):
        raw = os.environ.get(key, "").strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True

    state = session_state
    if state is None:
        try:
            import streamlit as st

            state = st.session_state
        except Exception:  # pragma: no cover - non-Streamlit contexts
            return False

    try:
        return bool(state.get("coco_debug", False))
    except Exception:  # pragma: no cover
        return False
