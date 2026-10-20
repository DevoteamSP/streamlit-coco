"""The rights of Ask CoCo: what is free, what asks and how the request is shown, what is refused.

Two halves. The first rebuilds the policy of the first host (the Spec-First Cockpit) as a small
subclass of FolderPolicy and runs that host's whole test suite on it: the proof that the package
can express it, and the place where every hardening case stays tested (a second path key on a
search, streams and device names, drive-relative paths, trailing dots, secret-named folders,
hostile git settings, a parent repository). The second half tests the package's own promises: the
default, each switch off and on, the neutral words, the public helpers.
Temporary directories only.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import streamlit_coco.gate
import streamlit_coco.policy
from streamlit_coco.cortex_tools import TOOLS
from streamlit_coco.policy import (
    WORDS,
    Command,
    FolderPolicy,
    git_readonly,
    inside,
    is_secret_name,
    request,
)

NL = chr(10)

LOOKUPS = (
    "snowflake_object_search",
    "snowflake_table_lookup",
    "semantic_view_search",
    "cortex_agent_search",
    "snowflake_product_docs",
    "snowflake_connections_list",
    "web_search",
    "web_fetch",
)
FAMILIES = ("commands", "files", "elsewhere", "queries", "statements", "tool")

# ---------------------------------------------------------------------- the host's policy, rebuilt

FILES = {
    "PROJECT.md": "# Alpha\n",
    "README.md": "# Alpha\n",
    ".env": "KEY=1\n",
    ".git/config": "[core]\n",
    "specs/functional_spec.md": "# Functional\nTODO: scope\n",
    "specs/decisions/001_choice.md": "# ADR 1\n",
    "specs/inputs/note.md": "# Input\n",
    "01_ingest/specs/spec.md": "# Ingest\n",
    "01_ingest/output/load.sql": "select 1;\n",
    "01_ingest/output/README.md": "# Output\n",
    "01_ingest/tests/test_load.sql": "select 1;\n",
    "98_project/tasks.md": "| id |\n",
    "98_project/actions.md": "| id |\n",
    "98_project/decisions.md": "| id |\n",
    "98_project/risks.md": "| id |\n",
    "98_project/attendance.md": "| id |\n",
    "98_project/team.md": "| name |\n",
    "98_project/budget.md": "| line |\n",
    "98_project/timesheets/lea.md": "| week |\n",
    "98_project/raf_history/2026-W40.md": "# W40\n",
    "98_project/budget_history/20261001_budget_snapshot.md": "# Budget\n",
    "98_project/dailies/20261001_daily.md": "# Daily\nDecision: ship.\n",
    "98_project/inputs/raw.md": "# Raw\n",
    "status/lea.md": "# Status\n",
}
# The host's audit script is not here: a stand-in that prints a report and exits 1, as it does.
AUDIT = 'import json, sys\nprint(json.dumps({"project_root": sys.argv[-1]}))\nsys.exit(1)\n'
NAMES = {
    "status": "Look at what has changed in the project's files",
    "diff": "Show the changes not shared yet",
    "log": "Look at the last changes shared",
    "audit": "Run the project audit",
}


def make_projects(tmp: Path) -> tuple[Path, Path]:
    """(projects folder, the alpha project). Beta holds one file; `outside.md` is next to them."""
    projects = tmp / "My projects"  # a space, as on a real machine
    alpha = projects / "alpha"
    for name, text in FILES.items():
        path = alpha / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (projects / "beta").mkdir()
    (projects / "beta" / "PROJECT.md").write_text("# Beta\n", encoding="utf-8")
    (tmp / "outside.md").write_text("# Outside\n", encoding="utf-8")
    return projects, alpha


def init_git(project: Path) -> bool:
    """A real repository with one commit, for the tests that run a listed command."""
    git = shutil.which("git")
    if not git:
        return False
    shutil.rmtree(project / ".git")
    for args in (
        ("init", "-q", "-b", "main"),
        ("add", "-A"),
        ("-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "seed"),
    ):
        subprocess.run([git, "-C", str(project), *args], capture_output=True, check=True)
    return True


def is_budget(relative: str) -> bool:
    """A stand-in for the host's own file classifier (a lower-case path from the project)."""
    parts = relative.split("/")
    if parts[0] != "98_project":
        return False
    name = parts[-1]
    held = parts[1:2] in (["timesheets"], ["budget_history"])
    return held or name in ("team.md", "budget.md") or name.startswith("budget")


class CockpitPolicy(FolderPolicy):
    """The Cockpit's policy as a host writes it on the package: the projects folder is the working
    folder, the open project is the scope, a member does not read budget files freely, the audit
    is one more listed command, and the words are the Cockpit's."""

    audit = Path("check_project.py")  # the host's script; the tests put a stand-in there

    def __init__(self, projects_dir, project=None, role="member", *, python=None, platform=None):
        root = Path(project) if project else None
        super().__init__(
            projects_dir,
            scope=root,
            changes=None if root else (lambda path: "while no project is open"),
            sql=True,
            lookups=True,
            standing=True,
        )
        self.root, self.member = root, role == "member"
        self.python = Path(python or sys.executable).as_posix()
        self.platform = platform or sys.platform
        self.uploads = self.base / "_coco_uploads"
        self.words = {
            **FolderPolicy.words,
            "undo": " The Cockpit cannot undo it.",
            "scope": "the open project" if root else "the projects folder",
            "folder": "the projects folder",
            "large": "a folder too large to check for secret or budget files",
            "files": "changes in this project",
            "elsewhere": "reading outside the project",
            "except": "the .git folder, files that may hold secrets and budget files",
            "also_asks": "Reading outside the scope, in .git, a file that may hold secrets or a "
            "budget file also asks",
        }

    def flag(self, parts):
        rel = parts if self.root else parts[1:]  # from the project, as the host's classifier wants
        if self.member and rel and is_budget("/".join(rel).lower()):
            return "budget", ("a budget file", "a folder with budget files")
        return None

    def commands(self):
        if not self.root:
            return []
        listed = git_readonly(self.root)  # asked again at each call: the repository may have gone
        if listed:
            listed[0] = replace(listed[0], name=NAMES["status"])
        if self.audit.is_file():
            project = self.root.resolve().as_posix()
            argv = [self.python, "-X", "utf8", "-B", "-I", self.audit.as_posix()]
            reads = "The project's files, checked against the method's rules"
            argv += ["--project-root", project]
            listed.append(Command(NAMES["audit"], argv, reads, self.platform))
        return listed if all(c.line for c in listed) else []  # a path the shell expands: none

    def rights(self, granted=()):
        rights = super().rights(granted)
        if self.root:
            rights["scope"] = f"the project {self.root.name} ({self.scope.as_posix()})"
            rights.setdefault("commands", [])
        return rights


Policy = CockpitPolicy


class PolicyCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.projects, self.alpha = make_projects(self.tmp)
        self.audit = CockpitPolicy.audit = self.tmp / "kit" / "check_project.py"
        self.audit.parent.mkdir()
        self.audit.write_text(AUDIT, encoding="utf-8")
        self.manager = Policy(
            self.projects, self.alpha, "manager", python="C:/Py/python.exe", platform="win32"
        )
        self.member = Policy(self.projects, self.alpha, "member")
        self.portfolio = Policy(self.projects, None, "manager")

    def path(self, relative: str) -> str:
        return str(self.alpha / relative)

    def ask(self, policy, tool, payload) -> dict:
        """The request shown for this call: it must be understood, and it must ask."""
        reason, facts = policy.judge(tool, payload)
        self.assertIsNone(reason, f"{tool} {payload} should not be refused")
        self.assertIsNotNone(facts, f"{tool} {payload} should ask")
        return facts

    def free(self, policy, tool, payload) -> None:
        self.assertEqual(
            policy.judge(tool, payload), (None, None), f"{tool} {payload} should be free"
        )

    def refused(self, policy, tool, payload) -> str:
        reason, facts = policy.judge(tool, payload)
        self.assertIsNotNone(reason, f"{tool} {payload} should be refused")
        self.assertIsNone(facts)
        return reason

    def read_ask(self, policy, relative: str) -> dict:
        return self.ask(policy, "Read", {"file_path": self.path(relative)})


class ReadingTest(PolicyCase):
    def test_reading_inside_the_project_is_free(self) -> None:
        for tool, payload in [
            ("Read", {"file_path": self.path("PROJECT.md")}),
            ("Glob", {"pattern": "**/*.md", "path": str(self.alpha)}),
            ("Grep", {"pattern": "TODO", "path": self.path("specs")}),
            ("read", {"file_path": "alpha/PROJECT.md"}),
        ]:  # relative to the projects folder
            with self.subTest(tool=tool):
                self.free(self.manager, tool, payload)

    def test_outside_the_open_project_asks_and_shows_the_path(self) -> None:
        for value in (
            str(self.projects / "beta" / "PROJECT.md"),
            str(self.tmp / "outside.md"),
            "../outside.md",
            "alpha/../beta/PROJECT.md",
            str(self.projects),
        ):
            with self.subTest(value=value):
                facts = self.ask(self.manager, "Read", {"file_path": value})
                self.assertEqual(facts["kind"], "read")
                self.assertEqual(
                    facts["question"], "Allow CoCo to read a file outside the open project?"
                )
                self.assertEqual(facts["evidence"], [{"label": "Path", "text": value}])
                self.assertEqual(facts["standing"]["id"], "elsewhere")

    def test_a_search_without_a_path_would_search_every_project_so_it_asks(self) -> None:
        facts = self.ask(self.manager, "Grep", {"pattern": "TODO"})
        self.assertEqual(
            facts["question"], "Allow CoCo to search a folder outside the open project?"
        )
        self.assertEqual(
            facts["evidence"],
            [
                {"label": "Path", "text": "(not given: the projects folder)"},
                {"label": "Pattern", "text": "TODO"},
            ],
        )
        self.free(self.portfolio, "Grep", {"pattern": "TODO"})

    def test_without_a_project_the_projects_folder_is_free_and_nothing_else(self) -> None:
        self.free(self.portfolio, "Read", {"file_path": str(self.projects / "beta" / "PROJECT.md")})
        facts = self.ask(self.portfolio, "Read", {"file_path": str(self.tmp / "outside.md")})
        self.assertEqual(
            facts["question"], "Allow CoCo to read a file outside the projects folder?"
        )

    def test_a_symlink_is_followed_before_comparing(self) -> None:
        link = self.alpha / "specs" / "link.md"
        try:
            link.symlink_to(self.tmp / "outside.md")
        except OSError:
            self.skipTest("no symlink right on this machine")
        facts = self.ask(self.manager, "Read", {"file_path": str(link)})
        self.assertIn("outside", facts["question"])
        self.assertEqual(facts["evidence"][0]["text"], str(link))  # the path as given

    def test_a_folder_link_is_followed_before_comparing(self) -> None:
        link = self.alpha / "specs" / "elsewhere"
        if os.name == "nt":  # a junction needs no special right
            made = (
                subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(self.tmp)], capture_output=True
                ).returncode
                == 0
            )
        else:
            link.symlink_to(self.tmp)
            made = True
        if not made:
            self.skipTest("no link right on this machine")
        self.assertIn(
            "outside",
            self.ask(self.manager, "Read", {"file_path": str(link / "outside.md")})["question"],
        )

    def test_the_git_folder_asks_and_gets_no_standing_permission(self) -> None:
        for relative in (".git", ".git/config", ".GIT/config"):
            with self.subTest(relative=relative):
                facts = self.read_ask(self.manager, relative)
                self.assertIn(".git", facts["question"])
                self.assertIsNone(facts["standing"])

    def test_files_that_hold_secrets_by_name_ask(self) -> None:
        for name in (
            ".env",
            ".env.local",
            "prod.pem",
            "key.p8",
            "server.key",
            "cert.pfx",
            "id_rsa",
            "id_rsa.pub",
            "connections.toml",
            "my_credentials.md",
            "Secret-notes.md",
            "AWS_CREDENTIAL.txt",
        ):
            with self.subTest(name=name):
                facts = self.read_ask(self.manager, name)
                self.assertEqual(
                    facts["question"], "Allow CoCo to read a file that may hold secrets?"
                )
                self.assertEqual(facts["evidence"], [{"label": "Path", "text": self.path(name)}])
                self.assertIsNone(facts["standing"])
        self.free(self.manager, "Read", {"file_path": self.path("specs/functional_spec.md")})

    def test_a_secret_outside_the_project_is_a_secret_first(self) -> None:
        (self.tmp / "id_rsa").write_text("x", encoding="utf-8")
        facts = self.ask(self.manager, "Read", {"file_path": str(self.tmp / "id_rsa")})
        self.assertIn("secrets", facts["question"])
        self.assertIsNone(facts["standing"])

    def test_budget_files_ask_for_a_member_as_in_browse(self) -> None:
        for relative in (
            "98_project/budget.md",
            "98_project/team.md",
            "98_project/timesheets/lea.md",
            "98_project/timesheets",
            "98_project/budget_history/20261001_budget_snapshot.md",
            "98_PROJECT/Budget.md",
        ):
            with self.subTest(relative=relative):
                facts = self.read_ask(self.member, relative)
                self.assertEqual(facts["question"], "Allow CoCo to read a budget file?")
                self.assertEqual(
                    facts["evidence"], [{"label": "Path", "text": self.path(relative)}]
                )
                self.assertIsNone(facts["standing"])
                self.free(self.manager, "Read", {"file_path": self.path(relative)})
        self.free(self.member, "Read", {"file_path": self.path("98_project/actions.md")})

    def test_budget_files_ask_for_a_member_in_the_portfolio_too(self) -> None:
        member = Policy(self.projects, None, "member")
        self.assertIn("budget", self.read_ask(member, "98_project/budget.md")["question"])
        self.free(member, "Read", {"file_path": self.path("PROJECT.md")})

    def test_a_pattern_that_leaves_the_project_asks(self) -> None:
        for tool, payload in [
            ("Glob", {"pattern": "../*", "path": str(self.alpha)}),
            ("Glob", {"pattern": "C:/Windows/*", "path": str(self.alpha)}),
            ("Glob", {"pattern": "/etc/*", "path": str(self.alpha)}),
            ("Grep", {"pattern": "x", "path": str(self.alpha), "include": "../*.md"}),
        ]:
            with self.subTest(payload=payload):
                facts = self.ask(self.manager, tool, payload)
                self.assertIn("cannot tell", facts["question"])
                self.assertIsNone(facts["standing"])

    def test_a_batch_of_one_to_eight_free_reads_is_free(self) -> None:
        read = {"name": "Read", "input": {"file_path": self.path("PROJECT.md")}}
        self.free(self.manager, "direct_tool_calling", {"tool_calls": [read] * 8})
        self.free(self.manager, "direct_tool_calling", {"tool_calls": [read]})

    def test_any_other_batch_asks_as_a_whole_tool_with_its_whole_input(self) -> None:
        read = {"name": "Read", "input": {"file_path": self.path("PROJECT.md")}}
        for label, payload in [
            ("none", {"tool_calls": []}),
            ("nine", {"tool_calls": [read] * 9}),
            ("extra key", {"tool_calls": [read], "code": "x"}),
            (
                "outside",
                {
                    "tool_calls": [
                        read,
                        {"name": "Read", "input": {"file_path": str(self.tmp / "outside.md")}},
                    ]
                },
            ),
            (
                "secret",
                {"tool_calls": [read, {"name": "Read", "input": {"file_path": self.path(".env")}}]},
            ),
            (
                "command",
                {"tool_calls": [read, {"name": "Bash", "input": {"command": "git status"}}]},
            ),
            (
                "write",
                {
                    "tool_calls": [
                        read,
                        {
                            "name": "Write",
                            "input": {"file_path": self.path("specs/a.md"), "content": "x"},
                        },
                    ]
                },
            ),
            (
                "nested",
                {
                    "tool_calls": [
                        read,
                        {"name": "direct_tool_calling", "input": {"tool_calls": [read]}},
                    ]
                },
            ),
            ("sql", {"tool_calls": [read, {"name": "sql_execute", "input": {"sql": "select 1"}}]}),
            ("not a list", {"tool_calls": "x"}),
            ("a member that is not a call", {"tool_calls": [read, "Read"]}),
        ]:
            with self.subTest(label):
                facts = self.ask(self.manager, "direct_tool_calling", payload)
                self.assertEqual(facts["kind"], "change")
                self.assertIn("direct tool calling", facts["question"])
                self.assertIn("tool_calls", facts["evidence"][0]["text"])

    def test_the_session_tool_list_is_explicit(self) -> None:
        self.assertIn("Read", TOOLS)

    def test_a_payload_that_is_not_an_object_is_refused(self) -> None:
        for tool in ("Read", "Bash", "sql_execute", "Whatever"):
            for payload in (None, "x", ["a"], 3):
                self.refused(self.manager, tool, payload)


