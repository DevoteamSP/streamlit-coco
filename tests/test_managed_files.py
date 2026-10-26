"""The managed agent and the files the user attaches: they go to a stage mounted in the sandbox.

What is proven: without a stage nothing is carried and the window says so; with one, the files are
put in this conversation's folder, the agent is told the sandbox paths (never the local ones), the
copies saved here are removed, a refusal lets the same file be attached again, files come in before
the first message only, and the folder leaves the stage when the conversation ends. A connection
stands in for Snowflake: no login.
"""

from __future__ import annotations

import base64
import unittest
from pathlib import Path
from unittest import mock

from coco_fixture import ConversationCase, FakeAgent

from streamlit_coco.backend import CarryError
from streamlit_coco.conversation import LABELS
from streamlit_coco.features import Attachments, Features
from streamlit_coco.managed import LABELS as MANAGED_LABELS
from streamlit_coco.managed import SANDBOX_WHERE, ManagedAgent, ManagedOptions
from streamlit_coco.policy import FolderPolicy
from streamlit_coco.testing.managed_fake import FakeClient, FakeConnection, text

STAGE = "DB.UP.FILES"


def agent_of(conn, stage=STAGE) -> ManagedAgent:
    options = ManagedOptions(account="a", token="t", upload_stage=stage, connection=conn)
    return ManagedAgent(lambda e: None, options, client_factory=lambda: FakeClient([text("x")]))


class SpecTest(unittest.TestCase):
    def test_the_stage_is_mounted_in_the_sandbox_and_an_option_of_the_host_stays(self) -> None:
        options = ManagedOptions(
            account="a",
            token="t",
            upload_stage=STAGE,
            upload_mount="/data",
            stage_mounts=[{"stage_name": "DB.X.Y", "is_vstage": False, "mount_path": "/y"}],
        )
        mounts = options.spec()["stage_mounts"]
        self.assertEqual(mounts[0]["mount_path"], "/y")
        self.assertEqual(
            mounts[1], {"stage_name": STAGE, "is_vstage": False, "mount_path": "/data"}
        )

    def test_without_a_stage_the_spec_has_no_mount(self) -> None:
        self.assertNotIn("stage_mounts", ManagedOptions(account="a", token="t").spec())

    def test_a_stage_name_that_is_not_a_name_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            ManagedOptions(upload_stage="DB.S.X; DROP TABLE T").spec()


class CarryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = FakeConnection()
        self.agent = agent_of(self.conn)
        self.local = Path(__file__)

    def test_a_file_is_put_in_the_folder_of_the_conversation_and_named_by_its_sandbox_path(
        self,
    ) -> None:
        paths = self.agent.carry([self.local])
        root = self.agent.upload_root
        self.assertTrue(root.startswith("/uploads/"))
        self.assertEqual(paths, [f"{root}/{self.local.name}"])
        put = self.conn.statements[0]
        self.assertIn(f"@{STAGE}/{root.rsplit('/', 1)[-1]}/", put)
        self.assertIn("AUTO_COMPRESS=FALSE OVERWRITE=FALSE", put)

    def test_a_quote_in_a_path_cannot_end_the_string(self) -> None:
        tricky = Path("/tmp/it's.csv")
        with mock.patch("pathlib.Path.resolve", return_value=tricky):
            self.agent.carry([tricky])
        self.assertIn("file:///tmp/it''s.csv", self.conn.statements[0])

    def test_no_stage_and_no_connection_carry_nothing(self) -> None:
        for agent in (agent_of(self.conn, stage=None), agent_of(None)):
            with self.assertRaises(CarryError) as caught:
                agent.carry([self.local])
            self.assertEqual(caught.exception.key, "attach_sandbox_none")
        self.assertIsNone(agent_of(self.conn, stage=None).upload_root)

    def test_after_the_first_message_nothing_is_carried(self) -> None:
        self.agent.send("hello", {}, FolderPolicy("."))
        with self.assertRaises(CarryError) as caught:
            self.agent.carry([self.local])
        self.assertEqual(caught.exception.key, "attach_sandbox_started")

    def test_a_failed_put_says_why(self) -> None:
        agent = agent_of(FakeConnection(fail="no right on the stage"))
        with self.assertRaises(CarryError) as caught:
            agent.carry([self.local])
        self.assertEqual(caught.exception.key, "attach_sandbox_failed")
        self.assertIn("no right on the stage", caught.exception.values["why"])

    def test_the_folder_leaves_the_stage_when_the_conversation_ends(self) -> None:
        self.agent.carry([self.local])
        folder = self.agent.upload_root.rsplit("/", 1)[-1]
        self.agent.close()
        self.assertEqual(self.conn.statements[-1], f"REMOVE @{STAGE}/{folder}/")
        self.assertTrue(self.conn.closed)

    def test_nothing_is_removed_when_nothing_was_put(self) -> None:
        self.agent.close()
        self.assertEqual(self.conn.statements, [])

    def test_a_new_connection_is_a_new_folder_and_the_old_one_goes(self) -> None:
        self.agent.carry([self.local])
        before = self.agent.upload_root
        self.agent.connect("p", ".")
        self.agent.close()
        self.assertNotEqual(self.agent.upload_root, before)
        self.assertTrue(any(s.startswith("REMOVE") for s in self.conn.statements))


