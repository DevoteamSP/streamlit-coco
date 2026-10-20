"""Ask CoCo, the window: what can be checked without a browser (feature file 1.1, 1.5, 1.6, 4).

Ported from the Cockpit's test_coco_ui.py: the view fixtures follow the contract of
streamlit_coco/conversation.py; a real conversation produces views of the same shape; the Markdown
renderer (static/coco/coco.js, run under node when it is installed) never lets a model's text
become markup. The pages, the keyboard and the layout are checked in a browser: see
streamlit_coco.testing.domdiff. Not ported, because they belong to the Cockpit: the old docked
panel's CSS check (`coco_panel`) and the Cockpit's page filters in the message context.
"""

# ruff: noqa: E501, UP031, E731
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coco_fixture import ConversationCase  # noqa: E402

from streamlit_coco import assets, labels, window  # noqa: E402
from streamlit_coco.errors import CocoError  # noqa: E402
from streamlit_coco.features import Features  # noqa: E402
from streamlit_coco.testing import fixtures as fx  # noqa: E402

STATIC = Path(assets.__file__).resolve().parent / "static"
STATUS = {"not_installed", "not_connected", "connecting", "ready", "working", "waiting", "lost"}
THREAD = {"user", "scope", "steps", "step", "answer", "draft", "system", "asked"}
STEP_STATE = {"run", "ok", "bad", "no"}
WAIT = {"request", "question", "plan"}
KEYS = {
    "status",
    "setup",
    "profiles",
    "profile",
    "error",
    "prompts",
    "thread",
    "request",
    "queue",
    "restore",
    "pill",
    "rev",
    "wait",
    "mode",
    "options",
    "granted",
    "session",
    "hidden",
    "attach",
    "type_ahead",
    "problem",
    "profile_files",
    "send_held",
    "page_text",
}


def check_table(test: unittest.TestCase, table: dict) -> None:
    test.assertTrue(table["id"] and table["columns"])
    for column in table["columns"]:
        test.assertTrue(column["name"])
        test.assertIn(column["kind"], ("text", "number"))
    for row in table["rows"]:
        test.assertEqual(len(row), len(table["columns"]))
        test.assertTrue(all(isinstance(cell, str) for cell in row))
    test.assertTrue(table["total"] is None or table["total"] >= len(table["rows"]))


def check_block(test: unittest.TestCase, block: dict) -> None:
    """A block of an answer or of a step's detail (the playground additions of utils/coco_runtime.py)."""
    test.assertIn(block["type"], ("data", "text"))
    if block["type"] == "text":
        test.assertTrue(block["text"].strip())
        return
    test.assertTrue(block["id"])
    test.assertTrue(block["title"] is None or isinstance(block["title"], str))
    test.assertTrue(block["fields"] or block["tables"] or block["json"])
    for item in block["fields"]:
        test.assertTrue(item["label"] and isinstance(item["value"], str))
    for table in block["tables"]:
        check_table(test, table)
    test.assertTrue(block["json"] is None or isinstance(block["json"], str))


def check_step(test: unittest.TestCase, step: dict) -> None:
    test.assertEqual(step["kind"], "step")
    test.assertIn(step["state"], STEP_STATE)
    test.assertIsInstance(step["label"], str)
    test.assertTrue(step["id"])
    for block in step.get("blocks") or []:
        check_block(test, block)
    test.assertTrue(step.get("raw") is None or set(step["raw"]) == {"request", "result"})
    test.assertIsInstance(step.get("standing", False), bool)


def check_question(test: unittest.TestCase, question: dict) -> None:
    test.assertTrue(question["id"] and question["text"])
    if question["kind"] == "choice":
        test.assertIsInstance(question["multi"], bool)
        test.assertTrue(question["options"] or question["other"])
        for option in question["options"]:
            test.assertTrue(option["label"] and isinstance(option["description"], str))
        test.assertTrue(question["other"] is None or question["other"]["label"])
    else:
        test.assertEqual(question["kind"], "form")
        test.assertTrue(question["fields"])
        for item in question["fields"]:
            test.assertIn(item["type"], ("text", "longtext", "number", "choice"))
            test.assertTrue(
                item["id"]
                and item["label"]
                and isinstance(item["required"], bool)
                and isinstance(item["value"], str)
            )
            test.assertEqual(item["type"] == "choice", bool(item["choices"]))


def check_wait(test: unittest.TestCase, view: dict) -> None:
    """The one waiting block: a request keeps its facts in `request`; a question or a plan leaves `request` empty."""
    wait = view["wait"]
    test.assertIn(wait["kind"], WAIT)
    test.assertTrue(wait["id"])
    test.assertTrue(
        wait["more"] is None or (wait["more"]["count"] >= 2 and wait["more"]["next"] in WAIT)
    )
    if wait["kind"] == "request":
        test.assertEqual((view["request"] or {}).get("id"), wait["id"])
    else:
        test.assertIsNone(view["request"])
    if wait["kind"] == "question":
        test.assertIn(wait["source"], ("coco", "app"))
        test.assertTrue(wait["questions"])
        for question in wait["questions"]:
            check_question(test, question)
    elif wait["kind"] == "plan":
        test.assertTrue(wait["text"].strip())


