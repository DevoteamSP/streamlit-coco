"""Smoke tests — import public surface (DSP N1 minimum)."""

from __future__ import annotations


def test_import_package() -> None:
    import streamlit_coco as st_coco

    assert st_coco.__version__
    assert callable(st_coco.query)
    assert callable(st_coco.check_environment)
    assert callable(st_coco.require_environment)
    assert callable(st_coco.list_snowflake_connections)
    assert issubclass(st_coco.SDKNotInstalledError, st_coco.CocoError)
    # The window's names resolve lazily, the rest of the interface eagerly.
    assert callable(st_coco.ask_coco)
    assert callable(st_coco.get_window)
    assert st_coco.Features().copy and st_coco.Attachments().multi
    assert callable(st_coco.Gate)
    assert callable(st_coco.policy.FolderPolicy)


def test_core_import_does_not_load_streamlit() -> None:
    """Headless scripts can import core package symbols without Streamlit."""
    import subprocess
    import sys

    script = """
import sys
import streamlit_coco as coco
_ = (
    coco.CocoSession,
    coco.query,
    coco.CocoOptions,
    coco.Features,
    coco.Gate,
    coco.policy.FolderPolicy,
    coco.get_session,
    coco.upload_to_cwd,
)
assert "streamlit" not in sys.modules, sorted(k for k in sys.modules if k.startswith("streamlit"))
print("ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_import_core_modules() -> None:
    import streamlit_coco.diagnostics  # noqa: F401
    import streamlit_coco.messages  # noqa: F401
    import streamlit_coco.options  # noqa: F401
    import streamlit_coco.permissions  # noqa: F401
    import streamlit_coco.session  # noqa: F401
    import streamlit_coco.text_renderer  # noqa: F401
    import streamlit_coco.tool_names  # noqa: F401
    import streamlit_coco.upload  # noqa: F401


def test_cwd_upload_export() -> None:
    import streamlit_coco as st_coco

    assert callable(st_coco.upload_to_cwd)
    assert issubclass(st_coco.CwdUploadError, st_coco.CocoError)
    assert callable(st_coco.cwd_uploader)


def test_classic_ui_is_the_default_and_the_window_stays_available() -> None:
    import inspect

    import streamlit_coco as st_coco

    for name in (
        "chat",
        "panel",
        "copilot_rail",
        "chat_input_bar",
        "send_prompt",
        "render_transcript",
        "render_approvals",
        "approve_pending",
        "deny_pending",
        "request_input",
        "is_debug_mode",
        "get_or_create_session",
    ):
        assert name in st_coco.__all__
        assert getattr(st_coco, name) is not None, name
    for name in ("chat", "panel", "copilot_rail"):
        param = inspect.signature(getattr(st_coco, name)).parameters["mini"]
        assert param.default is False


def test_all_names_resolve() -> None:
    import streamlit_coco as st_coco

    for name in st_coco.__all__:
        assert getattr(st_coco, name) is not None, name