class InputKeysTest(PolicyCase):
    """A key the policy does not check is a key that can change what runs: the call is no longer
    a free read, it asks, and is shown."""

    def test_a_search_is_checked_on_the_path_the_cli_reads(self) -> None:
        # Grep and Glob read `path`; `file_path` beside it was checked instead, and hid a folder
        # outside the project
        outside = str(self.projects / "beta")
        for tool in ("Grep", "Glob"):
            with self.subTest(tool=tool):
                facts = self.ask(
                    self.manager,
                    tool,
                    {"pattern": "x", "path": outside, "file_path": self.path("specs")},
                )
                self.assertEqual(facts["kind"], "change")
                self.assertIn("file_path", facts["evidence"][0]["text"])
                self.assertIn(
                    "outside",
                    self.ask(self.manager, tool, {"pattern": "x", "path": outside})["question"],
                )

    def test_the_options_a_model_sends_grep_out_of_habit_stay_free(self) -> None:
        """Seen live: "-n" and "output_mode" made every search fail. The CLI's Grep does not
        read them."""
        target = self.path("specs/functional_spec.md")
        self.free(
            self.manager,
            "grep",
            {"pattern": "UC\\d", "path": target, "-n": True, "output_mode": "content"},
        )
        self.free(
            self.manager,
            "Grep",
            {"pattern": "x", "path": target, "-i": True, "-C": 2, "glob": "*.md"},
        )
        self.assertIn(
            "outside",
            self.ask(
                self.manager,
                "Grep",
                {"pattern": "x", "path": str(self.tmp / "outside.md"), "-n": True},
            )["question"],
        )
        self.assertEqual(
            self.ask(self.manager, "Read", {"file_path": target, "-n": True})["kind"], "change"
        )  # only Grep

    def test_a_long_output_is_free_where_the_cli_put_it_for_this_session_only(self) -> None:
        """Seen live: the CLI moved a long file to its cache and told the agent to read it there."""
        mine, other = (
            self.tmp / "cache" / "tool_outputs" / "session-a",
            self.tmp / "cache" / "tool_outputs" / "session-b",
        )
        for folder in (mine, other):
            folder.mkdir(parents=True)
            (folder / "read_001.txt").write_text("x", encoding="utf-8")
        self.assertIn(
            "outside",
            self.ask(self.manager, "Read", {"file_path": str(mine / "read_001.txt")})["question"],
        )  # unknown session
        self.manager.spill = mine
        self.free(
            self.manager,
            "Read",
            {"file_path": str(mine / "read_001.txt"), "offset": 0, "limit": 200},
        )
        self.assertIn(
            "outside",
            self.ask(self.manager, "Read", {"file_path": str(other / "read_001.txt")})["question"],
        )
        self.assertIn(
            "outside",
            self.ask(
                self.manager, "Read", {"file_path": str(mine / ".." / "session-b" / "read_001.txt")}
            )["question"],
        )
        self.assertIn(
            "outside",
            self.ask(self.manager, "Grep", {"pattern": "x", "path": str(mine)})["question"],
        )  # only Read
        self.assertEqual(
            self.ask(
                self.manager, "Write", {"file_path": str(mine / "read_001.txt"), "content": "y"}
            )["kind"],
            "change",
        )

    def test_the_files_the_user_attached_are_free_to_read_and_only_those(self) -> None:
        upload = self.projects / "_coco_uploads" / "conv-1" / "data.csv"
        upload.parent.mkdir(parents=True)
        upload.write_text("a,b", encoding="utf-8")
        for policy in (self.manager, self.member, self.portfolio):
            self.free(policy, "Read", {"file_path": str(upload), "limit": 50})
            self.assertEqual(policy.uploads, self.projects / "_coco_uploads")
        self.assertIn(
            "outside",
            self.ask(self.manager, "Grep", {"pattern": "a", "path": str(upload.parent)})[
                "question"
            ],
        )  # only Read
        self.assertIn(
            "outside",
            self.ask(
                self.manager,
                "Read",
                {"file_path": str(self.projects / "_coco_uploads" / ".." / "beta" / "PROJECT.md")},
            )["question"],
        )
        self.assertEqual(
            self.ask(self.manager, "Write", {"file_path": str(upload), "content": "x"})["kind"],
            "change",
        )
        self.manager.uploads = None
        self.assertIn(
            "outside", self.ask(self.manager, "Read", {"file_path": str(upload)})["question"]
        )

    def test_any_key_outside_the_tools_schema_asks_and_is_shown(self) -> None:
        target = self.path("specs/functional_spec.md")
        for tool, payload in [
            ("Read", {"file_path": target, "path": str(self.tmp)}),
            ("Read", {"file_path": target, "filePath": "x"}),
            ("Glob", {"pattern": "*.md", "path": self.path("specs"), "cwd": str(self.tmp)}),
            ("Grep", {"pattern": "x", "path": self.path("specs"), "cwd": str(self.tmp)}),
        ]:
            with self.subTest(payload=payload):
                facts = self.ask(self.manager, tool, payload)
                self.assertEqual(facts["kind"], "change")
                self.assertIn(
                    next(k for k in payload if k in ("path", "filePath", "cwd")),
                    facts["evidence"][0]["text"],
                )

    def test_the_keys_the_cli_accepts_stay_free(self) -> None:
        target = self.path("specs/functional_spec.md")
        self.free(self.manager, "Read", {"file_path": target, "offset": 1, "limit": 10})
        self.free(self.manager, "Glob", {"pattern": "*.md", "path": self.path("specs")})
        self.free(
            self.manager,
            "Grep",
            {"pattern": "x", "path": self.path("specs"), "include": "*.md", "head_limit": 5},
        )

    def test_a_path_that_is_not_text_is_refused(self) -> None:
        for tool, payload in [
            ("Read", {"file_path": 3}),
            ("Read", {"file_path": ["a"]}),
            ("Glob", {"pattern": "*.md", "path": 3}),
            ("Grep", {"pattern": "x", "include": 3, "path": self.path("specs")}),
        ]:
            with self.subTest(payload=payload):
                self.assertIn("wrong type", self.refused(self.manager, tool, payload))


class PathTricksTest(PolicyCase):
    """Spellings of a path the app cannot place: they never count as inside, and never as free."""

    BS = chr(92)

    def test_a_stream_or_a_drive_relative_path_is_never_inside(self) -> None:
        for value in (
            self.path("98_project/team.md:x"),
            self.path("connections.toml::$DATA"),
            self.path("server.key::$DATA"),
            self.path(".git::$INDEX_ALLOCATION/config"),
            "C:alpha/PROJECT.md",
            "C:",
            "alpha/PROJECT.md:Zone.Identifier",
        ):
            with self.subTest(value=value):
                facts = self.ask(self.member, "Read", {"file_path": value})
                self.assertIn("cannot tell", facts["question"])
                self.assertEqual(facts["evidence"], [{"label": "Path", "text": value}])
                self.assertIsNone(facts["standing"])

    def test_a_windows_device_prefix_never_makes_a_read_free(self) -> None:
        value = self.BS * 2 + "?" + self.BS + self.path("PROJECT.md")
        facts = self.ask(self.member, "Read", {"file_path": value})
        # On POSIX, backslashes are literal names, not a Windows device namespace.
        question = "cannot tell" if os.name == "nt" else "outside"
        self.assertIn(question, facts["question"])
        self.assertEqual(facts["evidence"], [{"label": "Path", "text": value}])
        if os.name == "nt":
            self.assertIsNone(facts["standing"])
        else:
            self.assertEqual(facts["standing"]["id"], "elsewhere")

    def test_a_network_path_is_outside(self) -> None:
        facts = self.ask(
            self.manager,
            "Read",
            {"file_path": self.BS * 2 + "server" + self.BS + "share" + self.BS + "x.md"},
        )
        self.assertIn("outside", facts["question"])

    def test_a_device_name_is_not_a_file(self) -> None:
        for name in ("NUL", "con", "Aux.md", "COM1.txt", "specs/lpt3", "specs/PRN.md"):
            with self.subTest(name=name):
                self.assertIn("cannot tell", self.read_ask(self.manager, name)["question"])
        self.free(self.manager, "Read", {"file_path": self.path("specs/console.md")})

    def test_a_trailing_dot_or_space_is_never_read_as_free(self) -> None:
        # Windows drops a trailing dot or space: a folder that does not exist yet would become
        # the protected one
        for value in (
            "98_project/team.md.",
            "98_project/team.md ",
            "98_project /team.md",
            "specs/ ",
            "specs./x.md",
            "98_project/.. /team.md",
        ):
            with self.subTest(value=value):
                self.assertIn("cannot tell", self.read_ask(self.member, value)["question"])
        self.free(self.manager, "Read", {"file_path": self.path("specs/../PROJECT.md")})

    def test_mixed_separators_and_case_reach_the_same_rules(self) -> None:
        mixed = (
            str(self.alpha).replace(self.BS, "/") + self.BS + "98_PROJECT/" + self.BS + "Team.MD"
        )
        # Windows aliases case and separators; POSIX treats this as a different path.
        question = "budget" if os.name == "nt" else "outside"
        self.assertIn(question, self.ask(self.member, "Read", {"file_path": mixed})["question"])

    def test_a_short_name_is_expanded_before_the_rules_apply(self) -> None:
        out = (
            subprocess.run(
                ["cmd", "/c", "dir", "/x", str(self.alpha)], capture_output=True, text=True
            ).stdout
            if os.name == "nt"
            else ""
        )
        short = next(
            (
                line.split()[-2]
                for line in out.splitlines()
                if line.split()[-1:] == ["98_project"] and "~" in line.split()[-2]
            ),
            None,
        )
        if not short:
            self.skipTest("no 8.3 names on this volume")
        self.assertIn("budget", self.read_ask(self.member, short + "/team.md")["question"])

    def test_a_secret_name_anywhere_in_the_path_asks(self) -> None:
        for relative in (
            "secrets/notes.md",
            "credentials/a.md",
            "specs/.env/x.md",
            "specs/my_secret_plan/a.md",
        ):
            with self.subTest(relative=relative):
                self.assertIn("secrets", self.read_ask(self.manager, relative)["question"])
        self.free(self.manager, "Read", {"file_path": self.path("specs/secure.md")})

    def test_look_alike_letters_do_not_hide_a_secret_name(self) -> None:
        # the CLI opens a file whose name matches after NFC or lower-casing (Kelvin sign,
        # accents, narrow no-break space)
        kelvin = chr(0x212A)
        for name in (f"server.{kelvin}ey", f"{kelvin}EY.PEM", "SECRET.md", "Credentia" + "l.md"):
            with self.subTest(name=name):
                self.assertIn("secrets", self.read_ask(self.manager, name)["question"])
        (self.alpha / "specs" / ("caf" + chr(0xE9) + ".md")).write_text("x", encoding="utf-8")
        self.free(
            self.manager, "Read", {"file_path": self.path("specs/" + "cafe" + chr(0x301) + ".md")}
        )  # same folder, same rules

    def test_a_pattern_has_no_backslash(self) -> None:
        for tool, key in (("Glob", "pattern"), ("Grep", "include")):
            payload = {
                "pattern": "x",
                "path": self.path("specs"),
                key: "a" + self.BS + "beta" + self.BS + "*.md",
            }
            with self.subTest(tool=tool):
                self.assertIn("cannot tell", self.ask(self.manager, tool, payload)["question"])

    def test_a_path_the_system_cannot_resolve_is_refused(self) -> None:

        saved, streamlit_coco.policy.Path.resolve = (
            streamlit_coco.policy.Path.resolve,
            lambda self, strict=False: (_ for _ in ()).throw(RuntimeError("Symlink loop")),
        )
        try:
            self.assertIn(
                "not understood",
                self.refused(self.manager, "Read", {"file_path": self.path("PROJECT.md")}),
            )
        finally:
            streamlit_coco.policy.Path.resolve = saved

    def test_a_path_the_system_cannot_handle_is_an_answer_not_an_exception(self) -> None:
        for value in ("x" + chr(0) + "y.md", "a/" * 3000 + "x.md", "<>|?*.md"):
            with self.subTest(value=value[:12]):
                reason, facts = self.manager.judge("Read", {"file_path": self.path(value)})
                self.assertIsInstance(reason, (str, type(None)))


