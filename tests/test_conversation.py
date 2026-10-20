"""Ask CoCo, the conversation: states, steps, requests, queue, reconciliation (conversation.py)."""

from __future__ import annotations

import gc
import time
from pathlib import Path

from coco_fixture import ConversationCase, FakeAgent

from streamlit_coco.conversation import LABELS, Conversation
from streamlit_coco.features import Features
from streamlit_coco.policy import FolderPolicy


class StatesTest(ConversationCase):
    def test_not_installed_and_not_connected_and_connecting_and_ready(self) -> None:
        def missing(emit):
            agent = FakeAgent(emit)
            agent.missing = {"missing": "package", "command": "pip install x"}
            return agent

        conv = self.make(agent=missing)
        self.assertEqual(
            (conv.view()["status"], conv.view()["setup"]["missing"]), ("not_installed", "package")
        )
        view = self.view()
        self.assertEqual(
            (view["status"], view["profiles"], view["profile"]),
            ("not_connected", ["dev", "prod"], None),
        )
        self.conv.act({"type": "connect", "profile": "dev"})
        self.assertEqual(self.view()["status"], "connecting")
        self.assertTrue(self.conv.busy)
        self.tell({"t": "connected"})
        self.assertEqual(self.view()["status"], "ready")
        self.assertFalse(self.conv.busy)

    def test_a_host_can_say_how_its_package_is_installed(self) -> None:
        def missing(emit):
            agent = FakeAgent(emit)
            agent.missing = {"missing": "package", "command": "pip install x"}
            return agent

        self.assertEqual(self.make(agent=missing).view()["setup"]["command"], "pip install x")
        conv = self.make(agent=missing, labels={"agent.setup_package": "make cockpit"})
        self.assertEqual(conv.view()["setup"]["command"], "make cockpit")

    def test_the_connections_file_is_not_read_on_every_page_run(self) -> None:
        reads = []
        self.conv.agent.profiles = lambda: reads.append(1) or ["dev"]
        for _ in range(5):
            self.assertEqual(self.view()["profiles"], ["dev"])
        self.assertEqual(len(reads), 1)
        self.conv._names = (
            time.monotonic() - 60,
            ["old"],
        )  # a connection added meanwhile is found again
        self.assertEqual(self.view()["profiles"], ["dev"])
        self.assertEqual(len(reads), 2)

    def test_connect_failed_says_why_and_stays_not_connected(self) -> None:
        self.conv.act({"type": "connect", "profile": "dev"})
        self.tell({"t": "connect_failed", "message": "bad login"})
        view = self.view()
        self.assertEqual((view["status"], view["error"]), ("not_connected", "bad login"))

    def test_nothing_is_sent_when_not_connected(self) -> None:
        self.send()
        self.assertEqual((self.sent(), self.conv.queue), ([], []))

    def test_the_connect_action_gives_the_agent_the_working_folder(self) -> None:
        self.connect()
        self.assertEqual(self.conv.agent.cwds, [str(self.folder)])

    def test_prompts_are_at_most_three_and_only_on_the_first_screen(self) -> None:
        fill = {"title": "Check the audit", "text": "Check the audit, starting with ", "fill": True}
        self.conv.prompts = ["one", "two", fill, "four"]
        self.assertEqual(self.view()["prompts"], [])  # not ready yet
        self.connect()
        self.assertEqual(
            self.view()["prompts"], ["one", "two", fill]
        )  # an object passes through whole
        self.send()
        self.assertEqual(self.view()["prompts"], [])

    def test_drafts_open_the_window_with_one_bubble_each_and_no_agent_call(self) -> None:
        self.conv.add_drafts([("Lea", "Hello Lea"), ("Hugo", "Hello Hugo")])
        drafts = self.thread("draft")
        self.assertEqual(
            [(d["title"], d["text"]) for d in drafts],
            [("Lea", "Hello Lea"), ("Hugo", "Hello Hugo")],
        )
        self.assertEqual(self.conv.agent.calls, [])

    def test_disconnect_ends_the_conversation(self) -> None:
        self.connect()
        self.send()
        old = self.conv.agent
        self.conv.act({"type": "disconnect"})
        view = self.view()
        self.assertEqual(
            (view["status"], view["thread"], view["profile"]), ("not_connected", [], None)
        )
        self.assertIn(("close",), old.calls)

    def test_a_host_that_switches_nothing_on_gets_none_of_the_optional_keys(self) -> None:
        conv = self.make(features=Features(queue=False))
        conv.act({"type": "connect", "profile": "dev"})
        view = conv.view()
        self.assertEqual(
            {"type_ahead", "options", "hidden", "session", "attach", "wait", "mode", "granted"}
            & set(view),
            set(),
        )
        conv.inbox.put({"t": "connected"})
        conv.drain()
        self.assertEqual(
            {"options", "hidden", "session", "attach", "wait", "mode", "granted"}
            & set(conv.view()),
            set(),
        )

    def test_a_label_of_the_host_replaces_the_default_and_unknown_placeholders_are_kept(
        self,
    ) -> None:
        conv = self.make(
            labels={"pill_answer": "Réponse prête", "scope_about": "À propos de {nom}"}
        )
        self.assertEqual(
            (conv.t("pill_answer"), conv.t("note_declined")),
            ("Réponse prête", LABELS["note_declined"]),
        )
        self.assertEqual(conv.t("scope_about", name="alpha"), "À propos de {nom}")


class ThreadTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()

    def test_progress_prose_shows_before_the_tool_and_the_answer_after(self) -> None:
        self.send()
        self.tell({"t": "text", "text": "Je lis "})
        self.assertEqual(self.thread("answer")[0]["text"], "Je lis ")
        self.assertTrue(self.thread("answer")[0]["streaming"])
        self.tell(
            {"t": "text", "text": "le projet."},
            {"t": "snapshot", "text": "Je lis le projet."},
            self.step(),
        )
        self.assertEqual(self.thread("answer"), [])
        steps = self.thread("steps")[0]
        self.assertEqual(
            steps["summary"], "Je lis le projet."
        )  # the sentence is the section's summary
        self.assertEqual([i["kind"] for i in steps["items"]], ["step"])
        self.assertEqual(steps["items"][0]["state"], "run")
        self.assertFalse(steps["folded"])
        self.tell(
            {"t": "tool_result", "id": "t1", "content": "# Alpha", "error": False},
            {"t": "text", "text": "La réponse."},
            {"t": "result", "text": "La réponse.", "error": False},
        )
        steps, answer = self.thread("steps")[0], self.thread("answer")[0]
        self.assertTrue(steps["folded"])
        self.assertEqual(
            (
                steps["items"][0]["state"],
                steps["items"][0]["result"],
                answer["text"],
                answer["streaming"],
            ),
            ("ok", "# Alpha", "La réponse.", False),
        )

    def test_a_section_starts_at_each_sentence_before_a_group_of_calls(self) -> None:
        self.send()
        self.tell(
            self.step("t1"),
            {"t": "text", "text": "Now **the other file**\nand `more`."},
            self.step("t2"),
            self.step("t3"),
        )
        first, second = self.thread("steps")
        self.assertEqual((first["summary"], [i["id"] for i in first["items"]]), (None, ["t1"]))
        self.assertEqual(
            (second["summary"], [i["id"] for i in second["items"]]),
            ("Now **the other file** and `more`.", ["t2", "t3"]),
        )
        self.assertNotEqual(first["id"], second["id"])

    def test_a_step_is_named_by_the_policy_and_keeps_tool_input_and_result(self) -> None:
        self.send()
        self.tell(self.step(), {"t": "tool_result", "id": "t1", "content": "text", "error": False})
        step = self.thread("steps")[0]["items"][0]
        self.assertEqual(
            (step["label"], step["tool"], step["input"]["file_path"]),
            ("Read README.md", "Read", self.path("README.md")),
        )

    def test_a_policy_that_cannot_name_a_step_leaves_the_tool_name(self) -> None:
        class Broken(FolderPolicy):
            def describe(self, tool, payload):
                raise RuntimeError("no")

        self.conv.policy = Broken(self.folder)
        self.send()
        self.tell(self.step())
        self.assertEqual(self.thread("steps")[0]["items"][0]["label"], "Read")

    def test_a_failed_step_stays_outside_the_fold(self) -> None:
        self.send()
        self.tell(
            self.step("t1"),
            self.step("t2", path="missing.md"),
            {"t": "tool_result", "id": "t1", "content": "x", "error": False},
            {"t": "tool_result", "id": "t2", "content": "no such file", "error": True},
            {"t": "text", "text": "Done."},
        )
        thread = self.thread()
        steps = [i for i in thread if i["kind"] == "steps"][0]
        failed = [i for i in thread if i["kind"] == "step"][0]
        self.assertTrue(steps["folded"])
        self.assertEqual([s["id"] for s in steps["items"]], ["t1"])
        self.assertEqual(
            (failed["id"], failed["state"], failed["note"], failed["result"]),
            ("t2", "bad", "", "no such file"),
        )

    def test_a_step_running_for_more_than_30_seconds_shows_its_elapsed_time(self) -> None:
        self.send()
        self.tell(self.step(started=time.time() - 45))
        step = self.thread("steps")[0]["items"][0]
        self.assertGreaterEqual(step["elapsed"], 45)
        self.tell({"t": "tool_result", "id": "t1", "content": "", "error": False})
        self.assertEqual(self.thread("steps")[0]["items"][0]["elapsed"], 0)

    def test_about_the_scope_at_the_first_request_and_when_it_changes(self) -> None:
        for text, scope in (("one", "alpha"), ("two", "alpha"), ("three", "beta"), ("four", None)):
            self.send(text, scope=scope)
            self.tell({"t": "result", "text": "a", "error": False})
        scopes = [i["text"] for i in self.thread("scope")]
        self.assertEqual(scopes, ["About alpha", "About beta", LABELS["scope_none"]])

    def test_a_host_that_gives_no_scope_never_sees_the_line(self) -> None:
        self.send("one", scope=None)
        self.tell({"t": "result", "text": "a", "error": False})
        self.send("two", scope=None)
        self.assertEqual(self.thread("scope"), [])

    def test_late_events_of_a_finished_run_change_nothing(self) -> None:
        self.send()
        self.tell({"t": "result", "text": "Done.", "error": False})
        before = self.thread()
        self.tell({"t": "text", "text": "late"}, self.step())
        self.assertEqual(self.thread(), before)

    def test_steps_off_keeps_the_sentences_and_what_failed_but_not_the_cards(self) -> None:
        self.conv.features = Features(steps=False)
        self.send()
        self.tell(
            {"t": "snapshot", "text": "I read."},
            self.step("t1"),
            self.step("t2", path="missing.md"),
            {"t": "tool_result", "id": "t1", "content": "x", "error": False},
            {"t": "tool_result", "id": "t2", "content": "no", "error": True},
            {"t": "text", "text": "Done."},
        )
        thread = self.thread()
        self.assertEqual(
            [
                (i["kind"], i.get("summary"), len(i.get("items", [])))
                for i in thread
                if i["kind"] == "steps"
            ],
            [("steps", "I read.", 0)],
        )
        self.assertEqual([i["id"] for i in thread if i["kind"] == "step"], ["t2"])

    def test_reasoning_is_a_fold_among_the_steps_only_when_the_host_asks(self) -> None:
        self.send()
        self.tell(
            {"t": "reasoning", "text": "hmm"},
            self.step(),
            {"t": "tool_result", "id": "t1", "content": "x", "error": False},
        )
        item = self.thread("steps")[0]["items"][0]
        self.assertEqual((item["kind"], item["text"]), ("reasoning", "hmm"))
        self.tell({"t": "result", "text": "Done.", "error": False})
        self.conv.features = Features()
        self.send("again")
        self.tell({"t": "reasoning", "text": "no"})
        self.assertEqual(len(self.thread("steps")), 1)  # nothing new

    def test_reasoning_switch_reaches_the_agent_at_its_creation(self) -> None:
        calls = []

        def agent(emit):
            fake = FakeAgent(emit)
            fake.set_reasoning = lambda on: calls.append(on)
            return fake

        self.make(agent=agent)
        self.make(agent=agent, features=Features())
        self.assertEqual(calls, [True])


