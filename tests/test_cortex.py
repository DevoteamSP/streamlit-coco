"""Ask CoCo, the Cortex adapter without the SDK: the pre-tool gate, event translation, setup
    detection,
the host's options (cortex.py)."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coco_fixture import make_folder

import streamlit_coco.session as session_module
from streamlit_coco import cortex
from streamlit_coco.cortex import Agent, Translator, build_prompt, classify_error
from streamlit_coco.options import CocoOptions
from streamlit_coco.policy import Command, FolderPolicy


def event(type_: str, **kw) -> SimpleNamespace:
    base = dict(
        type=type_,
        text=None,
        delta=None,
        name=None,
        tool_use_id=None,
        input=None,
        content=None,
        is_error=None,
        message=None,
        subtype=None,
        metadata={},
    )
    return SimpleNamespace(**{**base, **kw})


def delta(kind: str, key: str, value: str) -> SimpleNamespace:
    return event(
        "stream_event",
        delta=value,
        metadata={"event": {"type": "content_block_delta", "delta": {"type": kind, key: value}}},
    )


class TranslatorTest(unittest.TestCase):
    def feed(self, *events) -> list[dict]:
        translator, out = Translator(), []
        for item in events:
            out += translator.feed(item)
        return out

    def test_only_text_deltas_reach_the_conversation(self) -> None:
        out = self.feed(
            delta("thinking_delta", "thinking", "hidden reasoning"),
            delta("input_json_delta", "partial_json", "hidden tool JSON"),
            delta("text_delta", "text", "Visible answer"),
            event("thinking", text="hidden reasoning"),
            event("system", subtype="init"),
        )
        self.assertEqual(out, [{"t": "text", "text": "Visible answer"}])

    def test_a_block_snapshot_is_passed_on_when_something_follows(self) -> None:
        out = self.feed(
            event("assistant_text", text="Je lis."),
            event("tool_use", tool_use_id="r1", name="Read", input={"file_path": "x"}),
            event("tool_result", tool_use_id="r1", content="ok", is_error=False),
        )
        self.assertEqual(
            out,
            [
                {"t": "snapshot", "text": "Je lis."},
                {"t": "tool_use", "id": "r1", "name": "Read", "input": {"file_path": "x"}},
                {"t": "tool_result", "id": "r1", "content": "ok", "error": False},
            ],
        )

    def test_the_result_echo_is_not_a_snapshot(self) -> None:
        out = self.feed(
            event("assistant_text", text="Je lis. Réponse."),
            event("result", is_error=False, metadata={"result": "Je lis. Réponse."}),
        )
        self.assertEqual(out, [{"t": "result", "text": "Je lis. Réponse.", "error": False}])

    def test_the_last_block_stays_a_snapshot_when_the_result_is_an_aggregate(self) -> None:
        out = self.feed(
            event("assistant_text", text="Réponse."),
            event("assistant_text", text="Je lis.Réponse."),
            event("result", is_error=False, metadata={"result": "Je lis.Réponse."}),
        )
        self.assertEqual(
            out,
            [
                {"t": "snapshot", "text": "Réponse."},
                {"t": "result", "text": "Je lis.Réponse.", "error": False},
            ],
        )

    def test_an_error_result_and_an_error_event_are_failures(self) -> None:
        self.assertEqual(
            self.feed(event("result", is_error=True, metadata={"result": "Invalid request"})),
            [{"t": "error", "message": "Invalid request", "retry": False}],
        )
        self.assertEqual(
            self.feed(event("error", message="Timed out waiting")),
            [{"t": "error", "message": "Timed out waiting", "retry": True}],
        )
        self.assertEqual(self.feed(event("error", message="Connection closed"))[0]["t"], "lost")

    def test_classification(self) -> None:
        for message, kind in [
            ("Connection reset", "lost"),
            ("broken pipe", "lost"),
            ("request timed out", "retry"),
            ("API overloaded", "retry"),
            ("Invalid argument", "fail"),
            ("", "fail"),
        ]:
            with self.subTest(message=message):
                self.assertEqual(classify_error(message), kind)


class AgentTest(unittest.TestCase):
    def test_the_module_imports_without_the_sdk_and_without_streamlit(self) -> None:
        code = (
            "import sys; sys.modules['cortex_code_agent_sdk'] = None;"
            "import streamlit_coco.cortex as m;"
            "print(m.Agent(lambda e: None).setup()['missing'], 'streamlit' in sys.modules)"
        )
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout.strip()), (0, "package False"), done.stderr)

    def test_a_missing_package_and_a_missing_program_are_told_apart(self) -> None:
        agent = Agent(lambda e: None)
        with patch.object(cortex.importlib.util, "find_spec", return_value=None):
            self.assertEqual(agent.setup(), {"missing": "package", "command": cortex._PACKAGE})
        with (
            patch.object(cortex.importlib.util, "find_spec", return_value=object()),
            patch.object(cortex, "cortex_cli", return_value=None),
        ):
            setup = agent.setup()
            self.assertEqual(setup["missing"], "program")
            self.assertNotEqual(setup["command"], cortex._PACKAGE)
        with (
            patch.object(cortex.importlib.util, "find_spec", return_value=object()),
            patch.object(cortex, "cortex_cli", return_value="/bin/cortex"),
        ):
            self.assertIsNone(agent.setup())

    def test_the_cortex_program_is_found_on_the_path_not_in_a_lab(self) -> None:
        with patch.object(cortex.shutil, "which", return_value="/somewhere/cortex") as which:
            self.assertEqual(cortex.cortex_cli(), "/somewhere/cortex")
            which.assert_called_once_with("cortex")

    def test_the_program_is_found_in_the_installers_folder_when_the_path_is_stale(self):
        with patch.object(cortex.shutil, "which", side_effect=[None, "/installed/cortex"]) as which:
            self.assertEqual(cortex.cortex_cli(), "/installed/cortex")
            self.assertIn("cortex", which.call_args.kwargs["path"])
        self.assertNotIn(
            "coco-lab", Path(cortex.__file__).read_text(encoding="utf-8").replace("# coco-lab", "")
        )

    def test_the_installers_shim_is_resolved_to_the_program(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            program, shim = Path(tmp) / "cortex.exe", Path(tmp) / "cortex.CMD"
            program.write_text("", encoding="utf-8")
            shim.write_text(f'@"{program}" %*', encoding="utf-8")
            with patch.object(cortex.shutil, "which", return_value=str(shim)):
                self.assertEqual(cortex.cortex_cli(), str(program))
            shim.write_text('@"C:/gone/cortex.exe" %*', encoding="utf-8")
            with patch.object(cortex.shutil, "which", return_value=str(shim)):
                self.assertEqual(cortex.cortex_cli(), str(shim))

    def test_the_profiles_are_the_connections_of_this_computer_and_none_when_unreadable(
        self,
    ) -> None:
        with patch("streamlit_coco.diagnostics.list_snowflake_connections", return_value=["dev"]):
            self.assertEqual(Agent(lambda e: None).profiles(), ["dev"])
        with patch("streamlit_coco.diagnostics.list_snowflake_connections", side_effect=OSError):
            self.assertEqual(Agent(lambda e: None).profiles(), [])

    def test_every_request_carries_the_rights_of_its_own_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(Path(tmp))
            listed = Command("Look at what changed", ["git", "status", "--short"], "what changed")
            policy = FolderPolicy(folder, commands=[listed])
            ctx = {"rights": policy.rights(), "scope": {"name": "alpha"}}
            prompt = build_prompt("What can you do?", ctx)
            self.assertIn(cortex.json.dumps(policy.rights(), ensure_ascii=False), prompt)
            self.assertTrue(prompt.endswith("What can you do?"))
            for command in policy.rights()["commands"]:
                self.assertIn(command["line"] + chr(10), prompt)
            self.assertNotIn(
                "Command lines you may propose",
                build_prompt("x", {"rights": FolderPolicy(folder).rights()}),
            )

    def test_the_hosts_instructions_are_added_once_and_stay_out_of_the_facts(self) -> None:
        prompt = build_prompt(
            "x", {"instructions": "Answer only about the audit.", "user": {"name": "Lea"}}
        )
        self.assertEqual(prompt.count("Answer only about the audit."), 1)
        facts = prompt.split("Context of this request: ")[1].split("\n\nUser message")[0]
        self.assertEqual(json.loads(facts), {"user": {"name": "Lea"}})
        self.assertNotIn("Answer only about the audit", build_prompt("x", {}))

    def test_the_prompt_is_general_and_says_nothing_of_any_host(self) -> None:
        prompt = build_prompt("x", {})
        for word in ("Cockpit", "Spec-First", "make cockpit", "budget", "timesheet", "member"):
            self.assertNotIn(word, prompt)

    def test_the_prompt_asks_for_the_five_things_of_the_conversation(self) -> None:
        prompt = build_prompt("x", {"rights": {}})
        for phrase in (
            "language of the user",
            "one short sentence",
            "never as done",
            "So call the tool",
            "Name the files",
        ):
            self.assertIn(phrase, prompt)

    def test_the_prompt_says_that_every_tool_may_be_proposed_and_the_application_asks(self) -> None:
        prompt = build_prompt("x", {"rights": {}})
        for phrase in (
            "any tool you have",
            "Nothing is refused",
            "one sentence of text that says what it shows",
            "asks the user for agreement",
            "use your question tool",
            "plan tool",
            "qualify every object name",
            "Answer in the language",
        ):
            self.assertIn(phrase, prompt)
        self.assertNotIn(
            "exactly those listed", prompt
        )  # the rights no longer limit what may be proposed


class StubSession:
    """What the adapter uses of CocoSession."""

    def __init__(self, options=None) -> None:
        self.options, self.listeners, self.started = options, [], 0
        self.sent, self.cancelled, self.closed, self.needs_polling, self.fail = [], 0, 0, True, None
        self.ready_error, self.is_ready, self.last_error = None, True, None
        self.modes, self.mode_error = [], None

    def add_event_listener(self, callback) -> None:
        self.listeners.append(callback)

    def start(self) -> None:
        self.started += 1

    def ensure_ready(self, timeout: float) -> None:
        if self.ready_error:
            raise self.ready_error

    def send(self, prompt: str) -> None:
        if self.fail:
            raise self.fail
        self.sent.append(prompt)

    def set_permission_mode(self, mode: str) -> None:
        if self.mode_error:
            raise self.mode_error
        self.modes.append(mode)

    def cancel(self) -> None:
        self.cancelled += 1

    def close(self) -> None:
        self.closed += 1
        if self.fail:
            raise self.fail


class AgentSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.events: list[dict] = []
        self.agent = Agent(self.events.append)
        self.agent.session = self.session = StubSession()
        self.ctx = {"rights": {}, "scope": {"name": "alpha"}}

    def test_a_message_goes_to_the_session_with_the_requests_policy(self) -> None:
        self.agent.send("Hello", self.ctx, "policy")
        self.assertEqual(self.agent.gate.policy, "policy")
        self.assertTrue(self.session.sent[0].endswith("Hello"))

    def test_the_rights_sent_with_a_message_name_what_runs_without_asking_now(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = FolderPolicy(make_folder(Path(tmp)))
            self.agent.gate._granted["commands"] = "runs any command"
            self.agent.send("Hello", {"rights": {}}, policy)
            self.assertIn("runs any command", self.session.sent[0])

    def test_a_session_that_cannot_take_the_message_ends_the_turn_with_a_failure(self) -> None:
        self.session.fail = RuntimeError("worker loop is unavailable")
        self.agent.send("Hello", self.ctx, "policy")
        self.assertEqual(
            self.events, [{"t": "error", "message": "worker loop is unavailable", "retry": False}]
        )
        self.agent.session = None  # not connected at all
        self.agent.send("Hello", self.ctx, "policy")
        self.assertEqual(self.events[-1]["t"], "error")

    def test_stop_cancels_the_session_and_reports_when_it_really_stopped(self) -> None:
        self.agent.send("Hello", self.ctx, "policy")
        self.agent.stop()
        self.assertEqual(self.session.cancelled, 1)
        time.sleep(0.3)
        self.assertEqual(self.events, [])  # still polling: not stopped yet
        self.session.needs_polling = False
        deadline = time.monotonic() + 3
        while not self.events and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertEqual(self.events, [{"t": "stopped"}])

    def test_stop_says_nothing_when_the_turn_ended_by_itself(self) -> None:
        self.agent.send("Hello", self.ctx, "policy")
        self.agent.stop()
        self.agent._on_event(event("result", is_error=False, metadata={"result": "Done"}))
        self.session.needs_polling = False
        time.sleep(0.5)
        self.assertEqual([e["t"] for e in self.events], ["result"])

    def test_closing_cancels_closes_and_can_be_repeated(self) -> None:
        self.agent.close()
        self.agent.close()
        self.assertEqual((self.session.cancelled, self.session.closed), (2, 2))
        self.session.fail = RuntimeError("already closed")
        with self.assertLogs(cortex._LOG, "WARNING"):
            self.agent.close()  # a failing close is not an error for the caller
        Agent(self.events.append).close()  # never connected


class ConnectTest(unittest.TestCase):
    """connect() against fakes of the two packages it imports: what the session is started with,
    and what is closed."""

    def setUp(self) -> None:
        self.events: list[dict] = []
        self.sessions: list[StubSession] = []
        sessions = self.sessions
        fake = lambda options: sessions.append(StubSession(options)) or sessions[-1]  # noqa: E731
        sdk = SimpleNamespace(
            HookMatcher=lambda **kw: SimpleNamespace(**kw),
            PermissionResultAllow=lambda updated_input=None: ("allow", updated_input),
            PermissionResultDeny=lambda message: ("deny", message),
        )
        patcher = patch.dict(sys.modules, {"cortex_code_agent_sdk": sdk})
        patcher.start()
        self.addCleanup(patcher.stop)
        sess = patch.object(session_module, "CocoSession", fake)
        sess.start()
        self.addCleanup(sess.stop)
        self.agent = Agent(self.events.append)
        self.addCleanup(self.agent.close)

    def options(self):
        return self.sessions[-1].options

    def test_the_session_starts_in_the_projects_folder_with_no_tool_list_and_no_mcp(self) -> None:
        self.agent.connect("dev", "C:/projects")
        options, extra = self.options(), self.options().extra_sdk_options
        self.assertEqual(
            (
                options.connection,
                options.cwd,
                options.require_approval_for,
                options.permission_mode,
            ),
            ("dev", "C:/projects", [], "default"),
        )
        for name in (
            "allowed_tools",
            "disallowed_tools",
        ):  # a list makes the program refuse the rest before any hook
            self.assertNotIn(name, extra)
            self.assertFalse(getattr(options, name))
        self.assertTrue(extra["no_mcp"])
        self.assertEqual(extra["env"]["PYTHONUTF8"], "1")
        self.assertEqual(self.sessions[-1].started, 1)
        self.assertEqual(options.hooks["PreToolUse"][0].timeout, cortex.HOOK_TIMEOUT)

    def test_the_callback_agrees_only_to_what_the_gate_let_through(self) -> None:
        import asyncio

        self.agent.connect("dev", "C:/projects")
        callback = self.options().extra_sdk_options["can_use_tool"]
        self.assertEqual(
            asyncio.run(callback("Write", {"file_path": "x", "content": "x"}, None)),
            ("deny", "Not agreed."),
        )

    def test_the_hook_turns_whatever_goes_wrong_into_a_denial(self) -> None:
        import asyncio

        self.agent.connect("dev", "C:/projects")
        hook = self.options().hooks["PreToolUse"][0].hooks[0]
        self.agent.gate.decide = lambda *a: (_ for _ in ()).throw(RuntimeError("boom"))
        with self.assertLogs(cortex._LOG, "ERROR"):
            out = asyncio.run(hook({"tool_name": "Read", "tool_input": {}}, "t1", None))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("boom", out["reason"])

    def test_the_chosen_configuration_file_must_be_one_the_program_reads_and_hold_the_profile(
        self,
    ) -> None:
        with (
            tempfile.TemporaryDirectory() as home,
            patch.object(cortex.Path, "home", return_value=Path(home)),
        ):
            (Path(home) / ".snowflake").mkdir()
            (Path(home) / ".snowflake" / "connections.toml").write_text(
                "[dev]\nrole = 'X'\n", encoding="utf-8"
            )
            self.agent.connect("dev", "C:/projects", "connections.toml")
            self.assertEqual(
                (len(self.sessions), [e["t"] for e in self.events if e["t"] != "connected"]),
                (1, []),
            )
            for file, profile in (
                ("work.toml", "dev"),
                ("connections.toml", "other"),
                ("config.toml", "dev"),
            ):
                self.events.clear()
                self.agent.connect(profile, "C:/projects", file)
                self.assertEqual(self.events[0]["t"], "connect_failed")
                self.assertIn(file, self.events[0]["message"])
            self.assertEqual(len(self.sessions), 1)

    def test_a_second_connect_closes_the_first_session(self) -> None:
        self.agent.connect("dev", "C:/projects")
        self.agent.connect("dev", "C:/projects")
        first, second = self.sessions
        self.assertEqual((first.closed, second.closed), (1, 0))
        self.assertIs(self.agent.session, second)

    def test_a_session_that_never_gets_ready_is_closed_and_reported_once(self) -> None:
        session = StubSession()
        session.ready_error = TimeoutError("not ready")
        self.agent.session = session
        self.agent._watch(session)
        self.assertEqual(self.events, [{"t": "connect_failed", "message": "not ready"}])
        self.assertEqual(session.closed, 1)

    def test_a_session_that_ends_is_closed_and_reported_lost(self) -> None:
        session = StubSession()
        session.is_ready, session.last_error = False, "process exited"
        self.agent.session = session
        self.agent._watch(session)
        self.assertEqual(
            self.events, [{"t": "connected"}, {"t": "lost", "message": "process exited"}]
        )
        self.assertEqual(session.closed, 1)


QUESTION_INPUT = {
    "questions": [
        {
            "questionId": "q-1",
            "question": "Which week?",
            "header": "Week",
            "multiSelect": False,
            "options": [
                {
                    "label": "2026-W41",
                    "description": "This week",
                    "freeForm": False,
                    "isCancel": False,
                },
                {"label": "2026-W40", "description": "", "freeForm": False, "isCancel": False},
                {
                    "label": "Something else",
                    "description": "Type your own feedback",
                    "freeForm": True,
                    "isCancel": False,
                },
                {
                    "label": "I need clarification, let's chat about this",
                    "description": "",
                    "freeForm": False,
                    "isCancel": True,
                },
            ],
        },
        {
            "question": "Which parts?",
            "multiSelect": True,
            "options": [{"label": "Risks"}, {"label": "Budget"}],
        },
    ]
}
PLAN_INPUT = {
    "plan": "1. Read the specs\n2. Draft the report",
    "question": "Is Friday the deadline?",
}


class WaitsTest(unittest.TestCase):
    """The program asks the host a question or presents a plan (control request can_use_tool):
    events out, the user's word back."""

    def setUp(self) -> None:
        self.events: list[dict] = []
        sessions = self.sessions = []
        fake = lambda options: sessions.append(StubSession(options)) or sessions[-1]  # noqa: E731
        sdk = SimpleNamespace(
            HookMatcher=lambda **kw: SimpleNamespace(**kw),
            PermissionResultAllow=lambda updated_input=None: ("allow", updated_input),
            PermissionResultDeny=lambda message: ("deny", message),
        )
        patcher = patch.dict(sys.modules, {"cortex_code_agent_sdk": sdk})
        patcher.start()
        self.addCleanup(patcher.stop)
        sess = patch.object(session_module, "CocoSession", fake)
        sess.start()
        self.addCleanup(sess.stop)
        self.agent = Agent(self.events.append)
        self.addCleanup(self.agent.close)
        self.agent.connect("dev", "C:/projects")
        deadline = time.monotonic() + 3
        while not self.events and time.monotonic() < deadline:
            time.sleep(0.005)
        self.events.clear()  # the "connected" of the session's watch
        self.callback = self.sessions[-1].options.extra_sdk_options["can_use_tool"]
        self.hook = self.sessions[-1].options.hooks["PreToolUse"][0].hooks[0]

    def call(self, name, tool_input, context=None) -> dict:
        out: dict = {}
        thread = threading.Thread(
            target=lambda: out.update(result=asyncio.run(self.callback(name, tool_input, context)))
        )
        thread.start()
        out["thread"] = thread
        deadline = time.monotonic() + 3
        while not self.events and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.005)
        return out

    def finish(self, out) -> tuple:
        out["thread"].join(3)
        return out["result"]

    def test_a_question_becomes_an_event_with_what_the_program_added_taken_out(self) -> None:
        out = self.call("AskUserQuestion", QUESTION_INPUT, SimpleNamespace(tool_use_id="ask_1_2"))
        event_ = self.events[0]
        self.assertEqual(
            (event_["t"], event_["source"], event_["tool_id"]), ("question", "coco", "ask_1_2")
        )
        first, second = event_["questions"]
        self.assertEqual(
            first,
            {
                "id": "q-1",
                "text": "Which week?",
                "kind": "choice",
                "multi": False,
                "other": {"label": "Something else"},
                "options": [
                    {"label": "2026-W41", "description": "This week"},
                    {"label": "2026-W40", "description": ""},
                ],
            },
        )
        self.assertEqual(
            (second["id"], second["multi"], second["other"]), ("q2", True, None)
        )  # no free answer where the asker gave none
        self.agent.skip(event_["id"])
        self.finish(out)

    def test_the_answer_goes_back_as_the_program_expects_it(self) -> None:
        out = self.call("AskUserQuestion", QUESTION_INPUT)
        self.agent.answer(
            self.events[0]["id"],
            [
                {"id": "q-1", "picked": [], "other": "The week before last"},
                {"id": "q2", "picked": ["Risks", "Budget"], "other": None},
            ],
        )
        verdict, updated = self.finish(out)
        self.assertEqual(verdict, "allow")
        self.assertEqual(
            updated,
            {
                "questions": QUESTION_INPUT["questions"],
                "answers": {"Which week?": "The week before last", "Which parts?": "Risks, Budget"},
            },
        )

    def test_the_hook_lets_the_question_and_the_plan_through_and_gives_them_the_model_calls_id(
        self,
    ) -> None:
        self.agent.gate.decide = lambda *a: self.fail("the user is asked, not the gate")
        for name in ("AskUserQuestion", "ask_user_question", "ExitPlanMode", "EnterPlanMode"):
            out = asyncio.run(self.hook({"tool_name": name, "tool_input": {}}, "toolu_9", None))
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "allow")
        call = self.call("AskUserQuestion", QUESTION_INPUT, SimpleNamespace(tool_use_id="ask_1_2"))
        self.assertEqual(
            self.events[0]["tool_id"], "toolu_9"
        )  # the id of the step the thread already holds
        self.agent.skip(self.events[0]["id"])
        self.finish(call)

    def test_skipping_and_a_stop_leave_nothing_hanging(self) -> None:
        out = self.call("AskUserQuestion", QUESTION_INPUT)
        self.agent.skip(self.events[0]["id"])
        self.agent.answer(
            self.events[0]["id"], [{"id": "q-1", "picked": ["2026-W41"]}]
        )  # too late: the first answer stands
        self.assertEqual(self.finish(out), ("deny", "The user skipped the question."))
        self.events.clear()
        out = self.call("AskUserQuestion", QUESTION_INPUT)
        self.agent.stop()
        self.assertEqual(self.finish(out)[0], "deny")
        self.assertEqual(
            asyncio.run(self.callback("AskUserQuestion", QUESTION_INPUT, None))[0], "deny"
        )  # after a stop: at once, no event
        self.assertEqual([e["t"] for e in self.events], ["question"])
        self.agent.send("again", {"rights": {}}, "policy")  # the next request asks again
        self.events.clear()
        out = self.call("AskUserQuestion", QUESTION_INPUT)
        self.assertEqual(self.events[0]["t"], "question")
        self.agent.skip(self.events[0]["id"])
        self.finish(out)

    def test_a_question_nobody_answers_expires_as_skipped(self) -> None:
        self.agent.expiry = 0.05
        out = self.call("AskUserQuestion", QUESTION_INPUT, SimpleNamespace(tool_use_id="ask_1_2"))
        self.assertEqual(self.finish(out)[0], "deny")
        self.assertEqual(
            self.events[-1], {"t": "expired", "id": self.events[0]["id"], "tool_id": "ask_1_2"}
        )

    def test_a_plan_is_an_event_and_approval_or_decline_goes_back(self) -> None:
        out = self.call("ExitPlanMode", PLAN_INPUT, SimpleNamespace(tool_use_id="plan_1"))
        self.assertEqual(
            {k: v for k, v in self.events[0].items() if k != "id"},
            {
                "t": "plan",
                "tool_id": "plan_1",
                "text": "1. Read the specs\n2. Draft the report\n\nIs Friday the deadline?",
            },
        )
        self.agent.approve_plan(self.events[0]["id"])
        self.assertEqual(self.finish(out), ("allow", {"message": "Plan approved."}))
        self.events.clear()
        out = self.call("ExitPlanMode", {"plan": "Do it"})
        self.agent.decline_plan(self.events[0]["id"], "  Leave the budget out  ")
        self.assertEqual(self.finish(out), ("deny", "Leave the budget out"))
        self.events.clear()
        out = self.call("ExitPlanMode", {"plan": "Do it"})
        self.agent.decline_plan(self.events[0]["id"], "")
        self.assertEqual(self.finish(out), ("deny", "The plan was not approved."))

    def test_other_tools_keep_the_gates_agreement(self) -> None:
        self.assertEqual(
            asyncio.run(self.callback("Bash", {"command": "ls"}, None)), ("deny", "Not agreed.")
        )

    def test_planning_is_the_programs_plan_mode_and_survives_a_late_connect(self) -> None:
        self.agent.set_planning(True)
        self.assertEqual(self.sessions[-1].modes, ["plan"])
        self.agent.set_planning(False)
        self.assertEqual(self.sessions[-1].modes, ["plan", "default"])
        self.sessions[-1].mode_error = RuntimeError("no client yet")
        with self.assertLogs(cortex._LOG, "WARNING"):
            self.agent.set_planning(True)  # not an error for the caller
        self.agent.connect("dev", "C:/projects")
        self.assertEqual(self.sessions[-1].options.permission_mode, "plan")
        Agent(self.events.append).set_planning(True)  # never connected

    def test_a_standing_tick_reaches_the_gate_only_when_set_and_a_revoke_is_forwarded(self) -> None:
        calls = []
        self.agent.gate.answer = lambda *a: calls.append(a)
        self.agent.decide("r1", True)
        self.agent.decide("r2", False, True)
        self.assertEqual(calls, [("r1", True), ("r2", False, True)])
        self.agent.gate.revoke = lambda pid: calls.append(("revoked", pid))
        self.agent.revoke("p1")
        self.assertEqual(calls[-1], ("revoked", "p1"))