class SearchTest(PolicyCase):
    """A search returns lines of the files it covers: one that would cover a file a direct read
    asks for, asks."""

    def search(self, policy, tool: str, relative: str = ""):
        return policy.judge(
            tool, {"pattern": "TODO", "path": self.path(relative) if relative else str(self.alpha)}
        )

    def test_a_member_searching_a_folder_that_holds_budget_files_asks(self) -> None:
        for tool in ("Grep", "Glob"):
            for relative in ("", "98_project", "98_project/timesheets"):
                with self.subTest(tool=tool, relative=relative):
                    reason, facts = self.search(self.member, tool, relative)
                    self.assertIsNone(reason)
                    self.assertIn("budget files", facts["question"])
                    self.assertEqual(
                        facts["evidence"][0],
                        {
                            "label": "Path",
                            "text": self.path(relative) if relative else str(self.alpha),
                        },
                    )
            for relative in ("specs", "98_project/dailies", "01_ingest"):
                with self.subTest(tool=tool, relative=relative):
                    self.assertEqual(self.search(self.member, tool, relative), (None, None))
            with self.subTest(tool=tool, who="manager"):
                self.assertEqual(self.search(self.manager, tool), (None, None))

    def test_a_member_searching_the_projects_folder_asks_too(self) -> None:
        member = Policy(self.projects, None, "member")
        self.assertIn(
            "budget",
            self.ask(member, "Grep", {"pattern": "x", "path": str(self.projects)})["question"],
        )
        self.assertIn(
            "budget",
            self.ask(member, "Grep", {"pattern": "x", "path": str(self.alpha)})["question"],
        )
        self.free(member, "Grep", {"pattern": "x", "path": self.path("specs")})
        self.free(member, "Grep", {"pattern": "x", "path": str(self.projects / "beta")})

    def test_a_grep_of_a_folder_that_holds_a_secret_named_file_asks(self) -> None:
        for name in (
            "server.key",
            "credentials.md",
            "my_secret.txt",
            "id_rsa",
            "cert.pem",
            "connections.toml",
        ):
            with self.subTest(name=name):
                (self.alpha / "specs" / name).write_text("x", encoding="utf-8")
                self.assertIn(
                    "secrets",
                    self.ask(self.manager, "Grep", {"pattern": "x", "path": self.path("specs")})[
                        "question"
                    ],
                )
                self.assertIn(
                    "secrets",
                    self.ask(self.manager, "Grep", {"pattern": "x", "path": str(self.alpha)})[
                        "question"
                    ],
                )
                self.free(
                    self.manager, "Grep", {"pattern": "x", "path": self.path("specs/decisions")}
                )
                (self.alpha / "specs" / name).unlink()

    def test_a_folder_the_clis_own_search_skips_is_not_looked_at(self) -> None:
        # Grep does not read names that start with a dot: the .env of the fixture does not make
        # the whole project ask
        self.free(self.manager, "Grep", {"pattern": "x", "path": str(self.alpha)})
        (self.alpha / ".config").mkdir()
        (self.alpha / ".config" / "secrets.md").write_text("x", encoding="utf-8")
        self.free(self.manager, "Grep", {"pattern": "x", "path": str(self.alpha)})

    def test_a_pattern_that_names_a_secret_file_asks(self) -> None:
        for tool, key, pattern in (
            ("Glob", "pattern", "**/.env*"),
            ("Glob", "pattern", "*.pem"),
            ("Glob", "pattern", "**/Credentials*.md"),
            ("Glob", "pattern", "id_rsa"),
            ("Grep", "include", "*.key"),
            ("Grep", "include", "secret*"),
        ):
            with self.subTest(pattern=pattern):
                payload = (
                    {"pattern": "x", "path": self.path("specs"), key: pattern}
                    if tool == "Grep"
                    else {"pattern": pattern, "path": self.path("specs")}
                )
                facts = self.ask(self.manager, tool, payload)
                self.assertIn("secrets", facts["question"])
                self.assertEqual(facts["evidence"][-1]["text"], pattern)
        self.free(self.manager, "Glob", {"pattern": "**/*.md", "path": self.path("specs")})

    def test_a_folder_too_large_to_check_asks(self) -> None:

        saved, streamlit_coco.policy._WALK_LIMIT = streamlit_coco.policy._WALK_LIMIT, 3
        try:
            self.assertIn(
                "too large",
                self.ask(self.manager, "Grep", {"pattern": "x", "path": str(self.alpha)})[
                    "question"
                ],
            )
        finally:
            streamlit_coco.policy._WALK_LIMIT = saved


class CommandsTest(PolicyCase):
    def lines(self, policy=None) -> dict[str, str]:
        listed = {c.name: c.line for c in (policy or self.manager).commands()}
        return {key: listed[name] for key, name in NAMES.items() if name in listed}

    def test_the_exact_lines_on_windows(self) -> None:
        project = self.alpha.resolve().as_posix()
        lines = self.lines()
        git = "git --no-pager --no-optional-locks -c core.fsmonitor=false"
        git += f' -c log.showSignature=false -C "{project}"'
        self.assertEqual(lines["status"], f"{git} status --short --branch")
        self.assertEqual(lines["diff"], f"{git} diff --no-ext-diff --no-textconv")
        self.assertEqual(lines["log"], f"{git} log -10 --oneline")
        script = self.audit.as_posix()
        self.assertEqual(
            lines["audit"],
            f'& "C:/Py/python.exe" -X utf8 -B -I "{script}" --project-root "{project}"',
        )

    def test_the_call_form_only_where_a_quoted_program_starts_the_line(self) -> None:
        posix = Policy(
            self.projects, self.alpha, "manager", python="/usr/bin/python3", platform="linux"
        )
        self.assertFalse(self.lines(posix)["audit"].startswith("&"))
        self.assertTrue(self.lines(posix)["audit"].startswith('"/usr/bin/python3" -X utf8 -B -I'))
        self.assertTrue(self.lines()["audit"].startswith('& "'))
        self.assertTrue(
            all(not line.startswith("&") for key, line in self.lines().items() if key != "audit")
        )

    def test_the_audit_is_dropped_if_the_script_is_missing(self) -> None:
        CockpitPolicy.audit = self.tmp / "missing.py"
        self.assertNotIn("audit", self.lines())

    def test_a_project_without_a_repository_of_its_own_gets_no_git_command(self) -> None:
        # git would climb to a parent repository and report files of other projects
        shutil.rmtree(self.alpha / ".git")
        self.assertEqual(sorted(self.lines()), ["audit"])

    def test_a_repository_cannot_make_a_listed_command_run_its_program(self) -> None:
        if not init_git(self.alpha):
            self.skipTest("no git on this machine")
        hook, marker = self.tmp / "hook.py", self.tmp / "ran.txt"
        hook.write_text(f"open({str(marker)!r}, 'w').write('x')\n", encoding="utf-8")
        run = f'"{sys.executable}" "{hook.as_posix()}"'
        for key, value in (
            ("core.fsmonitor", run),
            ("log.showSignature", "true"),
            ("gpg.program", run),
            ("core.pager", run),
            ("diff.external", run),
        ):
            subprocess.run(
                ["git", "-C", str(self.alpha), "config", key, value],
                check=True,
                capture_output=True,
            )
        (self.alpha / "specs" / "functional_spec.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.alpha), "status"], capture_output=True
        )  # the same repository, unguarded
        if not marker.exists():
            self.skipTest("this git does not run core.fsmonitor from a hook command")
        marker.unlink()
        for command in self.manager.commands():
            if command.name != NAMES["audit"]:
                with self.subTest(command.name):
                    done = subprocess.run(command.argv, capture_output=True, timeout=60)
                    self.assertEqual(done.returncode, 0, done.stderr)
                    self.assertFalse(marker.exists(), "the repository's program ran")

    def test_the_audit_runs_as_listed_and_exits_non_zero_when_it_finds_something(self) -> None:
        # the host's script is not here: a stand-in that prints a report and exits 1, as it does
        listed = Policy(self.projects, self.alpha, "manager").commands()
        audit = next(c for c in listed if c.name == NAMES["audit"])
        done = subprocess.run(
            audit.argv,
            capture_output=True,
            timeout=120,
            env={**os.environ, "PYTHONPATH": str(self.tmp)},
        )
        self.assertIn(done.returncode, (0, 1), done.stderr)
        self.assertTrue(done.stdout.lstrip().startswith(b"{"))

    def test_a_path_the_shell_would_expand_gets_no_command(self) -> None:
        # inside double quotes PowerShell expands $name and a backtick: the line would not run
        # on the folder it names
        for name in ("a$b", "a" + chr(96) + "b"):
            with self.subTest(name=name):
                folder = self.projects / name
                (folder / ".git").mkdir(parents=True)
                self.assertEqual(Policy(self.projects, folder, "manager").commands(), [])

    def test_without_a_project_there_is_no_listed_command(self) -> None:
        self.assertEqual(self.portfolio.commands(), [])
        self.assertEqual(
            self.ask(self.portfolio, "Bash", {"command": self.lines()["status"]})["kind"], "change"
        )

    def test_a_listed_line_is_shown_as_a_read_and_asks(self) -> None:
        for command in self.manager.commands():
            for suffix in ("", NL):
                with self.subTest(command=command.name):
                    facts = self.ask(self.manager, "Bash", {"command": command.line + suffix})
                    self.assertEqual(facts["kind"], "read")
                    self.assertEqual(facts["reads"], command.reads)
                    self.assertEqual(
                        facts["evidence"], [{"label": "Command", "text": command.line}]
                    )

    def test_any_other_command_is_a_change_with_the_exact_command(self) -> None:
        status, project = self.lines()["status"], self.alpha.resolve().as_posix()
        for label, line in [
            ("windows audit without the call form", self.lines()["audit"][2:]),
            ("appended command", status + " ; git push"),
            ("piped", status + " | more"),
            (
                "other project",
                status.replace(project, self.projects.resolve().as_posix() + "/beta"),
            ),
            ("extra flag", status + " --porcelain"),
            ("another spelling", f"git -C {project} status --short --branch"),
            ("without the hardening", status.replace(" -c core.fsmonitor=false", "")),
            ("a unicode space after", status + chr(0xA0)),
            ("a unicode space before", chr(0xA0) + status),
            ("a form feed after", status + chr(0x0C)),
            ("two lines", status + NL + "whoami"),
            ("whoami", "whoami"),
            ("empty", ""),
            *[
                (f"git {verb}", f'git --no-pager -C "{project}" {verb}')
                for verb in (
                    "add -A",
                    "commit -m x",
                    "push",
                    "pull",
                    "fetch",
                    "checkout main",
                    "reset --hard",
                    "stash",
                    "merge main",
                    "tag v1",
                )
            ],
        ]:
            with self.subTest(label):
                facts = self.ask(self.manager, "Bash", {"command": line})
                self.assertEqual(facts["kind"], "change")
                self.assertIn("cannot undo", facts["question"])
                self.assertEqual(facts["evidence"], [{"label": "Command", "text": line}])
                self.assertEqual(facts["standing"]["id"], "commands")

    def test_a_working_folder_or_any_key_is_shown_with_the_command(self) -> None:
        facts = self.ask(
            self.manager,
            "Bash",
            {
                "command": self.lines()["status"],
                "cwd": str(self.projects / "beta"),
                "description": "d",
            },
        )
        self.assertEqual(
            facts["kind"], "change"
        )  # a key beyond the CLI's own can move what the line does
        self.assertEqual(facts["evidence"][0]["text"], self.lines()["status"])
        self.assertIn("beta", facts["evidence"][1]["text"])
        self.assertNotIn('"description"', repr(facts["evidence"]))

    def test_a_multi_line_command_says_so(self) -> None:
        facts = self.ask(self.manager, "Bash", {"command": "a" + NL + "b" + NL + "c"})
        self.assertEqual(facts["changes"]["note"], "3 lines")
        self.assertEqual(facts["evidence"][0]["text"], "a" + NL + "b" + NL + "c")

    def test_a_command_that_is_not_text_is_shown_whole(self) -> None:
        facts = self.ask(self.manager, "Bash", {"command": ["ls"]})
        self.assertIn('"command"', facts["evidence"][0]["text"])

    def test_the_command_family_says_nobody_reads_each_call(self) -> None:
        offer = self.ask(self.manager, "Bash", {"command": "whoami"})["standing"]
        self.assertEqual(set(offer), {"id", "label", "covers", "until"})
        self.assertIn("without anyone reading each call", offer["covers"])
        self.assertIn("conversation ends", offer["until"])


