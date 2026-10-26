"""CoCo-free Streamlit harness for the managed window (``make e2e``).

The window on the managed agent (managed.py) with a scripted stand-in for Snowflake's client and
for the connector: no login, no network. The stand-in answers what it is told, so a test can read
what reached the agent: "run a risky command" asks for a Bash call, any other message is echoed
with the files the agent was told about. Attachments go to a fake upload stage; the audit log is a
file next to the working folder.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.managed import ManagedAgent, ManagedOptions
from streamlit_coco.testing.managed_fake import (
    FakeClient,
    FakeConnection,
    FakeConversation,
    FakeTurn,
    text,
    tool_use,
)

st.set_page_config(page_title="Sales explorer", layout="wide")
st.title("Sales explorer")
st.caption("A page with Ask CoCo on the managed agent, working in a Snowflake sandbox.")

WORKSPACE = Path(os.environ.get("COCO_E2E_WORKSPACE", "e2e_workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
AUDIT = WORKSPACE.parent / "managed-audit.jsonl"
OPTIONS = [
    "Allow this command",
    "Allow all bash for this session",
    "Deny",
]


class Echo(FakeConversation):
    def send(self, prompt: str) -> FakeTurn:
        self._client.sent.append(("send", prompt))
        asked = prompt.split("User message:\n")[-1]
        if "run a risky command" in asked:
            events = [
                tool_use("t1", "Bash", {"command": "rm -rf /workspace/build"}, options=OPTIONS),
                {"event": "response", "status": "paused"},
            ]
        else:
            files = [line[2:] for line in asked.splitlines() if line.startswith("- /uploads/")]
            events = text("Echo: " + asked.splitlines()[0] + (f" Files: {files}" if files else ""))
        return FakeTurn(events, self._client.cancelled)

    def send_permission_decisions(self, decisions: list) -> FakeTurn:
        self._client.sent.append(("decisions", list(decisions)))
        allowed = decisions and decisions[0][1] == "Allow this command"
        ran = {
            "event": "response.tool_result",
            "tool_use_id": decisions[0][0],
            "status": "success",
            "content": [{"type": "text", "text": "done"}],
        }
        events = [ran, *text("The command ran.")] if allowed else text("Not run.")
        return FakeTurn(events, self._client.cancelled)


class EchoClient(FakeClient):
    def __init__(self) -> None:
        super().__init__([])
        self.conversations.create = lambda **kw: Echo(self)


options = ManagedOptions(
    account="fake", token="fake", upload_stage="DB.E2E.FILES", connection=FakeConnection()
)
st_coco.ask_coco(
    WORKSPACE,
    agent=lambda emit: ManagedAgent(emit, options, client_factory=EchoClient),
    connection="fake",
    policy=st_coco.policy.FolderPolicy(
        WORKSPACE, words=st_coco.SANDBOX_WORDS, where=st_coco.SANDBOX_WHERE
    ),
    features=st_coco.Features(attachments=st_coco.Attachments(accept=[".csv"])),
    audit=st_coco.AuditLog(AUDIT, who="e2e"),
)
