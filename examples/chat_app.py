"""Ask CoCo on a page: the window, a test-prompt picker and the rights as pills.

The window (launcher at the bottom right) is one call. The sidebar shows what a host can add:
which tools run without asking (the pills build a FolderPolicy), a switch for each comfort, and
a picker that sends a test prompt through ``coco.ask``.
Run it without a login on the scripted agent: ``STREAMLIT_COCO_AGENT=mock``.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco import policy as rights

st.set_page_config(page_title="CoCo Chat", layout="wide")
st.title("CoCo for Streamlit")

COCO_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "SQL"]
PROMPTS_PATH = Path(__file__).resolve().parent / "testdata" / "prompts.json"


class PillPolicy(rights.FolderPolicy):
    """FolderPolicy with the sidebar's two groups: `free` tools run without asking (a refusal
    still stands), `ask` tools always ask, even a read; the rest keeps the default."""

    def __init__(self, folder, free, ask, **kwargs):
        super().__init__(folder, **kwargs)
        self.free, self.ask = {t.lower() for t in free}, {t.lower() for t in ask}

    def judge(self, tool, payload):
        why, req = super().judge(tool, payload)
        name = str(tool).lower()
        if name in self.ask and req is None and why is None:
            req = rights.request(
                "read",
                f"Allow {tool}?",
                where=self.where,
                reads=f"What the {tool} call asks for",
                evidence=[("Show input", json.dumps(payload, indent=2, default=str))],
            )
        elif name in self.free and name not in self.ask:
            req = None
        return why, req


@st.cache_data
def _load_test_prompts(_mtime: float) -> list[dict]:
    return list(json.loads(PROMPTS_PATH.read_text(encoding="utf-8")).get("prompts") or [])


def _secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


test_prompts = _load_test_prompts(PROMPTS_PATH.stat().st_mtime)

with st.sidebar:
    with st.popover("Settings", icon=":material/tune:", width="stretch"):
        copy_on = st.toggle("Copy buttons", value=True)
        steps_on = st.toggle("Tool details", value=True, help="One card per tool call")
        page_field = st.toggle("Latest answer in the page", help="render_output_field")
        st.caption("Runs without asking")
        free = st.pills(
            "Runs without asking",
            COCO_TOOLS,
            selection_mode="multi",
            default=["Read", "Glob", "Grep"],
            label_visibility="collapsed",
        )
        st.caption("Asks")
        ask = st.pills(
            "Asks",
            COCO_TOOLS,
            selection_mode="multi",
            default=["Edit", "Write", "Bash"],
            label_visibility="collapsed",
        )

connection = _secret("snowflake_connection")
coco = st_coco.ask_coco(
    ".",
    policy=PillPolicy(".", free or [], ask or [], sql=True, lookups=True, standing=True),
    features=st_coco.Features(
        copy=copy_on,
        steps=steps_on,
        planning=True,
        display=("latest", "shorten", "raw"),
        session_details=True,
    ),
    options=st_coco.CocoOptions(connection=connection) if connection else None,
)

with st.sidebar:
    if st.toggle("Test prompts", key="coco_show_test_prompts"):
        category = st.selectbox(
            "Category",
            ["all", *sorted({str(p.get("category") or "other") for p in test_prompts})],
            label_visibility="collapsed",
        )
        shown = {
            f"{p['id']} — {p.get('title') or p['id']}": p
            for p in test_prompts
            if category == "all" or p.get("category") == category
        }
        choice = st.selectbox("Prompt", list(shown) or ["(none)"], label_visibility="collapsed")
        picked = shown.get(choice)
        if picked and st.button("Send", type="primary", width="stretch"):
            coco.ask(picked.get("title") or picked["id"], picked["prompt"], key=picked["id"])

st.write("Open CoCo with the launcher at the bottom right and ask about this folder.")
if page_field:
    st_coco.render_output_field(coco)
