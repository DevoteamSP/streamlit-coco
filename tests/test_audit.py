"""The approval audit log (audit.py): one line for each call that asked, was covered or was refused.

The gate is driven as the agents drive it (a thread that blocks until the user answers); the log
is a file in a temporary folder.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from test_gate import GateCase
from test_scripted import MockCase

from streamlit_coco.audit import AuditLog
from streamlit_coco.gate import Gate
from streamlit_coco.policy import FolderPolicy

BASH = {"command": "rm -rf build"}


class LogTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "logs" / "audit.jsonl"

    def test_a_record_is_one_line_with_the_time_and_who(self) -> None:
        log = AuditLog(self.path, who=lambda: "ann@example.com")
        log({"decision": "allowed", "tool": "Bash", "reason": None})
        (line,) = self.path.read_text().splitlines()
        row = json.loads(line)
        self.assertEqual(
            (row["who"], row["decision"], row["tool"]), ("ann@example.com", "allowed", "Bash")
        )
        self.assertTrue(row["time"].endswith("+00:00"))
        self.assertNotIn("reason", row)  # an empty field is left out

    def test_the_file_is_the_owners_and_lines_are_appended(self) -> None:
        log = AuditLog(self.path, who="x")
        log({"decision": "a"})
        log({"decision": "b"})
        self.assertEqual([r["decision"] for r in log.read()], ["a", "b"])
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)

    def test_a_long_evidence_is_cut(self) -> None:
        log = AuditLog(self.path, evidence_chars=10)
        log({"decision": "a", "evidence": [{"label": "Command", "text": "x" * 50}]})
        self.assertEqual(log.read()[0]["evidence"][0]["text"], "x" * 10)

    def test_a_log_that_cannot_be_written_does_not_stop_the_decision(self) -> None:
        log = AuditLog(Path(self._tmp.name))  # a folder: the open fails
        with self.assertLogs("streamlit_coco.audit", "WARNING"):
            log({"decision": "allowed"})
        self.assertEqual(log.read(), [])


class GateAuditTest(GateCase):
    def setUp(self) -> None:
        super().setUp()
        self.rows: list[dict] = []
        self.gate = Gate(self.events.append, expiry=0.3)
        self.gate.audit = self.rows.append
        self.gate.begin(FolderPolicy(self.alpha, scope=self.alpha, standing=True))
        self.addCleanup(self.gate.cancel_all)

    def decisions(self) -> list[str]:
        return [r["decision"] for r in self.rows]

    def test_an_allowed_call_is_logged_with_what_the_user_was_shown(self) -> None:
        self.assertIsNone(self.allow("Bash", BASH))
        (row,) = self.rows
        self.assertEqual(row["decision"], "allowed")
        self.assertEqual(row["tool"], "Bash")
        self.assertEqual(row["kind"], "change")
        self.assertIn(BASH["command"], json.dumps(row["evidence"]))

    def test_a_declined_call_is_logged(self) -> None:
        out = self.ask("Bash", BASH)
        self.gate.answer(self.request_id(), False)
        out["thread"].join(3)
        self.assertEqual(self.decisions(), ["declined"])

    def test_an_expired_request_is_logged(self) -> None:
        out = self.ask("Bash", BASH)
        out["thread"].join(3)
        self.assertEqual(self.decisions(), ["expired"])

    def test_a_standing_permission_is_logged_when_it_is_given_and_each_time_it_covers(self) -> None:
        self.allow("Bash", BASH, standing=True)
        self.assertTrue(self.covered("Bash", {"command": "rm -rf dist"}))
        self.assertEqual(self.decisions(), ["allowed", "standing"])
        self.assertEqual(self.rows[0]["standing_granted"], "commands")
        self.assertEqual(self.rows[1]["standing"], "commands")
        self.gate.revoke("commands")
        self.assertEqual(self.decisions()[-1], "revoked")

    def test_a_call_that_runs_without_a_question_is_not_logged(self) -> None:
        self.gate.decide("Read", self.read, "t5")
        self.assertEqual(self.rows, [])

    def test_a_gate_without_a_log_works_as_before(self) -> None:
        self.gate.audit = None
        self.assertIsNone(self.allow("Bash", BASH))


class RedactionTest(unittest.TestCase):
    """What looks like a credential is not written. What looks like nothing is (see audit.py)."""

    CASES = {
        "mysql --password hunter2 -h db": "--password [redacted]",
        "export API_TOKEN=abc123def456": "API_TOKEN=[redacted]",
        'curl -H "Authorization: Bearer abcdef0123456789" x': "Bearer [redacted]",
        "psql postgres://bob:s3cret@db/x": "postgres://bob:[redacted]@db/x",
        "CREATE USER u PASSWORD = 'pw1'": "PASSWORD = [redacted]",
        'CREATE USER u IDENTIFIED BY "pw2"': "IDENTIFIED BY [redacted]",
        "aws s3 ls --access-key AKIAIOSFODNN7EXAMPLE": "[redacted]",
        "git clone https://x:ghp_" + "a" * 36 + "@github.com/o/r": "[redacted]",
        "-----BEGIN PRIVATE KEY-----\nMIIabc\n-----END PRIVATE KEY-----": "[redacted private key]",
        "token=eyJhbGciOiJIUzI1.eyJzdWIiOiIxMjM0.SflKxwRJSMeKKF2Q": "[redacted]",
    }

    def test_a_credential_is_replaced_and_nothing_else_of_the_line_goes(self) -> None:
        from streamlit_coco.audit import redact_secrets

        for text, expected in self.CASES.items():
            with self.subTest(text=text[:40]):
                out = redact_secrets(text)
                self.assertIn(expected, out)
                for secret in (
                    "hunter2",
                    "abc123def456",
                    "abcdef0123456789",
                    "s3cret",
                    "pw1",
                    "pw2",
                    "AKIAIOSFODNN7EXAMPLE",
                    "MIIabc",
                    "SflKxwRJSMeKKF2Q",
                ):
                    self.assertNotIn(secret, out)

    def test_an_ordinary_line_is_left_alone(self) -> None:
        from streamlit_coco.audit import redact_secrets

        for text in (
            "ls -la /tmp",
            "echo token count is 5",
            "SELECT * FROM T WHERE ID = 4",
            "git status --short",
            "python3 profile.py /uploads/x/orders.csv",
        ):
            self.assertEqual(redact_secrets(text), text)

    def test_what_does_not_look_like_a_secret_is_written_as_it_is(self) -> None:
        """The limit, stated: a password given as a plain argument is not caught."""
        from streamlit_coco.audit import redact_secrets

        self.assertEqual(redact_secrets("mysql -u root -p hunter2"), "mysql -u root -p hunter2")


class WrittenLineTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "audit.jsonl"

    def record(self, **fields) -> dict:
        return {"decision": "allowed", "tool": "Bash", **fields}

    def test_the_evidence_the_detail_and_the_reason_are_redacted_before_the_write(self) -> None:
        log = AuditLog(self.path)
        log(
            self.record(
                evidence=[{"label": "Command", "text": "run --password hunter2"}],
                detail="failed: token=abc12345678",
                reason="bad API_KEY: zzz99999",
            )
        )
        text = self.path.read_text()
        for secret in ("hunter2", "abc12345678", "zzz99999"):
            self.assertNotIn(secret, text)
        self.assertEqual(text.count("[redacted]"), 3)

    def test_a_secret_is_redacted_before_the_cut_never_cut_in_half(self) -> None:
        """A cut first would leave the start of a key that no longer has the shape of one."""
        log = AuditLog(self.path, evidence_chars=16)
        log(self.record(evidence=[{"label": "c", "text": "run AKIAIOSFODNN7EXAMPLE now"}]))
        text = self.path.read_text()
        self.assertNotIn("AKIA", text)
        self.assertIn("[redacted]", text)

    def test_redact_none_writes_the_text_as_shown_and_a_function_of_your_own_is_used(self) -> None:
        AuditLog(self.path, redact=None)(self.record(detail="password=visible1"))
        self.assertIn("visible1", self.path.read_text())
        other = Path(self._tmp.name) / "other.jsonl"
        AuditLog(other, redact=lambda text: text.replace("acme", "***"))(
            self.record(detail="acme corp")
        )
        self.assertIn("*** corp", other.read_text())

    def test_a_redactor_that_fails_writes_none_of_the_text(self) -> None:
        def broken(text: str) -> str:
            raise RuntimeError("boom")

        log = AuditLog(self.path, redact=broken)
        with self.assertLogs("streamlit_coco.audit", "WARNING"):
            log(self.record(detail="password=visible1"))
        text = self.path.read_text()
        self.assertNotIn("visible1", text)
        self.assertIn("redactor failed", text)


class OutcomeTest(MockCase):
    """An allowed call gets a second line when its result is known, joined by tool_id."""

    def setUp(self) -> None:
        super().setUp()
        self.rows: list[dict] = []
        self.conv.audit = self.rows.append

    def decisions(self) -> list[tuple]:
        return [(r["decision"], r.get("outcome")) for r in self.rows]

    def test_an_allowed_write_is_followed_by_its_outcome(self) -> None:
        self.ask("write a note")
        view = self.until(lambda v: v["status"] == "waiting")
        self.conv.act({"type": "allow", "id": view["request"]["id"]})
        self.until(self.done)
        self.assertEqual(self.decisions(), [("allowed", None), ("outcome", "succeeded")])
        allowed, outcome = self.rows
        self.assertEqual(allowed["tool_id"], outcome["tool_id"])
        self.assertEqual(outcome["tool"], allowed["tool"])

    def test_a_declined_call_has_no_outcome(self) -> None:
        self.ask("write a note")
        view = self.until(lambda v: v["status"] == "waiting")
        self.conv.act({"type": "decline", "id": view["request"]["id"]})
        self.until(self.done)
        self.assertEqual(self.decisions(), [("declined", None)])

    def test_a_failed_result_and_the_programs_own_refusal_are_told_apart(self) -> None:
        for content, error, expected in (
            ("boom", True, "failed"),
            ("Tool denied by the program", False, "not_run"),
        ):
            with self.subTest(expected=expected):
                self.rows.clear()
                self.conv._record({"decision": "allowed", "tool": "Bash", "tool_id": "t9"})
                self.assertEqual(self.conv._outcome_of({"error": error}, content)[0], expected)

    def test_a_standing_call_also_gets_an_outcome(self) -> None:
        self.conv._record({"decision": "standing", "tool": "Bash", "tool_id": "t7"})
        self.conv._outcome("t7", "succeeded")
        self.assertEqual(self.decisions(), [("standing", None), ("outcome", "succeeded")])

    def test_a_run_that_ends_before_a_result_says_so(self) -> None:
        self.conv._record({"decision": "allowed", "tool": "Bash", "tool_id": "zz"})
        self.ask("Hello there")
        self.until(self.done)
        outcome = [r for r in self.rows if r["decision"] == "outcome"]
        self.assertEqual([(r["tool_id"], r["outcome"]) for r in outcome], [("zz", "no_result")])

    def test_an_outcome_is_written_once_and_only_for_a_call_that_was_audited(self) -> None:
        self.conv._outcome("never-allowed", "succeeded")
        self.conv._record({"decision": "allowed", "tool": "Bash", "tool_id": "t1"})
        self.conv._outcome("t1", "succeeded")
        self.conv._outcome("t1", "failed")
        self.assertEqual(self.decisions(), [("allowed", None), ("outcome", "succeeded")])
