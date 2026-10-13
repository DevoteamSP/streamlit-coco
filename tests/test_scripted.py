"""Ask CoCo, end to end with the scripted agent: the real policy, gate and files."""

from __future__ import annotations

import base64
import os
import time
from unittest.mock import patch

from coco_fixture import ConversationCase

from streamlit_coco.conversation import LABELS, Conversation, agent_factory
from streamlit_coco.features import Features
from streamlit_coco.policy import FolderPolicy
from streamlit_coco.testing.scripted import ScriptedAgent


def scripted(emit):
    return ScriptedAgent(emit, delay=0, connect_delay=0)


class MockCase(ConversationCase):
    standing = True

    def setUp(self) -> None:
        super().setUp()
        self.conv.close()
        self.conv = self.make(
            agent=scripted,
            policy=FolderPolicy(self.folder, standing=True, sql=True),
            features=Features.all(),
        )
        self.addCleanup(self.conv.agent.close)
        self.reloads = 0
        self.conv.act({"type": "connect", "profile": "mock"})
        self.until(lambda v: v["status"] == "ready")

    def until(self, check, timeout: float = 10.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.reloads += self.conv.drain()
            view = self.conv.view()
            if check(view):
                return view
            time.sleep(0.01)
        self.fail(
            f"timeout, last view: {self.conv.view()['status']} {self.conv.view()['thread'][-3:]}"
        )

    def ask(self, text: str, scope: str | None = "alpha", **action) -> None:
        self.conv.act({"type": "send", "text": text, **action}, self.ctx(scope))

    def steps(self, view=None) -> dict:
        out = {}
        for item in (view or self.conv.view())["thread"]:
            for step in item["items"] if item["kind"] == "steps" else [item]:
                if step["kind"] == "step":
                    out[step["label"]] = step
        return out

    def answer(self, view=None) -> str:
        view = view or self.conv.view()
        return ([i["text"] for i in view["thread"] if i["kind"] == "answer"] or [""])[-1]

    def answers(self, view) -> int:
        return sum(i["kind"] == "answer" for i in view["thread"])

    def done(self, view) -> bool:
        return view["status"] == "ready" and self.answers(view) > 0


class StatesTest(MockCase):
    def test_a_plain_streamed_answer(self) -> None:
        self.ask("Hello there")
        view = self.until(self.done)
        self.assertEqual(self.answer(view), "This is a scripted answer. You wrote: Hello there")
        self.assertEqual(self.steps(view), {})

    def test_several_reads_then_an_answer(self) -> None:
        self.ask("reads please")
        view = self.until(self.done)
        steps = self.steps(view)
        self.assertEqual(list(steps)[:2], ["Read README.md", "List *.md"])
        self.assertIn("Read 2 files", steps)
        self.assertTrue(all(s["state"] == "ok" for s in steps.values()))
        self.assertIn("TODO", steps['Search for "TODO"']["result"])
        self.assertTrue([i for i in view["thread"] if i["kind"] == "steps"][0]["folded"])

    def test_a_script_that_breaks_ends_the_turn_with_a_failure(self) -> None:
        self.conv.agent._call = lambda *a, **k: 1 / 0
        self.ask("reads please")
        view = self.until(
            lambda v: v["status"] == "ready" and any(i["kind"] == "system" for i in v["thread"])
        )
        self.assertEqual(
            next(i["text"] for i in view["thread"] if i["kind"] == "system"), LABELS["failed_text"]
        )

    def test_a_command_asks_is_declined_and_is_never_run(self) -> None:
        self.ask("git status please")
        view = self.until(lambda v: v["status"] == "waiting")
        self.assertEqual(view["request"]["kind"], "change")
        self.assertIn("git status --short", str(view["request"]["evidence"]))
        self.conv.act({"type": "decline", "id": view["request"]["id"]})
        view = self.until(self.done)
        step = self.steps(view)["Run a command"]
        self.assertEqual(
            (step["state"], step["note"], step["result"]),
            ("no", LABELS["note_declined"], "Declined by the user."),
        )
        self.assertEqual(self.answer(view), "Understood, I did not run it.")

    def test_an_allowed_command_is_never_executed(self) -> None:
        self.ask("please unlisted")
        self.conv.act(
            {"type": "allow", "id": self.until(lambda v: v["status"] == "waiting")["request"]["id"]}
        )
        view = self.until(self.done)
        self.assertIn("nothing was executed", next(iter(self.steps(view).values()))["result"])

    def test_a_file_change_needing_agreement_calls_the_host_once(self) -> None:
        self.ask("write the note")
        view = self.until(lambda v: v["status"] == "waiting")
        self.assertEqual(view["request"]["kind"], "change")
        self.assertEqual(view["request"]["changes"]["file"], "coco_note.md")
        self.assertFalse(
            (self.folder / "coco_note.md").exists()
        )  # nothing happens before the answer
        self.conv.act({"type": "allow", "id": view["request"]["id"]})
        view = self.until(self.done)
        self.assertTrue(
            (self.folder / "coco_note.md").read_text(encoding="utf-8").startswith("# Note")
        )
        self.assertEqual((self.reloads, len(self.changed)), (1, 1))
        self.assertEqual(self.steps(view)["Create coco_note.md"]["state"], "ok")

    def test_an_edit_of_an_existing_file_shows_the_change(self) -> None:
        readme = self.folder / "README.md"
        self.ask("edit it")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.assertEqual(request["changes"]["file"], "README.md")
        self.assertEqual(
            [part["text"] for part in request["evidence"]], ["# Alpha", "# Alpha (reviewed)"]
        )
        self.assertEqual(
            readme.read_text(encoding="utf-8"), "# Alpha\n"
        )  # nothing happens before the answer
        self.conv.act({"type": "allow", "id": request["id"]})
        view = self.until(self.done)
        self.assertEqual(readme.read_text(encoding="utf-8"), "# Alpha (reviewed)\n")
        self.assertEqual((self.reloads, self.steps(view)["Change README.md"]["state"]), (1, "ok"))

    def test_a_declined_change_leaves_the_files_alone(self) -> None:
        self.ask("write the note")
        view = self.until(lambda v: v["status"] == "waiting")
        self.conv.act({"type": "decline", "id": view["request"]["id"]})
        self.until(self.done)
        self.assertFalse((self.folder / "coco_note.md").exists())
        self.assertEqual((self.changed, self.reloads), ([], 0))

    def test_what_is_unusual_asks_and_is_shown_as_what_it_is(self) -> None:
        for keyword, kind in [
            ("outside", "read"),
            ("forbidden", "read"),
            ("unlisted", "change"),
            ("write", "change"),
        ]:
            with self.subTest(keyword):
                self.ask(f"please {keyword}")
                request = self.until(lambda v: v["status"] == "waiting")["request"]
                self.assertEqual(request["kind"], kind)
                self.conv.act({"type": "decline", "id": request["id"]})
                view = self.until(lambda v: v["status"] == "ready" and self.answers(v) > 0)
                step = next(s for s in self.steps(view).values() if s["state"] == "no")
                self.assertEqual(
                    (step["note"], step["result"]),
                    (LABELS["note_declined"], "Declined by the user."),
                )
                self.conv.act({"type": "new"})
                self.until(lambda v: v["status"] == "ready")
        self.assertFalse((self.folder / "coco_note.md").exists())

    def test_a_failing_step(self) -> None:
        self.ask("this will fail")
        view = self.until(self.done)
        step = self.steps(view)["Read does_not_exist.md"]
        self.assertEqual((step["state"], step["note"]), ("bad", ""))  # the mark says it, no word
        self.assertTrue(step["result"])
        self.assertEqual(self.answer(view), "I could not read that file: it does not exist.")

    def test_a_slow_step_shows_its_elapsed_time_and_can_be_stopped(self) -> None:
        self.ask("slow one")
        view = self.until(lambda v: any(s["state"] == "run" for s in self.steps(v).values()))
        self.assertGreaterEqual(next(iter(self.steps(view).values()))["elapsed"], 30)
        self.conv.act({"type": "stop"})
        view = self.until(lambda v: v["status"] == "ready")
        step = next(iter(self.steps(view).values()))
        self.assertEqual((step["state"], step["note"]), ("bad", LABELS["note_stopped"]))
        self.assertIsNone(view["pill"])

    def test_stop_while_a_request_is_pending(self) -> None:
        self.ask("write the note")
        self.until(lambda v: v["status"] == "waiting")
        self.ask("queued behind the request")
        self.conv.act({"type": "stop"})
        view = self.until(lambda v: v["status"] == "ready")
        self.assertEqual(view["restore"], "queued behind the request")
        self.assertEqual([s["note"] for s in self.steps(view).values()], [LABELS["note_declined"]])

    def test_a_request_left_unanswered_expires(self) -> None:
        self.conv.agent.gate.expiry = 0.2
        self.ask("write the note")
        view = self.until(self.done)
        step = self.steps(view)["Create coco_note.md"]
        self.assertEqual((step["state"], step["note"]), ("no", LABELS["note_expired"]))
        self.assertIn("ten minutes", step["reason"])
        self.assertFalse((self.folder / "coco_note.md").exists())

    def test_a_lost_connection(self) -> None:
        self.ask("the connection is lost")
        view = self.until(lambda v: v["status"] == "lost")
        self.assertEqual(view["pill"]["label"], LABELS["pill_lost"])
        self.assertEqual(
            [i for i in view["thread"] if i["kind"] == "system"][0]["text"], LABELS["lost_text"]
        )
        self.assertEqual(next(iter(self.steps(view).values()))["note"], LABELS["note_interrupted"])

    def test_a_failure_that_can_be_retried(self) -> None:
        self.ask("retry me")
        view = self.until(lambda v: any(i["kind"] == "system" for i in v["thread"]))
        self.assertEqual([i["action"] for i in view["thread"] if i["kind"] == "system"], ["retry"])
        self.conv.act({"type": "retry"})
        view = self.until(self.done)
        self.assertEqual(self.answer(view), "This is a scripted answer. You wrote: retry me")
        self.assertEqual([i for i in view["thread"] if i["kind"] == "system"], [])

    def test_a_message_typed_meanwhile_is_queued_and_follows(self) -> None:
        self.ask("write the note")
        view = self.until(lambda v: v["status"] == "waiting")
        self.ask("and then hello")
        self.assertEqual(len(self.conv.view()["queue"]), 1)
        self.conv.act({"type": "allow", "id": view["request"]["id"]})
        view = self.until(lambda v: self.answers(v) == 2 and v["status"] == "ready")
        self.assertEqual(
            [i["text"] for i in view["thread"] if i["kind"] == "user"],
            ["write the note", "and then hello"],
        )

    def test_a_page_job_starting_with_plain_holds_no_keyword(self) -> None:
        self.ask("Plain: please write the note")
        view = self.until(self.done)
        self.assertIsNone(view["request"])
        self.assertTrue(self.answer(view).startswith("This is a scripted answer."))

    def test_the_screen_is_answered_from_what_the_message_carried(self) -> None:
        self.ask("screen", screen={"text": "Forecast 63.5", "selection": "63.5"})
        view = self.until(self.done)
        self.assertIn("Forecast 63.5", self.answer(view))
        self.assertIn("Selected: 63.5", self.answer(view))


class PlaygroundTest(MockCase):
    """The states of the design sheet, each reached by its keyword, through the real parts."""

    def waiting(self, kind: str) -> dict:
        return self.until(lambda v: v["status"] == "waiting" and v["wait"]["kind"] == kind)["wait"]

    def test_a_question_with_one_choice_is_answered_and_kept_in_the_thread(self) -> None:
        self.ask("onechoice")
        wait = self.waiting("question")
        (q,) = wait["questions"]
        self.assertEqual(
            (wait["source"], q["multi"], [o["label"] for o in q["options"]], q["other"]["label"]),
            ("coco", False, ["This week", "Last week"], "Something else"),
        )
        self.assertEqual(self.conv.view()["pill"]["kind"], "question")
        self.conv.act(
            {
                "type": "answer",
                "id": wait["id"],
                "answers": [{"id": "q1", "picked": ["This week"], "other": None}],
            }
        )
        view = self.until(self.done)
        self.assertEqual(
            [i["text"] for i in view["thread"] if i["kind"] == "user"][-1], "This week"
        )
        self.assertEqual(next(i for i in view["thread"] if i["kind"] == "asked")["note"], None)
        self.assertEqual(self.answer(view), "Understood. You answered: This week.")

    def test_a_question_can_be_skipped(self) -> None:
        self.ask("onechoice")
        self.conv.act({"type": "skip", "id": self.waiting("question")["id"]})
        view = self.until(self.done)
        self.assertEqual(
            next(i for i in view["thread"] if i["kind"] == "asked")["note"], LABELS["note_skipped"]
        )
        self.assertEqual(self.answer(view), "Understood, I go on without it.")

    def test_the_other_questions_have_their_shapes(self) -> None:
        for keyword, count, multi in [
            ("multichoice", 1, True),
            ("ownwords", 1, False),
            ("threeq", 3, False),
        ]:
            with self.subTest(keyword):
                self.ask(keyword)
                wait = self.waiting("question")
                self.assertEqual(
                    (len(wait["questions"]), wait["questions"][0]["multi"]), (count, multi)
                )
                self.conv.act({"type": "skip", "id": wait["id"]})
                self.until(self.done)
                self.conv.act({"type": "new"})
                self.until(lambda v: v["status"] == "ready")
        self.ask("ownwords")
        q = self.waiting("question")["questions"][0]
        self.assertEqual((q["options"], q["other"]["label"]), ([], "Your own words"))

    def test_a_long_form_is_answered_with_its_fields(self) -> None:
        self.ask("longform")
        wait = self.waiting("question")
        (q,) = wait["questions"]
        self.assertEqual((wait["source"], q["kind"], len(q["fields"])), ("app", "form", 6))
        self.conv.act(
            {
                "type": "answer",
                "id": wait["id"],
                "answers": [
                    {
                        "id": "q1",
                        "picked": [],
                        "other": None,
                        "fields": {"w": "Week 41", "b": "Access"},
                    }
                ],
            }
        )
        view = self.until(self.done)
        self.assertEqual(
            [i["text"] for i in view["thread"] if i["kind"] == "user"][-1],
            "Week: Week 41\nBlockers: Access",
        )

    def test_a_plan_is_approved_then_carried_out_and_declined_with_a_reason(self) -> None:
        self.ask("shortplan")
        wait = self.waiting("plan")
        self.assertEqual(wait["text"].count("\n"), 3)
        self.conv.act({"type": "approve_plan", "id": wait["id"]})
        view = self.until(self.done)
        plan = self.steps(view)[LABELS["plan_approved"]]
        self.assertEqual(
            (plan["state"], plan["tool"], plan["blocks"][0]["type"]), ("ok", None, "text")
        )
        self.assertEqual(self.answer(view), "The plan is carried out.")
        self.ask("longplan")
        wait = self.waiting("plan")
        self.assertEqual(wait["text"].count("\n"), 11)
        self.conv.act({"type": "decline_plan", "id": wait["id"], "reason": "Only the report"})
        view = self.until(
            lambda v: (
                v["status"] == "ready"
                and self.answer(v) == "Understood, I will plan again. You said: Only the report"
            )
        )
        self.assertEqual(self.steps(view)[LABELS["plan_proposed"]]["note"], LABELS["note_declined"])
        self.assertEqual(
            [i["text"] for i in view["thread"] if i["kind"] == "user"][-1], "Only the report"
        )

    def test_plan_first_answers_without_acting_and_carry_out_goes_on(self) -> None:
        self.conv.act({"type": "set", "option": "plan", "value": True})
        self.assertTrue(next(o for o in self.conv.view()["options"] if o["id"] == "plan")["on"])
        self.ask("write the note")
        view = self.until(self.done)
        self.assertEqual(
            (view["mode"], self.steps(view)), ({"planning": True, "can_carry_out": True}, {})
        )
        self.assertFalse((self.folder / "coco_note.md").exists())
        self.conv.act({"type": "carry_out"}, self.ctx())
        view = self.until(lambda v: v["status"] == "waiting")  # now it acts: the file change asks
        self.assertNotIn("mode", view)

    def test_two_things_waiting_at_once_come_in_order(self) -> None:
        self.ask("twowaits")
        view = self.until(
            lambda v: v["status"] == "waiting" and (v["wait"].get("more") or {}).get("count") == 2
        )
        self.assertEqual(
            (view["wait"]["kind"], view["wait"]["more"]),
            ("request", {"count": 2, "next": "question"}),
        )
        self.conv.act({"type": "allow", "id": view["request"]["id"]})
        wait = self.waiting("question")
        self.assertIsNone(wait["more"])
        self.conv.act({"type": "skip", "id": wait["id"]})
        self.until(self.done)

    def test_a_change_outside_the_folder_and_an_unknown_tool_ask(self) -> None:
        self.ask("outwrite")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.assertEqual(request["kind"], "change")
        self.conv.act({"type": "allow", "id": request["id"]})
        self.until(self.done)
        self.assertFalse(
            (self.folder.parent / "coco_outside_note.md").exists()
        )  # said, never written
        self.ask("unknowntool")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.assertEqual(request["kind"], "change")
        self.assertIn("mystery", request["question"])
        self.conv.act({"type": "decline", "id": request["id"]})
        self.until(self.done)

    def test_sql_results_are_tables_and_a_standing_permission_covers_the_next_query(self) -> None:
        self.ask("table24")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.assertEqual(request["standing"]["id"], "queries")
        self.conv.act({"type": "allow", "id": request["id"], "standing": True})
        view = self.until(self.done)
        (table,) = next(iter(self.steps(view).values()))["blocks"][0]["tables"]
        self.assertEqual(
            (len(table["rows"]), table["total"], table["columns"][0]),
            (24, 24, {"name": "CUSTOMER_ID", "kind": "number"}),
        )
        self.assertEqual([g["id"] for g in view["granted"]], ["queries"])
        self.ask("table1240")  # covered: not asked
        view = self.until(lambda v: v["status"] == "ready" and self.answers(v) == 2)
        step = list(self.steps(view).values())[-1]
        self.assertTrue(step["standing"])
        (table,) = step["blocks"][0]["tables"]
        self.assertEqual((len(table["rows"]), table["total"]), (200, 1240))
        ids = [
            t["id"]
            for i in view["thread"]
            for s in (i["items"] if i["kind"] == "steps" else [i])
            for b in s.get("blocks", [])
            for t in b["tables"]
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.conv.act({"type": "revoke", "id": "queries"})  # taken back: asked again
        self.ask("norows")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.conv.act({"type": "allow", "id": request["id"]})
        view = self.until(lambda v: v["status"] == "ready" and self.answers(v) == 3)
        self.assertEqual(list(self.steps(view).values())[-1]["note"], LABELS["rows_none"])

    def test_a_new_conversation_starts_without_grants(self) -> None:
        self.ask("status")
        request = self.until(lambda v: v["status"] == "waiting")["request"]
        self.conv.act({"type": "allow", "id": request["id"], "standing": True})
        view = self.until(lambda v: v["status"] == "ready" and v.get("granted"))
        self.assertTrue(view["granted"])
        self.conv.act({"type": "new"})
        view = self.until(lambda v: v["status"] == "ready")
        self.assertNotIn("granted", view)
        self.ask("status")
        self.until(lambda v: v["status"] == "waiting")  # asked again

    def test_structured_answers_code_and_raw_details(self) -> None:
        self.ask("structured")
        view = self.until(self.done)
        (block,) = next(i for i in view["thread"] if i["kind"] == "answer")["blocks"]
        self.assertEqual(
            (
                [f["label"] for f in block["fields"]],
                [t["label"] for t in block["tables"]],
                '"Risks"' in block["json"],
            ),
            (["Week", "Phase", "Budget", "Days remaining"], ["Risks"], True),
        )
        self.ask("codeblock")
        self.assertIn("```sql", self.answer(self.until(lambda v: self.answers(v) == 2)))
        self.conv.act({"type": "set", "option": "raw", "value": True})
        self.ask("rawdetails")
        view = self.until(lambda v: v["status"] == "ready" and self.answers(v) == 3)
        self.assertIn('"name": "Read"', list(self.steps(view).values())[-1]["raw"]["request"])

    def test_reasoning_is_sent_and_shown_only_when_the_host_asks(self) -> None:
        self.ask("reasoning")
        view = self.until(self.done)
        item = next(i for i in view["thread"] if i["kind"] == "steps")["items"][0]
        self.assertEqual(item["kind"], "reasoning")
        self.conv.close()
        self.conv = self.make(agent=scripted, features=Features())
        self.conv.act({"type": "connect", "profile": "mock"})
        self.until(lambda v: v["status"] == "ready")
        self.ask("reasoning")
        view = self.until(self.done)
        self.assertEqual([i for i in view["thread"] if i["kind"] == "steps"], [])

    def test_a_question_and_a_plan_that_nobody_answers_expire_in_the_thread(self) -> None:
        self.conv.agent.expiry = 0.3
        self.ask("onechoice")
        view = self.until(self.done)
        self.assertEqual(
            next(i for i in view["thread"] if i["kind"] == "asked")["note"], LABELS["note_expired"]
        )
        self.ask("shortplan")
        view = self.until(lambda v: v["status"] == "ready" and self.answers(v) == 2)
        plan = self.steps(view)[LABELS["plan_proposed"]]
        self.assertEqual(
            (plan["note"], "ten minutes" in plan["reason"]), (LABELS["note_expired"], True)
        )

    def test_the_name_of_an_attached_file_is_no_keyword(self) -> None:
        files = [{"name": "status_edit.csv", "data": base64.b64encode(b"a,b").decode()}]
        self.ask("Compare these", files=files)
        view = self.until(self.done)
        self.assertEqual(
            (
                self.answer(view).startswith("This is a scripted answer. You wrote: Compare these"),
                view["thread"][0]["files"],
            ),
            (True, ["status_edit.csv"]),
        )

    def test_session_details_and_the_connection_files(self) -> None:
        self.assertEqual(
            [f["label"] for f in self.conv.view()["session"]],
            ["Connection", "Model", "Session", "Program version"],
        )
        self.assertTrue(self.conv.view()["attach"]["multi"])
        agent = ScriptedAgent(lambda e: None)
        with patch.dict(
            os.environ, {"STREAMLIT_COCO_MOCK_FILES": "connections.toml=a,b;config.toml=c"}
        ):
            self.assertEqual(
                agent.connection_files(),
                [
                    {"file": "connections.toml", "profiles": ["a", "b"]},
                    {"file": "config.toml", "profiles": ["c"]},
                ],
            )
            self.assertEqual(agent.profiles(), ["a", "b", "c"])

    def test_a_connection_fails_with_a_message_and_a_wrong_file_is_said(self) -> None:
        events = []
        agent = ScriptedAgent(events.append, connect_delay=0)
        for profile, file in [("denied", None), ("mock", "config.toml")]:
            agent.connect(profile, "x", file=file)
            deadline = time.monotonic() + 3
            while len(events) < 1 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(events.pop()["t"], "connect_failed")
        self.conv.act({"type": "disconnect"})
        self.conv.act({"type": "connect", "profile": "denied"})
        view = self.until(lambda v: v["status"] == "not_connected" and v["error"])
        self.assertEqual(view["problem"], LABELS["problem_signin"])


class SelectionTest(ConversationCase):
    def test_the_mock_is_selected_only_by_its_variable(self) -> None:
        with patch.dict(os.environ, {"STREAMLIT_COCO_AGENT": "mock"}):
            agent = agent_factory()(lambda e: None)
        self.assertIsInstance(agent, ScriptedAgent)
        env = {k: v for k, v in os.environ.items() if k != "STREAMLIT_COCO_AGENT"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                type(agent_factory()(lambda e: None)).__module__, "streamlit_coco.cortex"
            )
            self.assertIsInstance(Conversation(self.folder, agent=scripted).agent, ScriptedAgent)

    def test_setup_and_profiles_states_can_be_reached(self) -> None:
        agent = ScriptedAgent(lambda e: None)
        with patch.dict(
            os.environ, {"STREAMLIT_COCO_MOCK_SETUP": "program", "STREAMLIT_COCO_MOCK_PROFILES": ""}
        ):
            self.assertEqual(agent.setup()["missing"], "program")
            self.assertEqual(agent.profiles(), [])
        with patch.dict(os.environ, {"STREAMLIT_COCO_MOCK_PROFILES": "a, b"}):
            self.assertEqual(agent.profiles(), ["a", "b"])

    def test_the_expiry_can_be_shortened(self) -> None:
        with patch.dict(os.environ, {"STREAMLIT_COCO_MOCK_EXPIRY": "5"}):
            self.assertEqual(ScriptedAgent(lambda e: None).gate.expiry, 5.0)
        self.assertEqual(ScriptedAgent(lambda e: None).gate.expiry, 600)

    def test_a_profile_can_fail_to_connect(self) -> None:
        conv = self.make(agent=lambda emit: ScriptedAgent(emit, connect_delay=0))
        conv.act({"type": "connect", "profile": "broken"})
        deadline = time.monotonic() + 3
        while conv.view()["status"] == "connecting" and time.monotonic() < deadline:
            conv.drain()
            time.sleep(0.01)
        self.assertEqual(
            (conv.view()["status"], conv.view()["error"]),
            ("not_connected", "The profile 'broken' could not connect."),
        )