def check_view(test: unittest.TestCase, view: dict) -> None:
    """The shape the window draws (section 9). Fails on a status, a kind or a field it would not know."""
    test.assertIn(view["status"], STATUS)
    test.assertIsInstance(view["prompts"], list)
    test.assertIsInstance(view["rev"], int)
    if view["status"] == "not_installed":
        test.assertIn(view["setup"]["missing"], ("package", "program"))
        test.assertTrue(view["setup"]["command"])
    for item in view["thread"]:
        test.assertIn(item["kind"], THREAD)
        if item["kind"] == "steps":
            test.assertIsInstance(item["folded"], bool)
            test.assertTrue(item["summary"] is None or item["summary"].strip())
            test.assertTrue(item["items"] or item["summary"])
            for part in item["items"]:
                if part["kind"] == "reasoning":
                    test.assertTrue(part["id"] and part["text"])
                else:
                    check_step(test, part)
        elif item["kind"] == "step":
            check_step(test, item)
        elif item["kind"] == "answer":
            test.assertIsInstance(item["streaming"], bool)
            test.assertIsInstance(item["text"], str)
            for block in item.get("blocks") or []:
                check_block(test, block)
        elif item["kind"] == "system":
            test.assertTrue(
                item["action"] in (None, "retry") or (item["action"]["label"] and item["id"])
            )
        elif item["kind"] == "asked":
            test.assertTrue(item["id"] and item["text"])
            test.assertIn(item["note"], (None, "Skipped", "Expired", "Cancelled"))
        elif item["kind"] in ("user", "draft"):
            test.assertTrue(item["id"])
            if item["kind"] == "user":
                test.assertTrue(all(isinstance(name, str) for name in item.get("files", [])))
                test.assertIsInstance(item.get("sending", 0), int)
                test.assertTrue(item.get("full") is None or item["full"].strip())
    request = view["request"]
    if request:
        test.assertIn(request["kind"], ("read", "change"))
        test.assertTrue(request["question"] and request["where"] and request["id"])
        test.assertEqual(request["kind"] == "change", bool(request["changes"]))
        test.assertEqual(request["kind"] == "read", bool(request["reads"]))
        test.assertTrue(all(part["text"] is not None for part in request["evidence"]))
    for queued in view["queue"]:
        test.assertTrue(queued["id"] and queued["text"])
        test.assertTrue(queued.get("note") is None or queued["note"].strip())
    if view["pill"]:
        test.assertIn(view["pill"]["kind"], ("request", "answer", "failed", "question", "plan"))
        test.assertTrue(view["pill"]["label"])
    check_playground(test, view)
    json.dumps(view)  # plain data only: it goes to the browser as JSON


def check_playground(test: unittest.TestCase, view: dict) -> None:
    """The keys the playground adds (all optional): a key the contract does not name fails."""
    test.assertEqual(set(view) - KEYS, set())
    if view.get("wait"):
        check_wait(test, view)
    if view["status"] == "waiting":
        test.assertTrue(view.get("wait") or view["request"])
    standing = (view["request"] or {}).get("standing")
    test.assertTrue(
        standing is None or all(standing[key] for key in ("id", "label", "covers", "until"))
    )
    mode = view.get("mode")
    test.assertTrue(
        mode is None or (mode["planning"] is True and isinstance(mode["can_carry_out"], bool))
    )
    for option in view.get("options") or []:
        test.assertIn(option["id"], ("plan", "latest", "shorten", "raw"))
        test.assertTrue(
            option["label"] and isinstance(option["on"], bool) and isinstance(option["sub"], str)
        )
    for granted in view.get("granted") or []:
        test.assertTrue(granted["id"] and granted["text"])
    for fact in view.get("session") or []:
        test.assertTrue(fact["label"] and fact["value"])
    test.assertGreaterEqual(view.get("hidden", 0), 0)
    attach = view.get("attach")
    test.assertTrue(
        attach is None
        or (
            isinstance(attach["multi"], bool)
            and isinstance(attach["accept"], list)
            and attach["max_mb"] > 0
            and isinstance(attach["existing"], list)
        )
    )
    test.assertIsInstance(view.get("type_ahead", False), bool)
    test.assertTrue(view.get("problem") is None or view["problem"].strip())
    for group in view.get("profile_files") or []:
        test.assertTrue(group["file"] and group["profiles"])
    for prompt in view["prompts"]:
        test.assertTrue(
            isinstance(prompt, str)
            or (prompt["title"] and prompt["text"] and isinstance(prompt["fill"], bool))
        )


class FixturesTest(unittest.TestCase):
    def test_every_fixture_has_the_contract_shape_and_survives_json(self) -> None:
        for name, view in fx.VIEWS.items():
            with self.subTest(name):
                check_view(self, view)
                self.assertEqual(json.loads(json.dumps(view)), view)

    def test_every_state_of_the_sheet_has_a_fixture(self) -> None:
        wanted = {
            "empty",
            "answer",
            "reminders",
            "pending",
            "not_connected_one",
            "not_connected_several",
            "not_connected_none",
            "not_installed_package",
            "not_installed_program",
            "menu",
            "step_run",
            "step_done_dots",
            "step_bad",
            "step_refused",
            "streaming",
            "folded",
            "ask_command",
            "ask_edit",
            "ask_create",
            "ask_replace",
            "after_allow",
            "after_decline",
            "expired",
            "pill_request",
            "pill_change",
            "pill_answer",
            "pill_failed",
            "long_evidence",
            "detail_open",
            "stopped",
            "long_step",
            "pinned",
            "lost",
            "typing_ahead",
            "waiting_typing",
            "queued",
            "confirm_idle",
            "confirm_working",
            "confirm_request",
            "confirm_queue",
            "confirm_disc",
        }
        self.assertEqual(wanted - set(fx.VIEWS), set())

    def test_the_status_of_a_pending_request_is_waiting_and_a_pill_names_what_is_asked(
        self,
    ) -> None:
        for name in ("ask_command", "ask_edit", "pill_request", "pill_change"):
            self.assertEqual(fx.VIEWS[name]["status"], "waiting")
        self.assertEqual(fx.VIEWS["pill_request"]["pill"]["label"], "Allow a command?")
        self.assertEqual(fx.VIEWS["pill_change"]["pill"]["label"], "Allow a file change?")


