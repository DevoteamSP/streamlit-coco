"""Skills shop: browse the skills on a Snowflake stage and chat with one of them (experimental).

A skill is a folder with a SKILL.md that Snowflake's managed coding agent loads from a stage. Only
developers publish (`make publish-skill`); this app reads. Pick a skill, open it, and chat with that
skill alone: the agent runs in Snowflake's sandbox, with the rights of the role you log in with.

`make skills-hub`. With STREAMLIT_COCO_AGENT=mock, or with "Sample skills" in the sidebar, no
Snowflake is needed: the shop shows the samples and the chat is the scripted agent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from shop import native  # noqa: E402
from shop.demo import build_demo_store  # noqa: E402
from shop.service import Shop  # noqa: E402
from shop.stores import CachedStore, NotOnAStage, StageStore  # noqa: E402

import streamlit_coco as st_coco  # noqa: E402
from streamlit_coco.diagnostics import (  # noqa: E402
    default_snowflake_connection_name,
    list_snowflake_connections,
)
from streamlit_coco.policy import FolderPolicy  # noqa: E402
from streamlit_coco.window import request_open  # noqa: E402

STATE = "skills_hub"
MOCK = os.environ.get("STREAMLIT_COCO_AGENT") == "mock"
NATIVE = native.in_native_app()

st.set_page_config(page_title="Skills shop", page_icon=":material/storefront:", layout="wide")


def _state() -> dict:
    return st.session_state.setdefault(STATE, {"shop": None, "base": None, "open": None})


def _connect_native(state: dict) -> None:
    """Inside the Native App: the shop reads the application's own stage and the chat runs with the
    application's rights; there is nothing to choose."""
    if state.get("kind") != "native":
        try:
            base, store = native.connect()
            store = CachedStore(store)
            store.index()  # the first read says now whether the stage can be read
        except Exception as error:  # noqa: BLE001 - the page says why, whatever it was
            st.error(f"The application could not open its skills: {error}")
            st.stop()
        state.update(shop=Shop(store), base=base, conn=base.connection, open=None, kind="native")
    with st.sidebar:
        st.subheader("Source")
        st.caption("The skills of this application. The agent runs as the application.")
        if st.button("Refresh the list"):
            state["shop"].store.refresh()


def _connect_sidebar(state: dict) -> None:
    if NATIVE:
        return _connect_native(state)
    with st.sidebar:
        st.subheader("Source")
        sources = ["Sample skills (no Snowflake)", "Stage in Snowflake"]
        source = st.radio(
            "Skills from", sources, index=0 if MOCK else 1, label_visibility="collapsed"
        )
        if source == sources[0]:
            if state.get("kind") != "demo":
                state.update(shop=Shop(build_demo_store()), base=None, open=None, kind="demo")
            return
        names = list_snowflake_connections()
        default = default_snowflake_connection_name("config.toml")
        profile = st.selectbox(
            "Profile",
            names,
            index=names.index(default) if default in names else None,
            placeholder="Pick the account to log in to",
        )
        role = st.text_input(
            "Role",
            value="PUBLIC",
            help="The agent works with the rights of this role, and the role must read the stage.",
        )
        stage = st.text_input("Stage", placeholder="DATABASE.SCHEMA.SKILL_STAGE")
        if st.button("Connect", type="primary", disabled=not (profile and stage)):
            old = state.get("conn")
            if old is not None:
                old.close()
            try:
                with st.spinner(f"Logging in with {profile}…"):
                    base = st_coco.options_from_connection(profile, role=role.strip() or None)
                    store = CachedStore(StageStore(base.connection, stage))
                    store.index()  # the first read says now whether the stage can be read
                state.update(
                    shop=Shop(store), base=base, conn=base.connection, open=None, kind="stage"
                )
            except Exception as error:  # noqa: BLE001 - the page says why, whatever it was
                st.error(f"Could not open the shop: {error}")
        if state.get("kind") == "stage" and st.button("Refresh the list"):
            state["shop"].store.refresh()


def _card(shop: Shop, skill, column) -> None:
    with column, st.container(border=True):
        st.markdown(f"**{skill.title}**")
        st.caption(f"{skill.pack or 'no pack'} · v{skill.version}")
        st.write(skill.description)
        if skill.has_scripts:
            st.badge("runs code", icon=":material/terminal:", color="orange")
        if st.button("Open", key=f"open-{skill.id}", icon=":material/arrow_forward:"):
            st.session_state[STATE]["open"] = skill.id
            st.rerun()


