"""Ask CoCo, the pre-tool gate: free, asked, refused; the answer; the standing permission by family.

The tests of the first host (the Spec-First Cockpit), on the ready-made policy with every piece
switched on. Temporary directories only.
"""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from streamlit_coco.gate import Gate
from streamlit_coco.policy import FolderPolicy, git_readonly

FILES = ("PROJECT.md", ".env", ".git/config", "specs/functional_spec.md", "../../outside.md")


def make_projects(tmp: Path) -> tuple[Path, Path]:
    """(the working folder, the alpha folder in it). `outside.md` is next to the working folder."""
    projects = tmp / "My projects"
    for name in FILES:
        path = projects / "alpha" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Text" + chr(10), encoding="utf-8")
    return projects, projects / "alpha"


def policy(projects: Path, scope: Path | None = None) -> FolderPolicy:
    """Every piece on, as the first host runs it."""
    listed = git_readonly(scope) if scope else ()
    return FolderPolicy(
        projects, scope=scope, commands=listed, sql=True, lookups=True, standing=True
    )


class GateCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.projects, self.alpha = make_projects(Path(self._tmp.name))
        self.events: list[dict] = []
        self.gate = Gate(self.events.append, expiry=5)
        self.gate.begin(policy(self.projects, self.alpha))
        self.addCleanup(self.gate.cancel_all)
        self.write = {"file_path": str(self.alpha / "specs" / "new.md"), "content": "# New\n"}
        self.read = {"file_path": str(self.alpha / "PROJECT.md")}
        self.outside = {"file_path": str(Path(self._tmp.name) / "outside.md")}

    def ask(self, tool, tool_input, tool_id="t1") -> dict:
        """Run the gate on a thread, as the hook does; wait until it has shown its request."""
        out: dict = {}
        thread = threading.Thread(
            target=lambda: out.update(reason=self.gate.decide(tool, tool_input, tool_id))
        )
        thread.start()
        out["thread"] = thread
        deadline = time.monotonic() + 3
        while not self.requests(tool_id) and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.005)
        return out

    def requests(self, tool_id=None) -> list[dict]:
        return [e for e in self.events if e["t"] == "request" and tool_id in (None, e["tool_id"])]

    def request_id(self, tool_id="t1") -> str:
        return self.requests(tool_id)[0]["id"]

    def of(self, kind: str) -> list[dict]:
        return [e for e in self.events if e["t"] == kind]

    def allow(self, tool, tool_input, *, standing=False, tool_id="t1"):
        """Ask, answer Allow (with or without the tick) and return the gate's reason."""
        out = self.ask(tool, tool_input, tool_id)
        self.gate.answer(self.request_id(tool_id), True, standing)
        out["thread"].join(3)
        return out["reason"]

    def covered(self, tool, tool_input, tool_id="t9") -> bool:
        """True when the call went through without a request."""
        before = len(self.requests())
        reason = self.gate.decide(tool, tool_input, tool_id)
        return reason is None and len(self.requests()) == before