FRAMES = range(38, 87)


class PlaygroundFixturesTest(unittest.TestCase):
    """Frames 38 to 86 of the design sheet each have one named view, `f<nn>_...`; they are the shared truth of the window and the runtime."""

    def names(self, n: int) -> list[str]:
        return [name for name in fx.VIEWS if re.match(rf"f{n}_", name)]

    def test_every_frame_from_38_to_86_has_exactly_one_fixture(self) -> None:
        for n in FRAMES:
            self.assertEqual(len(self.names(n)), 1, f"frame {n}: {self.names(n)}")
        self.assertEqual(len([name for name in fx.VIEWS if re.match(r"f\d+_", name)]), len(FRAMES))

    def test_gestures_and_closed_windows_name_fixtures_and_known_steps(self) -> None:
        self.assertLessEqual(set(fx.GESTURES) | fx.CLOSED, set(fx.VIEWS))
        for name, steps in fx.GESTURES.items():
            for gesture in steps:
                self.assertIn(gesture[0], ("press", "type", "attach", "dragover"), name)

    def test_something_waits_exactly_when_the_status_says_so(self) -> None:
        for n in FRAMES:
            view = fx.VIEWS[self.names(n)[0]]
            self.assertEqual(view["status"] == "waiting", bool(view.get("wait")), self.names(n))

    def test_the_fixtures_between_them_use_every_key_and_item_the_contract_adds(self) -> None:
        views = [fx.VIEWS[self.names(n)[0]] for n in FRAMES]
        used = {key for view in views for key in view}
        self.assertEqual(
            {
                "wait",
                "mode",
                "options",
                "granted",
                "session",
                "hidden",
                "attach",
                "type_ahead",
                "problem",
                "profile_files",
            }
            - used,
            set(),
        )
        items = [
            item
            for view in fx.VIEWS.values()
            for entry in view["thread"]
            for item in [entry, *entry.get("items", [])]
        ]
        self.assertEqual({"asked", "reasoning"} - {item["kind"] for item in items}, set())
        self.assertEqual(
            {"question", "plan", "request"}
            - {view["wait"]["kind"] for view in views if view.get("wait")},
            set(),
        )
        self.assertEqual(
            {"question", "plan"} - {view["pill"]["kind"] for view in views if view.get("pill")},
            set(),
        )
        for key in ("blocks", "raw", "standing", "files", "full", "sending"):
            self.assertTrue(any(key in item for item in items), key)


class SameShapeTest(unittest.TestCase):
    def test_a_view_has_the_shape_of_its_fixture(self) -> None:
        fx.assert_same_shape(
            self,
            fx.VIEWS["f38_question_choice"],
            json.loads(json.dumps(fx.VIEWS["f38_question_choice"])),
        )
        wrong = json.loads(json.dumps(fx.VIEWS["f38_question_choice"]))
        wrong["wait"]["questions"][0]["multi"] = "no"
        with self.assertRaises(AssertionError):
            fx.assert_same_shape(self, wrong, fx.VIEWS["f38_question_choice"])
        del wrong["wait"]
        with self.assertRaises(AssertionError):
            fx.assert_same_shape(self, wrong, fx.VIEWS["f38_question_choice"])


class ConversationViewTest(ConversationCase):
    """A real conversation produces views the window can draw (the Cockpit's RuntimeContractTest, on the package's)."""

    def test_states_from_not_connected_to_a_pending_request_and_a_lost_connection(self) -> None:
        check_view(self, self.conv.view())
        self.conv.act({"type": "connect", "profile": "dev"})
        check_view(self, self.conv.view())
        self.tell({"t": "connected"})
        first = self.view()
        check_view(self, first)
        self.assertEqual(first["status"], "ready")
        self.send("Update the glossary")
        self.send("Then the risks")
        check_view(self, self.view())
        self.tell({"t": "lost", "message": "closed"})
        view = self.view()
        check_view(self, view)
        self.assertEqual((view["status"], view["pill"]["kind"]), ("lost", "failed"))

    def test_a_failure_with_retry_is_a_system_line_the_window_knows(self) -> None:
        self.connect()
        self.send("Hi")
        self.tell({"t": "error", "message": "timed out", "retry": True})
        view = self.view()
        check_view(self, view)
        self.assertEqual(view["thread"][-1]["action"], "retry")


