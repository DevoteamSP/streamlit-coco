"""Ask CoCo for Streamlit, and a Python library for Snowflake CoCo.

The default UI is the 0.1.9 chat family (``chat``, ``panel``, ``copilot_rail``).
The floating window is off until you pass ``mini=True`` to one of those, or call
``ask_coco(cwd)``. Core / headless symbols import without loading Streamlit; UI
helpers are resolved lazily on first access.
"""

from __future__ import annotations

import os
from importlib import import_module, reload
from typing import Any

from streamlit_coco import policy
from streamlit_coco.audit import AuditLog
from streamlit_coco.diagnostics import (
    CocoEnvironment,
    check_environment,
    default_snowflake_connection_name,
    list_snowflake_connections,
    list_snowflake_toml_files,
    require_environment,
    resolve_snowflake_config_path,
)
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
from streamlit_coco.features import Attachments, Features
from streamlit_coco.gate import Gate
from streamlit_coco.managed import (
    SANDBOX_WHERE,
    SANDBOX_WORDS,
    ManagedOptions,
    managed_agent,
    options_from_connection,
)
from streamlit_coco.messages import CocoEvent, events_to_dataframe
from streamlit_coco.options import CocoOptions
from streamlit_coco.permissions import approve_pending, deny_pending
from streamlit_coco.query import query
from streamlit_coco.session import CocoChatResult, CocoRunStatus, CocoSession, get_session
from streamlit_coco.tool_names import (
    is_ask_user_question,
    is_exit_plan_mode,
    is_sql_tool,
    tool_family,
)
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

__version__ = "0.3.0"

# UI / Streamlit-backed exports — loaded on first attribute access.
_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    "chat": ("streamlit_coco.component", "chat"),
    "request_input": ("streamlit_coco.ui", "request_input"),
    "chat_input_bar": ("streamlit_coco.bootstrap", "chat_input_bar"),
    "get_or_create_session": ("streamlit_coco.bootstrap", "get_or_create_session"),
    "render_environment_status": ("streamlit_coco.bootstrap", "render_environment_status"),
    "render_start_gate": ("streamlit_coco.bootstrap", "render_start_gate"),
    "reset_session": ("streamlit_coco.bootstrap", "reset_session"),
    "stop_session": ("streamlit_coco.bootstrap", "stop_session"),
    "get_latest_assistant_text": ("streamlit_coco.display", "get_latest_assistant_text"),
    "render_session_status": ("streamlit_coco.display", "render_session_status"),
    "render_transcript": ("streamlit_coco.display", "render_transcript"),
    "panel": ("streamlit_coco.ui", "panel"),
    "copilot_rail": ("streamlit_coco.rail", "copilot_rail"),
    "transcript_display_config": ("streamlit_coco.rail", "transcript_display_config"),
    "transcript_view_pills": ("streamlit_coco.rail", "transcript_view_pills"),
    "render_approvals": ("streamlit_coco.ui", "render_approvals"),
    "render_plan_banner": ("streamlit_coco.ui", "render_plan_banner"),
    "send_prompt": ("streamlit_coco.ui", "send_prompt"),
    "is_debug_mode": ("streamlit_coco.debug", "is_debug_mode"),
    "ask_coco": ("streamlit_coco.window", "ask_coco"),
    "get_window": ("streamlit_coco.window", "get_window"),
    "cwd_uploader": ("streamlit_coco.uploader", "cwd_uploader"),
    "render_output_field": ("streamlit_coco.display", "render_output_field"),
    "app_viewer": ("streamlit_coco.viewer", "app_viewer"),
    "start_app_preview": ("streamlit_coco.app_preview", "start_app_preview"),
    "stop_app_preview": ("streamlit_coco.app_preview", "stop_app_preview"),
    "preview_running": ("streamlit_coco.app_preview", "preview_running"),
    "preview_url": ("streamlit_coco.app_preview", "preview_url"),
    "last_preview_exception": ("streamlit_coco.app_preview", "last_preview_exception"),
    "preview_log_tail": ("streamlit_coco.app_preview", "preview_log_tail"),
    "default_fix_prompt": ("streamlit_coco.app_preview", "default_fix_prompt"),
}

__all__ = [
    "ApprovalTimeoutError",
    "Attachments",
    "AuditLog",
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
    "Features",
    "Gate",
    "ManagedOptions",
    "SANDBOX_WHERE",
    "SANDBOX_WORDS",
    "QueryError",
    "SDKNotInstalledError",
    "SessionNotReadyError",
    "SessionStartError",
    "SnowflakeConfigNotFoundError",
    "UploadedPath",
    "app_viewer",
    "approve_pending",
    "ask_coco",
    "chat",
    "chat_input_bar",
    "check_environment",
    "copilot_rail",
    "cwd_uploader",
    "deny_pending",
    "default_fix_prompt",
    "default_snowflake_connection_name",
    "events_to_dataframe",
    "format_upload_prompt",
    "get_latest_assistant_text",
    "get_or_create_session",
    "get_session",
    "get_window",
    "managed_agent",
    "options_from_connection",
    "is_ask_user_question",
    "is_debug_mode",
    "is_exit_plan_mode",
    "is_sql_tool",
    "last_preview_exception",
    "list_cwd_uploads",
    "list_snowflake_connections",
    "list_snowflake_toml_files",
    "panel",
    "policy",
    "preview_log_tail",
    "preview_running",
    "preview_url",
    "query",
    "render_approvals",
    "render_environment_status",
    "render_output_field",
    "render_plan_banner",
    "render_session_status",
    "render_start_gate",
    "render_transcript",
    "request_input",
    "require_environment",
    "reset_session",
    "resolve_snowflake_config_path",
    "sanitize_upload_name",
    "send_prompt",
    "start_app_preview",
    "stop_app_preview",
    "stop_session",
    "tool_family",
    "transcript_display_config",
    "transcript_view_pills",
    "upload_to_cwd",
]


def __getattr__(name: str) -> Any:
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = target
    # Resolve from disk when the impl file changed. ``import_module`` alone
    # returns the cached module, so Streamlit can reload the caller (e.g.
    # preview_panel) while ``st_coco.app_viewer`` is still the old function.
    module = import_module(module_name)
    path = getattr(module, "__file__", None)
    if path and os.path.isfile(path):
        mtime = os.path.getmtime(path)
        if getattr(module, "_coco_src_mtime", None) not in (None, mtime):
            module = reload(module)
        module._coco_src_mtime = mtime
    return getattr(module, attr)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()) | {"__version__"})
