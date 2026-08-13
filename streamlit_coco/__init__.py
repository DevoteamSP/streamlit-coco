"""Streamlit component and Python library for Snowflake CoCo.

Core / headless symbols import without loading Streamlit. UI helpers
(``panel``, ``chat``, …) are resolved lazily on first access.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from streamlit_coco.ask_user import is_ask_user_question
from streamlit_coco.debug import is_debug_mode
from streamlit_coco.diagnostics import CocoEnvironment, check_environment, require_environment
from streamlit_coco.errors import (
    ApprovalTimeoutError,
    CLINotFoundError,
    CLIProbeError,
    CocoConnectionError,
    CocoError,
    CwdUploadError,
    QueryError,
    SDKNotInstalledError,
    SessionNotReadyError,
    SessionStartError,
    SnowflakeConfigNotFoundError,
)
from streamlit_coco.messages import CocoEvent, events_to_dataframe
from streamlit_coco.options import CocoOptions
from streamlit_coco.permissions import approve_pending, deny_pending
from streamlit_coco.query import query
from streamlit_coco.session import CocoChatResult, CocoRunStatus, CocoSession, get_session
from streamlit_coco.tool_names import is_exit_plan_mode, is_sql_tool, tool_family
from streamlit_coco.upload import (
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_MAX_BYTES,
    DEFAULT_UPLOAD_SUBDIR,
    UploadedPath,
    format_upload_prompt,
    list_cwd_uploads,
    sanitize_upload_name,
    upload_to_cwd,
)

__version__ = "0.1.6"

# UI / Streamlit-backed exports — loaded on first attribute access.
_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    "chat": ("streamlit_coco.component", "chat"),
    "request_input": ("streamlit_coco.ui", "request_input"),
    "chat_input_bar": ("streamlit_coco.bootstrap", "chat_input_bar"),
    "cwd_uploader": ("streamlit_coco.bootstrap", "cwd_uploader"),
    "get_or_create_session": ("streamlit_coco.bootstrap", "get_or_create_session"),
    "render_environment_status": ("streamlit_coco.bootstrap", "render_environment_status"),
    "render_start_gate": ("streamlit_coco.bootstrap", "render_start_gate"),
    "reset_session": ("streamlit_coco.bootstrap", "reset_session"),
    "stop_session": ("streamlit_coco.bootstrap", "stop_session"),
    "get_latest_assistant_text": ("streamlit_coco.display", "get_latest_assistant_text"),
    "render_output_field": ("streamlit_coco.display", "render_output_field"),
    "render_session_status": ("streamlit_coco.display", "render_session_status"),
    "render_transcript": ("streamlit_coco.display", "render_transcript"),
    "panel": ("streamlit_coco.ui", "panel"),
    "copilot_rail": ("streamlit_coco.rail", "copilot_rail"),
    "transcript_view_pills": ("streamlit_coco.rail", "transcript_view_pills"),
    "render_approvals": ("streamlit_coco.ui", "render_approvals"),
    "render_plan_banner": ("streamlit_coco.ui", "render_plan_banner"),
    "send_prompt": ("streamlit_coco.ui", "send_prompt"),
}

__all__ = [
    "ApprovalTimeoutError",
    "CLIProbeError",
    "CLINotFoundError",
    "CocoChatResult",
    "CocoConnectionError",
    "CocoEnvironment",
    "CocoError",
    "CocoEvent",
    "CocoOptions",
    "CocoRunStatus",
    "CocoSession",
    "CwdUploadError",
    "DEFAULT_ALLOWED_EXTENSIONS",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_UPLOAD_SUBDIR",
    "QueryError",
    "SDKNotInstalledError",
    "SessionNotReadyError",
    "SessionStartError",
    "SnowflakeConfigNotFoundError",
    "UploadedPath",
    "approve_pending",
    "chat",
    "chat_input_bar",
    "check_environment",
    "copilot_rail",
    "cwd_uploader",
    "deny_pending",
    "events_to_dataframe",
    "format_upload_prompt",
    "get_or_create_session",
    "get_session",
    "get_latest_assistant_text",
    "is_ask_user_question",
    "is_debug_mode",
    "is_exit_plan_mode",
    "is_sql_tool",
    "list_cwd_uploads",
    "panel",
    "query",
    "render_approvals",
    "render_plan_banner",
    "require_environment",
    "render_environment_status",
    "render_output_field",
    "render_session_status",
    "render_start_gate",
    "render_transcript",
    "request_input",
    "reset_session",
    "sanitize_upload_name",
    "send_prompt",
    "stop_session",
    "tool_family",
    "transcript_view_pills",
    "upload_to_cwd",
]


def __getattr__(name: str) -> Any:
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = target
    # Always resolve from the live module so Streamlit hot-reload of
    # ``streamlit_coco.rail`` (etc.) is not stuck on a stale cached function.
    return getattr(import_module(module_name), attr)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()) | {"__version__"})