class LabelsTest(unittest.TestCase):
    JS = "".join(
        p.read_text(encoding="utf-8")
        for p in [STATIC / "coco" / "coco.js", *sorted((STATIC / "coco" / "parts").glob("*.js"))]
    )

    def used(self) -> set[str]:
        """The keys the script reads: quoted whole in a call, or (a plural, a word) built from a quoted stem."""
        return {
            k
            for k in labels.DEFAULT
            if k.startswith("window.")
            and (
                f"'{k[7:]}'" in self.JS
                or k[7:]
                in ("wait.word_request", "wait.word_question", "wait.word_plan", "wait.word_other")
            )
        }

    def quoted(self) -> set[str]:
        return {"window." + k for k in re.findall(r"[LE]\(\s*'([a-z_]+(?:\.[a-z_]+)?)'", self.JS)}

    def test_every_sentence_the_window_reads_is_in_the_table_and_the_table_has_no_dead_key(
        self,
    ) -> None:
        used = self.used()
        self.assertEqual(sorted(self.quoted() - set(labels.DEFAULT)), [])
        window_keys = {k for k in labels.DEFAULT if k.startswith("window.")}
        self.assertEqual(sorted(window_keys - used), [])

    def test_the_conversations_sentences_are_in_the_same_table(self) -> None:
        from streamlit_coco.conversation import LABELS

        self.assertGreater(len(LABELS), 40)
        for key, text in LABELS.items():
            self.assertEqual(labels.DEFAULT["agent." + key], text)

    def test_a_host_override_reaches_the_window_and_the_conversation(self) -> None:
        from streamlit_coco.conversation import Conversation

        table = labels.table({"window.request.allow": "Autoriser", "mine.x": "y"})
        self.assertEqual(
            (table["window.request.allow"], table["mine.x"], table["window.request.decline"]),
            ("Autoriser", "y", "Decline"),
        )
        agent = lambda emit: SimpleNamespace(
            setup=lambda: None, close=lambda: None, profiles=lambda: []
        )  # noqa: E731
        conv = Conversation(
            Path("."),
            labels={"agent.pill_answer": "Reponse prete", "note_declined": "Refuse"},
            agent=agent,
        )
        self.assertEqual(
            (conv.t("pill_answer"), conv.t("note_declined")), ("Reponse prete", "Refuse")
        )


class HeldSendTest(ConversationCase):
    """Features(queue=False): the window never lets a message go while CoCo works, and a message that arrives anyway is handed back."""

    def test_the_view_says_send_is_held_and_a_refused_message_comes_back_in_restore(self) -> None:
        self.conv.features = Features(queue=False)
        self.connect()
        self.assertNotIn("send_held", self.view())
        self.send("first")
        self.assertTrue(self.view()["send_held"])
        self.send("second")
        view = self.view()
        self.assertEqual((self.conv.queue, view["restore"]), ([], "second"))
        self.assertIsNone(self.view()["restore"])  # handed over once

    def test_with_the_queue_nothing_is_held(self) -> None:
        self.connect()
        self.send("first")
        self.assertNotIn("send_held", self.view())

    def test_the_page_is_read_only_when_the_view_says_so(self) -> None:
        self.conv.features = Features(page_text=True)
        self.assertTrue(self.view()["page_text"])
        self.conv.features = Features()
        self.assertNotIn("page_text", self.view())
        self.assertIn("I.view.page_text", (STATIC / "coco" / "coco.js").read_text(encoding="utf-8"))


