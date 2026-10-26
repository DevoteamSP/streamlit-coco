"""The managed agent (managed.py) on a scripted stream of the Cortex Agent SDK: no login.

What is proven: the stream reaches the window as the same events the Cortex Code agent gives; a
call that asks reaches the policy and the gate, and only the user's Allow becomes "Allow this
command"; every other path (decline, expiry, stop, an option missing) is a decline; the run is
always created with `always_ask`; a failed connection says why; the three agents keep the
surface of backend.py.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from streamlit_coco.backend import AgentBackend
from streamlit_coco.cortex import Agent
from streamlit_coco.managed import (
    ManagedAgent,
    ManagedOptions,
    build_prompt,
    choose_option,
    managed_agent,
    options_from_connection,
    permission_of,
)
from streamlit_coco.policy import FolderPolicy
from streamlit_coco.testing.managed_fake import FakeClient, text, tool_use
from streamlit_coco.testing.scripted import ScriptedAgent

BASH = tool_use(
    "t1",
    "Bash",
    {"command": "echo hi"},
    options=["Allow this command", "Allow all bash for this session", "Deny"],
)
FINISHED = [{"event": "response", "status": "completed"}]


class Run:
    """A connected ManagedAgent on a fake client, and the events it emitted."""

    def __init__(self, turns, options=None, fail=None) -> None:
        self.events: list[dict] = []
        self.client = FakeClient(turns, fail)
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.agent = ManagedAgent(
            self.events.append,
            options or ManagedOptions(account="org-acc", token="x"),
            client_factory=lambda: self.client,
        )
        self.agent.connect("org-acc", str(self.folder))

    def until(self, condition, timeout: float = 5.0) -> None:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if condition():
                return
            time.sleep(0.01)
        raise AssertionError(f"timed out; events: {self.events}")

    def kinds(self) -> list[str]:
        return [e["t"] for e in self.events]

    def send(self, message: str = "go") -> None:
        self.until(lambda: "connected" in self.kinds() or "connect_failed" in self.kinds())
        self.agent.send(message, {}, FolderPolicy(self.folder))

    def answer(self, allow: bool) -> None:
        self.until(lambda: "request" in self.kinds())
        request = next(e for e in self.events if e["t"] == "request")
        self.agent.decide(request["id"], allow)

    def close(self) -> None:
        self.agent.close()
        self.tmp.cleanup()


class StreamTest(unittest.TestCase):
    def test_an_answer_reaches_the_window_as_text_and_a_result(self) -> None:
        run = Run([text("Hello there")])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "result" in run.kinds())
        self.assertEqual(run.kinds(), ["connected", "text", "result"])
        self.assertEqual(run.events[1]["text"], "Hello there")
        self.assertEqual(run.events[-1], {"t": "result", "text": "Hello there", "error": False})
        self.assertEqual(run.client.sent[0][0], "send")

    def test_a_tool_that_does_not_wait_is_a_step_and_a_result(self) -> None:
        free = tool_use("t1", "Read", {"path": "a.txt"})
        done = {
            "event": "response.tool_result",
            "tool_use_id": "t1",
            "status": "success",
            "content": [{"type": "text", "text": "file text"}],
        }
        run = Run([[free, done, *text("Read it")]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "result" in run.kinds())
        use = next(e for e in run.events if e["t"] == "tool_use")
        self.assertEqual((use["id"], use["name"]), ("t1", "Read"))
        result = next(e for e in run.events if e["t"] == "tool_result")
        self.assertEqual((result["content"], result["error"]), ("file text", False))
        self.assertNotIn("request", run.kinds())  # nothing asked: nothing was sent back
        self.assertEqual([k for k, _ in run.client.sent], ["send"])

    def test_a_failed_tool_is_an_error_step(self) -> None:
        bad = {
            "event": "response.tool_result",
            "tool_use_id": "t1",
            "status": "error",
            "content": [{"type": "text", "text": "boom"}],
        }
        run = Run([[tool_use("t1", "Read", {}), bad, *text("It failed")]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "result" in run.kinds())
        self.assertTrue(next(e for e in run.events if e["t"] == "tool_result")["error"])

    def test_an_error_event_is_an_error_for_the_window(self) -> None:
        run = Run([[{"event": "error", "message": "Error during execution"}]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "error" in run.kinds() or "lost" in run.kinds())
        self.assertNotIn("result", run.kinds())

    def test_a_cancelled_run_is_not_a_result(self) -> None:
        run = Run([[{"event": "response", "status": "cancelled"}]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: {"error", "lost"} & set(run.kinds()))
        self.assertNotIn("result", run.kinds())


class ApprovalTest(unittest.TestCase):
    def test_allow_sends_the_one_call_option_and_the_run_goes_on(self) -> None:
        run = Run([[BASH, *FINISHED], text("Ran it")])
        self.addCleanup(run.close)
        run.send()
        run.answer(True)
        run.until(lambda: "result" in run.kinds())
        self.assertEqual(run.client.sent[1], ("decisions", [("t1", "Allow this command")]))
        request = next(e for e in run.events if e["t"] == "request")
        self.assertEqual(request["tool_id"], "t1")  # the request sits on the step
        self.assertEqual(run.events[-1]["text"], "Ran it")

    def test_decline_sends_deny_with_the_reason_and_the_run_still_ends(self) -> None:
        run = Run([[BASH, *FINISHED], text("I did not run it")])
        self.addCleanup(run.close)
        run.send()
        run.answer(False)
        run.until(lambda: "result" in run.kinds())
        kind, decisions = run.client.sent[1]
        self.assertEqual(
            (kind, decisions), ("decisions", [("t1", "Deny", "Declined by the user.")])
        )

    def test_without_a_one_call_option_nothing_is_allowed(self) -> None:
        odd = tool_use(
            "t1",
            "Bash",
            {"command": "echo hi"},
            options=["Run it", "Allow all bash for this session", "Deny"],
        )
        run = Run([[odd, *FINISHED], text("ok")])
        self.addCleanup(run.close)
        run.send()
        run.answer(True)  # the user agrees, but the request offers no way to say so
        run.until(lambda: "result" in run.kinds())
        self.assertEqual(run.client.sent[1][1][0][:2], ("t1", "Deny"))
        self.assertIn("refused", run.kinds())

    def test_a_server_verdict_is_not_a_question(self) -> None:
        event = tool_use(
            "t1",
            "Bash",
            {},
            options=["Allow this command", "Allow all bash for this session", "Deny"],
        )
        event["permission"]["verdict"] = "allow"
        self.assertIsNone(permission_of(event))
        self.assertIsNone(permission_of(tool_use("t1", "Bash", {}, options=[])))
        self.assertIsNone(permission_of(tool_use("t1", "Bash", {})))
        self.assertEqual(
            permission_of(BASH),
            ("t1", ("Allow this command", "Allow all bash for this session", "Deny")),
        )

    def test_stop_while_the_user_is_asked_sends_nothing(self) -> None:
        run = Run([[BASH, *FINISHED]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "request" in run.kinds())
        run.agent.stop()
        run.until(lambda: "stopped" in run.kinds())
        self.assertEqual([k for k, _ in run.client.sent], ["send"])

    def test_a_conflict_on_cancel_is_not_a_warning(self) -> None:
        """Live: stopping while a request waits cancels a run the service already ended."""

        class ConflictError(Exception):
            pass

        run = Run([[BASH, *FINISHED]])
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "request" in run.kinds())
        original = run.client.cancelled

        def refuse():
            raise ConflictError("Agent run was already completed.")

        run.agent._turn.cancel = refuse
        with self.assertNoLogs("streamlit_coco.managed", "WARNING"):
            run.agent.stop()
            run.until(lambda: "stopped" in run.kinds())
        self.assertEqual(original, [])


class PromptTest(unittest.TestCase):
    """Nothing of this computer goes to Snowflake: found live, the agent once answered with the
    developer's local working folder."""

    CTX = {
        "scope": {"name": "Demo", "folder": "/Users/someone/secret-project"},
        "rights": {"summary": "Reading in /Users/someone/secret-project is free."},
        "instructions": "Answer for the finance team.",
        "user": {"name": "Ada", "language": "fr"},
    }

    def test_the_local_folder_and_rights_are_not_sent(self) -> None:
        prompt = build_prompt("Hello", self.CTX)
        self.assertNotIn("/Users/someone", prompt)
        self.assertNotIn("secret-project", prompt)
        self.assertNotIn("rights", prompt)

    def test_what_is_not_local_is_kept(self) -> None:
        prompt = build_prompt("Hello", self.CTX)
        self.assertIn("Answer for the finance team.", prompt)
        self.assertIn('"scope": {"name": "Demo"}', prompt)
        self.assertIn('"user": {"name": "Ada", "language": "fr"}', prompt)
        self.assertTrue(prompt.endswith("User message:\nHello"))

    def test_the_agent_is_told_it_runs_in_the_sandbox_and_has_no_question_tool(self) -> None:
        prompt = build_prompt("x", {})
        self.assertIn("Snowflake's sandbox", prompt)
        self.assertIn("no question tool and no plan tool", prompt)
        self.assertNotIn("working in the folder you were started in", prompt)

    def test_a_message_reaches_the_agent_with_that_prompt(self) -> None:
        run = Run([text("ok")])
        self.addCleanup(run.close)
        run.until(lambda: "connected" in run.kinds())
        run.agent.send("Hello", self.CTX, FolderPolicy(run.folder))
        run.until(lambda: "result" in run.kinds())
        sent = run.client.sent[0][1]
        self.assertNotIn("/Users/someone", sent)
        self.assertTrue(sent.endswith("User message:\nHello"))


