"""Shared helpers of the Ask CoCo conversation tests: a working folder, a fake agent, a test
case."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from streamlit_coco.conversation import Conversation
from streamlit_coco.features import Features
from streamlit_coco.policy import FolderPolicy

FILES = {
    "README.md": "# Alpha\n",
    ".env": "KEY=1\n",
    "notes/spec.md": "# Spec\nTODO: scope\n",
    "src/load.sql": "select 1;\n",
}


def make_folder(tmp: Path) -> Path:
    """A working folder with a few files (its path holds a space); `outside.md` sits next to it."""
    folder = tmp / "My work" / "alpha"
    for name, text in FILES.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (folder.parent / "beta").mkdir()
    (folder.parent / "beta" / "x.md").write_text("# Beta\n", encoding="utf-8")
    (tmp / "My work" / "outside.md").write_text("# Outside\n", encoding="utf-8")
    return folder


class FakeAgent:
    """Records what the conversation asks of an agent; the optional calls are recorded as they
    come."""

    OPTIONAL = ("answer", "skip", "approve_plan", "decline_plan", "set_planning", "revoke")

    def __init__(self, emit) -> None:
        self.emit, self.calls, self.missing, self.cwds = emit, [], None, []
        self.facts = [{"label": "Model", "value": "auto"}, {"label": "API token", "value": "x"}]
        self.files = [{"file": "connections.toml", "profiles": ["dev"]}]

    def __getattr__(self, name):
        if name not in self.OPTIONAL:
            raise AttributeError(name)
        return lambda *args: self.calls.append((name, *args))

    def setup(self):
        return self.missing

    def profiles(self):
        return ["dev", "prod"]

    def connect(self, profile, cwd, **kw):
        self.calls.append(("connect", profile))
        self.cwds.append(cwd)

    def send(self, text, ctx, policy):
        self.calls.append(("send", text))

    def decide(self, request_id, allow, standing=False):
        self.calls.append(("decide", request_id, allow, standing))

    def stop(self):
        self.calls.append(("stop",))

    def close(self):
        self.calls.append(("close",))

    def session_facts(self):
        return self.facts

    def connection_files(self):
        return self.files


class ConversationCase(unittest.TestCase):
    """A conversation on a fake agent. `features` and `policy` are the host's choices."""

    features = Features.all()
    standing = False

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.folder = make_folder(Path(self._tmp.name))
        self.changed: list[list[str]] = []
        self.conv = self.make()
        self.sent = lambda: [c[1] for c in self.conv.agent.calls if c[0] == "send"]

    def make(self, **kw) -> Conversation:
        kw.setdefault("features", self.features)
        kw.setdefault("policy", FolderPolicy(self.folder, standing=self.standing))
        kw.setdefault("agent", FakeAgent)
        kw.setdefault("on_files_changed", self.changed.append)
        return Conversation(self.folder, **kw)

    # helpers
    def ctx(self, scope="alpha", **more):
        return (
            {"scope": {"name": scope, "folder": str(self.folder.parent / scope)}, **more}
            if scope
            else more
        )

    def tell(self, *events) -> bool:
        for event in events:
            self.conv.inbox.put(event)
        return self.conv.drain()

    def connect(self) -> None:
        self.conv.act({"type": "connect", "profile": "dev"})
        self.tell({"t": "connected"})

    def send(self, text="Hello", scope="alpha", **kw) -> None:
        self.conv.act({"type": "send", "text": text, **kw.pop("action", {})}, self.ctx(scope, **kw))

    def view(self) -> dict:
        return self.conv.view()

    def thread(self, kind=None) -> list:
        return [i for i in self.view()["thread"] if kind is None or i["kind"] == kind]

    def steps(self) -> dict:
        """Every step of the thread by id, inside a fold or outside it."""
        out = {}
        for item in self.view()["thread"]:
            for step in item["items"] if item["kind"] == "steps" else [item]:
                if step["kind"] == "step":
                    out[step["id"]] = step
        return out

    def path(self, name: str) -> str:
        return str(self.folder / name)

    def step(self, tool_id="t1", name="Read", path="README.md", **extra):
        return {
            "t": "tool_use",
            "id": tool_id,
            "name": name,
            "input": {"file_path": self.path(path)},
            **extra,
        }

    def facts(self, tool="Write", path="notes/new.md", content="# New\n") -> dict:
        """The request the policy of the running message writes for a call."""
        payload = {"file_path": self.path(path), "content": content}
        return self.conv.run["message"]["policy"].judge(tool, payload)[1]

    def request(self, rid="r1", tool_id="t1", path="notes/new.md"):
        return {"t": "request", "id": rid, "tool_id": tool_id, "facts": self.facts("Write", path)}

    def write_call(self, tool_id="t1", path="notes/new.md"):
        return {
            "t": "tool_use",
            "id": tool_id,
            "name": "Write",
            "input": {"file_path": self.path(path), "content": "# New\n"},
        }

    def until(self, check, timeout: float = 10.0) -> dict:
        """Poll a conversation whose agent runs in a thread (the scripted agent)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.conv.drain()
            view = self.conv.view()
            if check(view):
                return view
            time.sleep(0.01)
        self.fail(
            f"timeout, last view: {self.conv.view()['status']} {self.conv.view()['thread'][-3:]}"
        )