class FileChangeTest(PolicyCase):
    def test_a_write_inside_the_project_is_shown_relative(self) -> None:
        facts = self.ask(
            self.manager,
            "Write",
            {
                "file_path": self.path("98_project/weeklies/20261002_weekly.md"),
                "content": "# Weekly\n",
            },
        )
        self.assertEqual(facts["kind"], "change")
        self.assertEqual(
            facts["question"], "Allow CoCo to create a file? The Cockpit cannot undo it."
        )
        self.assertEqual(
            facts["changes"],
            {"file": "98_project/weeklies/20261002_weekly.md", "lines": None, "note": ""},
        )
        self.assertEqual(facts["evidence"], [{"label": "New content", "text": "# Weekly\n"}])
        self.assertEqual(
            (facts["where"], facts["reads"], facts["evidence_label"]),
            ("alpha", None, "Show change"),
        )
        self.assertEqual(facts["standing"]["id"], "files")

    def test_a_replace(self) -> None:
        facts = self.ask(
            self.manager, "Write", {"file_path": self.path("status/lea.md"), "content": "# New\n"}
        )
        self.assertIn("replace a file?", facts["question"])
        self.assertEqual(facts["changes"]["file"], "status/lea.md")

    def test_an_edit(self) -> None:
        old, new = "# Functional\nTODO: scope", "# Functional\nDone"
        facts = self.ask(
            self.manager,
            "Edit",
            {
                "file_path": self.path("specs/functional_spec.md"),
                "old_string": old,
                "new_string": new,
            },
        )
        self.assertEqual(
            facts["question"], "Allow CoCo to change a file? The Cockpit cannot undo it."
        )
        self.assertEqual(
            facts["changes"], {"file": "specs/functional_spec.md", "lines": 2, "note": "2 lines"}
        )
        self.assertEqual(
            facts["evidence"], [{"label": "Replaces", "text": old}, {"label": "With", "text": new}]
        )

    def test_an_edit_that_matches_nothing_still_asks(self) -> None:
        # the CLI will fail it; the user is shown the call as it is
        self.ask(
            self.manager,
            "Edit",
            {
                "file_path": self.path("specs/functional_spec.md"),
                "old_string": "absent",
                "new_string": "x",
            },
        )

    def test_nothing_in_the_project_is_protected_from_being_asked(self) -> None:
        for relative in (
            "PROJECT.md",
            "98_project/tasks.md",
            "98_project/budget.md",
            "98_project/raf_history/2026-W40.md",
            "01_ingest/output/load.sql",
            "01_ingest/tests/test_load.sql",
            ".git/config",
            "specs/new.txt",
            "README.md",
            "98_project/timesheets/lea.md",
            "other/deep/x.md",
        ):
            with self.subTest(relative=relative):
                facts = self.ask(
                    self.manager, "Write", {"file_path": self.path(relative), "content": "x"}
                )
                self.assertEqual(facts["changes"]["file"], relative)
                self.assertNotIn("outside", facts["question"])
                # asked like any other, but .git is never left to a standing permission
                family = None if relative == ".git/config" else "files"
                self.assertEqual(facts["standing"] and facts["standing"]["id"], family)

    def test_the_files_family_never_covers_a_place_a_read_asks_for(self) -> None:
        """The package's rule, a deliberate change from the Cockpit's: with the permission given,
        an agent turned by a file it read could rewrite a hook or a credentials file unseen."""

        def offer(policy, relative):
            call = {"file_path": self.path(relative), "content": "x"}
            edit = {"file_path": self.path(relative), "old_string": "a", "new_string": "b"}
            write, change = self.ask(policy, "Write", call), self.ask(policy, "Edit", edit)
            self.assertEqual((write["kind"], change["kind"]), ("change", "change"))  # still asked
            self.assertEqual(write["standing"], change["standing"])
            return write["standing"]

        guarded = (".git/config", ".git/hooks/pre-commit", ".GIT/hooks/x", ".env", "specs/a.key")
        for relative in (*guarded, "secrets/notes.md", "specs/my_credentials.md", "specs/x.md:s"):
            with self.subTest(relative=relative):
                self.assertIsNone(offer(self.manager, relative))
                self.assertIsNone(offer(self.member, relative))
        for relative in ("98_project/budget.md", "98_project/timesheets/lea.md"):  # what flag marks
            with self.subTest(relative=relative):
                self.assertIsNone(offer(self.member, relative))
                self.assertEqual(offer(self.manager, relative)["id"], "files")
        for policy in (self.manager, self.member):
            self.assertEqual(
                offer(policy, "specs/x.md")["covers"],
                "Any change to any file inside alpha, except the .git folder, files that may hold "
                "secrets and budget files: create, change or replace.",
            )
        self.assertIsNone(offer(self.manager, str(self.tmp / "id_rsa")))  # outside, and a secret

    def test_outside_the_project_the_full_path_and_the_words_outside(self) -> None:
        for target in (
            self.tmp / "outside.md",
            self.projects / "beta" / "PROJECT.md",
            self.tmp / "new" / "x.md",
        ):
            with self.subTest(target=target.name):
                facts = self.ask(self.manager, "Write", {"file_path": str(target), "content": "x"})
                self.assertIn("outside the open project", facts["question"])
                self.assertEqual(facts["changes"]["file"], target.resolve().as_posix())
                self.assertIn("outside the open project", facts["changes"]["note"])
                self.assertIsNone(
                    facts["standing"]
                )  # the Files family is inside the open project only

    def test_without_a_project_every_change_is_outside(self) -> None:
        facts = self.ask(
            self.portfolio,
            "Edit",
            {
                "file_path": str(self.projects / "beta" / "PROJECT.md"),
                "old_string": "a",
                "new_string": "b",
            },
        )
        self.assertIn("while no project is open", facts["question"])
        self.assertIsNone(facts["standing"])

    def test_a_relative_path_is_resolved_like_the_cli_does(self) -> None:
        facts = self.ask(self.manager, "Write", {"file_path": "alpha/specs/rel.md", "content": "x"})
        self.assertEqual(facts["changes"]["file"], "specs/rel.md")
        self.assertIn(
            "outside",
            self.ask(self.manager, "Write", {"file_path": "../outside.md", "content": "x"})[
                "question"
            ],
        )

    def test_a_link_out_of_the_project_is_followed(self) -> None:
        link = self.alpha / "specs" / "link.md"
        try:
            link.symlink_to(self.tmp / "outside.md")
        except OSError:
            self.skipTest("no symlink right on this machine")
        self.assertIn(
            "outside",
            self.ask(self.manager, "Write", {"file_path": str(link), "content": "x"})["question"],
        )

    def test_an_edit_counts_the_lines_of_the_one_replacement(self) -> None:
        facts = self.ask(
            self.manager,
            "Edit",
            {
                "file_path": self.path("specs/once.md"),
                "old_string": "a" + NL + "b",
                "new_string": "c",
            },
        )
        self.assertEqual(facts["changes"]["lines"], 2)

    def test_a_large_write_is_shown_whole(self) -> None:
        content = "x" * 300_000
        self.assertEqual(
            self.ask(
                self.manager, "Write", {"file_path": self.path("specs/big.md"), "content": content}
            )["evidence"][0]["text"],
            content,
        )

    def test_other_inputs_of_a_file_tool_are_shown(self) -> None:
        facts = self.ask(
            self.manager,
            "Write",
            {"file_path": self.path("specs/x.md"), "content": "x", "mode": "append"},
        )
        self.assertIn("append", facts["evidence"][-1]["text"])

    def test_a_change_without_a_readable_path_is_shown_as_the_whole_input(self) -> None:
        facts = self.ask(self.manager, "Write", {"content": "x"})
        self.assertIn("Write", facts["question"])
        self.assertIn('"content"', facts["evidence"][0]["text"])

    def test_the_request_is_written_from_the_call_not_from_the_agents_words(self) -> None:
        facts = self.ask(
            self.manager, "Write", {"file_path": self.path("specs/x.md"), "content": "x"}
        )
        reason, again = self.manager.judge(
            "Write",
            {
                "file_path": self.path("specs/x.md"),
                "content": "x",
                "description": "Only reads, changes nothing",
            },
        )
        self.assertIsNone(reason)
        self.assertEqual(
            again["question"], facts["question"]
        )  # the words are an unknown key: shown, never believed
        self.assertEqual(again["kind"], "change")


class SqlTest(PolicyCase):
    """SQL runs on the user's Snowflake connection, reads and changes alike, and never without
    being asked (or standing)."""

    READS = (
        "SELECT 1",
        "select * from DB.S.T where x = 1;",
        "WITH a AS (SELECT 1) SELECT * FROM a",
        "show tables in schema DB.S",
        "DESCRIBE TABLE DB.S.T",
        "explain select 1",
        "select last_update, settings from DB.S.T",
    )
    CHANGES = (
        "DROP TABLE t",
        "select 1; drop table t",
        "select 1 -- x",
        "/* x */ select 1",
        "select 1 // x",
        "WITH a AS (SELECT 1) INSERT INTO t SELECT * FROM a",
        "select * into t2 from t",
        "select system$cancel_query(1)",
        "CALL p()",
        "use role accountadmin",
        "create table t as select 1",
        "insert into t values (1)",
        "explain delete from t",
        "update t set a = 1",
        "selectx 1",
    )

    def test_only_a_statement_that_surely_reads_is_shown_as_a_read(self) -> None:
        for policy in (self.manager, self.member, self.portfolio):
            for sql in self.READS + self.CHANGES:
                with self.subTest(sql=sql):
                    facts = self.ask(
                        policy, "sql_execute", {"sql": sql, "description": "the agent's words"}
                    )
                    self.assertEqual(facts["kind"], "read" if sql in self.READS else "change")
                    self.assertEqual(
                        facts["evidence"], [{"label": "Query", "text": sql}]
                    )  # the exact text, never the description
                    self.assertNotIn("the agent's words", str(facts))
                    self.assertEqual(facts["changes"] is None, sql in self.READS)
                    self.assertEqual(
                        facts["standing"]["id"], "queries" if sql in self.READS else "statements"
                    )

    def test_a_change_names_what_it_runs_and_says_it_cannot_be_undone(self) -> None:
        facts = self.ask(
            self.portfolio,
            "sql_execute",
            {"sql": "create table t (a int); drop table u; drop table v", "description": "d"},
        )
        self.assertEqual(
            facts["changes"],
            {"file": "Snowflake: CREATE, DROP", "lines": None, "note": "3 statements"},
        )
        self.assertIn("cannot undo", facts["question"])
        self.assertEqual(
            (facts["pill"], facts["evidence_label"]),
            ("Allow a change on Snowflake?", "Show statement"),
        )
        self.assertEqual(
            self.ask(self.portfolio, "sql_execute", {"sql": "select 1", "description": "d"})[
                "pill"
            ],
            "Allow a query?",
        )

    def test_the_statements_family_says_nobody_reads_each_call_the_queries_family_does_not(
        self,
    ) -> None:
        self.assertIn(
            "without anyone reading",
            self.ask(self.manager, "sql_execute", {"sql": "drop table t"})["standing"]["covers"],
        )
        self.assertNotIn(
            "without anyone",
            self.ask(self.manager, "sql_execute", {"sql": "select 1"})["standing"]["covers"],
        )

    def test_the_connection_and_any_other_input_are_shown_not_refused(self) -> None:
        for extra in (
            {"connection": "prod"},
            {"only_compile": True},
            {"timeout_seconds": 3600},
            {"query": "select 1"},
        ):
            with self.subTest(extra=extra):
                facts = self.ask(
                    self.manager, "sql_execute", {"sql": "select 1", "description": "d"} | extra
                )
                self.assertIn(next(iter(extra)), facts["evidence"][-1]["text"])

    def test_a_query_that_is_not_text_is_refused(self) -> None:
        for sql in (7, None, ["select 1"]):
            with self.subTest(sql=str(sql)[:10]):
                self.assertIn(
                    "not text",
                    self.refused(self.manager, "sql_execute", {"sql": sql, "description": "d"}),
                )
        self.refused(self.manager, "sql_execute", {"description": "d"})

    def test_an_empty_or_a_huge_query_asks(self) -> None:
        for sql in ("", "   ", "x" * 20_001):
            self.assertEqual(self.ask(self.manager, "sql_execute", {"sql": sql})["kind"], "change")

    def test_sql_in_a_batch_asks_as_a_whole(self) -> None:
        read = {"name": "Read", "input": {"file_path": str(self.alpha / "PROJECT.md")}}
        self.assertEqual(
            self.ask(
                self.manager,
                "direct_tool_calling",
                {"tool_calls": [read, {"name": "sql_execute", "input": {"sql": "select 1"}}]},
            )["kind"],
            "change",
        )


