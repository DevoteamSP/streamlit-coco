"""Basic CoCo chat example with native Streamlit input and output."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo Chat", layout="wide")
st.title("CoCo for Streamlit")

COCO_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "SQL"]
DEFAULT_AUTO_ALLOWED = ["Read", "Glob", "Grep"]
DEFAULT_REQUIRE_APPROVAL = ["Edit", "Write", "Bash"]

SESSION_KEY = "copilot"
GATE_KEY = "coco_started"
AUTO_KEY = "coco_auto_allowed_tools"
APPROVAL_KEY = "coco_require_approval_tools"
PLAN_KEY = "coco_plan_mode"
PROMPTS_PATH = Path(__file__).resolve().parent / "testdata" / "prompts.json"


def _optional_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def _tool_selection(key: str, default: list[str]) -> list[str]:
    value = st.session_state.get(key, default)
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    return list(value)


@st.cache_data
def _load_test_prompts(_mtime: float) -> list[dict]:
    payload = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    return list(payload.get("prompts") or [])


connection = _optional_secret("snowflake_connection")
auto_allowed = _tool_selection(AUTO_KEY, DEFAULT_AUTO_ALLOWED)
require_approval = _tool_selection(APPROVAL_KEY, DEFAULT_REQUIRE_APPROVAL)
plan_mode = bool(st.session_state.get(PLAN_KEY, False))

opts = st_coco.CocoOptions(
    connection=connection,
    cwd=".",
    allowed_tools=list(dict.fromkeys([*auto_allowed, *require_approval])),
    require_approval_for=require_approval,
    permission_mode="plan" if plan_mode else "default",
)
env = st_coco.check_environment(connection=connection)

if not st_coco.render_start_gate(
    opts,
    session_key=SESSION_KEY,
    gate_key=GATE_KEY,
    env=env,
):
    st.stop()

test_prompts = _load_test_prompts(PROMPTS_PATH.stat().st_mtime)
categories = sorted({str(item.get("category") or "other") for item in test_prompts})

session = st_coco.get_or_create_session(opts, key=SESSION_KEY)

with st.sidebar:
    ready = session.is_ready
    status = session.status.value
    st.markdown(
        f":{'green' if ready else 'orange'}-badge[{status}] "
        f":{'green' if ready else 'gray'}-badge[ready={str(ready).lower()}]"
    )

    with st.popover(
        "Settings",
        icon=":material/tune:",
        help="Display and tool permissions",
        width="stretch",
    ):
        st.caption("Display")
        output_mode = (
            st.segmented_control(
                "Output mode",
                options=["transcript", "field"],
                format_func=lambda value: "Transcript" if value == "transcript" else "Field",
                default="transcript",
                key="coco_output_mode",
                label_visibility="collapsed",
            )
            or "transcript"
        )
        debug_on = st.toggle(
            "CoCo debug mode",
            key="coco_debug",
            help="Show collapsed Raw tool payload under tool cards / approvals",
        )
        plan_on = st.toggle(
            "Plan mode",
            key=PLAN_KEY,
            help="Sets permission_mode=plan so ExitPlanMode approvals can be tested",
        )

        st.caption("Auto-allowed")
        auto_ui = (
            st.pills(
                "Auto-allowed tools",
                options=COCO_TOOLS,
                selection_mode="multi",
                default=DEFAULT_AUTO_ALLOWED,
                key=AUTO_KEY,
                label_visibility="collapsed",
            )
            or []
        )

        st.caption("Requires approval")
        approval_ui = (
            st.pills(
                "Require approval tools",
                options=COCO_TOOLS,
                selection_mode="multi",
                default=DEFAULT_REQUIRE_APPROVAL,
                key=APPROVAL_KEY,
                label_visibility="collapsed",
            )
            or []
        )

        with st.container(horizontal=True):
            if st.button("Reset session", type="primary", width="stretch"):
                st_coco.reset_session(opts, session_key=SESSION_KEY, warm_up=True)
                st.rerun()
            if st.button("Back to start", width="stretch"):
                st_coco.stop_session(session_key=SESSION_KEY, gate_key=GATE_KEY)
                st.rerun()

    mode_label = "Transcript" if output_mode == "transcript" else "Field"
    summary = [f":blue-badge[{mode_label}]"]
    if debug_on:
        summary.append(":orange-badge[debug]")
    if plan_on:
        summary.append(":violet-badge[plan]")
    st.markdown(" ".join(summary))
    st.caption(f"Auto · {', '.join(auto_ui) or '—'}")
    st.caption(f"Approve · {', '.join(approval_ui) or '—'}")

    if st.toggle("Test prompts", key="coco_show_test_prompts"):
        category = st.selectbox(
            "Category",
            options=["all", *categories],
            key="coco_test_prompt_category",
            label_visibility="collapsed",
        )
        filtered = [
            item for item in test_prompts if category == "all" or item.get("category") == category
        ]
        labels = {f"{item['id']} — {item.get('title') or item['id']}": item for item in filtered}
        selected_label = st.selectbox(
            "Prompt",
            options=list(labels.keys()) or ["(none)"],
            key="coco_test_prompt_id",
            label_visibility="collapsed",
        )
        selected = labels.get(selected_label)
        if selected and st.button(
            "Send",
            type="primary",
            width="stretch",
            key="coco_send_test_prompt",
        ):
            st.session_state["_coco_pending_test_prompt"] = selected["prompt"]

output_label = "CoCo transcript" if output_mode == "transcript" else "CoCo output"

# Apply sidebar "Send test prompt" after the session exists.
pending_test = st.session_state.pop("_coco_pending_test_prompt", None)
if pending_test:
    st_coco.send_prompt(session, pending_test)

st_coco.panel(
    session=session,
    output_label=output_label,
    output_mode=output_mode,
    show_tool_details=output_mode == "transcript",
    show_status=True,
    warm_up=True,
    run_every=0.25,
)

st_coco.chat_input_bar(
    session,
    placeholder="Ask CoCo about your data…",
)

with st.sidebar:
    if session.init_info:
        st.caption("Init")
        st.json(session.init_info)
    st_coco.render_environment_status(env, stacked=True)