class DataTest(unittest.TestCase):
    """Structured output and SQL results reach the conversation as `structured` events, whatever
    shape the program gives."""

    def feed(self, *events, **kw) -> list[dict]:
        translator, out = Translator(**kw), []
        for item in events:
            out += translator.feed(item)
        return out

    def test_the_structured_output_of_the_result_is_fields_tables_and_json(self) -> None:
        data = {
            "name": "spec-first",
            "version": "2.2",
            "dependencies": ["streamlit", "pandas"],
            "features": [{"name": "foo", "weeks": 3}, {"name": "bar", "weeks": 12}],
            "nested": {"a": 1},
        }
        out = self.feed(
            event("result", is_error=False, structured_output=data, metadata={"result": "Done"})
        )
        self.assertEqual([e["t"] for e in out], ["structured", "result"])
        block = out[0]["data"]
        self.assertEqual(
            (out[0]["tool_id"], block["type"], block["fields"]),
            (
                None,
                "data",
                [
                    {"label": "name", "value": "spec-first"},
                    {"label": "version", "value": "2.2"},
                    {"label": "dependencies", "value": "streamlit, pandas"},
                ],
            ),
        )
        self.assertEqual(
            block["tables"],
            [
                {
                    "id": "result-data-t1",
                    "label": "features",
                    "total": 2,
                    "rows": [["foo", "3"], ["bar", "12"]],
                    "columns": [
                        {"name": "name", "kind": "text"},
                        {"name": "weeks", "kind": "number"},
                    ],
                }
            ],
        )
        self.assertEqual(json.loads(block["json"]), data)

    def test_the_recorded_structured_result_of_the_package(self) -> None:
        line = json.loads(
            '{"type":"result","subtype":"success","duration_ms":500,"is_error":false,"structured_output":{"features":[{"name":"foo"}]}}'
        )
        out = self.feed(
            event(
                "result",
                is_error=False,
                structured_output=line["structured_output"],
                metadata={"result": None},
            )
        )
        self.assertEqual(out[0]["data"]["tables"][0]["rows"], [["foo"]])

    def test_a_result_without_structured_output_or_with_odd_ones_never_crashes(self) -> None:
        self.assertEqual(
            [e["t"] for e in self.feed(event("result", is_error=False, metadata={"result": "x"}))],
            ["result"],
        )
        for odd in ("plain text", 42, [1, 2], {"rows": "nope"}, {"rows": [1, 2]}, {"a": {"b": 1}}):
            with self.subTest(odd=odd):
                out = self.feed(
                    event("result", is_error=False, structured_output=odd, metadata={"result": "x"})
                )
                self.assertEqual(out[-1]["t"], "result")
                self.assertEqual(out[0]["data"]["tables"], [])

    def sql(self, content, error=False, name="sql_execute") -> list[dict]:
        return self.feed(
            event("tool_use", tool_use_id="s1", name=name, input={"sql": "select 1"}),
            event("tool_result", tool_use_id="s1", content=content, is_error=error),
        )

    def test_a_sql_result_in_the_programs_text_is_data_on_the_tool_result(self) -> None:
        text = (
            '3 row(s) returned.\n\nCUSTOMER,ORDERS\n\nAcme,1530\n"Dupont, SA",1433\nZeta,12\n'
            '{"type": "json", "json": {"query_id": "01c7"}}'
        )
        out = self.sql(text)
        self.assertEqual(
            [e["t"] for e in out], ["tool_use", "tool_result"]
        )  # one carrier: no second block for the same table
        self.assertEqual(
            out[1]["data"],
            {
                "columns": ["CUSTOMER", "ORDERS"],
                "total": 3,
                "rows": [["Acme", "1530"], ["Dupont, SA", "1433"], ["Zeta", "12"]],
            },
        )
        self.assertEqual(out[1]["content"], text)  # the text stays for the plain result

    def test_a_sql_result_as_data_is_data_too(self) -> None:
        for content in (
            {
                "sqlData": {
                    "columns": ["DB", "SCHEMA"],
                    "rows": [["SPEC_FIRST", "COCKPIT"]],
                    "truncated": False,
                }
            },
            json.dumps(
                {
                    "columns": [{"name": "DB"}, {"name": "SCHEMA"}],
                    "rows": [["SPEC_FIRST", "COCKPIT"]],
                    "row_count": 1,
                }
            ),
            json.dumps([{"DB": "SPEC_FIRST", "SCHEMA": "COCKPIT"}]),
        ):
            with self.subTest(content=str(content)[:30]):
                self.assertEqual(
                    self.sql(content)[1]["data"],
                    {"columns": ["DB", "SCHEMA"], "rows": [["SPEC_FIRST", "COCKPIT"]], "total": 1},
                )

    def test_the_rows_kept_are_capped_and_the_total_says_how_many_there_were(self) -> None:
        data = self.sql({"columns": ["N"], "rows": [[i] for i in range(500)]})[1]["data"]
        self.assertEqual((len(data["rows"]), data["total"]), (200, 500))

    def test_what_is_not_a_table_stays_text(self) -> None:
        for content, error in (
            ("Statement executed.", False),
            ("1 row(s) returned.\n\nA,B\n\n1", False),
            ("", False),
            (None, False),
            ("<error>Tool denied", True),
            ('{"rows": [[1]]}', False),
        ):
            with self.subTest(content=content):
                self.assertNotIn("data", self.sql(content, error)[1])
        self.assertNotIn("data", self.sql("1 row(s) returned.\n\nA\n\n1", name="Bash")[1])

    def test_raw_texts_ride_on_the_tool_events_only_when_asked(self) -> None:
        both = (
            event("tool_use", tool_use_id="r1", name="Read", input={"file_path": "x"}),
            event("tool_result", tool_use_id="r1", content="line 1\nline 2", is_error=False),
        )
        plain = self.feed(*both)
        self.assertNotIn("raw", plain[0])
        self.assertNotIn("raw", plain[1])
        use, result = self.feed(*both, raw=True)
        self.assertEqual(
            json.loads(use["raw"]["request"]), {"name": "Read", "input": {"file_path": "x"}}
        )
        self.assertEqual(
            (json.loads(result["raw"]["request"])["name"], result["raw"]["result"]),
            ("Read", "line 1\nline 2"),
        )

    def test_reasoning_is_passed_on_only_when_the_host_switches_it_on(self) -> None:
        thinking = event("thinking", text="The user wants a status.")
        self.assertEqual(self.feed(thinking), [])
        self.assertEqual(
            self.feed(thinking, reasoning=True),
            [{"t": "reasoning", "text": "The user wants a status."}],
        )
        agent = Agent(lambda e: None)
        agent.set_reasoning(True)
        agent.set_raw(True)
        self.assertEqual((agent._translator.reasoning, agent._translator.raw), (True, True))
        agent.session = StubSession()
        agent.send("x", {"rights": {}}, "policy")  # the next turn's translator keeps the switches
        self.assertEqual((agent._translator.reasoning, agent._translator.raw), (True, True))


class FactsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        (self.home / ".snowflake").mkdir()
        (self.home / ".snowflake" / "connections.toml").write_text(
            '[dev]\naccount = "acme-eu"\nuser = "jdoe"\npassword = "S3CRET-PASSWORD"\n'
            'role = "ANALYST_EU"\nwarehouse = "WH_XS"\ndatabase = "SPEC_FIRST"\n'
            'private_key_path = "C:/keys/private.p8"\n\n[prod]\n'
            'account = "acme"\ntoken = "S3CRET-TOKEN"\n',
            encoding="utf-8",
        )
        (self.home / ".snowflake" / "config.toml").write_text(
            'default_connection_name = "legacy"\n[connections.legacy]\nrole = "OLD"\n',
            encoding="utf-8",
        )
        (self.home / ".snowflake" / "notes.toml").write_text("not [valid toml", encoding="utf-8")
        patcher = patch.object(cortex.Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.agent = Agent(lambda e: None)

    def test_the_connection_files_and_their_profiles_by_file(self) -> None:
        self.assertEqual(
            self.agent.connection_files(),
            [
                {"file": "connections.toml", "profiles": ["dev", "prod"]},
                {"file": "config.toml", "profiles": ["legacy"]},
                {"file": "notes.toml", "profiles": []},
            ],
        )
        self.assertNotIn("S3CRET", json.dumps(self.agent.connection_files()))

    def test_no_snowflake_folder_is_no_file(self) -> None:
        with patch.object(cortex.Path, "home", return_value=self.home / "nowhere"):
            self.assertEqual(self.agent.connection_files(), [])

    def test_the_facts_are_what_the_profile_and_the_programs_first_message_say_and_never_a_secret(
        self,
    ) -> None:
        self.agent.profile = "dev"
        self.agent._program = (
            "C:/Users/me/AppData/Local/cortex/1.1.104+041358.66de1c44636f/cortex.exe"
        )
        self.assertEqual(
            self.agent.session_facts(),
            [
                {"label": "Connection", "value": "dev"},
                {"label": "Role", "value": "ANALYST_EU"},
                {"label": "Warehouse", "value": "WH_XS"},
                {"label": "Database", "value": "SPEC_FIRST"},
                {"label": "Program version", "value": "1.1.104"},
            ],
        )
        session = "0f8fad5b-d9cb-469f-a165-70867728950e"
        self.agent._on_event(
            event(
                "system",
                subtype="init",
                metadata={
                    "session_id": session,
                    "model": "claude-sonnet-4-6",
                    "claude_code_version": "unknown",
                },
            )
        )
        facts = {f["label"]: f["value"] for f in self.agent.session_facts()}
        self.assertEqual((facts["Model"], facts["Session"]), ("claude-sonnet-4-6", session))
        self.assertNotIn("S3CRET", json.dumps(facts))
        self.assertNotIn("jdoe", json.dumps(facts))

    def test_a_legacy_profile_and_an_unknown_one(self) -> None:
        self.agent.profile = "legacy"
        self.assertIn({"label": "Role", "value": "OLD"}, self.agent.session_facts())
        self.agent._cfg, self.agent.profile = None, "nobody"
        self.assertEqual(self.agent.session_facts(), [{"label": "Connection", "value": "nobody"}])
        self.assertEqual(
            Agent(lambda e: None).session_facts(), []
        )  # never connected: nothing to say

    def test_the_program_version_falls_back_on_the_first_message(self) -> None:
        self.agent.profile, self.agent._program = "dev", "C:/cortex/bin/cortex.cmd"
        self.agent._init = {"claude_code_version": "1.0.9"}
        self.assertIn({"label": "Program version", "value": "1.0.9"}, self.agent.session_facts())


class OptionsTest(unittest.TestCase):
    """The host's CocoOptions: what is used, and what is refused."""

    def test_a_tool_list_is_refused_with_a_word_naming_the_policy(self) -> None:
        for field in (
            {"allowed_tools": ["Read"]},
            {"disallowed_tools": ["Bash"]},
            {"require_approval_for": ["Write"]},
            {"require_approval_for": lambda *a: True},
        ):
            with self.subTest(field=list(field)), self.assertRaises(ValueError) as caught:
                Agent(lambda e: None, CocoOptions(**field))
            self.assertIn("policy", str(caught.exception))
        Agent(lambda e: None, CocoOptions(model="m"))  # nothing refused

    def test_model_turns_servers_schema_and_program_reach_the_session(self) -> None:
        sessions = []
        sdk = SimpleNamespace(
            HookMatcher=lambda **kw: SimpleNamespace(**kw),
            PermissionResultAllow=None,
            PermissionResultDeny=None,
        )
        host = CocoOptions(
            model="auto",
            max_turns=5,
            mcp_servers={"x": {"command": "y"}},
            output_schema={"type": "object"},
            cli_path="/my/cortex",
            connection="dev",
        )
        with (
            patch.dict(sys.modules, {"cortex_code_agent_sdk": sdk}),
            patch.object(
                session_module,
                "CocoSession",
                lambda options: sessions.append(StubSession(options)) or sessions[-1],
            ),
        ):
            agent = Agent(lambda e: None, host)
            agent.connect("", "C:/work")
            agent.close()
        options = sessions[0].options
        self.assertEqual(
            (
                options.model,
                options.max_turns,
                options.cli_path,
                options.connection,
                options.output_schema,
            ),
            ("auto", 5, "/my/cortex", "dev", {"type": "object"}),
        )
        self.assertEqual(options.mcp_servers, {"x": {"command": "y"}})
        self.assertNotIn("no_mcp", options.extra_sdk_options)
        self.assertEqual(options.require_approval_for, [])