class WindowTest(unittest.TestCase):
    """The mount: the floor of Streamlit, the refused options, the action the window sends."""

    def test_an_older_streamlit_gets_one_clear_error_naming_the_version(self) -> None:
        with (
            mock.patch.object(window.st, "__version__", "1.40.0"),
            self.assertRaises(CocoError) as caught,
        ):
            window.ask_coco(".")
        self.assertIn(
            "Streamlit " + ".".join(map(str, window.STREAMLIT_FLOOR)), str(caught.exception)
        )

    def test_options_with_tool_lists_are_refused_naming_the_policy(self) -> None:
        with self.assertRaises(ValueError) as caught:
            window.ask_coco(".", options=SimpleNamespace(allowed_tools=["Read"]))
        self.assertIn("policy", str(caught.exception))

    def test_a_working_folder_that_is_missing_or_a_file_is_one_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "notes.md"
            file.write_text("x", encoding="utf-8")
            for cwd, why in ((Path(tmp) / "nowhere", "does not exist"), (file, "is not a folder")):
                with self.assertRaises(CocoError) as caught:
                    window.ask_coco(cwd)
                self.assertIn(why, str(caught.exception))
                self.assertIn(str(cwd.resolve()), str(caught.exception))

    def test_labels_that_change_between_two_runs_reach_the_window_and_the_conversation(
        self,
    ) -> None:
        from streamlit.testing.v1 import AppTest

        def page() -> None:
            import streamlit as st

            import streamlit_coco as st_coco

            french = {"window.header.title": "Assistant", "agent.pill_answer": "Reponse prete"}
            st_coco.ask_coco(".", labels=french if st.session_state.get("fr") else None)

        # each AppTest has its own registry of components: the cached mount belongs to one
        window._component.cache_clear()
        self.addCleanup(window._component.cache_clear)
        with mock.patch.dict("os.environ", {"STREAMLIT_COCO_AGENT": "mock"}):
            app = AppTest.from_function(page, default_timeout=30).run()
            self.assertFalse(app.exception)
            s = app.session_state[window._slot("coco")]
            conv = s["conv"]
            conv.items.append({"kind": "system", "text": conv.t("lost_text"), "detail": ""})
            self.assertEqual(
                (s["labels"]["window.header.title"], conv.t("pill_answer")),
                ("CoCo", labels.DEFAULT["agent.pill_answer"]),
            )
            app.session_state["fr"] = True
            app.run()
            self.assertFalse(app.exception)
            s = app.session_state[window._slot("coco")]
            self.assertIs(s["conv"], conv)  # the same conversation: nothing was started again
            self.assertEqual(
                (s["labels"]["window.header.title"], conv.t("pill_answer")),
                ("Assistant", "Reponse prete"),
            )
            # what was written stays as written
            self.assertEqual(conv.items[-1]["text"], labels.DEFAULT["agent.lost_text"])
            app.session_state["fr"] = False
            app.run()
            self.assertEqual(conv.t("pill_answer"), labels.DEFAULT["agent.pill_answer"])

    def test_whatever_one_run_of_the_window_finds_the_page_reruns_once_and_then_no_more(
        self,
    ) -> None:
        class Rerun(Exception):
            pass

        conv = SimpleNamespace(
            drain=mock.Mock(side_effect=[True, False, False, False]),  # the agent changed a file
            w_forms={"form": {}},
            form_result=lambda key, take=True: {"skipped": False, "values": {}},  # answered
            result_for=lambda key, take=True: {"text": "done", "data": None},  # finished
            features=Features(),
            view=dict,
        )
        s = {"conv": conv, "asked": {"job"}, "told": set(), "ack": 0, "token": 0, "sess": "x"}
        s |= {"labels": {}, "theme": {}}
        mounted, reruns = [], 0
        with (
            mock.patch.object(window.st, "session_state", {window._slot("k"): s}),
            mock.patch.object(window.st, "rerun", side_effect=Rerun),
            mock.patch.object(window, "_component", lambda: lambda **kw: mounted.append(kw)),
        ):
            for _ in range(4):
                try:
                    window._window.__wrapped__("k")
                except Rerun:
                    reruns += 1
        self.assertEqual(reruns, 1)  # three reasons found in one run: one page run
        self.assertEqual(len(mounted), 3)  # afterwards the window is drawn, the page is left alone
        self.assertEqual((s["told"], s["asked"]), ({"form"}, set()))

    def test_result_keeps_the_key_asked_while_pending_and_hands_over_once(self) -> None:
        pending = [None]
        conv = SimpleNamespace(result_for=lambda key: pending[0])
        state = {window._slot("k"): {"conv": conv, "asked": {"job"}}}
        with mock.patch.object(window.st, "session_state", state):
            handle = window.Window("k")
            self.assertIsNone(handle.result("job"))
            self.assertEqual(state[window._slot("k")]["asked"], {"job"})  # the page is still rerun
            pending[0] = {"text": "done", "data": None}
            self.assertEqual(handle.result("job"), {"text": "done", "data": None})
            self.assertEqual(state[window._slot("k")]["asked"], set())

    def test_latest_answer_does_not_hand_over_the_restore_text(self) -> None:
        from streamlit_coco.conversation import Conversation

        conv = Conversation(".", agent=lambda emit: SimpleNamespace(setup=lambda: None))
        conv.items.append({"kind": "answer", "id": "a1", "text": "Hello"})
        conv.restore = "typed text"
        with mock.patch.object(window.st, "session_state", {window._slot("k"): {"conv": conv}}):
            self.assertEqual(window.Window("k").latest_answer, "Hello")
        self.assertEqual(conv.restore, "typed text")

    def run_act(self, acts: list[dict]) -> tuple[list, dict]:
        calls, state = [], {}
        slot = window._slot("k")
        conv = SimpleNamespace(act=lambda action, ctx=None: calls.append((action, ctx)))
        state[slot] = {"conv": conv, "ack": 0, "context": lambda: {"page": "ctx"}}
        for act in acts:
            state[f"{slot}:component"] = SimpleNamespace(act=act)
            with mock.patch.object(window.st, "session_state", state):
                window._on_act("k")
        return calls, state[slot]

    def test_type_is_the_conversations_name_and_only_a_message_carries_its_context(self) -> None:
        calls, s = self.run_act(
            [
                {"a": "send", "text": "Hi", "seq": 1},
                {"a": "allow", "id": "r1", "seq": 2},
                {"a": "stop", "seq": 3},
            ]
        )
        self.assertEqual(
            calls,
            [
                ({"type": "send", "text": "Hi"}, {"page": "ctx"}),
                ({"type": "allow", "id": "r1"}, None),
                ({"type": "stop"}, None),
            ],
        )
        self.assertEqual(s["ack"], 3)

    def test_a_repeat_is_ignored_a_poll_is_not_forwarded_and_a_missing_state_is_not_an_error(
        self,
    ) -> None:
        calls, _ = self.run_act(
            [
                {"a": "send", "text": "Hi", "seq": 1},
                {"a": "send", "text": "Hi", "seq": 1},
                {"a": "poll", "seq": 2},
                {"a": "decline", "id": "r", "seq": 3},
            ]
        )
        self.assertEqual([c[0]["type"] for c in calls], ["send", "decline"])
        with mock.patch.object(window.st, "session_state", {}):
            window._on_act("k")  # the run after a page switch has no state: nothing happens

    def test_open_with_drafts_adds_one_bubble_each_and_asks_the_window_to_open(self) -> None:
        drafts = []
        s = {"conv": SimpleNamespace(add_drafts=drafts.extend), "token": 0}
        with mock.patch.object(window.st, "session_state", {window._slot("k"): s}):
            window.Window("k").open(drafts=[("To Hugo", "Hi Hugo"), "Plain"])
            window.Window("k").open()
        self.assertEqual(drafts, [("To Hugo", "Hi Hugo"), ("", "Plain")])
        self.assertEqual(s["token"], 2)