class OtherToolsTest(PolicyCase):
    LOOKUPS = (
        "snowflake_object_search",
        "snowflake_table_lookup",
        "semantic_view_search",
        "cortex_agent_search",
        "snowflake_product_docs",
        "snowflake_connections_list",
        "web_search",
        "web_fetch",
    )

    def test_the_look_up_tools_are_reads_that_say_where_the_question_goes(self) -> None:
        for name in self.LOOKUPS:
            with self.subTest(name=name):
                facts = self.ask(
                    self.manager, name, {"query": "orders", "url": "https://example.invalid/x"}
                )
                self.assertEqual(facts["kind"], "read")
                self.assertIsNone(facts["changes"])
                self.assertTrue(facts["where"] and facts["reads"])
                self.assertIn("https://example.invalid/x", facts["evidence"][0]["text"])
                self.assertEqual(facts["standing"]["id"], "tool:" + name)
        self.assertIn(
            "leave this computer", self.ask(self.manager, "web_search", {"query": "x"})["where"]
        )
        self.assertIn(
            "Snowflake", self.ask(self.portfolio, "snowflake_table_lookup", {"table": "T"})["where"]
        )

    def test_any_tool_name_with_any_input_asks_as_a_change_naming_the_tool(self) -> None:
        for name, payload in (
            ("snowflake_stage_upload", {"file": "a.csv", "stage": "@S"}),
            ("Task", {"prompt": "go"}),
            ("mcp__x__y", {}),
            ("NotebookEdit", {"cell": 1}),
            ("Skill", {"skill": "spec-first"}),
            ("", {"a": [1, 2]}),
        ):
            with self.subTest(name=name):
                facts = self.ask(self.manager, name, payload)
                self.assertEqual(facts["kind"], "change")
                self.assertIn("cannot undo", facts["question"])
                self.assertEqual(
                    facts["evidence"],
                    [{"label": "Input", "text": json.dumps(payload, indent=2)}],
                )
                self.assertEqual(facts["standing"]["id"], "tool:" + name.lower())
        facts = self.ask(self.manager, "snowflake_stage_upload", {"x": 1})
        self.assertIn('"snowflake stage upload"', facts["question"])

    def test_the_input_is_shown_whole_as_pretty_json(self) -> None:
        payload = {"b": 1, "a": {"c": [1, 2]}, "é": "ü"}
        text = self.ask(self.manager, "Mystery", payload)["evidence"][0]["text"]
        self.assertEqual(text, json.dumps(payload, indent=2, ensure_ascii=False))
        self.assertIn("\n", text)

    def test_a_tool_family_covers_that_tool_only(self) -> None:
        a, b = (self.ask(self.manager, name, {})["standing"] for name in ("Mystery", "Other"))
        self.assertNotEqual(a["id"], b["id"])
        self.assertIn("whatever it is given", a["covers"])


class StandingOfferTest(PolicyCase):
    def test_every_request_that_asks_offers_the_family_of_the_call(self) -> None:
        for tool, payload, family in [
            ("Bash", {"command": "whoami"}, "commands"),
            ("Bash", {"command": self.manager.commands()[0].line}, "commands"),
            ("Write", {"file_path": self.path("specs/x.md"), "content": "x"}, "files"),
            (
                "Edit",
                {"file_path": self.path("specs/x.md"), "old_string": "a", "new_string": "b"},
                "files",
            ),
            ("sql_execute", {"sql": "select 1"}, "queries"),
            ("sql_execute", {"sql": "drop table t"}, "statements"),
            ("web_fetch", {"url": "x"}, "tool:web_fetch"),
            ("Task", {}, "tool:task"),
            ("Read", {"file_path": str(self.tmp / "outside.md")}, "elsewhere"),
            ("Grep", {"pattern": "x", "path": str(self.tmp)}, "elsewhere"),
        ]:
            with self.subTest(tool=tool, family=family):
                offer = self.ask(self.manager, tool, payload)["standing"]
                self.assertEqual(offer["id"], family)
                self.assertEqual(set(offer), {"id", "label", "covers", "until"})
                self.assertTrue(offer["label"] and offer["covers"].endswith("."))
                self.assertIn("until this conversation ends", offer["until"].lower())

    def test_the_covers_sentence_names_the_project_and_the_limits(self) -> None:
        self.assertIn(
            "alpha",
            self.ask(self.manager, "Write", {"file_path": self.path("specs/x.md"), "content": "x"})[
                "standing"
            ]["covers"],
        )
        elsewhere = self.ask(self.manager, "Read", {"file_path": str(self.tmp / "outside.md")})[
            "standing"
        ]["covers"]
        self.assertIn("secrets", elsewhere)
        self.assertIn(".git", elsewhere)
        call = {"file_path": self.path("a.md"), "content": "x"}
        covers = self.ask(self.manager, "Write", call)["standing"]["covers"]
        self.assertIn("except the .git folder, files that may hold secrets", covers)


class WordsTest(PolicyCase):
    def test_steps_are_named_from_the_call(self) -> None:
        for (tool, payload), expected in [
            (("Read", {"file_path": self.path("PROJECT.md")}), "Read PROJECT.md"),
            (("Grep", {"pattern": "TODO", "path": str(self.alpha)}), 'Search for "TODO"'),
            (
                ("direct_tool_calling", {"tool_calls": [{"name": "Read", "input": {}}] * 5}),
                "Read 5 files",
            ),
            (
                ("Edit", {"file_path": self.path("specs/functional_spec.md")}),
                "Change specs/functional_spec.md",
            ),
            (("Write", {"file_path": self.path("specs/new.md")}), "Create specs/new.md"),
            (("Write", {"file_path": self.path("status/lea.md")}), "Replace status/lea.md"),
            (
                ("Bash", {"command": self.manager.commands()[0].line}),
                "Look at what has changed in the project's files",
            ),
            (("Bash", {"command": "whoami"}), "Run a command"),
            (("sql_execute", {"sql": "select 1"}), "Run a query on Snowflake"),
            (("sql_execute", {"sql": "drop table A.B.C"}), "Run on Snowflake: DROP"),
            (("web_search", {"query": "x"}), "Search the web"),
            (("WebFetch", {}), "Use WebFetch"),
            (("snowflake_stage_upload", {}), "Use snowflake stage upload"),
            (
                ("Read", {"file_path": str(self.tmp / "outside.md")}),
                "Read outside.md",
            ),  # outside both: the name only
            (
                ("Read", {"file_path": str(self.projects / "beta" / "PROJECT.md")}),
                "Read beta/PROJECT.md",
            ),  # another project: from the projects folder
            (("Glob", {"pattern": str(self.alpha / "specs" / "*.md")}), "List specs/*.md"),
        ]:
            with self.subTest(tool=tool):
                self.assertEqual(self.manager.describe(tool, payload), expected)


class RightsTest(PolicyCase):
    def test_the_rights_say_what_is_free_what_asks_and_that_nothing_is_refused(self) -> None:
        rights = self.manager.rights()
        self.assertIn("alpha", rights["scope"])
        self.assertIn("Read, Glob, Grep", rights["without_asking"])
        self.assertIn("Everything else", rights["asked"])
        self.assertIn("Edit or Write anywhere", rights["asked"])
        self.assertIn("Nothing", rights["refused"])
        self.assertEqual(rights["running_without_asking_now"], [])
        self.assertEqual(
            [c["line"] for c in rights["commands"]], [c.line for c in self.manager.commands()]
        )
        self.assertNotIn("commands", self.portfolio.rights())
        self.assertIn("projects folder", self.portfolio.rights()["scope"])

    def test_the_rights_list_what_currently_runs_without_asking(self) -> None:
        self.assertEqual(
            self.manager.rights(["Any command, on this computer."])["running_without_asking_now"],
            ["Any command, on this computer."],
        )


# ---------------------------------------------------------------------- the package's own promises


