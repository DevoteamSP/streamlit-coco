"""Ask CoCo, the approval audit log: who allowed what, when (SEC-01).

Pure Python: no Streamlit, no SDK. Every call the gate judged that asked the user, was covered by a
standing permission, or was refused is one line of JSON in an append-only file:

    audit = st_coco.AuditLog("coco-audit.jsonl", who=lambda: st.user.get("email"))
    st_coco.ask_coco(".", audit=audit)

A line holds `time` (UTC), `who`, `conversation`, `agent`, `tool`, `decision` (`allowed`,
`declined`, `expired`, `refused`, `standing`, `revoked`), the request's `kind`, `question`, `where`
and `evidence` (the exact command, SQL or path the user was shown, cut at `evidence_chars`), and
`reason`, `standing_granted` where there is one. Calls that run without a question (a read inside
the working folder) are not logged. The file is created readable by its owner only; it can hold
what a command contains, so keep it where the application keeps its other logs.

A line of `decision: "outcome"` follows an allowed call (or one a standing permission covered) when
its result is known: `outcome` is `succeeded`, `failed` (the tool reported an error), `not_run` (the
program refused it itself) or `no_result` (the run ended first), and `tool_id` joins it to the
decision's line. `detail` says why a call failed or was not run.

Secrets: before a line is written, `redact` (default `redact_secrets`) rewrites the exact text the
user was shown (`evidence`), `detail` and `reason`. It catches what looks like a credential: a
`password=`, `token:` or `--api-key` value, a bearer token, a private key block, a password in a
URL, a SQL `IDENTIFIED BY`, and the usual token shapes (AWS, GitHub, Slack, JWT, `sk-`). It does
NOT protect a secret that looks like nothing: a password given as a plain argument (`mysql -p
hunter2`), a secret inside the text of a file the agent writes, an encoded blob, personal data in a
SQL statement or a result, or a secret split over lines. Redaction is a net, not a guarantee: keep
the file where the application keeps its other secrets-bearing logs. `redact=None` writes the text
as it was shown; a function of your own may replace the default.

A failing write is logged and does not stop CoCo: the log records decisions, it does not make them.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

_LOG = logging.getLogger(__name__)
_MASK = "[redacted]"
_NAME = (
    r"[A-Za-z0-9_.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key"
    r"|private[_-]?key|credential)[A-Za-z0-9_.-]*"
)
_VALUE = r"""(?:"[^"\n]*"|'[^'\n]*'|[^\s,;&'"]+)"""
_PEM = r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"
# (pattern, replacement), applied in order
_REDACTIONS = (
    (re.compile(_PEM, re.S), "[redacted private key]"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 " + _MASK),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), _MASK),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})\b"), _MASK),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), _MASK),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), _MASK),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), _MASK),
    (re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^/\s:@]+:)[^@\s/]+(@)"), r"\1" + _MASK + r"\2"),
    (re.compile(r"(?i)(\bidentified\s+by\s+)" + _VALUE), r"\1" + _MASK),
    (
        re.compile(
            r"(?i)(--?(?:password|passwd|pwd|token|secret|api[-_]?key|access[-_]?key)[= ]\s*)"
            + _VALUE
        ),
        r"\1" + _MASK,
    ),
    (re.compile(r"(?i)(\b" + _NAME + r"""["']?\s*[:=]\s*)""" + _VALUE), r"\1" + _MASK),
)


def redact_secrets(text: str) -> str:
    """`text` with what looks like a credential replaced by `[redacted]` (see the module docstring
    for what it catches and what it does not)."""
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


class AuditLog:
    """Append one JSON line per decision to `path` (folders are created). `who`: the person who
    answers, a text or a function returning it each time (the library cannot know who that is).
    `redact`: a function (text) -> text applied to the evidence, the detail and the reason before
    they are written (default `redact_secrets`; None: as shown). `evidence_chars`: the cut, made
    after the redaction so that a secret is never cut in half and left readable."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        who: str | Callable[[], str | None] | None = None,
        evidence_chars: int = 2000,
        redact: Callable[[str], str] | None = redact_secrets,
    ) -> None:
        self.path = Path(path).expanduser()
        self.who, self.evidence_chars, self.redact = who, evidence_chars, redact
        self._lock = threading.Lock()

    def __call__(self, record: dict) -> None:
        try:
            who = self.who() if callable(self.who) else self.who
            line = {
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "who": who,
                **{k: v for k, v in record.items() if v is not None},
            }
            for item in line.get("evidence") or ():
                item["text"] = self._clean(item["text"], self.evidence_chars)
            for key in ("detail", "reason"):
                if key in line:
                    line[key] = self._clean(line[key], self.evidence_chars)
            data = (json.dumps(line, ensure_ascii=False, default=str) + "\n").encode("utf-8")
            with self._lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
                try:
                    os.write(fd, data)
                finally:
                    os.close(fd)
        except Exception:  # noqa: BLE001 - the log records decisions, it does not make them
            _LOG.warning("Writing the CoCo audit log failed", exc_info=True)

    def _clean(self, value, limit: int) -> str:
        text = str(value)
        if self.redact is not None:
            try:
                text = self.redact(text)
            except Exception:  # noqa: BLE001 - a redactor that fails writes nothing of the text
                _LOG.warning("The CoCo audit redactor failed", exc_info=True)
                return "[not logged: the redactor failed]"
        return text[:limit]

    def read(self) -> list[dict]:
        """The lines written so far (for a page that shows them)."""
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return [json.loads(line) for line in lines if line.strip()]
