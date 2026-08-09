"""Typed exceptions for streamlit-coco."""

from __future__ import annotations

from typing import Any


class CocoError(Exception):
    """Base exception for streamlit-coco failures."""


class SDKNotInstalledError(CocoError, ImportError):
    """``cortex-code-agent-sdk`` is not installed."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or "cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]"
        )


class CLINotFoundError(CocoError):
    """CoCo CLI (``cortex``) is not on ``PATH``."""

    def __init__(self, *, cli_path: str | None = None) -> None:
        if cli_path:
            super().__init__(f"CoCo CLI not found at {cli_path!r}")
        else:
            super().__init__(
                "CoCo CLI not found on PATH. Install the cortex CLI and ensure "
                "`cortex --version` works, or set CORTEX_CODE_CLI_PATH."
            )


class CLIProbeError(CocoError):
    """CoCo CLI was found but ``--version`` failed."""

    def __init__(self, cli_path: str) -> None:
        super().__init__(f"CoCo CLI at {cli_path!r} did not respond to --version")


class SnowflakeConfigNotFoundError(CocoError):
    """No Snowflake ``connections.toml`` or legacy ``config.toml`` was found."""

    def __init__(self) -> None:
        super().__init__(
            "No Snowflake config found. Create ~/.snowflake/connections.toml "
            "(or legacy config.toml) with an authenticated connection."
        )


class CocoConnectionError(CocoError):
    """Snowflake connection name or authentication failure."""


class SessionStartError(CocoError):
    """Background CoCo session worker failed to start."""


class SessionNotReadyError(CocoError):
    """CoCo session is not ready (connect timeout or boot failure)."""


class ApprovalTimeoutError(CocoError, TimeoutError):
    """User did not respond to an approval prompt in time."""

    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Approval timed out for tool {tool_name}")
        self.tool_name = tool_name


class QueryError(CocoError):
    """Single-turn :func:`streamlit_coco.query` failed."""


class CwdUploadError(CocoError):
    """Browser → ``cwd`` upload failed (size, extension, path, or overwrite)."""


def wrap_exception(
    exc: BaseException,
    *,
    context: str | None = None,
    **details: Any,
) -> CocoError:
    """Map SDK / runtime failures to typed :class:`CocoError` subclasses."""
    if isinstance(exc, CocoError):
        return exc

    message = str(exc).strip() or repr(exc)
    lowered = message.lower()

    if isinstance(exc, ImportError):
        if "cortex" in lowered or "cortex_code_agent_sdk" in lowered:
            return SDKNotInstalledError(message)
        return SDKNotInstalledError(message)

    if isinstance(exc, TimeoutError) and context == "approval":
        tool_name = str(details.get("tool_name") or "unknown")
        return ApprovalTimeoutError(tool_name)

    if any(token in lowered for token in ("connection not found", "unknown connection")):
        return CocoConnectionError(message)

    if "connection" in lowered and any(
        token in lowered for token in ("failed", "error", "refused", "denied", "invalid")
    ):
        return CocoConnectionError(message)

    if "cortex" in lowered and any(
        token in lowered for token in ("not found", "no such file", "enoent")
    ):
        return CLINotFoundError()

    if context == "session_start":
        return SessionStartError(message)

    if context in {"session_ready", "session"}:
        return SessionNotReadyError(message)

    if context == "query":
        return QueryError(message)

    return CocoError(message)
