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


def _ro(text: str) -> str:
    return f"{text} Do not write or edit files."


# The suggested questions of each screen (the window shows them in an empty conversation).
PAGE_PROMPTS = {
    "Welcome": [
        ("List the files", "List the files in this workspace and briefly describe each."),
        (
            "Summarize sources",
            "If there are Tableau or Power BI extracts here, summarize the tables and which "
            "workbooks they come from.",
        ),
        (
            "Find collisions",
            "Look for table or column names that appear in more than one source with "
            "different shapes. List the collisions.",
        ),
    ],
    "1 · Load": [
        ("What did I load?", "List the BI files in this workspace: type, name and size."),
        (
            "Can you read them?",
            "Say which of the loaded Tableau and Power BI files you can read, and which look "
            "damaged or unsupported.",
        ),
        (
            "Which dashboards?",
            "List the dashboards or report pages in the loaded files, one line each.",
        ),
    ],
    "2 · Estate map": [
        (
            "Explain the estate map",
            "Read estate_map.json in out/ if it exists and explain how the sources relate.",
        ),
        (
            "Which tables clash?",
            "Read estate_map.json in out/ if it exists and list the tables that appear in more "
            "than one source with a different shape.",
        ),
        (
            "What is missing?",
            "From estate_map.json in out/ if it exists, say which sources or tables are not "
            "mapped yet.",
        ),
    ],
    "3 · KPIs": [
        (
            "Explain a KPI",
            "Read kpi_inventory.json in out/ if it exists and pick the KPI with the most "
            "definitions. Explain how its definitions differ.",
        ),
        (
            "KPIs that disagree",
            "Read kpi_inventory.json in out/ if it exists and list the KPIs whose definitions "
            "disagree across sources.",
        ),
        (
            "Which are risky?",
            "Read kpi_inventory.json in out/ if it exists and flag the KPIs a semantic view "
            "should not guess.",
        ),
    ],
    "4 · Access rules": [
        (
            "Explain the rules",
            "Read access_rules.json in out/ if it exists and explain who can see which rows.",
        ),
        (
            "Where do they differ?",
            "Read access_rules.json in out/ if it exists and list the branches present in one "
            "source and absent from another.",
        ),
        (
            "What is the risk?",
            "Read access_rules.json in out/ if it exists and say which difference exposes "
            "the most data.",
        ),
    ],
    "5 · Arbitration": [
        (
            "Summarize the choices",
            "Read decisions.json in out/ if it exists and summarize what was decided and "
            "what is still open.",
        ),
        (
            "Challenge my decisions",
            "Read decisions.json and access_rules.json in out/ if they exist and point out a "
            "decision that could be wrong.",
        ),
        (
            "What is left?",
            "Which differences in access_rules.json and kpi_inventory.json (in out/) have no "
            "decision yet?",
        ),
    ],
    "6 · Generate": [
        (
            "Review the semantic view",
            "Read the semantic_view files in out/ if they exist and check them against "
            "decisions.json.",
        ),
        (
            "Explain the policy",
            "Read row_access_policy.sql in out/ if it exists and explain it in plain words.",
        ),
        (
            "What will be written?",
            "List the files that will be written to out/ and what each one is for.",
        ),
    ],
}


def page_prompts(page: str) -> list[dict[str, str]]:
    return [
        {"title": title, "text": _ro(text)}
        for title, text in PAGE_PROMPTS.get(page, PAGE_PROMPTS["Welcome"])
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


def mount_window(page: str, *, split: bool = False):
    """Ask CoCo, set up for the current job kind (its folder, rights and schema), with the
    suggested questions of the screen `page`."""
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
        prompts=page_prompts(page),
        labels={"window.field.placeholder": "Ask about the BI sources…"},
        options=options,
        connection=options.connection,
        split=split,
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
