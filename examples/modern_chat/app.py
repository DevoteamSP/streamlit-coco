"""Modern chat: the Copilot rail, the floating window, or both.

The working folder is the repository root, so every surface can read this
project. The rail and the window do not share a transcript.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.mini import window_connection
from streamlit_coco.rail import ask_restore, present_ask, rail_minimized

REPO = Path(__file__).resolve().parents[2]
LOGO = Path(st_coco.__file__).resolve().parent / "static" / "coco" / "coco-logo.svg"
SESSION_KEY = "modern_session"
GATE_KEY = "modern_gate"
CONN_KEY = "modern_conn"
RAIL_KEY = "modern_coco"
WINDOW_KEY = "modern"

STARTERS = (
    {
        "title": "List the files",
        "text": (
            "List the files in this folder and say what each one is for. "
            "Do not write or edit files."
        ),
    },
    {
        "title": "Find ask_coco",
        "text": (
            "Grep this repo for `def ask_coco` and say which file defines it. "
            "Do not write or edit files."
        ),
    },
    {
        "title": "Explain the rail",
        "text": (
            "Read streamlit_coco/rail.py and explain what copilot_rail does, "
            "in a few sentences. Do not write or edit files."
        ),
    },
)

WINDOW_THEME = {
    # Header and launcher fill is on-accent; their icons are surface.
    # on-accent has to stay dark or those icons are white on a light bar.
    # accent is the Send button, so it has to contrast with that dark mark.
    "accent": "#D6FF4A",
    "on-accent": "#16181D",
    "surface": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B6862",
    "border": "#E6E4DF",
    # the page loads Outfit (.streamlit/config.toml). Theme font "inherit" does not reach the window
    # on Streamlit 1.60 (its host element renders in Times), so the page font is named.
    "font": "Outfit, system-ui, sans-serif",
    "radius": "16px",
}


def _optional_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def _connections() -> list[str]:
    secret = _optional_secret("snowflake_connection")
    return [str(secret)] if secret else []


st.set_page_config(
    page_title="Modern chat",
    page_icon=":material/forum:",
    layout="wide",
    initial_sidebar_state="expanded",
)

secret_connection = _optional_secret("snowflake_connection")
connection = st.session_state.get(CONN_KEY) or secret_connection
opts = st_coco.CocoOptions(cwd=str(REPO), connection=connection)
env = st_coco.check_environment(connection=connection)

session = None
if st.session_state.get(GATE_KEY):
    session = st_coco.get_or_create_session(opts, key=SESSION_KEY)
    if not session.is_ready and not session.is_connecting:
        session.start()


def _on_connect(chosen: str) -> None:
    st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
    st.session_state[CONN_KEY] = chosen
    st.session_state[GATE_KEY] = True


def _on_disconnect() -> None:
    st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
    st.session_state.pop(CONN_KEY, None)


def _on_clear() -> None:
    st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
    st.toast("Chat cleared")


def _mount_window(*, on_rail=None):
    return st_coco.ask_coco(
        REPO,
        key=WINDOW_KEY,
        connection=window_connection(session),
        prompts=[{"title": item["title"], "text": item["text"]} for item in STARTERS],
        labels={
            "window.field.placeholder": "Ask about this repo…",
            "window.launcher.label": "Ask CoCo",
        },
        theme=WINDOW_THEME,
        on_rail=on_rail,
    )


def _render_rail(*, ask: bool) -> None:
    with st.container(border=True):
        st_coco.copilot_rail(
            session,
            title="Copilot",
            key_prefix=RAIL_KEY,
            connected=session is not None,
            connections=_connections(),
            connection_name=connection if isinstance(connection, str) else None,
            on_connect=_on_connect,
            on_disconnect=_on_disconnect,
            connect_caption="Snowflake profile for this column.",
            on_clear=_on_clear if session is not None else None,
            show_copy=True,
            example_questions=[
                {"title": item["title"], "question": item["text"]} for item in STARTERS
            ],
            input_placeholder="Ask about this repo…",
            status_caption=f"cwd · `{REPO}`",
            ask=ask,
            own_window=False,
        )


def _header() -> str:
    st.title("Modern chat")
    surface = (
        st.segmented_control(
            "Surface",
            options=["Rail", "Window", "Both"],
            default="Rail",
            key="modern_surface",
            label_visibility="collapsed",
            width="content",
        )
        or "Rail"
    )
    captions = {
        "Rail": "Copilot stays in a column on the page.",
        "Window": "Ask CoCo floats over the page.",
        "Both": (
            "The column and Ask CoCo together. Minimize hides the column. Restore brings it back."
        ),
    }
    st.caption(captions.get(surface, captions["Rail"]))
    return surface


def _studio(surface: str, coco, *, minimized: bool = False) -> None:
    ready = session is not None and session.is_ready
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(":material/auto_awesome: **Studio**")
        if surface == "Both" and minimized:
            st.badge("Minimized", icon=":material/minimize:", color="orange")
        elif surface == "Both":
            st.badge("Both", icon=":material/view_column:", color="blue")
        elif surface == "Rail" and session is not None:
            color = "green" if ready else "orange"
            st.badge(session.status.value, color=color)
        elif surface == "Window":
            st.badge("Floating", icon=":material/open_in_new:", color="violet")
    st.caption(f"Working folder · `{REPO.name}`")

    read, ask, split = st.columns(3)
    with read:
        with st.container(border=True):
            st.markdown(":material/folder_open: **Read**")
            st.caption("Looking inside this folder is free.")
    with ask:
        with st.container(border=True):
            st.markdown(":material/front_hand: **Ask**")
            st.caption("A write, a command, or SQL waits for you.")
    with split:
        with st.container(border=True):
            st.markdown(":material/alt_route: **Two clients**")
            st.caption("The rail and the window do not share a transcript.")

    st.markdown("**Try one**")
    if coco is not None and (surface == "Window" or minimized):
        with st.container(horizontal=True):
            for item in STARTERS:
                if st.button(item["title"], key=f"modern_win_{item['title']}"):
                    coco.ask(item["title"], item["text"], key=item["title"])
        return

    if not ready:
        st.caption("Connect in the rail, then send one of these.")
    with st.container(horizontal=True):
        for item in STARTERS:
            if st.button(
                item["title"],
                key=f"modern_send_{item['title']}",
                disabled=not ready,
            ):
                st_coco.send_prompt(session, item["text"])
                st.rerun()


with st.sidebar:
    if LOGO.is_file():
        st.logo(str(LOGO), size="large")
    st.markdown("**Surfaces**")
    st.caption("Rail is the column. Window floats. Both shows them together.")
    if env.ready:
        st.badge("Environment ready", icon=":material/check:", color="green")
    else:
        st.badge("Check CoCo setup", icon=":material/warning:", color="orange")

surface = _header()
minimized = False
coco = None
if surface == "Both":
    coco = present_ask(
        True,
        RAIL_KEY,
        lambda: _mount_window(on_rail=ask_restore(RAIL_KEY)),
        window_key=WINDOW_KEY,
    )
    minimized = rail_minimized(RAIL_KEY)
else:
    present_ask(False, RAIL_KEY, lambda: None)
    if surface == "Window":
        coco = _mount_window()

if surface == "Window" or minimized:
    _studio(surface, coco, minimized=minimized)
else:
    main, rail = st.columns([1.15, 1])
    with main:
        _studio(surface, coco, minimized=False)
    with rail:
        _render_rail(ask=surface == "Both")