def _pretty(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


class FolderCase(unittest.TestCase):
    """One working folder, as `ask_coco(".")` gives it to the default policy."""

    CALLS = (  # one call of each kind that is not a read inside the folder
        ("Bash", {"command": "rm -rf build", "cwd": "/srv"}),
        ("Write", {"file_path": "new.md", "content": "# New"}),
        ("Edit", {"file_path": "notes.md", "old_string": "# Notes", "new_string": "# Done"}),
        ("sql_execute", {"sql": "drop table T", "connection": "prod"}),
        ("sql_execute", {"sql": "select 1"}),
        ("web_search", {"query": "weather"}),
        ("snowflake_table_lookup", {"table": "DB.S.T"}),
        ("Task", {"prompt": "go"}),
        ("mcp__x__y", {"a": "b"}),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.folder = self.tmp / "work"
        files = ("notes.md", "docs/guide.md", "src/app.py", ".env", ".git/config")
        for name in (*files, "../outside.md"):
            path = self.folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Notes\n", encoding="utf-8")
        self.outside = str(self.tmp / "outside.md")

    def path(self, relative: str) -> str:
        return str(self.folder / relative)

    def policy(self, **options) -> FolderPolicy:
        return FolderPolicy(self.folder, **options)

    def ask(self, policy, tool, payload) -> dict:
        reason, facts = policy.judge(tool, payload)
        self.assertIsNone(reason, f"{tool} {payload} should not be refused")
        self.assertIsNotNone(facts, f"{tool} {payload} should ask")
        return facts

    def write(self, policy, name: str) -> dict:
        return self.ask(policy, "Write", {"file_path": name, "content": "x"})


class DefaultTest(FolderCase):
    """`FolderPolicy(folder)`: the safest, not the richest."""

    def test_reading_inside_the_folder_is_free(self) -> None:
        read = {"name": "Read", "input": {"file_path": self.path("notes.md")}}
        for tool, payload in (
            ("Read", {"file_path": self.path("notes.md")}),
            ("Read", {"file_path": "docs/guide.md"}),  # relative to the working folder
            ("Glob", {"pattern": "**/*.md", "path": str(self.folder)}),
            ("Grep", {"pattern": "Notes"}),  # no path: the working folder itself
            ("Grep", {"pattern": "Notes", "path": self.path("docs")}),
            ("direct_tool_calling", {"tool_calls": [read, read]}),
        ):
            with self.subTest(tool=tool, payload=payload):
                self.assertEqual(self.policy().judge(tool, payload), (None, None))

    def test_a_read_the_folder_does_not_make_free_asks_in_neutral_words(self) -> None:
        for name, what in (
            (self.path(".env"), "a file that may hold secrets"),
            (self.outside, "a file outside the working folder"),
            (self.path(".git/config"), "a file of the .git folder"),
            (self.path("notes.md:x"), "a path the app cannot tell is inside the working folder"),
        ):
            with self.subTest(what=what):
                facts = self.ask(self.policy(), "Read", {"file_path": name})
                self.assertEqual(facts["kind"], "read")
                self.assertEqual(facts["question"], f"Allow CoCo to read {what}?")
                self.assertEqual(facts["evidence"], [{"label": "Path", "text": name}])
                self.assertIsNone(facts["standing"])
        facts = self.ask(self.policy(), "Grep", {"pattern": "x", "path": str(self.tmp)})
        self.assertIn("search a folder outside the working folder?", facts["question"])

    def test_every_other_call_asks_each_time_as_a_change_with_its_whole_input(self) -> None:
        policy = self.policy()
        for tool, payload in self.CALLS:
            with self.subTest(tool=tool, payload=payload):
                facts = self.ask(policy, tool, payload)
                self.assertEqual(facts["kind"], "change")
                self.assertIsNone(facts["reads"])
                self.assertTrue(facts["question"].endswith(" It cannot be undone."))
                self.assertIsNone(facts["standing"])
                shown = facts["changes"]["file"] + "".join(e["text"] for e in facts["evidence"])
                for value in payload.values():
                    self.assertIn(value, shown)
                self.assertEqual(policy.judge(tool, payload), (None, facts))  # and asks again

    def test_a_tool_the_default_does_not_know_is_named_and_shows_its_input(self) -> None:
        for tool, payload in self.CALLS[3:]:
            with self.subTest(tool=tool):
                facts = self.ask(self.policy(), tool, payload)
                self.assertIn("use the tool", facts["question"])
                self.assertEqual(facts["evidence"], [{"label": "Input", "text": _pretty(payload)}])

    def test_a_command_and_a_file_change_are_shown_as_what_they_are(self) -> None:
        policy, undo = self.policy(), " It cannot be undone."
        facts = self.ask(policy, "Bash", {"command": "rm -rf build", "cwd": "/srv"})
        self.assertEqual(facts["question"], "Allow CoCo to run a command on this computer?" + undo)
        self.assertEqual(facts["evidence"][0], {"label": "Command", "text": "rm -rf build"})
        self.assertIn("/srv", facts["evidence"][1]["text"])
        facts = self.ask(policy, "Write", {"file_path": "new.md", "content": "# New"})
        self.assertEqual(facts["question"], "Allow CoCo to create a file?" + undo)
        self.assertEqual(facts["changes"], {"file": "new.md", "lines": None, "note": ""})
        self.assertEqual(facts["evidence"], [{"label": "New content", "text": "# New"}])
        self.assertEqual(facts["where"], "work")
        facts = self.write(policy, self.outside)
        self.assertIn("replace a file outside the working folder?", facts["question"])
        self.assertEqual(facts["changes"]["file"], Path(self.outside).as_posix())

    def test_a_call_the_app_cannot_read_is_refused(self) -> None:
        for tool, payload in (("Read", None), ("Bash", "ls"), ("Read", {"file_path": 3})):
            reason, facts = self.policy().judge(tool, payload)
            self.assertTrue(reason)
            self.assertIsNone(facts)

    def test_nothing_of_a_host_is_said(self) -> None:
        policy = self.policy()
        calls = (*self.CALLS, ("Read", {"file_path": self.outside}), ("Grep", {"pattern": "x"}))
        said = [policy.judge(tool, payload)[1] for tool, payload in calls]
        said += [policy.rights(), [policy.describe(tool, payload) for tool, payload in calls]]
        for word in ("Cockpit", "project", "budget", "member", "audit"):
            self.assertNotIn(word, json.dumps(said))

    def test_the_rights_say_the_same_rules(self) -> None:
        rights = self.policy().rights(["x"])
        self.assertEqual(rights["scope"], f"the working folder ({self.folder.as_posix()})")
        self.assertIn("Read, Glob, Grep", rights["without_asking"])
        self.assertIn("Everything else, each time", rights["asked"])
        self.assertIn("in .git or a file that may hold secrets also asks", rights["asked"])
        self.assertNotIn("query", rights["refused"])  # SQL is off: a query is a tool like another
        self.assertEqual(rights["running_without_asking_now"], ["x"])
        self.assertNotIn("commands", rights)


class SwitchTest(FolderCase):
    """Each piece changes something only when it is switched on."""

    def test_commands(self) -> None:
        listed = Command("Count the lines", ["wc", "-l", "notes.md"], "How long the notes are")
        call = {"command": "wc -l notes.md"}
        off, on = self.policy(), self.policy(commands=[listed])
        self.assertEqual(self.ask(off, "Bash", call)["kind"], "change")
        self.assertEqual(off.describe("Bash", call), "Run a command")
        facts = self.ask(on, "Bash", call)
        self.assertEqual((facts["kind"], facts["reads"]), ("read", listed.reads))
        self.assertEqual(facts["question"], "Allow CoCo to count the lines?")
        self.assertEqual(facts["evidence"], [{"label": "Command", "text": "wc -l notes.md"}])
        self.assertEqual(on.describe("Bash", call), "Count the lines")
        self.assertEqual(on.rights()["commands"], [{"name": listed.name, "line": listed.line}])
        for other in ("wc -l notes.md; rm notes.md", "wc  -l notes.md", "WC -l notes.md"):
            self.assertEqual(self.ask(on, "Bash", {"command": other})["kind"], "change")
        self.assertEqual(self.ask(on, "Bash", {**call, "cwd": "/srv"})["kind"], "change")

    def test_a_command_the_shell_would_expand_is_never_listed(self) -> None:
        bad = Command("Look", ["ls", "a$HOME"], "Names")
        policy = self.policy(commands=[bad])
        self.assertEqual(policy.commands(), [])
        self.assertNotIn("commands", policy.rights())

        class Careless(FolderPolicy):
            def commands(self):
                return [bad]

        careless = Careless(self.folder)
        self.assertNotIn("commands", careless.rights())
        self.assertEqual(self.ask(careless, "Bash", {"command": 'ls "a$HOME"'})["kind"], "change")
        self.assertEqual(self.ask(careless, "Bash", {"command": ""})["kind"], "change")

    def test_changes_default_is_the_scope(self) -> None:
        policy = self.policy(standing=True)
        edit = {"file_path": "src/app.py", "old_string": "a", "new_string": "b"}
        near = self.ask(policy, "Edit", edit)
        self.assertEqual(near["changes"], {"file": "src/app.py", "lines": 1, "note": "1 line"})
        self.assertEqual(near["standing"]["id"], "files")
        self.assertEqual(
            near["standing"]["covers"],
            "Any change to any file inside work, except the .git folder and files that may hold "
            "secrets: create, change or replace.",
        )
        far = self.write(policy, self.outside)
        self.assertEqual(far["changes"]["note"], "outside the working folder")
        self.assertIsNone(far["standing"])
        for name in (".git/hooks/pre-commit", ".env", "docs/id_rsa", "notes.md:stream"):
            with self.subTest(name=name):  # asked each time, whatever was said to stop asking
                guarded = self.write(policy, name)
                self.assertEqual(guarded["kind"], "change")
                self.assertIsNone(guarded["standing"])

    def test_changes_as_patterns(self) -> None:
        unusual = "outside what it usually changes"
        for patterns in (["docs/*", "*.md"], ("notes.md", "docs/*.md"), "*.md"):
            policy = self.policy(changes=patterns, standing=True)
            with self.subTest(patterns=patterns):
                for name in ("notes.md", "docs/guide.md", "docs/new.md"):
                    facts = self.write(policy, name)
                    self.assertEqual(facts["changes"]["file"], name)
                    self.assertEqual(facts["standing"]["id"], "files")
                    named = ", ".join([patterns] if isinstance(patterns, str) else patterns)
                    covers = facts["standing"]["covers"]
                    self.assertIn(f"the files inside work that match {named}, except", covers)
                    self.assertNotIn("any file", covers)  # it says no more than it gives
                facts = self.write(policy, "src/app.py")
                self.assertIn(f"replace a file {unusual}? It cannot be undone.", facts["question"])
                self.assertEqual(facts["changes"]["file"], (self.folder / "src/app.py").as_posix())
                self.assertEqual(facts["changes"]["note"], unusual)
                self.assertIsNone(facts["standing"])  # the family covers the ordinary files only
                far = self.write(policy, "../outside.md")
                self.assertIn("outside the working folder", far["question"])
                self.assertIsNone(far["standing"])
        everything = self.policy(changes="*", standing=True)  # a pattern does not open what is kept
        self.assertEqual(self.write(everything, "src/app.py")["standing"]["id"], "files")
        for name in (".env", ".git/config"):
            self.assertIsNone(self.write(everything, name)["standing"])

    def test_changes_as_a_function(self) -> None:
        seen = []

        def rule(path):
            seen.append(path)
            return None if path.suffix == ".md" else "that is not a note"

        policy = self.policy(changes=rule, standing=True)
        edit = {"file_path": "src/app.py", "old_string": "a" + NL + "b", "new_string": "c"}
        facts = self.ask(policy, "Edit", edit)
        self.assertIn("change a file that is not a note? It cannot be undone.", facts["question"])
        self.assertEqual(facts["changes"]["note"], "2 lines, that is not a note")
        self.assertIsNone(facts["standing"])
        self.assertEqual(seen, [self.folder / "src" / "app.py"])  # the resolved path
        offer = self.write(policy, "a.md")["standing"]
        self.assertEqual(offer["id"], "files")
        self.assertIn("to the files this application calls ordinary, except", offer["covers"])
        self.assertEqual(self.write(policy, self.outside)["standing"]["id"], "files")  # its rule
        for name in (".git/notes.md", "secrets/a.md"):  # ordinary for the rule, still asked
            self.assertIsNone(self.write(policy, name)["standing"])
        broken = self.policy(changes=lambda path: 1 / 0)  # a rule that fails: the call does not run
        reason, facts = broken.judge("Write", {"file_path": "a.md", "content": "x"})
        self.assertTrue(reason)
        self.assertIsNone(facts)

    def test_sql(self) -> None:
        off, on = self.policy(), self.policy(sql=True)
        for sql, kind in (("select 1", "read"), ("drop table T", "change")):
            call = {"sql": sql, "connection": "prod"}
            with self.subTest(sql=sql):
                facts = self.ask(off, "sql_execute", call)
                self.assertEqual(facts["kind"], "change")
                self.assertEqual(facts["changes"]["file"], "Tool: sql execute")
                self.assertEqual(off.describe("sql_execute", call), "Use sql execute")
                facts = self.ask(on, "sql_execute", call)
                self.assertEqual(facts["kind"], kind)
                self.assertEqual(facts["evidence"][0], {"label": "Query", "text": sql})  # exact
                self.assertIn("prod", facts["evidence"][1]["text"])  # shown, not refused
                self.assertIn("Snowflake", facts["where"])
        self.assertEqual(
            on.describe("sql_execute", {"sql": "select 1"}), "Run a query on Snowflake"
        )
        self.assertEqual(
            on.describe("sql_execute", {"sql": "drop table T"}), "Run on Snowflake: DROP"
        )
        # a query that is not text: asked whole while SQL is a tool like another, refused once read
        self.assertEqual(self.ask(off, "sql_execute", {"sql": 7})["kind"], "change")
        self.assertEqual(on.judge("sql_execute", {"sql": 7}), ("The query is not text.", None))
        self.assertIn("query", on.rights()["refused"])

    def test_lookups(self) -> None:
        off, on = self.policy(), self.policy(lookups=True)
        for tool in ("web_search", "snowflake_table_lookup", "snowflake_product_docs"):
            with self.subTest(tool=tool):
                self.assertEqual(self.ask(off, tool, {"query": "x"})["kind"], "change")
                self.assertTrue(off.describe(tool, {}).startswith("Use "))
                facts = self.ask(on, tool, {"query": "x"})
                self.assertEqual((facts["kind"], facts["changes"]), ("read", None))
                self.assertTrue(facts["where"] and facts["reads"])
                self.assertFalse(on.describe(tool, {}).startswith("Use "))
        self.assertEqual(self.ask(on, "snowflake_stage_upload", {})["kind"], "change")

    def test_standing(self) -> None:
        offered = (
            ("Bash", {"command": "ls"}, "commands"),
            ("Write", {"file_path": "new.md", "content": "x"}, "files"),
            ("sql_execute", {"sql": "select 1"}, "queries"),
            ("sql_execute", {"sql": "drop table T"}, "statements"),
            ("web_search", {"query": "x"}, "tool:web_search"),
            ("Task", {}, "tool:task"),
            ("Read", {"file_path": self.outside}, "elsewhere"),
        )
        off = self.policy(sql=True, lookups=True)
        on = self.policy(sql=True, lookups=True, standing=True)
        for tool, payload, family in offered:
            with self.subTest(family=family):
                self.assertIsNone(self.ask(off, tool, payload)["standing"])
                offer = self.ask(on, tool, payload)["standing"]
                self.assertEqual(offer["id"], family)
                self.assertEqual(set(offer), {"id", "label", "covers", "until"})
        elsewhere = self.ask(on, "Read", {"file_path": self.outside})["standing"]
        self.assertTrue(elsewhere["label"].endswith("for reading outside the working folder"))
        self.assertIn("outside the working folder, except the .git folder", elsewhere["covers"])
        for name in (".env", ".git/config"):  # never a family
            self.assertIsNone(self.ask(on, "Read", {"file_path": self.path(name)})["standing"])
        # with SQL off a statement is a tool like another: its family is that tool
        alone = self.ask(self.policy(standing=True), "sql_execute", {"sql": "select 1"})
        self.assertEqual(alone["standing"]["id"], "tool:sql_execute")

    def test_scope(self) -> None:
        docs = self.folder / "docs"
        policy = FolderPolicy(self.folder, scope=docs, standing=True)
        self.assertEqual(policy.judge("Read", {"file_path": "docs/guide.md"}), (None, None))
        facts = self.ask(policy, "Read", {"file_path": "notes.md"})  # in the folder, not the scope
        self.assertEqual(facts["question"], "Allow CoCo to read a file outside the folder docs?")
        self.assertEqual(facts["where"], "docs")
        searched = self.ask(policy, "Grep", {"pattern": "x"})  # no path: the working folder
        self.assertIn("outside the folder docs", searched["question"])
        written = self.write(policy, "docs/new.md")
        self.assertEqual(written["changes"]["file"], "new.md")
        self.assertIn("docs", written["standing"]["covers"])
        self.assertIn("outside the folder docs", self.write(policy, "notes.md")["question"])
        self.assertEqual(policy.rights()["scope"], f"the folder docs ({docs.as_posix()})")
        self.assertEqual(policy.describe("Read", {"file_path": "notes.md"}), "Read notes.md")


class AlsoReadTest(FolderCase):
    """`also_read`: folders read freely besides the scope. It widens reading, and only reading."""

    def setUp(self) -> None:
        super().setUp()
        self.types = self.tmp / "types"
        for name in ("guide.md", "rules/naming.md", "keys/server.pem", ".env", ".git/config"):
            path = self.types / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Guide\n", encoding="utf-8")
        self.also = self.policy(also_read=[self.types], standing=True)

    def at(self, relative: str) -> str:
        return str(self.types / relative)

    def test_reading_there_is_free_as_inside_the_scope(self) -> None:
        read = {"name": "Read", "input": {"file_path": self.at("guide.md")}}
        for tool, payload in (
            ("Read", {"file_path": self.at("guide.md")}),
            ("Read", {"file_path": "../types/rules/naming.md"}),  # relative to the working folder
            ("Glob", {"pattern": "**/*.md", "path": self.at("rules")}),
            ("Glob", {"pattern": "*.md", "path": str(self.types)}),
            ("Grep", {"pattern": "Guide", "path": self.at("rules")}),
            ("direct_tool_calling", {"tool_calls": [read, read]}),
        ):
            with self.subTest(tool=tool, payload=payload):
                self.assertEqual(self.also.judge(tool, payload), (None, None))
                asked = self.ask(self.policy(standing=True), tool, payload)  # off: it asks
                if tool != "direct_tool_calling":
                    self.assertEqual(asked["standing"]["id"], "elsewhere")
        self.assertEqual(self.also.judge("Read", {"file_path": "notes.md"}), (None, None))

    def test_the_folders_may_be_given_in_any_form(self) -> None:
        call = {"file_path": self.at("guide.md")}
        for given in (self.types, str(self.types), "../types", [Path("../types")], (self.types,)):
            with self.subTest(given=given):
                self.assertEqual(self.policy(also_read=given).judge("Read", call), (None, None))
        self.assertEqual(self.policy().also, [])

    def test_what_a_read_asks_for_in_the_scope_asks_there_too(self) -> None:
        for relative, what in (
            (".env", "a file that may hold secrets"),
            ("keys/server.pem", "a file that may hold secrets"),
            (".git/config", "a file of the .git folder"),
            ("guide.md:stream", "a path the app cannot tell is inside the working folder"),
            ("guide.md.", "a path the app cannot tell is inside the working folder"),
        ):
            with self.subTest(relative=relative):
                facts = self.ask(self.also, "Read", {"file_path": self.at(relative)})
                self.assertEqual(facts["question"], f"Allow CoCo to read {what}?")
                self.assertIsNone(facts["standing"])
        # a search that would cover a secret-named file, or that names one
        searched = self.ask(self.also, "Grep", {"pattern": "x", "path": str(self.types)})
        self.assertIn("a folder with files that may hold secrets", searched["question"])
        named = self.ask(self.also, "Glob", {"pattern": "*.pem", "path": self.at("rules")})
        self.assertIn("secrets", named["question"])
        left = self.ask(self.also, "Glob", {"pattern": "../*", "path": self.at("rules")})
        self.assertIn("cannot tell", left["question"])

    def test_flag_applies_there_with_the_names_from_that_folder(self) -> None:
        seen = []

        class Named(FolderPolicy):
            def flag(self, parts):
                seen.append(parts)
                return ("named", "a naming rule") if parts[-1] == "naming.md" else None

        policy = Named(self.folder, also_read=[self.types])
        facts = self.ask(policy, "Read", {"file_path": self.at("rules/naming.md")})
        self.assertEqual(facts["question"], "Allow CoCo to read a naming rule?")
        self.assertEqual(seen, [("rules", "naming.md")])
        searched = self.ask(policy, "Glob", {"pattern": "*", "path": self.at("rules")})
        self.assertIn("a naming rule", searched["question"])
        self.assertEqual(policy.judge("Read", {"file_path": self.at("guide.md")}), (None, None))

    def test_a_path_that_leaves_the_folder_is_not_free(self) -> None:
        for raw in (
            self.at("../outside.md"),
            self.at("rules/../../outside.md"),
            "../types/../x.md",
        ):
            with self.subTest(raw=raw):
                facts = self.ask(self.also, "Read", {"file_path": raw})
                self.assertEqual(
                    facts["question"], "Allow CoCo to read a file outside the working folder?"
                )
                self.assertEqual(facts["standing"]["id"], "elsewhere")
        beside = self.ask(self.also, "Read", {"file_path": str(self.tmp / "types2" / "a.md")})
        self.assertIn("outside", beside["question"])  # a name that starts the same is not inside
        above = self.ask(self.also, "Grep", {"pattern": "x", "path": str(self.tmp)})
        self.assertIn("outside", above["question"])  # nor the folder that holds it

    def test_a_link_out_of_the_folder_is_followed(self) -> None:
        away = self.tmp / "away"
        away.mkdir()
        (away / "private.md").write_text("x", encoding="utf-8")
        link = self.types / "elsewhere"
        if os.name == "nt":  # a junction needs no special right
            done = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(away)], capture_output=True
            )
            made = done.returncode == 0
        else:
            link.symlink_to(away)
            made = True
        if not made:
            self.skipTest("no link right on this machine")
        facts = self.ask(self.also, "Read", {"file_path": str(link / "private.md")})
        self.assertIn("outside the working folder", facts["question"])
        searched = self.ask(self.also, "Grep", {"pattern": "x", "path": str(link)})
        self.assertIn("outside the working folder", searched["question"])

    def test_a_change_there_is_a_change_outside_the_scope(self) -> None:
        edit = {"file_path": self.at("guide.md"), "old_string": "a", "new_string": "b"}
        for tool, payload in (
            ("Write", {"file_path": self.at("new.md"), "content": "x"}),
            ("Write", {"file_path": self.at("guide.md"), "content": "x"}),
            ("Edit", edit),
        ):
            with self.subTest(tool=tool, payload=payload):
                facts = self.ask(self.also, tool, payload)
                self.assertEqual(facts["kind"], "change")
                self.assertIn("a file outside the working folder?", facts["question"])
                self.assertEqual(facts["changes"]["file"], Path(payload["file_path"]).as_posix())
                self.assertIn("outside the working folder", facts["changes"]["note"])
                self.assertIsNone(facts["standing"])  # never left to "File changes"
                self.assertEqual(facts, self.ask(self.policy(standing=True), tool, payload))
        inside_it = self.ask(self.also, "Write", {"file_path": "new.md", "content": "x"})
        self.assertEqual(inside_it["standing"]["id"], "files")
        self.assertNotIn("types", inside_it["standing"]["covers"])

    def test_the_rights_name_them(self) -> None:
        named = self.also.rights()["also_read_without_asking"]
        self.assertEqual(named["folders"], [self.types.as_posix()])
        self.assertIn("Edit and Write there are asked", named["how"])
        self.assertNotIn("also_read_without_asking", self.policy().rights())
        rest = {k: v for k, v in self.also.rights().items() if k != "also_read_without_asking"}
        self.assertEqual(rest, self.policy().rights())