def _library(shop: Shop) -> None:
    left, right = st.columns([3, 1])
    query = left.text_input("Search", placeholder="Search the skills", label_visibility="collapsed")
    packs = shop.packs()
    pack = right.selectbox("Pack", ["All packs", *packs], label_visibility="collapsed")
    skills = shop.skills(query=query, pack=None if pack == "All packs" else pack)
    if not skills:
        st.info(
            "No skill matches." if shop.all_versions() else "The shop is empty: publish a skill."
        )
        return
    columns = st.columns(3)
    for i, skill in enumerate(skills):
        _card(shop, skill, columns[i % 3])


def _detail(shop: Shop, state: dict, skill_id: str) -> None:
    if st.button("Back to the shop", icon=":material/arrow_back:"):
        state["open"] = None
        st.rerun()
    versions = shop.versions(skill_id)
    if not versions:
        st.warning("This skill is not in the shop any more.")
        return
    chosen = st.selectbox("Version", [v.version for v in versions], help="The latest is first.")
    skill = shop.get(skill_id, chosen)
    st.header(skill.title)
    st.caption(f"{skill.pack or 'no pack'} · v{skill.version} · published {skill.published_at}")
    st.write(skill.description)
    if skill.has_scripts:
        st.warning(
            "This skill carries code. The agent may run it in its sandbox; each run asks first.",
            icon=":material/terminal:",
        )
    if st.button("Chat with this skill", type="primary", icon=":material/chat:"):
        _start_chat(shop, state, skill)

    about, files, history = st.tabs(["About", "Files", "Versions"])
    with about:
        st.markdown(shop.about(skill))
    with files:
        st.code("\n".join(skill.files), language=None)
        st.caption(f"sha256 {skill.sha256}")
    with history:
        st.dataframe(
            [
                {"version": v.version, "published": v.published_at, "sha256": v.sha256[:12]}
                for v in versions
            ],
            hide_index=True,
        )


def _start_chat(shop: Shop, state: dict, skill) -> None:
    with st.spinner("Checking the files on the stage…"):
        verdict = shop.verify(skill)
    if not verdict.ok:
        st.error(" ".join(verdict.problems) + " This version is not offered for a chat.")
        return
    state["chat"] = (skill.id, skill.version)
    state["notice"] = f"A new conversation, with the skill {skill.title} only."
    state["open_window"] = True
    st.rerun()


def _chat(shop: Shop, state: dict) -> None:
    chat = state.get("chat")
    if not chat:
        return
    try:
        skill = shop.get(*chat)
    except KeyError:
        return
    key = f"shop-{skill.id}-{skill.version}"
    st.sidebar.success(f"Chat: {skill.title} v{skill.version}")
    if state.pop("open_window", False):
        request_open(key)  # before the mount: it opens the window of that mount, once
    prompts = [{"title": "Run the skill", "text": skill.run_prompt}] if skill.run_prompt else None
    labels = {"window.field.placeholder": f"Ask {skill.title}…"}
    if state.get("kind") == "demo" or MOCK:
        from streamlit_coco.testing.scripted import ScriptedAgent

        st_coco.ask_coco(
            APP_ROOT,
            key=key,
            agent=lambda emit: ScriptedAgent(emit),
            connection="mock",
            prompts=prompts,
            labels=labels,
        )
    else:
        try:
            options = shop.chat_options(state["base"], skill)
        except NotOnAStage as error:
            st.sidebar.error(str(error))
            return
        st_coco.ask_coco(
            APP_ROOT,
            key=key,
            agent=st_coco.managed_agent(options),
            connection=state["base"].label,
            policy=FolderPolicy(APP_ROOT, words=st_coco.SANDBOX_WORDS, where=st_coco.SANDBOX_WHERE),
            prompts=prompts,
            labels=labels,
        )
    if state.get("notice"):
        st.toast(state.pop("notice"))


def main() -> None:
    st.title(":material/storefront: Skills shop")
    st.caption(
        "streamlit-coco · managed coding agent (experimental) · developers publish, you chat"
    )
    state = _state()
    _connect_sidebar(state)
    shop: Shop | None = state.get("shop")
    if shop is None:
        st.write("Pick a profile, a role and the stage that holds the skills, then **Connect**.")
        st.stop()
    st.caption(f"Skills from {shop.store.label}")
    try:
        if state.get("open"):
            _detail(shop, state, state["open"])
        else:
            _library(shop)
    except Exception as error:  # noqa: BLE001 - a stage the role cannot read, a broken index
        st.error(f"The shop could not be read: {error}")
        st.stop()
    _chat(shop, state)


main()