class AssetsTest(unittest.TestCase):
    def test_the_official_mark_is_used_and_everything_is_local(self) -> None:
        copy = (STATIC / "coco" / "coco-logo.svg").read_text(encoding="utf-8")
        self.assertIn(assets.spark(), copy)
        self.assertTrue((STATIC / "coco" / "coco-logo-round.svg").exists())
        for name in ("coco.js", "coco.css"):
            text = (STATIC / "coco" / name).read_text(encoding="utf-8")
            for forbidden in (
                "fetch(",
                "@import",
                "<script",
                "<link",
                "XMLHttpRequest",
                "googleapis",
                "cdn.",
            ):
                self.assertNotIn(forbidden, text, f"{name} must stay local: {forbidden}")
            self.assertIsNone(re.search(r"url\(\s*['\"]?https?:", text))

    def test_the_parts_are_joined_in_a_fixed_order_and_stay_local(self) -> None:
        self.assertEqual(
            assets.GROUPS, ("questions", "plans", "standing", "data", "files", "page", "session")
        )
        for group in assets.GROUPS:
            for name in (f"parts/{group}.js", f"parts/{group}.css"):
                text = (STATIC / "coco" / name).read_text(encoding="utf-8")
                for forbidden in (
                    "fetch(",
                    "@import",
                    "<script",
                    "<link",
                    "XMLHttpRequest",
                    "googleapis",
                    "cdn.",
                ):
                    self.assertNotIn(forbidden, text, f"{name} must stay local: {forbidden}")
                self.assertIsNone(re.search(r"url\(\s*['\"]?https?:", text))
        bundle = assets.js()
        self.assertTrue(
            bundle.startswith((STATIC / "coco" / "coco.js").read_text(encoding="utf-8"))
        )
        at = [bundle.rindex(f"part('{g}'") for g in assets.GROUPS]
        self.assertEqual(at, sorted(at))

    def test_the_font_is_shipped_with_its_licence_and_the_window_is_isolated(self) -> None:
        for weight in assets.WEIGHTS:
            self.assertGreater(
                (STATIC / "fonts" / f"Montserrat-{weight}.ttf").stat().st_size, 100_000
            )
        self.assertIn(
            "SIL OPEN FONT LICENSE", (STATIC / "fonts" / "OFL.txt").read_text(encoding="utf-8")
        )
        self.assertIn("const COCO_FONTS", assets.js())
        self.assertNotIn("const COCO_FONTS =", assets.js(False))
        source = Path(window.__file__).read_text(encoding="utf-8")
        self.assertIn("isolate_styles=True", source)
        self.assertNotIn("st.chat_input", source)

    def test_the_theme_has_its_defaults_in_the_css_and_nothing_of_a_host_is_named(self) -> None:
        css = assets.css()
        for name in (
            "accent",
            "on-accent",
            "surface",
            "text",
            "muted",
            "border",
            "danger",
            "font",
            "radius",
        ):
            self.assertIn(f"--coco-{name}:", css)
        everything = css + assets.js(False)
        for host in ("st-key-shell_rail", "st-key-ab_", "00-tokens", "cockpit_coco"):
            self.assertNotIn(host, everything)


