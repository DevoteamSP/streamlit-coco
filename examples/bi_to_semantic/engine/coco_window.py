"""Ask CoCo for BI → Semantic: the window, its rights per job kind, and the results handed back."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine import state
from engine.access_parse import merge_access_payloads
from engine.coco_jobs import (
    PENDING_KEY,
    SESSION_KIND_KEY,
    STRUCTURED,
    WRITES,
    current_kind,
    cwd_for,
)
from engine.extract import accept_structured, load_schema
from engine.paths import OUT_DIR
from engine.ui_common import optional_secret
from streamlit_coco import CocoOptions, policy
from streamlit_coco.features import Features
from streamlit_coco.window import ask_coco

PROMPTS = [
    {
        "title": "List the files",
        "text": (
            "List the files in this workspace and briefly describe each. "
            "Do not write or edit files."
        ),
    },
    {
        "title": "Summarize sources",
        "text": (
            "If there are Tableau or Power BI extracts here, summarize the tables "
            "and which workbooks they come from. Do not write or edit files."
        ),
    },
    {
        "title": "Find collisions",
        "text": (
            "Look for table or column names that appear in more than one source "
            "with different shapes. List the collisions. Do not write or edit files."
        ),
    },
]
SCHEMAS = {
    "estate": "estate_map.schema.json",
    "kpi": "kpi_inventory.schema.json",
    "access": "access_rules.schema.json",
}


class BiPolicy(policy.FolderPolicy):
    """A job that answers with data writes nothing: Write and Edit are refused."""

    def __init__(self, folder, *, writes: bool) -> None:
        super().__init__(folder, also_read=[OUT_DIR])  # out/: the earlier steps' JSON
        self.writes = writes

    def judge(self, tool, payload):
        name = str(tool).lower()
        if name in ("write", "edit") and not self.writes:
            return "This step only reads the sources and answers with data.", None
        return super().judge(tool, payload)


def mount_window(connection: str | None = None, on_rail=None):
    """The floating window, set up for the current job kind: its folder, rights and schema."""
    kind = current_kind()
    cwd = cwd_for(kind)
    cwd.mkdir(parents=True, exist_ok=True)
    # Read when a session starts; a job of another kind starts a new one (`dispatch_pending`).
    options = st.session_state.setdefault("tts_coco_options", CocoOptions(max_turns=40))
    options.connection = optional_secret("snowflake_connection")
    options.output_schema = load_schema(SCHEMAS[kind]) if kind in STRUCTURED else None
    return ask_coco(
        cwd,
        policy=BiPolicy(cwd, writes=kind in WRITES),
        features=Features(copy=False, display=("latest", "shorten")),
        prompts=PROMPTS,
        labels={"window.field.placeholder": "Ask about the BI sources…"},
        options=options,
        connection=connection or options.connection,
        on_rail=on_rail,
    )


def dispatch_pending(coco) -> None:
    """Send the job a screen queued (`coco.ask` reruns the page)."""
    job = st.session_state.pop(PENDING_KEY, None)
    if not job:
        return
    kind, before = job["kind"], st.session_state.get(SESSION_KIND_KEY, "chat")
    st.session_state[SESSION_KIND_KEY] = kind
    # Another folder already started a new conversation (`ask_coco`); the same folder with
    # another schema needs one.
    if kind != before and cwd_for(kind) == cwd_for(before):
        coco.new()
    coco.ask(job["label"], job["prompt"], key=kind)


def _apply_structured_output(coco, kind: str, data: dict[str, Any]) -> None:
    schema = load_schema(SCHEMAS[kind])
    on_ok = {"estate": state.set_estate, "kpi": state.set_metrics, "access": state.set_access}[kind]
    if kind == "access":
        existing = state.get_access()

        def on_ok(payload: dict[str, Any]) -> None:
            state.set_access(merge_access_payloads(existing, payload))

    ok, errors = accept_structured(data, schema=schema, on_ok=on_ok)
    if ok:
        st.toast(f"Stored · {kind}")
    else:
        coco.notice(f"The {kind} payload failed schema validation: " + "; ".join(errors[:3]))
    st.rerun()


def collect_results(coco) -> None:
    """Hand a finished data job to the page: store it, or say in the thread that it failed."""
    for kind in STRUCTURED:
        found = coco.result(kind)
        if found is None:
            continue
        data = found.get("data")
        if isinstance(data, dict):
            _apply_structured_output(coco, kind, data)
        else:
            coco.notice(f"The {kind} job finished without structured output. Retry it.")
            st.rerun()