class OptionsTest(unittest.TestCase):
    def test_the_run_always_asks_snowflake_too(self) -> None:
        for options in (
            ManagedOptions(account="a", token="t"),
            ManagedOptions(account="a", token="t", workspace_mounts=[{"name": "W"}]),
        ):
            self.assertEqual(options.spec()["permission_policy"], "always_ask")
        run = Run([text("x")], ManagedOptions(account="a", token="t", instructions="Be brief."))
        self.addCleanup(run.close)
        run.send()
        run.until(lambda: "result" in run.kinds())
        self.assertEqual(run.client.spec["permission_policy"], "always_ask")
        self.assertEqual(run.client.spec["instructions"], "Be brief.")
        self.assertEqual(run.client.spec["models"], {"orchestration": "auto"})

    def test_the_options_say_what_is_missing(self) -> None:
        with self.assertRaises(ValueError):
            ManagedOptions(token="t").client()
        with self.assertRaises(ValueError):
            ManagedOptions(account="a").client()

    def test_the_option_that_answers(self) -> None:
        self.assertEqual(choose_option(["Allow this command", "Deny"], True), "Allow this command")
        self.assertEqual(choose_option(["Allow Once", "Deny"], True), "Allow Once")
        self.assertEqual(choose_option(["allow once", "deny"], False), "deny")
        self.assertIsNone(choose_option(["Allow Always", "Deny"], True))
        # the server's own standing grant is never what an Allow means
        self.assertIsNone(choose_option(["Allow all bash for this session", "Deny"], True))
        self.assertEqual(choose_option(["Allow Once", "Reject it"], False), "Reject it")
        self.assertIsNone(choose_option(["Allow Once"], False))


