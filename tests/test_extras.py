"""Ask CoCo, data, files, requests of the page, display options (extras.py): temp folders, a fake
agent."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from coco_fixture import ConversationCase

from streamlit_coco import extras as ex
from streamlit_coco.conversation import LABELS
from streamlit_coco.features import Attachments, Features
from streamlit_coco.testing import fixtures as fx


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


class Case(ConversationCase):
    def kind(self, kind):
        return [i for i in self.view()["thread"] if i["kind"] == kind]

    def answer(self):
        self.tell({"t": "result", "text": "Done.", "error": False})
        return self.kind("answer")[0]


class DataTest(Case):
    def setUp(self):
        super().setUp()
        self.connect()
        self.send("who")

    def rows(self, n):
        return {
            "columns": [{"name": "C", "kind": "text"}, "N"],
            "rows": [[f"c{i}", i] for i in range(n)],
            "total": n,
        }

    def test_a_query_result_becomes_a_step_block_with_its_count(self) -> None:
        self.tell(
            {"t": "tool_use", "id": "s1", "name": "sql_execute", "input": {"sql": "select 1"}},
            {
                "t": "tool_result",
                "id": "s1",
                "content": json.dumps([{"A": "x", "B": 1}, {"A": "y", "B": 2}]),
            },
        )
        step = self.kind("steps")[0]["items"][0]
        fx.assert_same_shape(
            self, step["blocks"], fx.VIEWS["f63_query_result"]["thread"][1]["items"][0]["blocks"]
        )
        self.assertEqual(
            (step["note"], step["result"], step["blocks"][0]["tables"][0]["columns"][1]["kind"]),
            ("2 rows", "", "number"),
        )

    def test_one_row_is_said_in_the_singular_and_a_host_can_say_it_otherwise(self) -> None:
        self.conv.labels["rows_one"] = "{n} ligne"
        self.tell(
            {"t": "tool_use", "id": "s1", "name": "sql_execute", "input": {}},
            {
                "t": "tool_result",
                "id": "s1",
                "content": "",
                "data": {"columns": ["A"], "rows": [["x"]]},
            },
        )
        self.assertEqual(self.kind("steps")[0]["items"][0]["note"], "1 ligne")

    def test_no_rows_says_so_on_the_step_and_draws_no_table(self) -> None:
        self.tell(
            {"t": "tool_use", "id": "s1", "name": "sql_execute", "input": {}},
            {"t": "tool_result", "id": "s1", "content": "[]", "data": []},
        )
        step = self.kind("steps")[0]["items"][0]
        self.assertEqual((step["note"], "blocks" in step), (LABELS["rows_none"], False))

    def test_a_structured_answer_is_one_data_block_and_a_table_alone_has_no_json(self) -> None:
        self.tell(
            {"t": "text", "text": "Here."},
            {
                "t": "structured",
                "data": {
                    "title": "Weekly status",
                    "week": "W41",
                    "risks": [{"ID": "R1", "OWNER": "Cam"}],
                },
            },
        )
        answer = self.answer()
        fx.assert_same_shape(
            self, answer["blocks"], fx.VIEWS["f67_data_answer"]["thread"][1]["blocks"]
        )
        self.assertEqual(answer["blocks"][0]["fields"], [{"label": "week", "value": "W41"}])
        self.assertIsNone(ex._blocks(self.conv, self.rows(3))[0]["json"])

    def test_a_table_keeps_200_rows_and_says_the_total(self) -> None:
        table = ex._blocks(self.conv, self.rows(1240))[0]["tables"][0]
        self.assertEqual((len(table["rows"]), table["total"]), (200, 1240))
        table = ex._blocks(self.conv, {**self.rows(500), "total": 1240})[0]["tables"][0]
        self.assertEqual((len(table["rows"]), table["total"]), (200, 1240))

    def test_only_the_three_latest_tables_keep_their_rows(self) -> None:
        blocks = [ex._blocks(self.conv, self.rows(50))[0] for _ in range(5)]
        self.assertEqual([len(b["tables"][0]["rows"]) for b in blocks], [5, 5, 50, 50, 50])
        self.assertEqual(blocks[0]["tables"][0]["total"], 50)

    def test_nothing_is_added_without_data(self) -> None:
        self.tell({"t": "text", "text": "plain"})
        self.assertNotIn("blocks", self.answer())


class FilesTest(Case):
    def setUp(self):
        super().setUp()
        self.connect()

    def files(self, name="a.csv", data=b"x,y\n1,2\n"):
        return [{"name": name, "size": len(data), "data": b64(data)}]

    def saved(self):
        return sorted(
            p.relative_to(self.folder).as_posix()
            for p in (self.folder / "_coco_uploads").rglob("*")
            if p.is_file()
        )

    def attach(self, text, **kw):
        self.send(text, action={"files": kw["files"]})

    def test_a_file_is_saved_in_the_working_folder_and_named_to_the_agent(self) -> None:
        self.attach("compare", files=self.files())
        user = self.kind("user")[0]
        fx.assert_same_shape(self, user, fx.VIEWS["f73_files_sent"]["thread"][0])
        path = Path(self.conv.agent.calls[-1][1].split("- ")[-1])
        self.assertTrue(path.is_file() and path.parent.parent == self.folder / "_coco_uploads")
        self.assertEqual(user["files"], ["a.csv"])
        self.assertNotIn("_coco_uploads", user["text"])
        self.assertEqual(self.conv.run["message"]["policy"].uploads, self.folder / "_coco_uploads")

    def test_name_tricks(self) -> None:
        for raw, want in [
            ("../../x.csv", "x.csv"),
            ("C:\\Windows\\evil.csv", "evil.csv"),
            ("/etc/p.csv", "p.csv"),
            ("CON.txt", "_CON.txt"),
            ("nul", "_nul"),
            ("e\u0301te\u0301.md", "\u00e9t\u00e9.md"),
            ("a" * 400 + ".csv", "a" * 100 + ".csv"),
            ("..", "file"),
            ("a<b>.csv", "ab.csv"),
        ]:
            self.assertEqual(ex.clean_name(raw), want, raw)
        self.attach("t", files=self.files("../../../escape.csv"))
        self.assertEqual(self.saved()[0].split("/")[-1], "escape.csv")
        self.assertEqual([p.name for p in self.folder.parent.glob("escape*")], [])

    def test_a_second_file_of_the_same_name_gets_a_number_and_the_same_file_is_refused(
        self,
    ) -> None:
        self.attach("one", files=self.files(data=b"1"))
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("two", files=self.files(data=b"2"))
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("again", files=self.files(data=b"2"))
        self.assertEqual([s.split("/")[-1] for s in self.saved()], ["a (2).csv", "a.csv"])
        self.assertIn(LABELS["attach_duplicate"], self.kind("system")[0]["text"])

    def test_size_and_type_are_decided_here(self) -> None:
        self.attach("big", files=self.files(data=b"0" * (10 * 1024 * 1024 + 1)))
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("odd", files=self.files("clip.mp4"))
        self.assertEqual(self.saved(), [])
        texts = [s["text"] for s in self.kind("system")]
        self.assertIn("the limit is 10 MB", texts[0])
        self.assertIn(LABELS["attach_type"], texts[1])
        self.assertEqual(len(self.kind("user")), 2)  # the text still went

    def test_only_refused_files_and_no_text_sends_nothing(self) -> None:
        self.attach("", files=self.files("clip.mp4"))
        self.assertEqual((self.sent(), self.kind("user")), ([], []))

    def test_files_only_goes_and_bad_base64_is_refused(self) -> None:
        self.attach("", files=self.files())
        self.assertEqual(self.kind("user")[0]["text"], "")
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("", files=[{"name": "b.csv", "data": "!!!"}])
        self.assertIn(LABELS["attach_unreadable"], self.kind("system")[0]["text"])

    def test_attach_is_offered_when_ready_only(self) -> None:
        fx.assert_same_shape(self, self.view()["attach"], fx.FILES_OK)
        self.conv.act({"type": "disconnect"})
        self.assertNotIn("attach", self.view())

    def test_the_host_decides_what_is_accepted(self) -> None:
        self.conv.features = Features(
            attachments=Attachments(multi=False, accept=[".md"], max_mb=1)
        )
        self.assertEqual(
            self.view()["attach"], {"multi": False, "accept": [".md"], "max_mb": 1, "existing": []}
        )
        two = self.files("a.md") + self.files("b.md") + self.files("c.csv")
        self.attach("go", files=two)
        self.assertEqual([s.split("/")[-1] for s in self.saved()], ["a.md"])  # one file at a time
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("any", files=self.files("c.csv"))
        self.assertIn(LABELS["attach_type"], self.kind("system")[0]["text"])
        self.tell({"t": "result", "text": "ok", "error": False})
        self.attach("big", files=self.files("d.md", b"0" * (2 * 1024 * 1024)))
        self.assertIn("the limit is 1 MB", self.kind("system")[1]["text"])

    def test_no_accept_list_accepts_any_type(self) -> None:
        self.conv.features = Features(attachments=Attachments(accept=[]))
        self.attach("any", files=self.files("clip.mp4"))
        self.assertEqual([s.split("/")[-1] for s in self.saved()], ["clip.mp4"])

    def test_without_attachments_the_host_has_no_attach_and_no_file_is_taken(self) -> None:
        self.conv.features = Features()
        self.assertNotIn("attach", self.view())
        self.attach("go", files=self.files())
        self.assertEqual(self.saved() if (self.folder / "_coco_uploads").exists() else [], [])
        self.assertEqual(self.kind("user")[0]["text"], "go")


class PageTest(Case):
    def test_a_request_before_connecting_waits_then_goes_and_its_result_is_handed_once(
        self,
    ) -> None:
        self.assertTrue(
            self.conv.request_from_page(
                "Build the sales dashboard", "Full prompt text", self.ctx(), key="k"
            )
        )
        queue = self.view()["queue"]
        fx.assert_same_shape(self, queue, fx.VIEWS["f76_page_before_connect"]["queue"])
        self.assertEqual(
            (queue[0]["note"], queue[0]["full"]), (LABELS["queue_note"], "Full prompt text")
        )
        self.connect()
        view = self.view()  # connected: the held request goes
        self.assertEqual(self.sent(), ["Full prompt text"])
        fx.assert_same_shape(
            self,
            view["thread"][0] if view["thread"] else self.view()["thread"][0],
            fx.VIEWS["f75_page_request"]["thread"][0],
        )
        self.assertEqual(self.kind("user")[0]["text"], "Build the sales dashboard")
        self.assertIsNone(self.conv.result_for("k"))  # not finished
        self.tell(
            {"t": "text", "text": "Built."},
            {"t": "structured", "data": {"rows": [["a"]], "columns": ["C"]}},
            {"t": "result", "text": "Built.", "error": False},
        )
        got = self.conv.result_for("k")
        self.assertEqual(got["text"], "Built.")
        self.assertIsNone(self.conv.result_for("k"))  # once

    def test_connected_goes_at_once_and_take_back_works_while_held(self) -> None:
        self.conv.request_from_page("L", "T", self.ctx())
        self.conv.act({"type": "unqueue", "id": self.view()["queue"][0]["id"]})
        self.assertEqual((self.view()["queue"], self.sent()), ([], []))
        self.connect()
        self.conv.request_from_page("L", "T", self.ctx())
        self.assertEqual(self.sent(), ["T"])

    def test_a_request_without_context_goes_with_the_working_folders_rights(self) -> None:
        self.connect()
        self.assertTrue(self.conv.request_from_page("L", "T"))
        self.assertIn("scope", self.conv.run["message"]["ctx"]["rights"])

    def test_a_notice_button_runs_its_function_once(self) -> None:
        hits = []
        item_id = self.conv.notice("The result is on the page.", "Show it", lambda: hits.append(1))
        fx.assert_same_shape(self, self.kind("system")[0], fx.VIEWS["f77_page_result"]["thread"][3])
        self.conv.act({"type": "system_action", "id": item_id})
        self.conv.act({"type": "system_action", "id": item_id})
        self.assertEqual(hits, [1])


class OptionsTest(Case):
    def setUp(self):
        super().setUp()
        self.connect()

    def test_options_are_listed_and_a_host_without_any_sees_none(self) -> None:
        fx.assert_same_shape(self, self.view()["options"], fx.OPTIONS)
        self.assertNotIn("hidden", self.view())
        self.conv.features = Features()
        self.assertNotIn("options", self.view())
        self.conv.features = Features(display=("latest",))
        self.assertEqual([o["id"] for o in self.view()["options"]], ["latest"])

    def test_a_display_switch_the_conversation_does_not_know_is_refused_at_the_host(self) -> None:
        with self.assertRaises(ValueError):
            Features(display=("sparkle",))

    def test_latest_only_hides_earlier_messages_and_show_earlier_brings_them_back(self) -> None:
        for n in range(3):
            self.send(f"q{n}")
            self.tell({"t": "result", "text": f"a{n}", "error": False})
        self.conv.act({"type": "set", "option": "latest", "value": True})
        view = self.view()
        self.assertEqual(
            (view["hidden"], [i["text"] for i in view["thread"] if i["kind"] == "user"]),
            (4, ["q2"]),
        )
        self.assertTrue(next(o for o in view["options"] if o["id"] == "latest")["on"])
        self.conv.act({"type": "show_earlier"})
        view = self.view()
        self.assertEqual((len(self.kind("user")), "hidden" in view), (3, False))

    def test_raw_details_reach_steps_only_when_on_and_the_agent_is_told(self) -> None:
        calls = []
        self.conv.agent.set_raw = calls.append
        self.send("a")
        raw = {"request": "{}", "result": "{}"}
        self.tell(
            {"t": "tool_use", "id": "s1", "name": "Bash", "input": {}},
            {"t": "tool_result", "id": "s1", "content": "x", "raw": raw},
        )
        self.assertNotIn("raw", self.kind("steps")[0]["items"][0])
        self.conv.act({"type": "set", "option": "raw", "value": True})
        self.tell(
            {"t": "tool_use", "id": "s2", "name": "Bash", "input": {}},
            {"t": "tool_result", "id": "s2", "content": "x", "raw": raw},
        )
        fx.assert_same_shape(
            self, self.kind("steps")[0]["items"][1]["raw"], {"request": "", "result": ""}
        )
        self.assertEqual(calls, [True])

    def test_new_conversation_resets_options_and_files_folder(self) -> None:
        self.conv.act({"type": "set", "option": "raw", "value": True})
        first = self.conv.ex["id"]
        self.conv.act({"type": "new"})
        self.assertFalse(self.conv.ex["opts"]["raw"])
        self.assertNotEqual(self.conv.ex["id"], first)

    def test_unknown_options_and_options_the_host_did_not_offer_pass_through(self) -> None:
        self.send("a")
        self.assertFalse(
            ex.act(self.conv, {"type": "set", "option": "nothing", "value": True}, None)
        )
        self.assertTrue(
            ex.act(self.conv, {"type": "set", "option": "plan", "value": True}, None)
        )  # the waits' state
        self.assertTrue(next(o for o in self.view()["options"] if o["id"] == "plan")["on"])
        self.conv.features = Features(display=("latest",))
        self.assertFalse(ex.act(self.conv, {"type": "set", "option": "raw", "value": True}, None))
        self.assertFalse(self.conv.ex["opts"]["raw"])


class SessionTest(Case):
    def test_session_facts_without_secrets_only_when_ready_and_asked_for(self) -> None:
        self.assertNotIn("session", self.view())
        self.connect()
        self.assertEqual(self.view()["session"], [{"label": "Model", "value": "auto"}])
        fx.assert_same_shape(self, self.view()["session"], fx.FACTS)
        self.conv.features = Features()
        self.assertNotIn("session", self.view())

    def test_connecting_not_connected_and_profile_files(self) -> None:
        self.conv.agent.files = [
            {"file": "connections.toml", "profiles": ["dev"]},
            {"file": "config.toml", "profiles": ["old"]},
        ]
        view = self.view()
        fx.assert_same_shape(
            self, view["profile_files"], fx.VIEWS["f84_profile_files"]["profile_files"]
        )
        self.assertNotIn("problem", view)
        self.conv.error = "250001 (08001): Incorrect username or password was specified."
        self.assertEqual(self.view()["problem"], LABELS["problem_signin"])
        self.conv.error = "connection timed out"
        self.conv.ex["files"] = (0, None)
        self.assertEqual(self.view()["problem"], LABELS["problem_network"])
        self.conv.act({"type": "connect", "profile": "dev"})
        view = self.view()
        self.assertEqual(
            (view["type_ahead"], "profile_files" in view, "problem" in view), (True, False, False)
        )

    def test_typed_ahead_waits_for_the_connection(self) -> None:
        self.conv.act({"type": "connect", "profile": "dev"})
        self.send("early")
        self.assertEqual(self.view()["queue"][0]["note"], LABELS["queue_note"])
        self.tell({"t": "connected"})
        view = self.view()  # the very view that sees the connection already says the message went
        self.assertEqual(
            (
                view["status"],
                view["queue"],
                [i["text"] for i in view["thread"] if i["kind"] == "user"],
            ),
            ("working", [], ["early"]),
        )
        self.assertEqual(self.sent(), ["early"])

    def test_a_view_without_use_has_none_of_the_keys(self) -> None:
        self.conv.features = Features(queue=False)
        self.connect()
        self.assertEqual(
            set(self.view()) & {"hidden", "session", "attach", "type_ahead", "problem", "options"},
            set(),
        )


class WiringTest(Case):
    """What the parts left for each other: connect with a file, the options merged, one id space,
    system actions."""

    def setUp(self):
        super().setUp()
        self.calls = []
        agent = self.conv.agent
        agent.connect = lambda profile, cwd, **kw: self.calls.append(("connect", profile, kw))
        agent.set_raw = lambda on: self.calls.append(("raw", on))
        agent.set_planning = lambda on: self.calls.append(("planning", on))

    def test_connect_passes_the_chosen_file_and_a_restart_keeps_it(self) -> None:
        self.conv.act({"type": "connect", "profile": "old", "file": "config.toml"})
        self.tell({"t": "connected"})
        self.assertEqual(self.calls, [("connect", "old", {"file": "config.toml"})])
        self.conv.act({"type": "new"})  # a fresh agent of the same profile and file
        self.assertEqual(self.conv.file, "config.toml")
        self.conv.act({"type": "disconnect"})
        self.conv.agent.connect = lambda profile, cwd, **kw: self.calls.append(
            ("connect", profile, kw)
        )
        self.conv.act({"type": "connect", "profile": "dev"})
        self.assertEqual(self.calls[-1], ("connect", "dev", {}))

    def test_plan_first_leads_one_merged_list_and_raw_reaches_the_agent(self) -> None:
        self.connect()
        self.assertEqual(
            [o["id"] for o in self.view()["options"]], ["plan", "latest", "shorten", "raw"]
        )
        self.conv.act({"type": "set", "option": "plan", "value": True})
        self.conv.act({"type": "set", "option": "raw", "value": True})
        self.assertEqual(
            [c for c in self.calls if c[0] != "connect"], [("planning", True), ("raw", True)]
        )
        self.assertEqual([o["on"] for o in self.view()["options"]], [True, False, False, True])
        self.assertEqual(self.view()["mode"], {"planning": True, "can_carry_out": False})
        self.conv.act({"type": "set", "option": "plan", "value": False})
        self.assertNotIn("mode", self.view())

    def test_every_id_of_a_conversation_is_its_own(self) -> None:
        self.connect()
        self.conv.add_drafts([("To Lea", "Hello")])
        self.send("one")
        self.tell(
            {"t": "tool_use", "id": "s1", "name": "sql_execute", "input": {}},
            {
                "t": "tool_result",
                "id": "s1",
                "content": "",
                "data": {"columns": ["A"], "rows": [["x"]]},
            },
            {"t": "structured", "data": {"week": "W41", "risks": [{"ID": "R1"}]}},
            {"t": "result", "text": "Done.", "error": False},
        )
        self.conv.notice("On the page.", "Show it")
        self.conv.request_from_page("L", "T", self.ctx())
        view = self.view()
        ids = [i["id"] for i in view["thread"] if "id" in i]
        for item in view["thread"]:
            ids += [x["id"] for x in item.get("items", []) if "id" in x] + [
                t["id"] for b in item.get("blocks", []) for t in b["tables"]
            ]
            ids += [b["id"] for b in item.get("blocks", [])]
            ids += [
                t["id"]
                for x in item.get("items", [])
                for b in x.get("blocks", [])
                for t in b["tables"]
            ]
            ids += [b["id"] for x in item.get("items", []) for b in x.get("blocks", [])]
        self.assertGreater(len(ids), 8)
        self.assertEqual(len(ids), len(set(ids)))

    def test_a_system_action_goes_to_whoever_owns_the_line(self) -> None:
        self.connect()
        hits = []
        mine = self.conv.notice("On the page.", "Show it", lambda: hits.append("page"))
        self.send("go")
        self.tell({"t": "granted", "id": "commands", "text": "runs any command"})
        ask_again = next(i["id"] for i in self.kind("system") if i["id"] != mine)
        self.conv.act({"type": "system_action", "id": mine})
        self.assertEqual(
            (hits, [g["id"] for g in self.view().get("granted", [])]), (["page"], ["commands"])
        )
        self.conv.act({"type": "system_action", "id": ask_again})
        self.assertEqual(self.view().get("granted"), None)

    def test_the_policy_reads_where_the_files_are_saved(self) -> None:
        self.connect()
        self.attach_one()
        policy = self.conv.run["message"]["policy"]
        path = self.conv.agent.calls[-1][1].split("- ")[-1]
        self.assertEqual(policy.uploads, Path(self.folder) / "_coco_uploads")
        self.assertEqual(
            policy.judge("Read", {"file_path": path}), (None, None)
        )  # attached: read without asking
        self.assertIsNotNone(
            policy.judge("Read", {"file_path": str(self.folder.parent / "outside.md")})[1]
        )

    def attach_one(self):
        self.send("compare", action={"files": [{"name": "a.csv", "data": b64(b"x,y")}]})
