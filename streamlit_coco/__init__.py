"""Ask CoCo for Streamlit, and a Python library for Snowflake CoCo.

``ask_coco(cwd)`` mounts the assistant window. Core / headless symbols import without loading
Streamlit; UI helpers (``ask_coco``, ``cwd_uploader``, …) are resolved lazily on first access.
"""

from __future__ import annotations

import os
from importlib import import_module, reload
from typing import Any

from streamlit_coco import policy
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
from streamlit_coco.messages import CocoEvent, events_to_dataframe
from streamlit_coco.options import CocoOptions
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

__version__ = "0.2.0.dev0"

# UI / Streamlit-backed exports — loaded on first attribute access.
_LAZY_ATTRS: dict[str, tuple[str, str]] = {
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
    "QueryError",
    "SDKNotInstalledError",
    "SessionNotReadyError",
    "SessionStartError",
    "SnowflakeConfigNotFoundError",
    "UploadedPath",
    "app_viewer",
    "ask_coco",
    "check_environment",
    "cwd_uploader",
    "default_fix_prompt",
    "default_snowflake_connection_name",
    "events_to_dataframe",
    "format_upload_prompt",
    "get_session",
    "get_window",
    "is_ask_user_question",
    "is_exit_plan_mode",
    "is_sql_tool",
    "last_preview_exception",
    "list_cwd_uploads",
    "list_snowflake_connections",
    "list_snowflake_toml_files",
    "policy",
    "preview_log_tail",
    "preview_running",
    "preview_url",
    "query",
    "require_environment",
    "resolve_snowflake_config_path",
    "render_output_field",
    "sanitize_upload_name",
    "start_app_preview",
    "stop_app_preview",
    "tool_family",
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