class ReconcileTest(ConversationCase):
    """The final result repeats text already streamed (the reconciliation checks)."""

    def setUp(self) -> None:
        super().setUp()
        self.connect()
        self.send()

    def answers(self) -> list[str]:
        out = []
        for item in self.thread():
            out += [item["summary"]] if item["kind"] == "steps" and item["summary"] else []
            out += [item["text"]] if item["kind"] == "answer" else []
        return out

    def test_a_repeat_of_the_last_block_is_not_replayed(self) -> None:
        self.tell(
            {"t": "text", "text": "Je lis les fichiers."},
            {"t": "snapshot", "text": "Je lis les fichiers."},
        )
        self.tell(self.step("r1"), {"t": "tool_result", "id": "r1", "content": "", "error": False})
        self.tell(
            {"t": "text", "text": "Réponse finale : "},
            {"t": "text", "text": "A-2."},
            {"t": "snapshot", "text": "Réponse finale : A-2."},
            {"t": "result", "text": "Réponse finale : A-2.", "error": False},
        )
        self.assertEqual(self.answers(), ["Je lis les fichiers.", "Réponse finale : A-2."])

    def test_an_aggregate_of_the_whole_turn_is_not_replayed(self) -> None:
        self.tell(
            {"t": "text", "text": "Je lis les fichiers."},
            {"t": "snapshot", "text": "Je lis les fichiers."},
            self.step("r1"),
            {"t": "tool_result", "id": "r1", "content": "", "error": False},
            {"t": "text", "text": "Réponse finale : A-2."},
            {"t": "snapshot", "text": "Réponse finale : A-2."},
        )
        self.tell(
            {"t": "result", "text": "Je lis les fichiers.Réponse finale : A-2.", "error": False}
        )
        self.assertEqual(self.answers(), ["Je lis les fichiers.", "Réponse finale : A-2."])

    def test_a_result_with_nothing_streamed_is_the_answer(self) -> None:
        self.tell(
            {"t": "snapshot", "text": "Réponse complète."},
            {"t": "result", "text": "Réponse complète.", "error": False},
        )
        self.assertEqual(self.answers(), ["Réponse complète."])
        self.send("again")
        self.tell({"t": "result", "text": "Réponse complète.", "error": False})
        self.assertEqual(
            [a["text"] for a in self.thread("answer")], ["Réponse complète.", "Réponse complète."]
        )

    def test_a_partial_stream_is_completed_by_the_result(self) -> None:
        self.tell({"t": "text", "text": "Réponse "}, {"t": "snapshot", "text": "Réponse complète."})
        self.tell({"t": "result", "text": "Réponse complète.", "error": False})
        self.assertEqual(self.answers(), ["Réponse complète."])

    def test_a_partial_stream_is_completed_by_a_result_alone(self) -> None:
        self.tell(
            {"t": "text", "text": "Réponse "},
            {"t": "result", "text": "Réponse complète.", "error": False},
        )
        self.assertEqual(self.answers(), ["Réponse complète."])

    def test_a_new_final_answer_after_commentary_is_not_dropped(self) -> None:
        self.tell(
            {"t": "snapshot", "text": "Je vérifie."},
            self.step("r1"),
            {"t": "tool_result", "id": "r1", "content": "", "error": False},
            {"t": "snapshot", "text": "La réponse est A-2."},
            {"t": "result", "text": "La réponse est A-2.", "error": False},
        )
        self.assertEqual(self.answers(), ["Je vérifie.", "La réponse est A-2."])

    def test_a_result_that_brings_something_new_is_added(self) -> None:
        self.tell(
            {"t": "text", "text": "Hello."},
            {"t": "result", "text": "Something else entirely.", "error": False},
        )
        self.assertEqual(self.answers(), ["Hello.", "Something else entirely."])


class RequestTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()
        self.send("Create a note")
        self.tell({"t": "text", "text": "I propose a note."}, self.write_call(), self.request())

    def test_a_pending_request_is_shown_with_its_facts_and_its_step_waits_behind_it(self) -> None:
        view, facts = self.view(), self.facts()
        self.assertEqual(view["status"], "waiting")
        self.assertEqual(
            (view["request"]["id"], view["request"]["kind"], view["request"]["question"]),
            ("r1", "change", facts["question"]),
        )
        self.assertEqual(view["request"]["changes"]["file"], "notes/new.md")
        self.assertEqual(
            view["pill"], {"kind": "request", "label": facts["pill"], "name": facts["where"]}
        )
        self.assertEqual(self.steps(), {})  # the step is not shown yet
        self.assertEqual(
            (self.thread("steps")[0]["summary"], self.thread("steps")[0]["items"]),
            ("I propose a note.", []),
        )

    def test_allow_makes_it_the_running_step_marked_allowed_by_you(self) -> None:
        self.conv.act({"type": "allow", "id": "r1"})
        self.assertIn(("decide", "r1", True, False), self.conv.agent.calls)
        view, step = self.view(), self.steps()["t1"]
        self.assertEqual(
            (view["status"], view["request"], step["state"], step["allowed"], step["note"]),
            ("working", None, "run", True, LABELS["note_allowed"]),
        )
        self.tell({"t": "tool_result", "id": "t1", "content": "Wrote", "error": False})
        self.assertEqual((self.steps()["t1"]["state"], self.steps()["t1"]["allowed"]), ("ok", True))

    def test_an_answer_is_given_once_and_not_after_the_request_is_gone(self) -> None:
        self.conv.act({"type": "allow", "id": "r1"})
        self.conv.act({"type": "decline", "id": "r1"})  # a double click, then the other button
        self.conv.act({"type": "allow", "id": "r1"})
        self.assertEqual(
            [c for c in self.conv.agent.calls if c[0] == "decide"], [("decide", "r1", True, False)]
        )
        self.assertEqual(self.steps()["t1"]["state"], "run")

    def test_an_answer_to_an_expired_request_is_ignored(self) -> None:
        self.tell({"t": "expired", "id": "r1", "tool_id": "t1"})
        self.conv.act({"type": "allow", "id": "r1"})
        self.assertEqual([c for c in self.conv.agent.calls if c[0] == "decide"], [])
        self.assertEqual(self.steps()["t1"]["note"], LABELS["note_expired"])

    def test_a_request_that_arrives_after_the_run_ended_is_dropped(self) -> None:
        self.tell(
            {"t": "result", "text": "x", "error": False},
            {"t": "request", "id": "r2", "tool_id": "t2", "facts": self.facts_after()},
        )
        self.assertIsNone(self.view()["request"])
        self.assertFalse(self.conv.busy)

    def facts_after(self) -> dict:
        return FolderPolicy(self.folder).judge(
            "Write", {"file_path": self.path("notes/n.md"), "content": "x"}
        )[1]

    def test_an_event_that_cannot_be_applied_is_dropped_and_logged_not_raised_into_the_page(
        self,
    ) -> None:
        with self.assertLogs("streamlit_coco.conversation", "ERROR"):
            self.tell({"t": "tool_use"}, {"t": "text", "text": "Still here."})
        self.assertEqual(self.thread("answer")[0]["text"], "Still here.")

    def test_decline_says_declined_once_and_the_run_goes_on(self) -> None:
        self.conv.act({"type": "decline", "id": "r1"})
        self.assertIn(("decide", "r1", False, False), self.conv.agent.calls)
        self.tell(
            {"t": "tool_result", "id": "t1", "content": "Declined by the user.", "error": True},
            {"t": "text", "text": "Understood."},
            {"t": "result", "text": "Understood.", "error": False},
        )
        view = self.view()
        self.assertEqual(
            [(s["state"], s["note"]) for s in self.steps().values()],
            [("no", LABELS["note_declined"])],
        )
        self.assertEqual(
            [i["kind"] for i in view["thread"] if i["kind"] == "step"], ["step"]
        )  # outside the fold
        self.assertEqual(view["status"], "ready")
        self.assertEqual(self.thread("answer")[0]["text"], "Understood.")

    def test_an_unanswered_request_expires_as_a_decline(self) -> None:
        self.tell({"t": "expired", "id": "r1", "tool_id": "t1"})
        view = self.view()
        self.assertEqual((view["request"], view["status"]), (None, "working"))
        self.tell({"t": "tool_result", "id": "t1", "content": "No answer", "error": True})
        step = self.steps()["t1"]
        self.assertEqual(
            (step["state"], step["note"], step["reason"]),
            ("no", LABELS["note_expired"], LABELS["reason_expired"]),
        )

    def test_the_policy_is_checked_again_after_the_answer(self) -> None:
        self.conv.act({"type": "allow", "id": "r1"})
        self.tell({"t": "refused", "tool_id": "t1", "reason": "An edit must match existing text."})
        self.tell({"t": "tool_result", "id": "t1", "content": "denied", "error": False})
        step = self.steps()["t1"]
        self.assertEqual(
            (step["state"], step["note"], step["reason"]),
            ("no", LABELS["note_not_allowed"], "An edit must match existing text."),
        )

    def test_a_refused_call_is_shown_not_allowed_with_the_reason_whatever_the_cli_reports(
        self,
    ) -> None:
        self.tell({"t": "result", "text": "x", "error": False})
        self.send("Read it")
        self.tell(
            self.step("t9", path="../outside.md"),
            {"t": "refused", "tool_id": "t9", "reason": "This is outside."},
            {"t": "tool_result", "id": "t9", "content": "denied", "error": False},
        )
        step = self.steps()["t9"]
        self.assertEqual(
            (step["state"], step["note"], step["reason"]),
            ("no", LABELS["note_not_allowed"], "This is outside."),
        )
        self.assertEqual(step["result"], "denied")

    def test_a_refusal_that_arrives_before_the_tool_use_still_wins(self) -> None:
        self.tell({"t": "result", "text": "x", "error": False})
        self.send("Read it")
        self.tell(
            {"t": "refused", "tool_id": "t9", "reason": "No."},
            self.step("t9"),
            {"t": "tool_result", "id": "t9", "content": "ok", "error": False},
        )
        self.assertEqual(self.steps()["t9"]["state"], "no")


class WrittenFilesTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()
        self.send("Create a note")

    def succeed(self, tool_id="t1", path="notes/new.md", error=False) -> bool:
        self.tell(self.write_call(tool_id, path), self.request("r" + tool_id, tool_id, path))
        self.conv.act({"type": "allow", "id": "r" + tool_id})
        return self.tell({"t": "tool_result", "id": tool_id, "content": "Wrote", "error": error})

    def test_a_written_file_calls_the_host_once_and_the_page_reloads_before_the_turn_ends(
        self,
    ) -> None:
        (self.folder / "notes" / "new.md").write_text("# New\n", encoding="utf-8")
        self.assertTrue(self.succeed())
        self.assertEqual(self.changed, [[str((self.folder / "notes" / "new.md").resolve())]])
        self.assertIsNotNone(self.conv.run)  # the turn has not ended
        self.assertFalse(self.tell({"t": "text", "text": "More."}))
        self.assertEqual(len(self.changed), 1)

    def test_several_files_of_one_drain_are_one_call(self) -> None:
        for name in ("a.md", "b.md"):
            (self.folder / name).write_text("x", encoding="utf-8")
        self.tell(
            self.write_call("w1", "a.md"),
            self.write_call("w2", "b.md"),
            {"t": "tool_result", "id": "w1", "content": "ok", "error": False},
            {"t": "tool_result", "id": "w2", "content": "ok", "error": False},
        )
        self.assertEqual(
            [[Path(p).name for p in call] for call in self.changed], [["a.md", "b.md"]]
        )

    def test_a_failed_or_refused_change_calls_nothing_and_reloads_nothing(self) -> None:
        (self.folder / "notes" / "new.md").write_text("# New\n", encoding="utf-8")
        self.assertFalse(self.succeed(error=True))
        self.tell({"t": "refused", "tool_id": "t2", "reason": "No."})
        self.assertFalse(self.succeed("t2"))
        self.assertEqual(self.changed, [])

    def test_a_file_that_is_not_on_disk_after_a_success_calls_nothing(self) -> None:
        self.assertFalse(self.succeed())
        self.assertEqual(self.changed, [])

    def test_a_change_outside_the_folder_or_without_a_path_calls_nothing(
        self,
    ) -> None:
        for index, given in enumerate(
            ({"file_path": str(self.folder.parent / "beta" / "x.md")}, {}, {"file_path": None})
        ):
            self.tell({"t": "tool_use", "id": f"w{index}", "name": "Write", "input": given})
            self.assertFalse(
                self.tell(
                    {"t": "tool_result", "id": f"w{index}", "content": "Wrote", "error": False}
                )
            )
        self.assertEqual(self.changed, [])

    def test_a_read_changes_nothing(self) -> None:
        self.assertFalse(
            self.tell(self.step(), {"t": "tool_result", "id": "t1", "content": "x", "error": False})
        )

    def test_a_hook_that_fails_is_logged_and_the_page_still_reloads(self) -> None:
        def broken(paths):
            raise RuntimeError("no")

        self.conv._on_files_changed = broken
        (self.folder / "notes" / "new.md").write_text("# New\n", encoding="utf-8")
        with self.assertLogs("streamlit_coco.conversation", "ERROR"):
            self.assertTrue(self.succeed())


class ContextTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()

    def test_the_page_text_is_cut_typed_and_only_kept_when_the_host_asks(self) -> None:
        screen = {"text": "x" * 20000, "selection": "Forecast 63.5", "dialog": 7, "other": "no"}
        self.send("hi", action={"screen": screen})
        ctx = self.conv.run["message"]["ctx"]
        self.assertEqual(len(ctx["screen"]["text"]), 12000)
        self.assertEqual(
            set(ctx["screen"]), {"text", "selection"}
        )  # a wrong type and an unknown key are dropped
        self.tell({"t": "result", "text": "a", "error": False})
        self.send("again", action={"screen": "not a dict"})
        self.assertNotIn("screen", self.conv.run["message"]["ctx"])
        self.tell({"t": "result", "text": "a", "error": False})
        self.conv.features = Features()  # page_text off: the screen never travels
        self.send("third", action={"screen": screen})
        self.assertNotIn("screen", self.conv.run["message"]["ctx"])

    def test_the_context_keeps_what_the_host_gave_and_adds_the_rights_of_the_policy(self) -> None:
        given = self.ctx(
            instructions="Be brief.", user={"name": "Lea", "language": "fr"}, week="W40"
        )
        self.conv.act({"type": "send", "text": "Hi"}, given)
        ctx = self.conv.run["message"]["ctx"]
        self.assertEqual(
            {k: ctx[k] for k in ("scope", "instructions", "user", "week")},
            {k: given[k] for k in ("scope", "instructions", "user", "week")},
        )
        self.assertEqual(ctx["rights"], self.conv.policy.rights())
        self.assertNotIn("rights", given)

    def test_a_send_without_context_still_goes(self) -> None:
        self.conv.act({"type": "send", "text": "Hi"})
        self.assertEqual(self.sent(), ["Hi"])

    def test_the_context_is_frozen_when_the_message_is_sent(self) -> None:
        ctx = self.ctx(week="W40")
        self.conv.act({"type": "send", "text": "Hi"}, ctx)
        ctx["week"] = "W41"
        ctx["scope"]["name"] = "beta"
        self.assertEqual(self.conv.run["message"]["ctx"]["week"], "W40")
        self.assertEqual(self.conv.run["message"]["ctx"]["scope"]["name"], "alpha")

    def test_a_policy_function_is_called_once_per_message_and_frozen_with_it(self) -> None:
        def per_scope(ctx):
            return FolderPolicy(self.folder.parent / ctx["scope"]["name"])

        self.conv.policy = per_scope
        self.send("first", scope="alpha")
        self.send("second", scope="beta")  # typed while working
        queued = self.conv.queue[0]
        self.assertEqual(
            (queued["ctx"]["scope"]["name"], queued["policy"].base.name), ("beta", "beta")
        )
        first = self.conv.run["message"]["policy"]
        self.assertEqual(first.base.name, "alpha")
        self.tell({"t": "result", "text": "a", "error": False})
        self.assertEqual(self.conv.run["message"]["policy"].base.name, "beta")
        self.assertEqual(first.base.name, "alpha")  # navigation afterwards moves nothing

    def test_a_policy_function_that_fails_leaves_the_safest_policy(self) -> None:
        def broken(ctx):
            raise RuntimeError("no")

        self.conv.policy = broken
        with self.assertLogs("streamlit_coco.conversation", "ERROR"):
            self.send("look")
        policy = self.conv.run["message"]["policy"]
        self.assertIsInstance(policy, FolderPolicy)
        self.assertIsNotNone(
            policy.judge("Write", {"file_path": self.path("x.md"), "content": "x"})[1]
        )  # asks

    def test_without_a_policy_the_working_folder_is_read_freely_and_every_change_asks(self) -> None:
        self.conv.policy = None
        self.send("look", scope=None)
        policy = self.conv.run["message"]["policy"]
        self.assertEqual(policy.judge("Read", {"file_path": self.path("README.md")}), (None, None))
        reason, facts = policy.judge("Write", {"file_path": self.path("x.md"), "content": "x"})
        self.assertEqual((reason, facts["kind"]), (None, "change"))


class QueueTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()
        self.send("first")

    def test_a_message_typed_while_working_is_queued_visibly(self) -> None:
        self.send("second")
        self.assertEqual(self.sent(), ["first"])
        self.assertEqual([q["text"] for q in self.view()["queue"]], ["second"])
        self.assertEqual([i["text"] for i in self.thread("user")], ["first"])

    def test_a_message_typed_behind_a_request_waits_behind_it(self) -> None:
        self.tell(self.write_call(), self.request())
        self.send("second")
        self.assertEqual(self.view()["status"], "waiting")
        self.assertEqual(self.sent(), ["first"])
        self.assertEqual(len(self.view()["queue"]), 1)

    def test_after_a_decline_the_run_goes_on_and_the_queue_follows(self) -> None:
        self.tell(self.write_call(), self.request())
        self.send("second")
        self.conv.act({"type": "decline", "id": "r1"})
        self.assertEqual(self.sent(), ["first"])
        self.tell({"t": "result", "text": "ok", "error": False})
        self.assertEqual(self.sent(), ["first", "second"])
        self.assertEqual((self.view()["queue"], self.view()["restore"]), ([], None))

    def test_the_queue_follows_a_finished_run_in_order(self) -> None:
        self.send("second")
        self.send("third")
        self.tell({"t": "result", "text": "a", "error": False})
        self.assertEqual(self.sent(), ["first", "second"])
        self.tell({"t": "result", "text": "b", "error": False})
        self.assertEqual(self.sent(), ["first", "second", "third"])

    def test_taking_a_message_back_returns_its_text_to_the_field_once(self) -> None:
        self.send("second")
        self.conv.act({"type": "unqueue", "id": self.view()["queue"][0]["id"]})
        view = self.view()
        self.assertEqual((view["queue"], view["restore"]), ([], "second"))
        self.assertIsNone(self.view()["restore"])
        self.tell({"t": "result", "text": "a", "error": False})
        self.assertEqual(self.sent(), ["first"])

    def test_stop_returns_the_queue_to_the_field_when_the_run_has_really_ended(self) -> None:
        self.send("second")
        self.send("third")
        self.conv.act({"type": "stop"})
        self.assertIn(("stop",), self.conv.agent.calls)
        self.assertEqual(self.view()["status"], "working")  # not ended yet
        self.tell({"t": "stopped"})
        view = self.view()
        self.assertEqual(
            (view["status"], view["queue"], view["restore"]), ("ready", [], "second\n\nthird")
        )
        self.assertEqual(self.sent(), ["first"])

    def test_a_failure_returns_the_queue_to_the_field(self) -> None:
        self.send("second")
        self.tell({"t": "error", "message": "boom", "retry": False})
        view = self.view()
        self.assertEqual((view["queue"], view["restore"]), ([], "second"))
        self.assertEqual(self.sent(), ["first"])

    def test_a_lost_connection_returns_the_queue_to_the_field_and_a_taken_back_text_is_kept(
        self,
    ) -> None:
        self.send("second")
        self.send("third")
        self.conv.act({"type": "unqueue", "id": self.view()["queue"][0]["id"]})
        self.tell({"t": "lost", "message": "closed"})
        self.assertEqual(self.view()["restore"], "second\n\nthird")

    def test_a_new_conversation_discards_the_queue(self) -> None:
        self.send("second")
        self.conv.act({"type": "new"})
        view = self.view()
        self.assertEqual((view["queue"], view["restore"], view["thread"]), ([], None, []))

    def test_the_stop_button_declines_a_pending_request(self) -> None:
        self.tell(self.write_call(), self.request())
        self.conv.act({"type": "stop"})
        self.assertIn(("decide", "r1", False, False), self.conv.agent.calls)
        self.assertIsNone(self.view()["request"])
        self.tell({"t": "stopped"})
        step = self.steps()["t1"]
        self.assertEqual((step["state"], step["note"]), ("no", LABELS["note_declined"]))

    def test_stop_marks_the_running_step_stopped_only_when_the_run_has_ended(self) -> None:
        self.tell(self.step())
        self.conv.act({"type": "stop"})
        self.assertEqual(self.thread("steps")[0]["items"][0]["state"], "run")
        self.tell({"t": "result", "text": "", "error": False})
        step = self.steps()["t1"]
        self.assertEqual((step["state"], step["note"]), ("bad", LABELS["note_stopped"]))
        self.assertIsNone(self.view()["pill"])

    def test_without_the_queue_feature_a_message_typed_while_working_is_not_taken(self) -> None:
        self.conv.features = Features(queue=False)
        self.send("second")
        self.assertEqual((self.conv.queue, self.sent()), ([], ["first"]))
        self.conv.act({"type": "new"})
        self.conv.act({"type": "connect", "profile": "dev"})
        self.send("early")  # while connecting
        self.assertEqual(self.conv.queue, [])
        self.assertNotIn("type_ahead", self.view())


class FailureTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.connect()
        self.send("first")

    def test_a_failure_that_can_end_differently_offers_try_again(self) -> None:
        self.tell({"t": "error", "message": "Timed out", "retry": True})
        system = self.thread("system")[0]
        self.assertEqual(
            (system["action"], system["detail"], system["text"]),
            ("retry", "Timed out", LABELS["failed_text"]),
        )
        self.assertEqual(
            self.view()["pill"], {"kind": "failed", "label": LABELS["pill_failed"], "name": "alpha"}
        )

    def test_a_deterministic_failure_offers_no_retry(self) -> None:
        self.tell({"t": "error", "message": "Invalid request", "retry": False})
        self.assertIsNone(self.thread("system")[0]["action"])
        self.conv.act({"type": "retry"})
        self.assertEqual(self.sent(), ["first"])

    def test_try_again_sends_the_same_message_without_a_second_bubble(self) -> None:
        self.tell({"t": "error", "message": "Timed out", "retry": True})
        self.conv.act({"type": "retry"})
        self.assertEqual(self.sent(), ["first", "first"])
        self.assertEqual(self.thread("system"), [])
        self.assertEqual([i["text"] for i in self.thread("user")], ["first"])
        self.assertEqual(self.view()["status"], "working")

    def test_an_error_result_is_a_failure(self) -> None:
        self.tell({"t": "result", "text": "max turns", "error": True, "message": "max turns"})
        self.assertEqual(self.thread("system")[0]["detail"], "max turns")
        self.assertEqual(self.thread("answer"), [])

    def test_a_running_step_is_interrupted_by_a_failure(self) -> None:
        self.tell(self.step(), {"t": "error", "message": "boom", "retry": False})
        step = self.steps()["t1"]
        self.assertEqual((step["state"], step["note"]), ("bad", LABELS["note_interrupted"]))

    def test_a_lost_connection_replaces_the_composer_and_says_what_happened_to_the_work(
        self,
    ) -> None:
        self.tell(
            self.step(),
            self.write_call("t2"),
            self.request("r2", "t2"),
            {"t": "lost", "message": "closed"},
        )
        view = self.view()
        self.assertEqual(view["status"], "lost")
        self.assertEqual(view["pill"]["label"], LABELS["pill_lost"])
        self.assertEqual(self.thread("system")[0]["text"], LABELS["lost_text"])
        steps = {i: (s["state"], s["note"]) for i, s in self.steps().items()}
        self.assertEqual(
            steps,
            {"t1": ("bad", LABELS["note_interrupted"]), "t2": ("no", LABELS["note_cancelled"])},
        )
        self.assertIsNone(view["request"])

    def test_reconnect_starts_a_new_session_of_the_same_profile_and_keeps_the_thread(self) -> None:
        self.tell({"t": "lost", "message": "closed"})
        self.conv.act({"type": "reconnect"})
        self.assertEqual(self.view()["status"], "connecting")
        self.assertIn(("connect", "dev"), self.conv.agent.calls)
        self.assertEqual(len(self.thread("user")), 1)
        self.tell({"t": "connected"})
        self.assertEqual(self.view()["status"], "ready")

    def test_a_lost_connection_while_idle(self) -> None:
        self.tell({"t": "result", "text": "a", "error": False}, {"t": "lost", "message": "closed"})
        self.assertEqual(self.thread("system")[0]["text"], LABELS["lost_text"])


class NewConversationTest(ConversationCase):
    def test_new_ends_the_session_and_starts_a_fresh_one_of_the_same_profile(self) -> None:
        self.connect()
        self.send("hi")
        old = self.conv.agent
        self.conv.act({"type": "new"})
        self.assertIn(("close",), old.calls)
        self.assertIsNot(self.conv.agent, old)
        self.assertEqual((self.view()["thread"], self.view()["status"]), ([], "connecting"))
        self.assertIn(("connect", "dev"), self.conv.agent.calls)
        self.send("x")  # typed ahead: it waits for the connection
        self.assertEqual(self.sent(), [])
        self.tell({"t": "connected"})
        self.view()  # the held message goes now
        self.assertEqual(self.sent(), ["x"])
        self.tell({"t": "result", "text": "ok", "error": False})
        self.send("About beta", scope="beta")
        self.assertEqual(self.thread("scope")[-1]["text"], "About beta")

    def test_events_of_the_old_session_are_never_read(self) -> None:
        self.connect()
        self.send("hi")
        old_inbox = self.conv.inbox
        self.conv.act({"type": "new"})
        old_inbox.put({"t": "text", "text": "ghost"})
        self.conv.drain()
        self.assertEqual(self.thread("answer"), [])


class SessionEndTest(ConversationCase):
    def test_a_second_lost_event_says_nothing_more(self) -> None:
        # the failed turn and the session's own watch both report the same loss
        self.connect()
        self.send("hi")
        self.tell({"t": "lost", "message": "closed"}, {"t": "lost", "message": "session ended"})
        self.assertEqual(len(self.thread("system")), 1)

    def test_a_changed_working_folder_ends_the_conversation_once_and_says_why(self) -> None:
        self.connect()
        self.send("hi")
        self.send("queued")
        old, elsewhere = self.conv.agent, self.folder.parent / "elsewhere"
        elsewhere.mkdir()
        self.conv.set_cwd(elsewhere)
        self.assertIn(("close",), old.calls)
        self.assertEqual(
            self.conv.agent.cwds, [str(elsewhere)]
        )  # the new session works in the new folder
        view = self.view()
        self.assertEqual((view["status"], view["queue"], view["request"]), ("connecting", [], None))
        self.assertEqual([i["kind"] for i in view["thread"]], ["system"])
        self.assertEqual(view["thread"][0]["text"], LABELS["folder_changed"])
        self.conv.set_cwd(elsewhere)  # the next page run
        self.assertEqual(len(self.thread("system")), 1)

    def test_the_same_folder_spelled_again_changes_nothing(self) -> None:
        self.connect()
        self.conv.set_cwd(Path(str(self.folder)))
        self.assertEqual((self.view()["status"], self.thread()), ("ready", []))

    def test_a_folder_changed_before_connecting_ends_nothing(self) -> None:
        self.conv.set_cwd(self.folder.parent)
        self.assertEqual((self.view()["status"], self.thread()), ("not_connected", []))
        self.connect()
        self.assertEqual(self.conv.agent.cwds, [str(self.folder.parent)])

    def test_dropping_the_conversation_closes_the_agent(self) -> None:
        # the browser session ended: nothing else would stop the Cortex Code process
        conv = Conversation(self.folder, agent=FakeAgent)
        agent = conv.agent
        del conv
        gc.collect()
        self.assertIn(("close",), agent.calls)


