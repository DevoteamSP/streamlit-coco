"""Welcome — what this app is, what happens, and how to use it."""

from __future__ import annotations

import streamlit as st
from engine import state

_STEPS = (
    (
        ":material/upload_file:",
        "1 · Load",
        "Upload Tableau or Power BI files, or copy an MIT demo pack into the agent workspace.",
        "No Copilot",
        "blue",
    ),
    (
        ":material/hub:",
        "2 · Estate map",
        "Parse workbooks and reports into tables, relationships, and contested names.",
        "Local parse",
        "blue",
    ),
    (
        ":material/speed:",
        "3 · KPIs",
        "Inventory calculated fields and DAX measures — including the ones that disagree.",
        "Local parse",
        "blue",
    ),
    (
        ":material/policy:",
        "4 · Access rules",
        "Compare Tableau User Filters (via Copilot) or Power BI table contracts (local).",
        "Copilot for Tableau",
        "orange",
    ),
    (
        ":material/gavel:",
        "5 · Arbitration",
        "You pick which KPI and access definitions win. The agent proposes; it does not decide.",
        "You decide",
        "green",
    ),
    (
        ":material/deployed_code:",
        "6 · Generate",
        "Write one semantic view and one row access policy, then build a Streamlit consumer.",
        "Write + approval",
        "orange",
    ),
)


def run() -> None:
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button(
            "Get started — load sources",
            type="primary",
            icon=":material/navigate_next:",
            key="bts_welcome_next",
        ):
            st.switch_page("screens/load.py")
        if state.has_mapped_estate():
            with st.popover(
                "Clear project",
                icon=":material/delete:",
                key="bts_welcome_clear",
            ):
                estate = state.get_estate() or {}
                n_tables = len(estate.get("tables") or [])
                st.caption(
                    "This project already has a mapped estate"
                    + (f" ({n_tables} tables)" if n_tables else "")
                    + ". Clear workspace sources, `out/` artifacts, and all step state."
                )
                if st.button(
                    "Confirm clear project",
                    type="primary",
                    icon=":material/delete:",
                    key="bts_welcome_clear_ok",
                ):
                    state.clear_project()
                    st.toast("Project cleared")
                    st.rerun()

    st.markdown(
        "Your KPI definitions and access rules are not in Snowflake. They live in "
        "**Tableau** workbooks and **Power BI** reports — duplicated, and they no "
        "longer agree with each other."
    )
    st.markdown(
        "This app reads those files, shows the drift, then writes **one semantic view**, "
        "**one row access policy**, and a **Streamlit consumer** that must use that view. "
        "It is not a BI clone and not chat-with-your-data. It is an example of "
        "how [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) embeds an "
        "agent that *acts*, under approval."
    )

    st.subheader("What you get")
    out1, out2, out3 = st.columns(3, gap="medium")
    with out1.container(border=True, height="stretch"):
        st.markdown("**:material/account_tree: Semantic view**")
        st.caption(
            "One YAML / SQL definition of tables, dimensions, and metrics — "
            "deployed with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`."
        )
    with out2.container(border=True, height="stretch"):
        st.markdown("**:material/policy: Row access policy**")
        st.caption(
            "One platform rule instead of a different User Filter or table contract "
            "in every dashboard."
        )
    with out3.container(border=True, height="stretch"):
        st.markdown("**:material/web: Streamlit consumer**")
        st.caption(
            "A generated app bound to the view — disconnected (no warehouse) "
            "or live with `SEMANTIC_VIEW(...)`."
        )

    st.subheader("What happens")
    st.caption(
        "Six screens, in order. Early steps are local parse. Later steps queue work "
        "on the shared Copilot session — they do not open a new agent."
    )
    for start in range(0, len(_STEPS), 3):
        cols = st.columns(3, gap="medium")
        for col, (icon, title, body, badge, color) in zip(cols, _STEPS[start : start + 3]):
            with col.container(border=True, height="stretch"):
                st.markdown(f"**{icon} {title}**")
                st.caption(body)
                st.badge(badge, color=color)

    st.subheader("How to use it")
    h1, h2 = st.columns(2, gap="medium")
    with h1.container(border=True, height="stretch"):
        st.markdown("**1. Load sources**")
        st.caption(
            "On **1 · Load**, use an MIT pack or upload your own `.twb` / `.twbx` / "
            "`.pbix` / `.pbit`. Files land in the agent working directory. Packs are "
            "MIT © Tableau and MIT © Microsoft."
        )
        st.markdown("**2. Open Copilot once**")
        st.caption(
            "Use **Copilot** in the header to connect. Later screens reuse that streamed "
            "session. Buttons only queue a job."
        )
    with h2.container(border=True, height="stretch"):
        st.markdown("**3. Walk the screens**")
        st.caption(
            "Estate map and KPIs need no account. Access rules need Copilot for Tableau "
            "(Power BI contracts are local). Arbitration is you. Generate writes SQL "
            "under approval."
        )
        st.markdown("**4. Generate the consumer**")
        st.caption(
            "Screen 6 writes the semantic view and row access policy, then builds a "
            "Streamlit app that must consume that view. Disconnected mode needs no warehouse."
        )


run()