class ConnectionTest(unittest.TestCase):
    def test_a_failed_connection_says_why(self) -> None:
        run = Run([], fail="Programmatic access token is invalid.")
        self.addCleanup(run.close)
        run.until(lambda: "connect_failed" in run.kinds())
        self.assertIn("invalid", run.events[0]["message"])

    def test_the_window_gets_an_account_and_facts_without_a_secret(self) -> None:
        run = Run([text("x")], ManagedOptions(account="org-acc", token="SECRET-TOKEN"))
        self.addCleanup(run.close)
        run.until(lambda: "connected" in run.kinds())
        self.assertEqual(run.agent.profiles(), ["org-acc"])
        self.assertEqual(run.agent.connection_files(), [])
        self.assertNotIn("SECRET", str(run.agent.session_facts()))
        self.assertIsNone(run.agent.setup())

    def test_close_closes_the_client(self) -> None:
        run = Run([text("x")])
        run.until(lambda: "connected" in run.kinds())
        run.close()
        self.assertTrue(run.client.closed)


class FromConnectionTest(unittest.TestCase):
    """options_from_connection logs in with the connector and gives the SDK its session token."""

    def _home(self, toml: str):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        folder = Path(home.name) / ".snowflake"
        folder.mkdir()
        (folder / "connections.toml").write_text(toml, encoding="utf-8")
        return mock.patch("streamlit_coco.diagnostics.Path.home", return_value=Path(home.name))

    def _connect(self, **kwargs):
        conn = SimpleNamespace(host="acc.snowflakecomputing.com", rest=SimpleNamespace(token="T1"))
        conn.closed = False
        conn.close = lambda: setattr(conn, "closed", True)
        with mock.patch("snowflake.connector.connect", return_value=conn) as connect:
            options = options_from_connection("dev", **kwargs)
        return options, conn, connect

    def test_the_session_token_is_read_each_time_and_never_shown(self) -> None:
        with self._home('[dev]\naccount = "x"\nauthenticator = "snowflake_jwt"\n'):
            options, conn, connect = self._connect(role="PUBLIC")
        self.assertEqual(connect.call_args.kwargs, {"connection_name": "dev", "role": "PUBLIC"})
        self.assertEqual(options.base_url, "https://acc.snowflakecomputing.com")
        self.assertEqual(options.label, "dev")
        self.assertEqual(options.auth.get_token(), "T1")
        conn.rest.token = "T2"  # renewed by the connector
        self.assertEqual(options.auth.get_token(), "T2")
        self.assertNotIn("T2", repr(options.auth))

    def test_private_key_path_is_given_to_the_connector_under_its_own_name(self) -> None:
        with self._home('[dev]\nprivate_key_path = "~/k.p8"\n'):
            _, _, connect = self._connect()
        self.assertEqual(
            connect.call_args.kwargs["private_key_file"], str(Path("~/k.p8").expanduser())
        )
        self.assertNotIn("role", connect.call_args.kwargs)  # the profile's own role

    def test_a_key_file_the_profile_already_names_is_left_alone(self) -> None:
        with self._home('[dev]\nprivate_key_path = "~/a.p8"\nprivate_key_file = "/b.p8"\n'):
            _, _, connect = self._connect()
        self.assertNotIn("private_key_file", connect.call_args.kwargs)

    def test_closing_the_agent_closes_the_connection(self) -> None:
        with self._home("[dev]\n"):
            options, conn, _ = self._connect(workspace_mounts=[{"name": "W"}])
        self.assertEqual(options.spec()["workspace_mounts"], [{"name": "W"}])
        agent = ManagedAgent(lambda e: None, options, client_factory=lambda: FakeClient([]))
        agent.close()
        self.assertTrue(conn.closed)


