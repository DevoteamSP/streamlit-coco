"""CoCo-free Streamlit harness for Playwright UX e2e tests.

Exercises real library helpers (upload, rich markdown, copy, transcript windowing)
without Cortex CLI / Snowflake.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_coco.bootstrap import cwd_uploader
from streamlit_coco.clipboard import render_copy_button
from streamlit_coco.display import render_message_body
from streamlit_coco.rich_text import window_transcript
from streamlit_coco.tool_cards import render_tool_card

st.set_page_config(page_title="CoCo UX e2e harness", layout="wide")
st.title("CoCo UX e2e harness")
st.caption("Fixture app for Playwright — no live CoCo agent.")

WORKSPACE = Path(__file__).resolve().parent / "workspaces" / "e2e_ux"
WORKSPACE.mkdir(parents=True, exist_ok=True)

GATE_KEY = "e2e_ux_started"
EXTRA_KEY = "_coco_transcript_extra_e2e_harness"
MAX_MESSAGES = 5

ASSISTANT_WITH_SQL = (
    "Here is a sample query:\n\n"
    "```sql\nSELECT customer_id, SUM(amount) AS total\n"
    "FROM orders\nGROUP BY 1;\n```\n\n"
    "And a tiny Python snippet:\n\n"
    "```python\nprint('hello coco')\n```\n"
)


def _seed_transcript() -> list[dict]:
    """Enough items to hide earlier messages when max_messages=5."""
    items: list[dict] = []
    for i in range(8):
        items.append(
            {
                "id": f"user-{i}",
                "role": "user",
                "kind": "text",
                "content": f"Earlier user message {i}",
            }
        )
        items.append(
            {
                "id": f"asst-{i}",
                "role": "assistant",
                "kind": "text",
                "content": f"Earlier assistant reply {i}",
            }
        )
    items.append(
        {
            "id": "asst-sql",
            "role": "assistant",
            "kind": "text",
            "content": ASSISTANT_WITH_SQL,
        }
    )
    items.append(
        {
            "id": "tool-sql-1",
            "kind": "tool",
            "name": "SQL",
            "status": "completed",
            "input": {"sql": "SELECT 1 AS n"},
            "result": "n\n1",
        }
    )
    return items


if GATE_KEY not in st.session_state:
    st.session_state[GATE_KEY] = False

if not st.session_state[GATE_KEY]:
    st.markdown("Click below to open the UX harness (no CoCo connection).")
    if st.button("Start harness", type="primary", key="e2e_start_harness"):
        st.session_state[GATE_KEY] = True
        st.session_state["e2e_transcript"] = _seed_transcript()
        st.session_state[EXTRA_KEY] = 0
        st.rerun()
    st.stop()

st.caption("Harness ready")
st.markdown(
    '<span data-testid="e2e-harness-ready">ready</span>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(f"`cwd` · `{WORKSPACE}`")
    cwd_uploader(
        str(WORKSPACE),
        overwrite="replace",
        key="e2e_cwd_uploader",
        file_type=["csv", "md", "txt"],
        accept_multiple_files=False,
        label="Upload into agent workspace",
    )
    if st.button("Reset harness", key="e2e_reset"):
        st.session_state[GATE_KEY] = False
        st.session_state.pop("e2e_transcript", None)
        st.session_state[EXTRA_KEY] = 0
        st.rerun()

full = list(st.session_state.get("e2e_transcript") or _seed_transcript())
extra = int(st.session_state.get(EXTRA_KEY, 0) or 0)
visible, hidden = window_transcript(full, max_messages=MAX_MESSAGES, extra=extra)

with st.container(border=True):
    st.subheader("Transcript")
    if hidden > 0:
        st.caption(f"{hidden} earlier message{'s' if hidden != 1 else ''} hidden")
        st.markdown(
            '<span data-testid="e2e-messages-hidden">hidden</span>',
            unsafe_allow_html=True,
        )
        if st.button("Load earlier", key="e2e_load_earlier", type="secondary"):
            st.session_state[EXTRA_KEY] = extra + MAX_MESSAGES
            st.rerun()

    for item in visible:
        role = item.get("role")
        kind = item.get("kind")
        item_id = str(item.get("id") or "")

        if kind == "tool":
            render_tool_card(item, show_tool_details=True, show_copy=True)
            continue

        if role == "user":
            with st.chat_message("user"):
                render_message_body(str(item.get("content") or ""))
            continue

        if kind == "text" or role == "assistant":
            content = str(item.get("content") or "")
            with st.chat_message("assistant"):
                render_message_body(content)
                if content:
                    copy_label = "Copy SQL" if item_id == "asst-sql" else "Copy"
                    render_copy_button(
                        content,
                        key=f"e2e_copy_{item_id}",
                        label=copy_label,
                    )
                if item_id == "asst-sql":
                    st.markdown(
                        '<span data-testid="e2e-assistant-sql">sql-msg</span>',
                        unsafe_allow_html=True,
                    )

st.caption("Harness footer")
st.markdown(
    '<span data-testid="e2e-harness-footer">footer</span>',
    unsafe_allow_html=True,
)
