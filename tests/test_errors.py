"""Tests for streamlit-coco typed errors."""

from __future__ import annotations

import pytest

from streamlit_coco.errors import (
    ApprovalTimeoutError,
    CLINotFoundError,
    CocoConnectionError,
    CocoError,
    QueryError,
    SDKNotInstalledError,
    SessionNotReadyError,
    SessionStartError,
    SnowflakeConfigNotFoundError,
    wrap_exception,
)


def test_sdk_not_installed_is_import_error() -> None:
    err = SDKNotInstalledError()
    assert isinstance(err, ImportError)
    assert isinstance(err, CocoError)
    assert "streamlit-coco[sdk]" in str(err)


def test_approval_timeout_is_timeout_error() -> None:
    err = ApprovalTimeoutError("Write")
    assert isinstance(err, TimeoutError)
    assert err.tool_name == "Write"


def test_wrap_exception_maps_connection_failures() -> None:
    wrapped = wrap_exception(RuntimeError("Connection not found: bad_prod"))
    assert isinstance(wrapped, CocoConnectionError)


def test_wrap_exception_maps_missing_cli() -> None:
    wrapped = wrap_exception(OSError("cortex: command not found"))
    assert isinstance(wrapped, CLINotFoundError)


def test_wrap_exception_query_context() -> None:
    wrapped = wrap_exception(RuntimeError("agent subprocess exited"), context="query")
    assert isinstance(wrapped, QueryError)


def test_wrap_exception_session_contexts() -> None:
    start = wrap_exception(RuntimeError("worker died"), context="session_start")
    ready = wrap_exception(RuntimeError("timed out"), context="session_ready")
    assert isinstance(start, SessionStartError)
    assert isinstance(ready, SessionNotReadyError)


def test_wrap_exception_passthrough() -> None:
    original = SnowflakeConfigNotFoundError()
    assert wrap_exception(original) is original


def test_require_environment_raises_without_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    from streamlit_coco.diagnostics import require_environment

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "cortex_code_agent_sdk":
            raise ImportError("no sdk")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(SDKNotInstalledError):
        require_environment()
