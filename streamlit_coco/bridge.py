"""Bridge helpers between CocoSession and Streamlit component state."""

from __future__ import annotations

from typing import Any

from streamlit_coco.debug import is_debug_mode
from streamlit_coco.session import CocoSession


def build_component_data(
    session: CocoSession,
    *,
    placeholder: str,
    show_tool_details: bool,
    show_thinking: bool,
    show_structured_inline: bool,
    height: int | str,
    include_transcript: bool = True,
) -> dict[str, Any]:
    pending = session.permission_manager.active_pending()
    transcript = session.get_transcript_snapshot() if include_transcript else []
    return {
        "transcript": transcript,
        "status": session.status.value,
        "pending_approval": pending.to_dict() if pending else None,
        "last_error": session.last_error,
        "header": {
            "title": "CoCo",
            "model": session.options.model,
            "connection": session.options.connection,
            "permission_mode": session.options.permission_mode,
        },
        "placeholder": placeholder,
        "show_tool_details": show_tool_details,
        "debug_mode": is_debug_mode(),
        "show_thinking": show_thinking,
        "show_structured_inline": show_structured_inline,
        "height": height,
        "scroll_token": session.get_revision(),
        "needs_polling": session.needs_polling,
    }