class DecisionTest(GateCase):
    def test_the_gate_hands_the_sessions_output_folder_to_the_policy(self) -> None:
        seen = []

        class Recorder:
            spill = None

            def judge(self, tool, tool_input):
                seen.append(self.spill)
                return None, None

        gate = Gate(lambda event: None)
        gate.begin(Recorder())
        gate.spill = "the session's folder"
        gate.decide("Read", {"file_path": "x"}, "t1")
        self.assertEqual(seen, ["the session's folder"])

    def test_a_read_inside_the_scope_is_free(self) -> None:
        self.assertIsNone(self.gate.decide("Read", self.read, "t1"))
        self.assertEqual(self.events, [])
        self.assertTrue(self.gate.agreed("Read", self.read))

    def test_a_read_of_a_secret_asks_and_is_not_refused(self) -> None:
        call = {"file_path": str(self.alpha / ".env")}
        self.assertFalse(self.gate.agreed("Read", call))
        out = self.ask("Read", call)
        self.assertEqual(
            self.requests()[0]["facts"]["question"],
            "Allow CoCo to read a file that may hold secrets?",
        )
        self.gate.answer(self.request_id(), False)
        out["thread"].join(3)
        self.assertEqual(out["reason"], "Declined by the user.")
        self.assertEqual(self.of("refused"), [])

    def test_a_call_the_app_cannot_read_is_refused_and_never_asked(self) -> None:
        reason = self.gate.decide("Read", 3, "t1")
        self.assertEqual(reason, "The tool input is not understood.")
        self.assertEqual(self.events, [{"t": "refused", "tool_id": "t1", "reason": reason}])
        self.assertFalse(self.gate.agreed("Read", 3))

    def test_without_a_request_running_everything_is_refused(self) -> None:
        self.gate.policy = None
        self.assertEqual(self.gate.decide("Read", {}, "t1"), "No request is running.")
        self.assertFalse(self.gate.agreed("Read", {}))

    def test_the_hook_waits_for_the_window_then_returns_an_explicit_decision(self) -> None:
        for allow in (True, False):
            self.events.clear()
            out = self.ask("Write", self.write)
            self.assertTrue(out["thread"].is_alive())  # waiting, not answering
            request = self.requests()[0]
            self.assertEqual((request["tool_id"], request["facts"]["kind"]), ("t1", "change"))
            self.assertEqual(request["facts"]["standing"]["id"], "files")
            self.gate.answer(request["id"], allow)
            out["thread"].join(3)
            self.assertEqual(out["reason"], None if allow else "Declined by the user.")

    def test_every_other_tool_waits_too(self) -> None:
        line = self.gate.policy.commands()[0].line
        for tool, call, kind in (
            ("Bash", {"command": line}, "read"),
            ("Bash", {"command": "whoami"}, "change"),
            ("sql_execute", {"sql": "select 1"}, "read"),
            ("Task", {"prompt": "x"}, "change"),
            ("web_search", {"query": "x"}, "read"),
        ):
            with self.subTest(tool=tool, kind=kind):
                self.events.clear()
                self.assertFalse(self.gate.agreed(tool, call))
                self.assertIsNone(self.allow(tool, call))
                self.assertEqual(self.requests()[0]["facts"]["kind"], kind)
                self.assertTrue(self.gate.agreed(tool, call))

    def test_an_allow_is_checked_again_what_was_shown_must_still_be_what_runs(self) -> None:
        target = self.alpha / "specs" / "functional_spec.md"
        call = {"file_path": str(target), "content": "x"}  # shown as "replace a file"
        out = self.ask("Write", call)
        target.unlink()  # now it would be "create a file"
        self.gate.answer(self.request_id(), True, True)
        out["thread"].join(3)
        self.assertIn("no longer what you were shown", out["reason"])
        self.assertEqual(
            self.events[-1], {"t": "refused", "tool_id": "t1", "reason": out["reason"]}
        )
        self.assertFalse(self.gate.agreed("Write", call))
        self.assertEqual(self.of("granted"), [])  # nothing is granted by an Allow that did not run

    def test_a_request_left_unanswered_expires_as_a_decline(self) -> None:
        gate = Gate(self.events.append, expiry=0.05)
        gate.policy = self.gate.policy
        self.assertIn("No answer", gate.decide("Write", self.write, "t1"))
        self.assertEqual(
            self.events[-1], {"t": "expired", "id": self.request_id(), "tool_id": "t1"}
        )

    def test_the_sdk_callback_only_agrees_to_what_the_user_agreed(self) -> None:
        self.assertFalse(self.gate.agreed("Write", self.write))
        self.allow("Write", self.write)
        self.assertTrue(self.gate.agreed("Write", self.write))
        self.assertFalse(self.gate.agreed("Write", {**self.write, "content": "other"}))
        self.assertTrue(self.gate.agreed("Read", self.read))
        self.assertFalse(self.gate.agreed("Read", self.outside))

    def test_stopping_declines_what_is_pending(self) -> None:
        out = self.ask("Write", self.write)
        self.gate.cancel_all()
        out["thread"].join(3)
        self.assertEqual(out["reason"], "Declined by the user.")

    def test_the_first_answer_stands(self) -> None:
        for first, second, expected in (
            (False, True, "Declined by the user."),
            (True, False, None),
        ):
            self.events.clear()
            out = self.ask("Write", self.write)
            rid = self.request_id()
            self.gate.answer(rid, first)
            self.gate.answer(rid, second, True)  # a double click, or a Stop after the Decline
            out["thread"].join(3)
            self.assertEqual(out["reason"], expected)
            self.assertEqual(self.of("granted"), [])

    def test_an_answer_after_the_end_of_the_request_is_ignored(self) -> None:
        gate = Gate(self.events.append, expiry=0.05)
        gate.policy = self.gate.policy
        self.assertIn("No answer", gate.decide("Write", self.write, "t1"))
        gate.answer(self.request_id(), True, True)  # too late: no slot, no error
        gate.answer("nobody", True)
        self.assertFalse(gate.agreed("Write", self.write))
        self.assertEqual(gate.granted(), [])

    def test_a_call_that_reaches_the_gate_after_a_stop_is_declined_at_once(self) -> None:
        # otherwise it would wait ten minutes for an answer nobody can give
        self.gate.cancel_all()
        self.assertEqual(self.gate.decide("Write", self.write, "t1"), "Declined by the user.")
        self.assertEqual(self.events, [])
        self.gate.begin(self.gate.policy)  # the next request starts clean
        out = self.ask("Write", self.write)
        self.assertTrue(out["thread"].is_alive())
        self.gate.cancel_all()
        out["thread"].join(3)

    def test_an_agreement_does_not_outlive_its_request(self) -> None:
        self.allow("Write", self.write)
        self.assertTrue(self.gate.agreed("Write", self.write))
        self.gate.begin(self.gate.policy)
        self.assertFalse(self.gate.agreed("Write", self.write))


