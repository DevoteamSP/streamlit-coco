"""Smoke tests — import public surface (DSP N1 minimum)."""

from __future__ import annotations

import pytest


def test_import_package() -> None:
    import streamlit_coco as st_coco

    assert st_coco.__version__
    assert callable(st_coco.query)
    assert callable(st_coco.check_environment)
    assert callable(st_coco.require_environment)
    assert issubclass(st_coco.SDKNotInstalledError, st_coco.CocoError)
    # Lazy UI export resolves without breaking public surface.
    assert callable(st_coco.panel)


def test_core_import_does_not_load_streamlit() -> None:
    """Headless scripts can import core package symbols without Streamlit."""
    import subprocess
    import sys

    script = """
import sys
import streamlit_coco as coco
_ = coco.CocoSession, coco.query, coco.CocoOptions, coco.approve_pending, coco.get_session
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
    import streamlit_coco.ask_user  # noqa: F401
    import streamlit_coco.bootstrap  # noqa: F401
    import streamlit_coco.debug  # noqa: F401
    import streamlit_coco.diagnostics  # noqa: F401
    import streamlit_coco.display  # noqa: F401
    import streamlit_coco.messages  # noqa: F401
    import streamlit_coco.options  # noqa: F401
    import streamlit_coco.permissions  # noqa: F401
    import streamlit_coco.session  # noqa: F401
    import streamlit_coco.sql_tool  # noqa: F401
    import streamlit_coco.text_renderer  # noqa: F401
    import streamlit_coco.tool_cards  # noqa: F401
    import streamlit_coco.tool_extract  # noqa: F401
    import streamlit_coco.tool_names  # noqa: F401
    import streamlit_coco.ui  # noqa: F401


def test_ccv2_component_registers_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """CCv2 skill: st.components.v2.component must not re-run on every mount."""
    import streamlit as st

    from streamlit_coco import component as coco_component

    calls: list[tuple] = []
    mount = object()

    def fake_register(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        return mount

    class _V2:
        component = staticmethod(fake_register)

    monkeypatch.setattr(st.components, "v2", _V2(), raising=False)
    coco_component._get_component.cache_clear()
    try:
        assert coco_component._get_component() is mount
        assert coco_component._get_component() is mount
        assert len(calls) == 1
        assert calls[0][0][0] == "streamlit_coco"
        assert calls[0][1].get("isolate_styles") is True
    finally:
        coco_component._get_component.cache_clear()


def test_fragment_poll_pauses_on_pending_approval() -> None:
    from streamlit_coco.component import _fragment_poll_seconds
    from streamlit_coco.options import CocoOptions
    from streamlit_coco.session import CocoSession

    session = CocoSession(options=CocoOptions(), key="poll-test")
    assert _fragment_poll_seconds(session, 0.25, default_when=False) == 0.25
    assert _fragment_poll_seconds(session, None, default_when=True) == 0.25
    assert _fragment_poll_seconds(session, None, default_when=False) is None

    session.permission_manager.create_request("Write", {"path": "x.py"})
    assert _fragment_poll_seconds(session, 0.25, default_when=True) is None
    assert _fragment_poll_seconds(session, None, default_when=True) is None


def test_frontend_export_returns_cleanup() -> None:
    from importlib import resources

    js = resources.files("streamlit_coco.frontend").joinpath("main.js").read_text(encoding="utf-8")
    assert "export default function" in js
    assert "return () =>" in js
    assert "_cocoAbort" in js
    assert "provide_input" not in js
    assert "execute_plan" in js
    assert "Execute plan" in js


def test_frontend_css_uses_theme_tokens() -> None:
    from importlib import resources

    css = (
        resources.files("streamlit_coco.frontend").joinpath("style.css").read_text(encoding="utf-8")
    )
    assert "--st-yellow-background-color" in css
    assert "--st-red-text-color" in css
    assert "color: #fff" not in css
    assert "color: #c62828" not in css