class Audit(HTMLParser):
    """Only the tags and attributes the renderer writes may exist in its output."""

    TAGS = {
        "p",
        "br",
        "b",
        "i",
        "code",
        "pre",
        "ul",
        "ol",
        "li",
        "a",
        "blockquote",
        "hr",
        "div",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }
    ATTRS = {"a": {"href", "target", "rel"}, "p": {"class", "role", "aria-level"}, "div": {"class"}}

    def audit(self, test: unittest.TestCase, html: str) -> None:
        self.test = test
        self.feed(html)

    def handle_starttag(self, tag, attrs) -> None:
        self.test.assertIn(tag, self.TAGS)
        for name, value in attrs:
            self.test.assertIn(name, self.ATTRS.get(tag, set()), f"<{tag} {name}>")
            if name == "href":
                self.test.assertRegex(value, r"(?i)^(https?://|mailto:)")


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class MarkdownTest(unittest.TestCase):
    """An answer is Markdown from a model: rendered by the window with every tag written by the window itself."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.module = Path(cls._tmp.name) / "coco.mjs"
        cls.module.write_text(
            (STATIC / "coco" / "coco.js").read_text(encoding="utf-8"), encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def render(self, *texts: str) -> list[str]:
        script = (
            "import {renderMarkdown} from %s; const t = JSON.parse(process.argv[1]); console.log(JSON.stringify(t.map(renderMarkdown)));"
            % json.dumps(self.module.as_uri())
        )
        done = subprocess.run(
            ["node", "--input-type=module", "-e", script, json.dumps(list(texts))],
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        return json.loads(done.stdout)

    def test_the_bundle_with_its_parts_loads_and_a_part_that_fails_costs_only_itself(self) -> None:
        extra = "part('t1', (C) => { C.thread.x = () => null; });\npart('t2', () => { throw new Error('boom'); });\npart('t3', (C) => { C.block.y = () => ''; });\n"
        module = Path(self._tmp.name) / "bundle.mjs"
        module.write_text(
            assets.js()
            + "\n"
            + extra
            + "export const seen = [typeof COCO.thread.x, typeof COCO.block.y];\n",
            encoding="utf-8",
        )
        script = "import {seen} from %s; console.log(JSON.stringify(seen));" % json.dumps(
            module.as_uri()
        )
        done = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        self.assertEqual(json.loads(done.stdout), ["function", "function"])

    def test_all_seven_parts_register_without_an_error_and_use_the_core_slots(self) -> None:
        module = Path(self._tmp.name) / "seven.mjs"
        tail = (
            "export const report = {errors: errors.length, wait: Object.keys(COCO.wait).sort(), panel: Object.keys(COCO.panel).sort(), menu: COCO.menu.map((m) => m.order),"
            " local: [...COCO.local], handlers: Object.keys(handlers).sort(), escape: COCO.escape.length, change: COCO.change.length, input: COCO.input.length};\n"
        )
        module.write_text(
            "const errors = []; console.error = (...a) => errors.push(a);\n"
            + assets.js()
            + "\n"
            + tail,
            encoding="utf-8",
        )
        script = "import {report} from %s; console.log(JSON.stringify(report));" % json.dumps(
            module.as_uri()
        )
        done = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        report = json.loads(done.stdout)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["wait"], ["plan", "question"])
        self.assertEqual(report["panel"], ["details", "without_asking"])
        self.assertEqual(report["local"], ["shorten"])
        for action in (
            "answer",
            "skip",
            "approve_plan",
            "decline_plan",
            "carry_out",
            "revoke",
            "show_earlier",
            "show_all",
            "data-larger",
            "attach",
            "profiles",
            "pick",
            "copy",
        ):
            self.assertIn(action, report["handlers"])
        self.assertGreaterEqual(
            report["escape"], 3
        )  # the plan's reason, the wider view, the list of profiles
        self.assertGreaterEqual(report["change"], 3)
        self.assertEqual(report["menu"], [70, 80])

    def test_markup_in_a_model_text_is_text(self) -> None:
        hostile = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "**<b onmouseover=x>bold</b>**",
            "`<script>`",
            "```\n<script>alert(1)</script>\n```",
            "[click](javascript:alert(1))",
            "[click](JaVaScRiPt:alert(1))",
            "[x](data:text/html;base64,AAAA)",
            '[a](https://example.org/?q="onmouseover="x)',
            "| <script> | b |\n|---|---|\n| <img src=x onerror=y> | 2 |",
            "# <iframe src=x>",
            "> <svg onload=x>",
            '- <a href="javascript:x">y</a>',
        ]
        for text, html in zip(hostile, self.render(*hostile)):
            with self.subTest(text):
                Audit().audit(self, html)

    def test_the_formatting_a_model_uses_is_kept(self) -> None:
        text = "## Title\n\nSome **bold**, *italic* and `code`.\n\n- one\n- two\n\n1. first\n2. second\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\nx < y\n```\n\nSee [the guide](https://example.org/a?b=1&c=2)."
        html = self.render(text)[0]
        for wanted in (
            '<p class="mdh" role="heading" aria-level="3">Title</p>',
            "<b>bold</b>",
            "<i>italic</i>",
            "<code>code</code>",
            "<ul><li>one</li><li>two</li></ul>",
            "<ol><li>first</li><li>second</li></ol>",
            "<th>a</th>",
            "<td>2</td>",
            "<pre><code>x &lt; y</code></pre>",
            'href="https://example.org/a?b=1&amp;c=2"',
            'rel="noopener noreferrer"',
        ):
            self.assertIn(wanted, html)

    def test_nested_lists_images_links_and_emphasis(self) -> None:
        html = self.render("- a\n  - b\n    - c\n- d\n\n1. one\n   - inner\n2. two")[0]
        self.assertIn("<ul><li>a<ul><li>b<ul><li>c</li></ul></li></ul></li><li>d</li></ul>", html)
        self.assertIn("<ol><li>one<ul><li>inner</li></ul></li><li>two</li></ol>", html)
        html = self.render(
            "![a chart](https://example.org/x.png) and ![](https://example.org/y.png)"
        )[0]
        self.assertNotIn("<img", html)
        self.assertNotIn("example.org", html)  # an image is never fetched, and not linked either
        self.assertIn("[image: a chart]", html)
        for text in (
            "[a](file:///etc/passwd)",
            "[a](//evil.example/x)",
            "[a](vbscript:x)",
            "[a](JAVASCRIPT:x)",
            "[a](data:text/html,x)",
        ):
            self.assertNotIn("<a ", self.render(text)[0], text)
        self.assertEqual(
            self.render("[a](mailto:x@y.org)")[0].count('rel="noopener noreferrer"'), 1
        )
        html = self.render("# Title\n\n__strong__ and a\nsecond line")[0]
        for wanted in ('role="heading"', "<b>strong</b>", "a<br>second line"):
            self.assertIn(wanted, html)

    def test_a_huge_or_hostile_answer_is_rendered_in_bounded_time(self) -> None:
        script = r"""import {renderMarkdown} from %s; const out = [];
            for (const b of ['[x](', '*a ', '_a ', '`', '| a |\n|---|\n', '- ']) { const t0 = Date.now(); renderMarkdown(b.repeat(150000)); out.push(Date.now() - t0); }
            const t0 = Date.now(); renderMarkdown('## T\n\nsome **text** with `code` and [a link](https://example.org).\n\n'.repeat(15000)); out.push(Date.now() - t0);
            console.log(JSON.stringify(out));""" % json.dumps(self.module.as_uri())
        done = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        for ms in json.loads(done.stdout):
            self.assertLess(ms, 5000)

    def test_a_streamed_partial_text_does_not_break(self) -> None:
        for html in self.render("```\nunclosed fence", "**not closed", "| a | b |", "- ", ""):
            self.assertNotIn("<script", html)


FIELDS = [
    {"id": "who", "label": "Name", "type": "text"},
    {"id": "n", "label": "Days", "type": "number", "required": False},
    {
        "id": "mood",
        "label": "Mood",
        "type": "choice",
        "choices": ["Calm", "Worried"],
        "value": "Calm",
    },
]


class FormTest(ConversationCase):
    """coco.form: the application's form waits with CoCo's questions, with no agent and no connection."""

    def ask(self) -> dict:
        self.conv.ask_form("k", "Who is away?", FIELDS)
        return self.view()

    def answer(self, **values) -> None:
        wait = self.view()["wait"]
        self.conv.act(
            {
                "type": "answer",
                "id": wait["id"],
                "answers": [{"id": "q1", "picked": [], "other": None, "fields": values}],
            }
        )

    def test_it_waits_as_an_application_question_without_a_connection(self) -> None:
        view = self.ask()
        check_view(self, view)
        wait = view["wait"]
        self.assertEqual(
            (view["status"], wait["kind"], wait["source"], wait["questions"][0]["kind"]),
            ("not_connected", "question", "app", "form"),
        )
        self.assertEqual(
            [f["type"] for f in wait["questions"][0]["fields"]], ["text", "number", "choice"]
        )
        self.assertEqual(view["pill"]["kind"], "question")
        self.assertIsNone(self.conv.form_result("k"))

    def test_an_answer_comes_back_once_and_is_not_asked_again(self) -> None:
        self.ask()
        self.answer(who="Lea", n="3", mood="Calm")
        self.assertNotIn("wait", self.view())
        self.assertEqual(
            self.conv.form_result("k"),
            {"skipped": False, "values": {"who": "Lea", "n": "3", "mood": "Calm"}},
        )
        self.assertIsNone(self.conv.form_result("k"))
        self.ask()
        self.assertNotIn("wait", self.view())

    def test_a_skipped_form_reads_skipped_true_with_no_values(self) -> None:
        wait = self.ask()["wait"]
        self.conv.act({"type": "skip", "id": wait["id"]})
        self.assertEqual(self.conv.form_result("k"), {"skipped": True, "values": {}})

    def test_it_is_asked_once_per_key_and_stop_leaves_it(self) -> None:
        self.connect()
        self.send("work")
        self.conv.ask_form("k", "Who is away?", FIELDS)
        self.conv.ask_form("k", "Who is away?", FIELDS)
        self.assertEqual(self.view()["wait"]["more"], None)
        self.conv.act({"type": "stop"})
        self.assertEqual(self.view()["wait"]["source"], "app")

    def test_an_answer_with_only_optional_fields_empty_still_counts(self) -> None:
        self.ask()
        self.answer(who="", n="", mood="")
        self.assertEqual(self.conv.form_result("k")["skipped"], False)


class StructuredTest(unittest.TestCase):
    """Structured output is the session's: the adapter's `structured` event is what `result(key)` hands over."""

    def test_a_request_of_the_page_gets_the_structured_data_once(self) -> None:
        import tempfile
        import time

        from coco_fixture import make_folder

        from streamlit_coco.conversation import Conversation
        from streamlit_coco.policy import FolderPolicy
        from streamlit_coco.testing.scripted import ScriptedAgent

        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(Path(tmp))
            conv = Conversation(
                folder,
                policy=FolderPolicy(folder),
                agent=lambda emit: ScriptedAgent(emit, delay=0, connect_delay=0),
            )
            try:
                conv.act({"type": "connect", "profile": "mock"})
                end = time.monotonic() + 10
                while conv.view()["status"] != "ready" and time.monotonic() < end:
                    conv.drain()
                    time.sleep(0.01)
                self.assertTrue(
                    conv.request_from_page(
                        "Get the status", "give me the structured status", {}, key="status"
                    )
                )
                got = None
                while got is None and time.monotonic() < end:
                    conv.drain()
                    got = conv.result_for("status", take=False)
                    time.sleep(0.01)
                self.assertEqual(
                    got["data"]["Week"], "2026-W41"
                )  # the payload itself, not a drawing of it
                self.assertEqual(conv.result_for("status")["data"]["Phase"], "6 of 7")
                self.assertIsNone(conv.result_for("status"))  # handed over once
            finally:
                conv.close()

    def test_ask_has_no_schema_argument(self) -> None:
        import inspect

        self.assertNotIn("schema", inspect.signature(window.Window.ask).parameters)


class DefaultsNameNoHostTest(unittest.TestCase):
    def test_no_default_sentence_names_the_cockpit(self) -> None:
        for key, text in labels.DEFAULT.items():
            self.assertNotIn("ockpit", text, key)
