"""The floating window is opt-in. Classic mounts keep their old signature defaults."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from streamlit_coco.mini import options_for_window, prompts_from_questions, window_connection
from streamlit_coco.options import CocoOptions


def _rail_page() -> None:
    import streamlit_coco as st_coco

    st_coco.copilot_rail(None, connected=False, title="Copilot", key_prefix="demo", ask=True)


def test_prompts_from_rail_questions() -> None:
    prompts = prompts_from_questions(
        [
            "List the files",
            {"title": "Explain", "question": "Read BRIEF.md", "deferred": True},
            ("Suggest", "Suggest one change", False),
        ],
        deferred=False,
    )
    assert prompts == [
        {"title": "List the files", "text": "List the files", "fill": False},
        {"title": "Explain", "text": "Read BRIEF.md", "fill": True},
        {"title": "Suggest", "text": "Suggest one change", "fill": False},
    ]


def test_window_options_drop_session_tool_lists() -> None:
    opts = CocoOptions(
        connection="demo",
        cwd=".",
        allowed_tools=["Read", "Bash"],
        disallowed_tools=["Write"],
        require_approval_for=["Bash"],
        model="auto",
    )
    window_opts = options_for_window(opts)
    assert window_opts is not None
    assert window_opts.connection == "demo"
    assert window_opts.model == "auto"
    assert window_opts.allowed_tools == []
    assert window_opts.disallowed_tools == []
    assert window_opts.require_approval_for == []


def test_a_ready_rail_hands_its_profile_to_the_window() -> None:
    from types import SimpleNamespace

    ready = SimpleNamespace(is_ready=True, options=SimpleNamespace(connection="demo"))
    idle = SimpleNamespace(is_ready=False, options=SimpleNamespace(connection="demo"))
    assert window_connection(ready) == "demo"
    assert window_connection(idle) is None
    assert window_connection(None) is None


def test_conversation_connects_with_the_rail_profile(tmp_path) -> None:
    from streamlit_coco.conversation import Conversation
    from streamlit_coco.testing.scripted import ScriptedAgent

    conv = Conversation(
        tmp_path,
        agent=lambda emit: ScriptedAgent(emit, delay=0, connect_delay=0),
        connect="mock",
    )
    assert conv.profile == "mock"
    assert conv.conn == "connecting"
    conv.close()


def _rail_by_default() -> None:
    import streamlit_coco as st_coco

    st_coco.copilot_rail(None, connected=False, title="Copilot", key_prefix="demo")


def _ask_switch_off() -> None:
    from streamlit_coco.rail import ask_coco_switch

    ask_coco_switch("demo_ask")


def test_the_rail_has_no_minimize_unless_asked_for() -> None:
    """ask=False is the default: a 0.1.9 rail upgrades with no new control."""
    app = AppTest.from_function(_rail_by_default, default_timeout=30).run()
    assert not app.exception, app.exception
    assert not any(b.key == "demo_ask_coco" for b in app.button)
    assert "_streamlit_coco:demo" not in app.session_state


def _rail_page_owns_the_window() -> None:
    import streamlit as st

    import streamlit_coco as st_coco

    st.session_state["demo_ask_coco_on"] = True
    st_coco.copilot_rail(
        None,
        connected=False,
        title="Copilot",
        key_prefix="demo",
        ask=True,
        own_window=False,
    )


def test_own_window_false_keeps_minimize_on_the_rail() -> None:
    app = AppTest.from_function(_rail_page_owns_the_window, default_timeout=30).run()
    assert not app.exception, app.exception
    assert any(b.key == "demo_ask_coco" and b.help == "Minimize" for b in app.button)
    assert "_streamlit_coco:demo" not in app.session_state


def test_ask_switch_defaults_to_off() -> None:
    app = AppTest.from_function(_ask_switch_off, default_timeout=30).run()
    assert not app.exception, app.exception
    assert app.session_state["demo_ask"] == "Off"


def test_rail_minimize_hides_the_rail_and_restore_brings_it_back(monkeypatch) -> None:
    from streamlit_coco import window

    # each AppTest has its own component registry; a cached mount belongs to one
    window._component.cache_clear()
    monkeypatch.setenv("STREAMLIT_COCO_AGENT", "mock")
    app = AppTest.from_function(_rail_page, default_timeout=30).run()
    assert not app.exception, app.exception
    chat = next(b for b in app.button if b.key == "demo_ask_coco")
    assert chat.help == "Minimize"
    app = chat.click().run()
    assert not app.exception, app.exception
    assert app.session_state["demo_ask_coco_on"] is True
    window = app.session_state["_streamlit_coco:demo"]
    assert callable(window["on_rail"])
    assert window["token"] == 1
    # Restore lives in the window. Clearing the flag is what that icon does.
    app.session_state["demo_ask_coco_on"] = False
    app = app.run()
    assert not app.exception, app.exception
    assert app.session_state["demo_ask_coco_on"] is False
    assert any(b.key == "demo_ask_coco" and b.help == "Minimize" for b in app.button)