class StandingTest(GateCase):
    def test_an_allow_with_the_tick_grants_the_family_and_says_so(self) -> None:
        out = self.ask("Bash", {"command": "whoami"})
        offer = self.requests()[0]["facts"]["standing"]
        self.gate.answer(self.request_id(), True, True)
        out["thread"].join(3)
        self.assertEqual(
            self.of("granted"),
            [{"t": "granted", "id": "commands", "text": offer["covers"], "family": "commands"}],
        )
        self.assertEqual(self.gate.granted(), [offer["covers"]])

    def test_without_the_tick_or_with_a_decline_nothing_is_granted(self) -> None:
        self.allow("Bash", {"command": "whoami"})
        out = self.ask("Bash", {"command": "ls"}, "t2")
        self.gate.answer(self.request_id("t2"), False, True)
        out["thread"].join(3)
        self.assertEqual((self.of("granted"), self.gate.granted()), ([], []))
        self.assertFalse(self.covered("Bash", {"command": "pwd"}))

    def test_a_covered_call_is_not_asked_and_is_reported_as_not_asked(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        for index, command in enumerate(
            ("ls", "git push --force", "a\nb", self.gate.policy.commands()[0].line)
        ):
            call = {"command": command}
            self.events.clear()
            self.assertIsNone(self.gate.decide("Bash", call, f"c{index}"))
            self.assertEqual(self.events, [{"t": "standing", "tool_id": f"c{index}"}])
            self.assertTrue(self.gate.agreed("Bash", call))  # the SDK callback agrees too

    def test_a_grant_never_covers_another_family(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        for tool, call in (
            ("Write", self.write),
            ("sql_execute", {"sql": "select 1"}),
            ("sql_execute", {"sql": "drop table t"}),
            ("Task", {"prompt": "x"}),
            ("web_search", {"query": "x"}),
            ("Read", self.outside),
        ):
            with self.subTest(tool=tool):
                self.assertTrue(self.not_covered(tool, call))

    def not_covered(self, tool, call) -> bool:
        """True when the call is asked: it waits for an answer."""
        out = self.ask(tool, call, "probe")
        asked = bool(self.requests("probe"))
        self.gate.cancel_all()
        out["thread"].join(3)
        self.gate.begin(self.gate.policy)
        self.events[:] = [e for e in self.events if e.get("tool_id") != "probe"]
        return asked

    def test_each_family_covers_what_it_says_and_no_more(self) -> None:
        cases = {
            "files": (
                ("Write", self.write),
                [
                    (
                        "Edit",
                        {
                            "file_path": str(self.alpha / "specs" / "functional_spec.md"),
                            "old_string": "a",
                            "new_string": "b",
                        },
                    )
                ],
                [  # outside the scope; and inside it, a hook or a file that may hold secrets
                    ("Write", {"file_path": str(Path(self._tmp.name) / "o.md"), "content": "x"}),
                    (
                        "Write",
                        {"file_path": str(self.alpha / ".git" / "hooks" / "x"), "content": "x"},
                    ),
                    ("Write", {"file_path": str(self.alpha / ".env"), "content": "x"}),
                ],
            ),
            "queries": (
                ("sql_execute", {"sql": "select 1"}),
                [("sql_execute", {"sql": "show tables"})],
                [("sql_execute", {"sql": "drop table t"})],
            ),
            "statements": (
                ("sql_execute", {"sql": "drop table t"}),
                [
                    ("sql_execute", {"sql": "select 1"}),
                    ("sql_execute", {"sql": "create table t (a int)"}),
                ],
                [],
            ),
            "tool:web_fetch": (
                ("web_fetch", {"url": "a"}),
                [("web_fetch", {"url": "b"})],
                [("web_search", {"query": "a"})],
            ),
            "elsewhere": (
                ("Read", self.outside),
                [("Grep", {"pattern": "x", "path": str(Path(self._tmp.name))})],
                [
                    ("Read", {"file_path": str(self.alpha / ".env")}),
                    ("Read", {"file_path": str(self.alpha / ".git" / "config")}),
                ],
            ),
        }
        for family, (grant, inside, beyond) in cases.items():
            with self.subTest(family=family):
                gate = self.gate = Gate(self.events.append, expiry=5)
                gate.begin(policy(self.projects, self.alpha))
                self.events.clear()
                self.allow(*grant, standing=True)
                self.assertEqual([e["id"] for e in self.of("granted")], [family])
                for tool, call in inside:
                    self.assertTrue(
                        self.covered(tool, call), f"{family} should cover {tool} {call}"
                    )
                for tool, call in beyond:
                    self.assertTrue(
                        self.not_covered(tool, call), f"{family} should not cover {tool} {call}"
                    )
                gate.cancel_all()

    def test_the_queries_grant_does_not_cover_a_statement_that_changes(self) -> None:
        self.allow("sql_execute", {"sql": "select 1"}, standing=True)
        self.assertTrue(self.not_covered("sql_execute", {"sql": "drop table t"}))

    def test_revoke_takes_the_permission_back_at_once(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        self.assertTrue(self.covered("Bash", {"command": "ls"}))
        self.gate.revoke("commands")
        self.assertEqual(self.of("revoked"), [{"t": "revoked", "id": "commands"}])
        self.assertEqual(self.gate.granted(), [])
        self.assertTrue(self.not_covered("Bash", {"command": "ls"}))
        self.assertFalse(self.gate.agreed("Bash", {"command": "ls"}))

    def test_revoking_what_is_not_granted_says_nothing(self) -> None:
        self.gate.revoke("commands")
        self.gate.revoke("nobody")
        self.assertEqual(self.of("revoked"), [])

    def test_granting_twice_is_announced_once(self) -> None:
        first, second = (
            self.ask("Bash", {"command": "one"}, "t1"),
            self.ask("Bash", {"command": "two"}, "t2"),
        )
        self.gate.answer(self.request_id("t1"), True, True)
        self.gate.answer(self.request_id("t2"), True, True)
        first["thread"].join(3)
        second["thread"].join(3)
        self.assertEqual(len(self.of("granted")), 1)
        self.assertEqual(len(self.gate.granted()), 1)

    def test_the_grant_holds_across_the_requests_of_one_conversation(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        self.gate.begin(
            policy(self.projects, self.alpha)
        )  # the next message of the same conversation
        self.assertTrue(self.covered("Bash", {"command": "ls"}))
        self.gate.begin(policy(self.projects))  # another project, or none
        self.assertTrue(self.covered("Bash", {"command": "ls"}))

    def test_the_grant_ends_with_the_conversation(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        self.gate.begin(policy(self.projects, self.alpha), new_conversation=True)
        self.assertEqual(self.gate.granted(), [])
        self.assertTrue(self.not_covered("Bash", {"command": "ls"}))
        fresh = Gate(self.events.append)  # a new conversation makes a new agent, so a new Gate
        fresh.begin(self.gate.policy)
        self.assertEqual(fresh.granted(), [])

    def test_stopping_a_request_keeps_the_grants(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        self.gate.cancel_all()
        self.gate.begin(self.gate.policy)
        self.assertTrue(self.covered("Bash", {"command": "ls"}))

    def test_a_covered_call_is_checked_again_a_call_the_app_cannot_read_is_still_refused(
        self,
    ) -> None:
        self.allow("sql_execute", {"sql": "drop table t"}, standing=True)
        self.assertEqual(
            self.gate.decide("sql_execute", {"sql": 3}, "t5"), "The query is not text."
        )
        self.assertFalse(self.gate.agreed("sql_execute", {"sql": 3}))
        self.assertEqual(self.events[-1]["t"], "refused")

    def test_a_pending_request_and_a_grant_given_to_another_do_not_interfere(self) -> None:
        first = self.ask("Bash", {"command": "one"}, "t1")
        second = self.ask("Bash", {"command": "two"}, "t2")
        self.assertEqual(len(self.requests()), 2)
        self.gate.answer(self.request_id("t1"), True, True)
        first["thread"].join(3)
        self.assertIsNone(first["reason"])
        self.assertTrue(
            second["thread"].is_alive()
        )  # its own request stays, to be answered by the user
        self.assertTrue(
            self.covered("Bash", {"command": "three"})
        )  # a call that comes now is covered
        self.gate.answer(self.request_id("t2"), False)
        second["thread"].join(3)
        self.assertEqual(second["reason"], "Declined by the user.")
        self.assertEqual(
            len(self.gate.granted()), 1
        )  # the decline took nothing back and added nothing

    def test_revoking_while_a_request_is_pending_leaves_it_pending(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        self.gate.revoke("commands")
        out = self.ask("Bash", {"command": "ls"}, "t2")
        self.gate.revoke("commands")
        self.assertTrue(out["thread"].is_alive())
        self.gate.answer(self.request_id("t2"), True, True)  # a new tick grants again
        out["thread"].join(3)
        self.assertEqual(
            [e["t"] for e in self.events if e["t"] in ("granted", "revoked")],
            ["granted", "revoked", "granted"],
        )

    def test_calls_decided_at_the_same_time_all_see_the_grant(self) -> None:
        self.allow("Bash", {"command": "whoami"}, standing=True)
        results = []
        threads = [
            threading.Thread(
                target=lambda n=n: results.append(
                    self.gate.decide("Bash", {"command": f"c{n}"}, f"c{n}")
                )
            )
            for n in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(3)
        self.assertEqual(results, [None] * 8)
        self.assertEqual(len(self.of("standing")), 8)
        self.assertEqual(len(self.requests()), 1)

    def test_a_policy_that_offers_no_standing_permission_is_asked_each_time(self) -> None:
        # the default policy: a tick sent anyway grants nothing
        self.gate.begin(FolderPolicy(self.projects))
        self.assertIsNone(self.allow("Bash", {"command": "whoami"}, standing=True))
        self.assertIsNone(self.requests()[0]["facts"]["standing"])
        self.assertEqual((self.of("granted"), self.gate.granted()), ([], []))
        self.assertTrue(self.not_covered("Bash", {"command": "whoami"}))


if __name__ == "__main__":
    unittest.main()