class SearchOrderTest(FolderCase):
    """A search names the first place it would cover that a read asks for. That place goes by
    name, not by the order the filesystem lists a folder (it differs between macOS and Linux)."""

    def test_the_place_a_search_names_does_not_depend_on_the_listing_order(self) -> None:
        class Flags(FolderPolicy):
            def flag(self, parts):
                kinds = {"draft.md": ("draft", "a draft"), "memo.md": ("memo", "a memo")}
                return kinds.get(parts[-1])

        for name in ("docs/aaa/draft.md", "docs/zzz/memo.md"):
            path = self.folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x", encoding="utf-8")
        real_walk = os.walk

        def listed_backwards(top):
            for root, dirs, files in real_walk(top):
                dirs.reverse()
                files.reverse()
                yield root, dirs, files

        policy = Flags(self.folder)
        for tool in ("Grep", "Glob"):
            with self.subTest(tool=tool):
                call = {"pattern": "x", "path": "docs"}
                forward = self.ask(policy, tool, call)["question"]
                with mock.patch("os.walk", listed_backwards):
                    backward = self.ask(policy, tool, call)["question"]
                self.assertEqual(forward, backward)
                self.assertIn("a draft", forward)  # aaa/ comes before zzz/ in name order
                self.assertNotIn("a memo", forward)


class ExtensionTest(FolderCase):
    """The two documented extension points, and the words."""

    def test_flag_is_one_more_reason_a_place_is_not_read_freely(self) -> None:
        class Drafts(FolderPolicy):
            def flag(self, parts):
                return ("draft", "a draft") if parts[-1].startswith("draft") else None

        for name in ("docs/draft.md", "../draft.md", "docs/draft.pem"):
            (self.folder / name).write_text("x", encoding="utf-8")
        policy = Drafts(self.folder, standing=True)
        facts = self.ask(policy, "Read", {"file_path": "docs/draft.md"})
        self.assertEqual(facts["question"], "Allow CoCo to read a draft?")
        self.assertEqual(facts["reads"], "A draft")
        self.assertIsNone(facts["standing"])
        for tool in ("Grep", "Glob"):  # a search that would cover one asks too
            searched = self.ask(policy, tool, {"pattern": "x", "path": "docs"})
            self.assertIn("a draft", searched["question"])
            self.assertEqual(policy.judge(tool, {"pattern": "x", "path": "src"}), (None, None))
        self.assertEqual(policy.judge("Read", {"file_path": "notes.md"}), (None, None))
        self.assertEqual(self.write(policy, "docs/new.md")["standing"]["id"], "files")
        self.assertIsNone(self.write(policy, "docs/draft.md")["standing"])  # nor changed unseen
        # outside the scope the place is outside, whatever the host calls it
        far = self.ask(policy, "Read", {"file_path": "../draft.md"})
        self.assertEqual(far["standing"]["id"], "elsewhere")
        # the package's own reasons come first
        self.assertIn(
            "secrets", self.ask(policy, "Read", {"file_path": "docs/draft.pem"})["question"]
        )

    def test_flag_may_give_a_search_its_own_words_and_cannot_pass_for_outside(self) -> None:
        class Private(FolderPolicy):
            def flag(self, parts):
                return "outside", ("a private file", "a folder with private files")

        policy = Private(self.folder, standing=True)
        read = self.ask(policy, "Read", {"file_path": "notes.md"})
        self.assertIn("read a private file?", read["question"])
        facts = self.ask(policy, "Grep", {"pattern": "x", "path": "docs"})
        self.assertIn("search a folder with private files?", facts["question"])
        self.assertIsNone(read["standing"])  # the key is the host's own: never "Reading elsewhere"
        self.assertIsNone(facts["standing"])

    def test_words_are_replaced_in_one_place(self) -> None:
        class Hosted(FolderPolicy):
            words = {**FolderPolicy.words, "undo": " The host cannot undo it.", "scope": "the case"}

        policy = Hosted(self.folder, standing=True)
        for tool, payload in (("Task", {}), ("Bash", {"command": "ls"})):
            question = self.ask(policy, tool, payload)["question"]
            self.assertTrue(question.endswith("? The host cannot undo it."))
        facts = self.ask(policy, "Read", {"file_path": self.outside})
        self.assertEqual(facts["question"], "Allow CoCo to read a file outside the case?")
        self.assertIn("outside the case", facts["standing"]["label"])
        self.assertIn("a file outside the case?", self.write(policy, self.outside)["question"])
        self.assertTrue(policy.rights()["scope"].startswith("the case ("))
        self.assertEqual(FolderPolicy.words["undo"], " It cannot be undone.")
        self.assertIs(self.policy().words, FolderPolicy.words)

    def test_the_attached_files_and_the_long_outputs_are_free_only_when_named(self) -> None:
        policy = self.policy()
        call = {"file_path": self.outside}
        self.assertIsNotNone(policy.judge("Read", call)[1])
        policy.uploads = self.tmp
        self.assertEqual(policy.judge("Read", call), (None, None))
        policy.uploads, policy.spill = None, self.tmp
        self.assertEqual(policy.judge("Read", call), (None, None))
        self.assertEqual(self.ask(policy, "Write", {**call, "content": "x"})["kind"], "change")