class SurfaceTest(unittest.TestCase):
    def test_the_three_agents_keep_the_surface_of_the_conversation(self) -> None:
        agents = [
            ManagedAgent(lambda e: None, ManagedOptions(account="a", token="t")),
            Agent(lambda e: None),
            ScriptedAgent(lambda e: None),
        ]
        for agent in agents:
            with self.subTest(agent=type(agent).__name__):
                self.assertIsInstance(agent, AgentBackend)

    def test_managed_agent_is_a_factory_of_the_window(self) -> None:
        make = managed_agent(ManagedOptions(account="a", token="t"))
        self.assertIsInstance(make(lambda e: None), ManagedAgent)

    def test_the_module_imports_without_streamlit(self) -> None:
        import subprocess
        import sys

        code = "import sys, streamlit_coco.managed; print('streamlit' in sys.modules)"
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
        self.assertEqual(done.stdout.strip(), "False", done.stderr)


if __name__ == "__main__":
    unittest.main()


class EnvironmentTest(unittest.TestCase):
    """The probe of an application that only uses the managed agent: no `cortex` program needed."""

    def test_managed_does_not_look_for_the_program_and_is_ready_with_the_sdk(self) -> None:
        from streamlit_coco import check_environment

        with mock.patch("shutil.which", side_effect=AssertionError("looked for cortex")):
            env = check_environment(managed=True)
        self.assertIsNone(env.cli_path)
        self.assertFalse(env.cli_ok)
        self.assertTrue(env.managed)
        self.assertEqual(env.ready, env.sdk_installed)

    def test_the_default_still_needs_the_program(self) -> None:
        from streamlit_coco import check_environment

        with mock.patch("shutil.which", return_value=None):
            env = check_environment()
        self.assertFalse(env.ready)
        self.assertFalse(env.managed)

    def test_require_environment_raises_for_the_program_unless_managed(self) -> None:
        from streamlit_coco import CLINotFoundError, require_environment

        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(CLINotFoundError):
                require_environment()
            self.assertTrue(require_environment(managed=True).managed)

    def test_managed_still_needs_the_sdk(self) -> None:
        from streamlit_coco import SDKNotInstalledError, require_environment

        with mock.patch.dict("sys.modules", {"cortex_agent_sdk": None}):
            with self.assertRaises(SDKNotInstalledError):
                require_environment(managed=True)