class CarryingAgent(FakeAgent):
    """What the conversation asks of an agent that works elsewhere."""

    root = "/uploads/abc"
    refuse: str | None = None

    def carry(self, paths):
        self.calls.append(("carry", [Path(p).read_bytes() for p in paths]))
        if self.refuse:
            raise CarryError(self.refuse, why="boom")
        return [f"{self.root}/{Path(p).name}" for p in paths]

    @property
    def upload_root(self):
        return self.root


class WindowFilesTest(ConversationCase):
    features = Features(attachments=Attachments())

    def make(self, **kw):
        return super().make(agent=CarryingAgent, **kw)

    def setUp(self) -> None:
        super().setUp()
        self.connect()

    def attach(self, name="a.csv", data=b"x,y\n1,2\n"):
        spec = {"name": name, "size": len(data), "data": base64.b64encode(data).decode()}
        self.send("compare", action={"files": [spec]})

    def left_here(self):
        folder = self.folder / "_coco_uploads"
        return [p for p in folder.rglob("*") if p.is_file()] if folder.exists() else []

    def test_the_agent_is_told_the_sandbox_path_and_no_copy_stays_here(self) -> None:
        self.attach()
        prompt = self.conv.agent.calls[-1][1]
        self.assertIn("- /uploads/abc/a.csv", prompt)
        self.assertNotIn(str(self.folder), prompt)
        self.assertEqual(self.left_here(), [])
        self.assertIn(("carry", [b"x,y\n1,2\n"]), self.conv.agent.calls)

    def test_attaching_is_the_consent_to_read_the_folder_of_the_sandbox(self) -> None:
        self.attach()
        self.assertEqual(self.conv.run["message"]["policy"].uploads, Path("/uploads/abc"))

    def test_a_refused_file_is_said_and_can_be_attached_again(self) -> None:
        self.conv.agent.refuse = "attach_sandbox_started"
        self.attach()
        said = [i["text"] for i in self.thread("system")]
        self.assertTrue(any(LABELS["attach_sandbox_started"] in s for s in said), said)
        self.assertEqual(self.left_here(), [])
        self.conv.agent.refuse = None
        self.tell({"t": "result", "text": "Done.", "error": False})
        self.attach()
        self.assertIn("- /uploads/abc/a.csv", self.sent()[-1])

    def test_a_failure_of_the_upload_says_why(self) -> None:
        self.conv.agent.refuse = "attach_sandbox_failed"
        self.attach()
        self.assertTrue(any("boom" in i["text"] for i in self.thread("system")))


class WordsTest(unittest.TestCase):
    def test_the_first_screen_does_not_say_it_reads_project_files(self) -> None:
        self.assertNotIn("project files", MANAGED_LABELS["window.first.sub"])
        self.assertIn("sandbox", MANAGED_LABELS["window.first.sub"])
        self.assertEqual(ManagedAgent.labels, MANAGED_LABELS)

    def test_the_where_line_names_the_sandbox_not_a_folder(self) -> None:
        from streamlit_coco.managed import SANDBOX_WORDS

        policy = FolderPolicy("/tmp/some local folder", words=SANDBOX_WORDS, where=SANDBOX_WHERE)
        _, facts = policy.judge("Bash", {"command": "ls"})
        self.assertEqual(facts["where"], SANDBOX_WHERE)
        self.assertNotIn("some local folder", str(facts))

    def test_the_default_where_is_still_the_folders_name(self) -> None:
        _, facts = FolderPolicy("/tmp/some local folder").judge("Bash", {"command": "ls"})
        self.assertEqual(facts["where"], "some local folder")