class HelpersTest(FolderCase):
    def test_inside(self) -> None:
        base = scope = self.folder
        for raw in ("notes.md", "docs/../notes.md", self.path("docs/guide.md"), "new/x.md", "."):
            with self.subTest(raw=raw):
                self.assertIsNone(inside(base, scope, raw))
        for raw in ("../outside.md", self.outside, "docs/../../outside.md", "//server/share/x.md"):
            with self.subTest(raw=raw):
                self.assertEqual(inside(base, scope, raw), "outside")
        streams = ("notes.md:stream", "notes.md::$DATA", "C:notes.md", "notes.md.", "docs /a.md")
        for raw in (*streams, "x" + chr(0) + "y", 3, None):
            with self.subTest(raw=raw):
                self.assertEqual(inside(base, scope, raw), "odd")
        for raw in ("NUL", "docs/con", "aux.md"):  # Windows opens a device, whatever the folder
            with self.subTest(raw=raw):
                self.assertTrue(inside(base, scope, raw))
        self.assertEqual(inside(base, self.folder / "docs", "notes.md"), "outside")
        self.assertIsNone(inside(base, self.folder / "docs", "docs/guide.md"))

    def test_is_secret_name(self) -> None:
        secret = (
            ".env",
            ".env.local",
            "prod.pem",
            "key.p8",
            "server.KEY",
            "cert.pfx",
            "id_rsa.pub",
        )
        for name in (*secret, "connections.toml", "my_credentials.md", "Secrets"):
            self.assertTrue(is_secret_name(name), name)
        for name in ("notes.md", "environment.md", "keys.md", "pem.md", "connections.md"):
            self.assertFalse(is_secret_name(name), name)

    def test_a_command_line_is_written_for_the_shell_it_runs_in(self) -> None:
        def line(*argv, platform="linux"):
            return Command("n", argv, "r", platform).line

        back = "a" + chr(92) + "b"
        self.assertEqual(
            line("git", "-c", "core.x=false", "log", "-10"), "git -c core.x=false log -10"
        )
        self.assertEqual(line("git", "-C", "C:/My projects/a"), 'git -C "C:/My projects/a"')
        self.assertEqual(line("ls", ""), 'ls ""')
        self.assertEqual(line("/usr/bin/python3", "-I", "x.py"), '"/usr/bin/python3" -I x.py')
        self.assertEqual(line("C:/Py/p.exe", "-I", platform="win32"), '& "C:/Py/p.exe" -I')
        self.assertEqual(line("ls", back, platform="win32"), f'ls "{back}"')  # PowerShell keeps it
        for bad in ("a$b", "a" + chr(96) + "b", 'a"b', back):
            self.assertIsNone(line("ls", bad), bad)
        self.assertIsNone(line())
        self.assertEqual(Command("n", ["ls", Path("a")], "r").argv, ("ls", "a"))

    def test_git_readonly(self) -> None:
        self.assertEqual(git_readonly(self.folder / "docs"), [])  # git would climb to the parent's
        listed = git_readonly(self.folder)
        self.assertEqual([c.argv[9] for c in listed], ["status", "diff", "log"])
        hardened = ("git", "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false")
        hardened += ("-c", "log.showSignature=false", "-C", self.folder.as_posix())
        for command in listed:
            self.assertEqual(command.argv[:9], hardened)
            self.assertTrue(command.name and command.reads and command.line)
            self.assertNotIn("project", command.name)
        policy = self.policy(commands=listed)
        self.assertEqual(self.ask(policy, "Bash", {"command": listed[0].line})["kind"], "read")

    def test_request_cannot_be_misspelt(self) -> None:
        offer = {"id": "mine", "label": "Do not ask again", "covers": "Mine.", "until": "The end"}
        read = request("read", "?", where="x", reads="A", evidence=[("Path", "a")], standing=offer)
        change = request("change", "?", where="x", changes="A thing")
        keys = {"kind", "question", "where", "reads", "changes", "pill", "evidence_label"}
        keys |= {"evidence", "standing"}
        self.assertEqual((set(read), set(change)), (keys, keys))
        self.assertEqual(read["evidence"], [{"label": "Path", "text": "a"}])
        self.assertEqual((read["pill"], change["pill"]), ("Allow a read?", "Allow a change?"))
        self.assertEqual(change["changes"], {"file": "A thing", "lines": None, "note": ""})
        counted = request("change", "?", where="x", changes={"file": "f", "lines": 2})
        self.assertEqual(counted["changes"], {"file": "f", "lines": 2, "note": ""})
        for bad in (
            lambda: request("write", "?", where="x", changes="f"),
            lambda: request("change", "?", where="x"),
            lambda: request("read", "?", where="x", changes="f"),
            lambda: request("change", "?", where="x", changes={"path": "f"}),
            lambda: request("read", "?", where="x", standing={"id": "mine"}),
        ):
            self.assertRaises(ValueError, bad)

    def test_every_request_of_the_ready_made_policy_has_the_same_parts(self) -> None:
        listed = git_readonly(self.folder)
        policy = self.policy(sql=True, lookups=True, standing=True, commands=listed)
        more = (("Read", {"file_path": self.outside}), ("Bash", {"command": listed[0].line}))
        keys = set(request("read", "?", where="x"))
        for tool, payload in (*self.CALLS, *more):
            self.assertEqual(set(self.ask(policy, tool, payload)), keys, tool)

    def test_the_names_the_policy_knows_are_those_of_the_cortex_tools(self) -> None:
        known = {"Read", "Glob", "Grep", "direct_tool_calling", "Edit", "Write", "Bash"}
        self.assertLessEqual(known, set(TOOLS))
        for name in known:
            self.assertFalse(self.policy().describe(name, {}).startswith("Use "), name)

    def test_the_rights_layer_is_pure_python(self) -> None:
        allowed = {"__future__", "dataclasses", "fnmatch", "json", "os", "pathlib", "re", "sys"}
        allowed |= {"threading", "typing", "uuid"}
        for module in (streamlit_coco.policy, streamlit_coco.gate):
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = {alias.name.split(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    names = {(node.module or "").split(".")[0]}
                else:
                    continue
                self.assertLessEqual(names, allowed, module.__name__)


class WordsTableTest(FolderCase):
    """Every sentence the ready-made policy can put on screen comes from one table, WORDS."""

    def setUp(self) -> None:
        super().setUp()
        (self.folder / "docs" / "server.key").write_text("x", encoding="utf-8")
        (self.tmp / "more").mkdir()
        (self.tmp / "more" / "rules.md").write_text("x", encoding="utf-8")
        # every word replaced by a marker that keeps its slots: «key»[slot][slot]
        self.marked = {}
        for key, text in WORDS.items():
            slots = [name for _, name, _, _ in string.Formatter().parse(text) if name]
            self.marked[key] = f"«{key}»" + "".join("[{" + slot + "}]" for slot in slots)

    def unmarked(self, text) -> str:
        """What is left of a sentence once the markers and what fills their slots are taken out:
        punctuation only, when the policy wrote nothing of its own."""
        self.assertIsInstance(text, str)
        rest, before = text, None
        while rest != before:
            before, rest = rest, re.sub(r"\[[^\[\]]*\]", "", rest)
        return re.sub("«[a-z_]+»", "", rest)

    def no_english(self, text, about) -> None:
        self.assertNotRegex(self.unmarked(text), "[A-Za-z]", f"{about}: {text!r}")

    def said(self, policy, tool, payload) -> list:
        """Everything the policy says of one call; each sentence it wrote is checked."""
        about = f"{tool} {payload}"
        reason, facts = policy.judge(tool, payload)
        step = policy.describe(tool, payload)
        self.no_english(step, about)
        if reason is not None:
            self.no_english(reason, about)
        if facts:
            for part in ("question", "pill", "evidence_label"):
                self.no_english(facts[part], about)
            self.assertTrue(facts["where"] == policy.where or facts["where"].startswith("«"))
            if facts["reads"] is not None:
                self.no_english(facts["reads"], about)
            if facts["changes"]:
                self.no_english(facts["changes"]["note"], about)
                if str(tool).lower() not in ("edit", "write"):  # else it is the file's path
                    self.no_english(facts["changes"]["file"], about)
            for evidence in facts["evidence"]:
                self.no_english(evidence["label"], about)
            for part in (facts["standing"] or {}).values():
                if str(part).split(":")[0] not in FAMILIES:  # not its id
                    self.no_english(part, about)
        return [reason, facts, step]

    def test_a_policy_given_every_word_says_no_sentence_of_its_own(self) -> None:
        words, docs = self.marked, self.folder / "docs"
        full = self.policy(
            words=words,
            sql=True,
            lookups=True,
            standing=True,
            commands=git_readonly(self.folder, words),
            also_read=[self.tmp / "more"],
        )

        def rule(path):
            if path.suffix != ".md":
                raise RuntimeError("a rule that fails")

        narrow = FolderPolicy(self.folder, scope=docs, changes=["*.md"], standing=True, words=words)
        ruled = self.policy(words=words, changes=rule, standing=True)
        bare = self.policy(words=words)  # every switch off
        edit = {"old_string": "a" + NL + "b", "new_string": "c"}
        read = {"name": "Read", "input": {"file_path": self.path("notes.md")}}
        calls = [
            # reads and searches: free, and each reason to ask, for a file and for a folder
            ("Read", {"file_path": self.path("notes.md")}),
            ("Read", {"file_path": self.outside}),
            ("Read", {"file_path": self.path(".env")}),
            ("Read", {"file_path": self.path(".git/config")}),
            ("Read", {"file_path": self.path("notes.md:stream")}),
            ("Read", {"file_path": 3}),
            ("Read", {"file_path": self.outside, "mode": "raw"}),
            ("Glob", {"pattern": "*.md", "path": str(self.tmp)}),
            ("Glob", {"pattern": "*", "path": self.path(".git")}),
            ("Glob", {}),
            ("Grep", {"pattern": "x", "path": self.path("docs")}),
            ("Grep", {"pattern": "x", "path": str(self.tmp), "include": "*.md"}),
            ("direct_tool_calling", {"tool_calls": [read, read]}),
            ("direct_tool_calling", {"tool_calls": []}),
            # commands: listed, unlisted, of several lines, with another input
            ("Bash", {"command": full.commands()[0].line}),
            ("Bash", {"command": full.commands()[1].line}),
            ("Bash", {"command": full.commands()[2].line}),
            ("Bash", {"command": "rm -rf build"}),
            ("Bash", {"command": "a" + NL + "b", "cwd": "/srv"}),
            # file changes: ordinary, of one line and of several, outside, guarded
            ("Write", {"file_path": "new.md", "content": "x"}),
            ("Write", {"file_path": "notes.md", "content": "x"}),
            ("Edit", {"file_path": "notes.md", "old_string": "a", "new_string": "b"}),
            ("Edit", {"file_path": "docs/guide.md", **edit}),
            ("Write", {"file_path": self.outside, "content": "x"}),
            ("Write", {"file_path": ".git/hooks/pre-commit", "content": "x"}),
            ("Write", {"file_path": "src/app.py", "content": "x"}),
            ("Write", {"file_path": "docs/data.csv", "content": "x"}),
            # SQL: a query, a statement, several, one without a first word, none, not text
            ("sql_execute", {"sql": "select 1"}),
            ("sql_execute", {"sql": "drop table T", "connection": "prod"}),
            ("sql_execute", {"sql": "create table T (a int); 123; drop table T"}),
            ("sql_execute", {"sql": ""}),
            ("sql_execute", {"sql": 7}),
            # each look-up, a tool nobody knows, a tool without a name, an input that is no object
            *((name, {"query": "x"}) for name in LOOKUPS),
            ("Task", {"prompt": "go"}),
            ("", {"a": 1}),
            ("Task", "go"),
        ]
        said = []
        for policy in (full, narrow, ruled, bare):
            for tool, payload in calls:
                with self.subTest(scope=policy.where, tool=tool, payload=payload):
                    said.append(self.said(policy, tool, payload))
            rights = policy.rights([])
            for part in ("scope", "without_asking", "asked", "refused"):
                self.no_english(rights[part], part)
            for command in rights.get("commands", ()):
                self.no_english(command["name"], "a command")
            said.append(rights)
        self.no_english(full.rights()["also_read_without_asking"]["how"], "also read")
        offers = [f[1]["standing"] for f in said if isinstance(f, list) and f[1]]
        families = {offer["id"] for offer in offers if offer}
        self.assertLessEqual(set(FAMILIES), {family.split(":")[0] for family in families})
        # a folder too large to check
        saved, streamlit_coco.policy._WALK_LIMIT = streamlit_coco.policy._WALK_LIMIT, 0
        try:
            said.append(self.said(full, "Grep", {"pattern": "x", "path": self.path("src")}))
        finally:
            streamlit_coco.policy._WALK_LIMIT = saved
        # and no word of the table is left unused: each one showed in what was said
        shown = set(re.findall("«([a-z_]+)»", json.dumps(said, ensure_ascii=False, default=str)))
        self.assertEqual(set(WORDS) - shown, {"pill_change"})  # only `request()` without a pill
        self.assertEqual(
            request("change", "?", where="x", changes="y")["pill"], WORDS["pill_change"]
        )

    def test_the_words_are_given_once_and_merged_over_the_defaults(self) -> None:
        french = {"undo": " Sans retour possible.", "ask_create": "Créer un fichier{far} ?{undo}"}
        policy = self.policy(words=french)
        created = self.write(policy, "new.md")
        self.assertEqual(created["question"], "Créer un fichier ? Sans retour possible.")
        self.assertEqual(created["pill"], "Allow a file change?")  # a word not given: the default
        self.assertTrue(
            self.write(policy, "notes.md")["question"].endswith("? Sans retour possible.")
        )
        self.assertIs(FolderPolicy.words, WORDS)
        self.assertEqual(WORDS["undo"], " It cannot be undone.")

        class Hosted(FolderPolicy):
            words = {**FolderPolicy.words, "scope": "the case", "undo": " No way back."}

        both = Hosted(self.folder, words={"undo": " Sans retour possible."})  # over the class too
        self.assertTrue(self.write(both, "new.md")["question"].endswith(" Sans retour possible."))
        far = self.ask(both, "Read", {"file_path": self.outside})
        self.assertEqual(far["question"], "Allow CoCo to read a file outside the case?")
        named = {"scope_given": "le dossier {name}", "outside_file": "un fichier hors de {scope}"}
        scoped = FolderPolicy(self.folder, scope=self.folder / "docs", words=named)
        far = self.ask(scoped, "Read", {"file_path": "notes.md"})
        self.assertEqual(far["question"], "Allow CoCo to read un fichier hors de le dossier docs?")
        self.assertEqual(far["reads"], "Un fichier hors de le dossier docs")

    def test_git_readonly_takes_the_words_too(self) -> None:
        listed = git_readonly(self.folder, {"git_status": "Voir ce qui a changé", "git_log": 3})
        self.assertEqual(listed[0].name, "Voir ce qui a changé")
        self.assertEqual(listed[0].reads, WORDS["git_status_reads"])
        self.assertEqual(listed[2].name, WORDS["git_log"])  # not text: the default
        self.assertEqual([c.line for c in listed], [c.line for c in git_readonly(self.folder)])

    def test_a_word_that_cannot_be_filled_never_stops_a_call(self) -> None:
        broken = {
            "ask_read": "Lire {quoi} ?",  # a slot that does not exist
            "ask_command": "Commande {",  # a stray brace
            "ask_tool": "Outil {tool.nom}",  # a slot that has no such part
            "outside_file": "{0}",  # a slot without a name
            "pill_command": 3,  # not text
            "tick": None,
            "undo": ["x"],
            "step_read": "{chemin}",
            "rights_scope": "{scope} ({dossier})",
            "refused_type": "{cle}",
        }
        calls = (*self.CALLS, ("Read", {"file_path": self.outside}), ("Read", {"file_path": 3}))

        class Empty(FolderPolicy):
            words = {}  # a table that forgot every key

        class NotATable(FolderPolicy):
            words = None

        default = self.policy(sql=True, lookups=True, standing=True)
        for words, kind in ((broken, FolderPolicy), (None, Empty), (None, NotATable)):
            policy = kind(self.folder, sql=True, lookups=True, standing=True, words=words)
            for tool, payload in calls:
                with self.subTest(kind=kind.__name__, tool=tool, payload=payload):
                    self.assertEqual(policy.judge(tool, payload), default.judge(tool, payload))
                    self.assertEqual(
                        policy.describe(tool, payload), default.describe(tool, payload)
                    )
            self.assertEqual(policy.rights(["x"]), default.rights(["x"]))


if __name__ == "__main__":
    unittest.main()