class AuditPolicy(FolderPolicy):
    """A host's policy that knows a command which exits non-zero for what it finds."""

    def exit_note(self, tool, tool_input, content):
        return "Exit status 1" if tool == "Bash" and "errors" in content else None


class ResultTest(ConversationCase):
    def setUp(self) -> None:
        super().setUp()
        self.conv.policy = AuditPolicy(self.folder)
        self.connect()
        self.send("Run the audit")

    def test_a_call_the_cli_refuses_itself_is_not_a_completed_step(self) -> None:
        """Seen live: SQL allowed by the user, refused by the CLI's own tool list, and shown as
        completed."""
        self.tell(
            {
                "t": "tool_use",
                "id": "q1",
                "name": "sql_execute",
                "input": {"sql": "select 1", "description": "d"},
            },
            {
                "t": "tool_result",
                "id": "q1",
                "error": False,
                "content": "Tool denied: not matched by any --allowed-tools pattern\n\n"
                "This tool is PERMANENTLY blocked",
            },
        )
        self.assertEqual(self.steps()["q1"]["state"], "bad")
        self.assertEqual(self.steps()["q1"]["reason"], LABELS["reason_cli_refused"])

    def run_command(self, content, error, tool_id="t1"):
        self.tell(
            {"t": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": "audit"}},
            {"t": "tool_result", "id": tool_id, "content": content, "error": error},
        )
        return self.steps()[tool_id]

    def test_a_command_that_printed_its_report_is_a_finished_step_whatever_its_exit_status(
        self,
    ) -> None:
        step = self.run_command(
            '`audit` failed with error: {"errors": 2, "findings": []}', error=True
        )
        self.assertEqual(step["state"], "ok")
        self.assertTrue(step["result"].startswith("Exit status 1"))
        self.assertIn('"errors": 2', step["result"])

    def test_a_command_that_could_not_run_is_a_failed_step(self) -> None:
        self.assertEqual(
            self.run_command("Traceback (most recent call last): ...", error=True)["state"], "bad"
        )

    def test_a_policy_without_an_exit_note_fails_the_step(self) -> None:
        self.conv.run["message"]["policy"] = FolderPolicy(self.folder)
        self.assertEqual(self.run_command('{"errors": 2}', error=True)["state"], "bad")

    def test_a_finished_turns_results_are_cut_for_the_window_and_the_running_ones_are_not(
        self,
    ) -> None:
        # the window polls: what it is sent must not grow with the whole conversation
        big = "line of a large result" + chr(10)
        self.tell(
            {"t": "tool_use", "id": "a", "name": "Bash", "input": {"command": "x"}},
            {"t": "tool_result", "id": "a", "content": big * 800, "error": False},
        )
        self.assertEqual(len(self.steps()["a"]["result"]), len(big * 800))  # running turn: whole
        self.tell({"t": "result", "text": "Done.", "error": False})
        sent = self.steps()["a"]["result"]
        self.assertTrue(sent.startswith(big) and sent.endswith("[truncated]") and len(sent) < 2_100)
        kept = next(i for i in self.conv.items if i["kind"] == "turn")["seq"][0]["step"]["result"]
        self.assertEqual(len(kept), len(big * 800))  # the conversation keeps it whole

    def test_a_big_result_is_cut_and_says_so(self) -> None:
        step = self.run_command("x" * 5_000_000, error=False)
        self.assertLess(len(step["result"]), 30_000)
        self.assertTrue(step["result"].endswith("[truncated]"))
        self.assertEqual(self.run_command("short", error=False, tool_id="t2")["result"], "short")


class PillTest(ConversationCase):
    def test_answer_pill_until_seen(self) -> None:
        self.connect()
        self.send("hi")
        self.assertIsNone(self.view()["pill"])
        self.tell({"t": "result", "text": "Done.", "error": False})
        self.assertEqual(
            self.view()["pill"], {"kind": "answer", "label": LABELS["pill_answer"], "name": "alpha"}
        )
        self.conv.act({"type": "seen"})
        self.assertIsNone(self.view()["pill"])

    def test_a_read_that_asks_has_the_pill_the_policy_wrote_and_none_means_the_default(
        self,
    ) -> None:
        self.connect()
        self.send("hi")
        facts = self.facts("Write")
        self.tell(
            self.write_call("c1"), {"t": "request", "id": "rc", "tool_id": "c1", "facts": facts}
        )
        self.assertEqual(self.view()["pill"]["label"], facts["pill"])
        self.assertIsNone(self.view()["request"]["reads"])
        self.conv.act({"type": "decline", "id": "rc"})
        self.tell(
            self.step("c2"),
            {
                "t": "request",
                "id": "rd",
                "tool_id": "c2",
                "facts": {**facts, "pill": None, "kind": "read"},
            },
        )
        self.assertEqual(self.view()["pill"]["label"], LABELS["pill_read"])
