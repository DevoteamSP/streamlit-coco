"""Ask CoCo: what the agent may do without asking, and what a request shows.

Pure Python: no Streamlit, no SDK. A policy answers three questions about one tool call (`Policy`);
`FolderPolicy` is the ready-made one, built around the agent's working folder.

Nothing is refused for what it is. A reading tool (Read, Glob, Grep, a batch of them) inside the
scope is free; every other call asks, each time, unless a standing permission covers it (gate.py).
A read that asks says what is unusual ("outside the working folder", "a file that may hold
secrets") and shows the exact path. Only a call the app cannot interpret is refused: an input that
is not an object, a path that is not text, a path the system cannot resolve.

Paths are read as text before the system can normalise them, then resolved the way Cortex Code
resolves them (relative to the working folder, links followed): a spelling the app cannot place (a
stream, a drive-relative path, a trailing dot, a device name) never counts as inside. A search that
would cover a file a direct read asks for asks too.

The default is the safest, not the richest: `FolderPolicy(folder)` offers no standing permission
and shows every call it does not know as a change, with its whole input. `commands`, `changes`,
`sql`, `lookups` and `standing` each change something only when switched on.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Protocol

_READ = {"read", "glob", "grep"}
_BATCH = "direct_tool_calling"
# What each reading tool of Cortex Code 1.1.104 reads from its input. A key outside this list means
# the call is not a plain read: it asks, and the whole input is shown. The options the model sends
# out of habit for Grep are read by nobody.
_KEYS = {
    "read": {"file_path", "offset", "limit"},
    "glob": {"pattern", "path"},
    "grep": {
        *("pattern", "path", "include", "head_limit", "-n", "-i", "-A", "-B", "-C", "context"),
        *("output_mode", "multiline", "type", "glob", "offset"),
    },
}
_TEXT = ("file_path", "path", "pattern", "include")
_SQL = "sql_execute"  # the name hooks are given (the program's permission name is "sql")
_BASH_KEYS = {"command", "description", "timeout_ms"}
_SQL_READS = {"select", "with", "show", "describe", "desc", "explain"}  # first word of a read
_SQL_WRITES = re.compile(
    r"\b(insert|update|delete|merge|create|alter|drop|truncate|grant|revoke|copy|put|remove|call|"
    r"use|set|unset|undrop|execute|into|begin|commit|rollback)\b|system\$"
)
_SECRET = re.compile(
    r"^\.env|\.(pem|p8|key|pfx)$|^id_rsa|^connections\.toml$|credential|secret", re.I
)
# In a pattern: no wildcard reasoning, the name anywhere.
_NAMES_SECRET = re.compile(
    r"\.env|\.(pem|p8|key|pfx)|id_rsa|connections\.toml|credential|secret", re.I
)
# With every name that starts with a dot, what Cortex Code's Grep skips.
_NOT_SEARCHED = {"node_modules", "__pycache__", "dist", "build"}
_WALK_LIMIT = 20_000  # files looked at before a folder counts as too large to check
_DRIVE = re.compile(r"^[A-Za-z]:[/\\]")
_ROOTED = re.compile(r"[A-Za-z]:|[/\\]")
_DEVICE = re.compile(r"^(con|prn|aux|nul|com\d|lpt\d)(\..*)?$", re.I)
_PLAIN = re.compile(r"[A-Za-z0-9_.=-]+")  # an argument typed as it is; any other goes in quotes
_UNTIL = "Until this conversation ends, or you take it back in the menu"
_SNOW = "Snowflake, with your account and your rights"
# What a read that asks is, for a read and for a search: the unusual thing the request says.
_WHY = {
    "outside": ("a file outside {scope}", "a folder outside {scope}"),
    "odd": ("a path the app cannot tell is inside {scope}",) * 2,
    "git": ("a file of the .git folder", "the .git folder"),
    "secret": ("a file that may hold secrets", "a folder with files that may hold secrets"),
}
# The look-up tools of Cortex Code and the web: reads, and where the question goes.
# (action, where, reads)
_LOOKUPS = {
    "snowflake_object_search": (
        "search Snowflake objects",
        _SNOW,
        "Names of objects in your Snowflake account",
    ),
    "snowflake_table_lookup": (
        "look up a table on Snowflake",
        _SNOW,
        "The description of a table in your Snowflake account",
    ),
    "semantic_view_search": (
        "search semantic views on Snowflake",
        _SNOW,
        "Semantic views in your Snowflake account",
    ),
    "cortex_agent_search": (
        "search Cortex agents on Snowflake",
        _SNOW,
        "Cortex agents in your Snowflake account",
    ),
    "snowflake_product_docs": (
        "look in Snowflake's documentation",
        "Snowflake's documentation service: your question leaves this computer",
        "Pages of Snowflake's documentation",
    ),
    "snowflake_connections_list": (
        "list your Snowflake connections",
        "Your Snowflake connections file; the list goes to Cortex Code",
        "The names of your Snowflake connections",
    ),
    "web_search": (
        "search the web",
        "The web: your search words leave this computer",
        "Search results from the web",
    ),
    "web_fetch": (
        "fetch a web page",
        "The web: the address below is called from this computer",
        "A page from the web",
    ),
}


class Policy(Protocol):
    """What the window and the gate ask of a policy. `FolderPolicy` is one; a host may write one."""

    def judge(self, tool: str, payload) -> tuple[str | None, dict | None]:
        """(why the call is refused, the request to show). Both None: free. Never raises."""

    def describe(self, tool: str, payload) -> str:
        """The step's name, in plain words."""

    def rights(self, granted=()) -> dict:
        """What the agent is told it may do, generated from the same rules."""


def request(
    kind: str,
    question: str,
    *,
    where: str,
    reads: str | None = None,
    changes=None,
    evidence=(),
    evidence_label: str = "Show input",
    pill: str | None = None,
    standing: dict | None = None,
) -> dict:
    """One request to show, written from the checked call and never from the agent's description.

    kind            "read" or "change"
    question        the sentence the user answers
    where           what the request is about (a folder's name, "Snowflake, with your account ...")
    reads           a read: what it reads
    changes         a change: what it changes, as a few words or {"file", "lines", "note"}
    evidence        (label, exact text) pairs, one click away under `evidence_label`
    pill            the few words the closed launcher shows
    standing        the standing permission offered: {"id", "label", "covers", "until"}, or None
    """
    if kind not in ("read", "change"):
        raise ValueError(f"A request is a read or a change, not {kind!r}.")
    if isinstance(changes, str):
        changes = {"file": changes}
    if changes is not None:
        changes = {"lines": None, "note": "", **changes}
        if set(changes) != {"file", "lines", "note"}:
            raise ValueError("What changes is a few words, or file, lines and note.")
    if (kind == "read") != (changes is None):
        raise ValueError("A change says what it changes; a read changes nothing.")
    if standing is not None and set(standing) != {"id", "label", "covers", "until"}:
        raise ValueError("A standing permission has an id, a label, what it covers and until when.")
    return {
        "kind": kind,
        "question": question,
        "where": where,
        "reads": reads,
        "changes": changes,
        "pill": pill or ("Allow a read?" if kind == "read" else "Allow a change?"),
        "evidence_label": evidence_label,
        "evidence": [{"label": label, "text": text} for label, text in evidence],
        "standing": standing,
    }


def is_secret_name(name: str) -> bool:
    """A file or folder name that may hold secrets: .env*, *.pem, *.p8, *.key, *.pfx, id_rsa*,
    connections.toml, and any name holding "credential" or "secret"."""
    return bool(_SECRET.search(name))


def _spelling(raw: str) -> bool:
    """A spelling the system maps to another file: a stream (file:name), a drive-relative path
    (C:name), a trailing dot or space."""
    parts = [part for part in re.split(r"[/\\]", raw) if part not in (".", "..")]
    return ":" in _DRIVE.sub("", raw) or any(part != part.rstrip(". ") for part in parts)


def _odd(part: str) -> bool:
    """One name of a resolved path that is not a plain file or folder name."""
    return bool(_DEVICE.match(part)) or part != part.rstrip(". ") or ":" in part


def _locate(base: Path, scope: Path, raw: str) -> tuple[bool, tuple[str, ...]]:
    """(inside the scope?, the names from the scope, else from the drive). `scope` is resolved.
    Raises what the system raises for a path it cannot resolve."""
    path = (base / raw).resolve()
    within = path.is_relative_to(scope)
    return within, path.relative_to(scope if within else path.anchor).parts


def inside(base, scope, raw) -> str | None:
    """None when the path `raw`, placed as Cortex Code resolves it (relative to `base`, links
    followed), is inside `scope`. Else why not: "outside", or "odd" for a spelling the app cannot
    place (a stream, a drive-relative path, a trailing dot or space, a device name, a path the
    system cannot resolve). Never raises. It does not look at what the file is: see
    `is_secret_name`."""
    try:
        if _spelling(raw):
            return "odd"
        within, parts = _locate(Path(base), Path(scope).resolve(), raw)
    except Exception:  # whatever the system says about a path, it is not inside
        return "odd"
    if any(_odd(part) for part in parts):
        return "odd"
    return None if within else "outside"


@dataclass(frozen=True)
class Command:
    """One exact command line with its plain name. A call whose command is this line, character for
    character, is shown as a read under `name`; `reads` says what it reads. Only for a command
    that surely changes nothing."""

    name: str
    argv: tuple[str, ...]
    reads: str
    platform: str = sys.platform  # the shell differs: PowerShell on "win32"

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", tuple(str(arg) for arg in self.argv))

    @property
    def line(self) -> str | None:
        """The line as the shell is given it. None when it cannot be written safely: inside
        double quotes PowerShell and sh expand $name and a backtick (and sh reads a backslash), so
        the line would not run on what it names. Such a command is never listed."""
        expanded = '"$' + chr(96) + ("" if self.platform == "win32" else chr(92))
        quoted = [arg for arg in self.argv if not _PLAIN.fullmatch(arg)]
        if not self.argv or any(ch in arg for arg in quoted for ch in expanded):
            return None
        line = " ".join(f'"{arg}"' if arg in quoted else arg for arg in self.argv)
        # PowerShell reads a line that starts with a quoted program as text: the call form runs it
        return "& " + line if self.platform == "win32" and line.startswith('"') else line


def git_readonly(repo) -> list[Command]:
    """status, diff and log of one repository, as commands that only read. None when `repo` is
    not a repository of its own: git would climb to a parent repository and report its files."""
    repo = Path(repo)
    if not (repo / ".git").exists():
        return []
    # A repository can name programs for git to run (core.fsmonitor, a signature check, a pager,
    # an external diff, a textconv): these lines switch each one off, and take no lock, so a
    # "read-only" command writes nothing in .git.
    git = ("git", "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false")
    git += ("-c", "log.showSignature=false", "-C", repo.resolve().as_posix())
    return [
        Command(
            "Look at what has changed in the files",
            (*git, "status", "--short", "--branch"),
            "The list of changed files and the branch",
        ),
        Command(
            "Show the changes not shared yet",
            (*git, "diff", "--no-ext-diff", "--no-textconv"),
            "The text of the changes not shared yet",
        ),
        Command(
            "Look at the last changes shared",
            (*git, "log", "-10", "--oneline"),
            "The ten latest changes shared",
        ),
    ]


def _json(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _human(tool) -> str:
    return re.sub(r"[_\-\s]+", " ", str(tool)).strip() or "unknown tool"


def _extra(payload: dict, known: set) -> list[tuple[str, str]]:
    rest = {key: value for key, value in payload.items() if key not in known}
    return [("Other inputs", _json(rest))] if rest else []


def _line(payload: dict) -> str:
    # not str.strip(): it drops Unicode spaces the shell keeps
    return str(payload.get("command", "")).strip(" \t\r\n")


def _sql_verbs(sql: str) -> list[str]:
    """The first word of each statement, as the user is shown it. Not a parser: it only names
    what is asked."""
    parts = [part.strip() for part in sql.split(";") if part.strip()]
    return [(re.match(r"[A-Za-z]*", part).group().upper() or "STATEMENT") for part in parts]


def _sql_reads(sql: str) -> bool:
    """True only when this is surely one statement that reads. Anything it cannot be sure of
    counts as a change: a second statement, a comment (it can hide the first word), WITH or SELECT
    that writes (INTO), CALL, SYSTEM$."""
    low = sql.strip().rstrip(";").lower()
    if any(mark in low for mark in (";", "--", "/*", "//")) or _SQL_WRITES.search(low):
        return False
    verbs = _sql_verbs(low)
    return bool(verbs) and verbs[0].lower() in _SQL_READS


class FolderPolicy:
    """The default policy: reading inside `scope` (default: `folder`, the agent's working folder)
    is free, every other call asks, each time.

    commands    `Command`s: a call that is exactly one of these lines is shown as a read
    changes     which files a change is ordinary for: a function (resolved path) -> None, or the
                words that end the question ("outside the working folder"); or glob patterns,
                compared with the path from the scope ("*" crosses folders). Default: the scope
    sql         a SQL call shows its exact statement and is told apart as a query (surely one
                reading statement) or a statement (anything else)
    lookups     the known read-only tools of Cortex Code are shown as reads
    standing    each request offers its family as a standing permission

    A host with rules of its own subclasses it: `flag` (one more reason a place is not read
    freely), `commands` (commands that depend on the request) and `words`.
    """

    # The words a host may replace: give the instance or the subclass a new dict.
    words = {
        "undo": " It cannot be undone.",  # ends a question that changes something
        "scope": "the working folder",  # what reading is free in: "a file outside {scope}"
        "folder": "the working folder",  # where a search that names no folder looks
        "large": "a folder too large to check for files that may hold secrets",
        "unusual": "outside what it usually changes",  # a file the `changes` patterns leave out
        "files": "changes in this folder",  # the standing permissions, after "Do not ask again for"
        "elsewhere": "reading outside {scope}",
        "elsewhere_covers": "Reading and searching outside {scope}, except the .git folder and "
        "files that may hold secrets.",
        "also_asks": "Reading outside the scope, in .git or a file that may hold secrets also asks",
    }

    def __init__(
        self,
        folder,
        *,
        scope=None,
        commands=(),
        changes=None,
        sql: bool = False,
        lookups: bool = False,
        standing: bool = False,
    ) -> None:
        self.base = Path(folder)  # the agent's working folder
        self.scope = Path(scope or folder).resolve()
        self.where = Path(scope or folder).name or self.scope.name
        if scope is not None:
            self.words = {**self.words, "scope": f"the folder {self.where}"}
        self.sql, self.lookups, self.standing = sql, lookups, standing
        self._commands = list(commands)
        self._changes = (changes,) if isinstance(changes, str) else changes
        # Where Cortex Code keeps this session's long tool outputs, once known (the gate says).
        self.spill: Path | None = None
        # Where the host saves the files the user attached: attaching them is the consent to read.
        self.uploads: Path | None = None

    # ------------------------------------------------------------------ for a host to override

    def flag(self, parts: tuple[str, ...]):
        """One more reason a place inside the scope is not read freely. `parts`: the names of the
        path, from the scope. None, or (a key of your own, the words): the words are what a read
        asks for ("a draft"), or a pair when a search needs its own ("a draft", "a folder with
        drafts"). A search of a folder that holds such a file asks too."""
        return None

    def commands(self) -> list[Command]:
        """The listed commands for this request."""
        return [command for command in self._commands if command.line]

    # ------------------------------------------------------------------ the three questions

    def judge(self, tool: str, payload) -> tuple[str | None, dict | None]:
        """(why the call is refused, the request to show). Never raises. Both None: free."""
        try:
            return None, self._facts(tool, payload)
        except ValueError as error:
            return str(error), None
        except Exception:  # whatever the system says about a path, the call does not run
            return "This request is not understood.", None

    def describe(self, tool: str, payload) -> str:
        """The name of a step, made from the call: 'Read notes.md', 'Search for "TODO"'."""
        name, payload = str(tool).lower(), payload if isinstance(payload, dict) else {}

        def shown(value) -> str:
            """From the scope, else from the working folder, else the name: never a full path."""
            try:
                path = (self.base / str(value)).resolve()
            except (OSError, ValueError):
                return Path(str(value)).name
            for anchor in (self.scope, self.base.resolve()):
                if path.is_relative_to(anchor):
                    return path.relative_to(anchor).as_posix() or "."
            return path.name

        target = payload.get("file_path") or ""
        if name == "read":
            return f"Read {shown(target)}"
        if name == "glob":
            pattern = str(payload.get("pattern") or "files")
            return f"List {shown(pattern) if _ROOTED.match(pattern) else pattern}"
        if name == "grep":
            return f'Search for "{payload.get("pattern", "")}"'
        if name == _BATCH:
            calls = payload.get("tool_calls")
            return f"Read {len(calls) if isinstance(calls, list) else 0} files"
        if name == "edit":
            return f"Change {shown(target)}"
        if name == "write":
            return (
                f"{'Replace' if (self.base / str(target)).exists() else 'Create'} {shown(target)}"
            )
        if name == "bash":
            line = _line(payload)
            return next((c.name for c in self.commands() if c.line == line), "Run a command")
        if name == _SQL and self.sql:
            sql = str(payload.get("sql") or "")
            if _sql_reads(sql):
                return "Run a query on Snowflake"
            return "Run on Snowflake: " + ", ".join(dict.fromkeys(_sql_verbs(sql)))
        if name in _LOOKUPS and self.lookups:
            return _LOOKUPS[name][0][0].upper() + _LOOKUPS[name][0][1:]
        return f"Use {_human(tool)}"

    def rights(self, granted=()) -> dict:
        """What the agent may do for this request, in words: sent with every message. `granted`:
        what currently runs without asking."""
        unread = "a path or a query that is not text" if self.sql else "a path that is not text"
        rights = {
            "scope": f"{self.words['scope']} ({self.scope.as_posix()})",
            "without_asking": "Read, Glob, Grep (and a batch of 1 to 8 of them) inside the scope; "
            "always give full paths. A long output that was moved to a file of this session may "
            "be read where the tool says it is",
            "asked": "Everything else, each time, and the user sees the exact call and answers: "
            "any Bash command, Edit or Write anywhere, sql_execute, the Snowflake and web tools, "
            "any other tool. " + self.words["also_asks"],
            "refused": "Nothing, for what it is. Only an input the app cannot read is refused "
            f"(not an object, {unread})",
            "running_without_asking_now": list(granted),
        }
        # shown as reads; the rest of Bash as changes
        listed = [{"name": c.name, "line": c.line} for c in self.commands() if c.line]
        if listed:
            rights["commands"] = listed
        return rights

    # ------------------------------------------------------------------ what is free, what asks

    def _why(self, key: str) -> tuple[str, tuple[str, str]]:
        words = (self.words["large"],) * 2 if key == "large" else _WHY[key]
        scope = self.words["scope"]
        return key, (words[0].format(scope=scope), words[1].format(scope=scope))

    def _flag(self, parts: tuple[str, ...], *, secrets: bool = True, host: bool = True):
        """Why this place is not read freely, for a path given by its names: (key, words)."""
        if any(part.lower() == ".git" for part in parts):
            return self._why("git")
        if any(_odd(part) for part in parts):
            return self._why("odd")
        if secrets and any(is_secret_name(part) for part in parts):
            return self._why("secret")
        found = self.flag(parts) if host else None
        if not found:
            return None
        words = found[1]
        return "host", (words, words) if isinstance(words, str) else tuple(words)

    def _place(self, raw: str):
        """None when the place is inside the scope and ordinary; else (key, words). Raises when
        the system cannot resolve it."""
        if _spelling(raw):
            return self._why("odd")
        within, parts = _locate(self.base, self.scope, raw)
        return self._flag(parts, host=within) or (None if within else self._why("outside"))

    def _holds(self, folder: Path, *, grep: bool):
        """A search returns lines or names of the files it covers and Cortex Code gives no way to
        filter them: the kind of the first file it would cover that a direct read asks for
        (secrets by name for a Grep; what the host flags for both)."""
        base, seen = folder.relative_to(self.scope).parts, 0
        for top, dirs, files in os.walk(folder):
            if grep:
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _NOT_SEARCHED]
                files = [f for f in files if not f.startswith(".")]
            else:
                dirs[:] = [d for d in dirs if d.lower() != ".git"]
            seen += len(files)
            if seen > _WALK_LIMIT:
                return self._why("large")
            here = base + Path(top).relative_to(folder).parts
            for name in files:
                kind = self._flag(here + (name,), secrets=grep)
                if kind:
                    return kind
        return None

    def _plain_batch(self, payload: dict) -> bool:
        calls = payload.get("tool_calls")
        if (
            set(payload) != {"tool_calls"}
            or not isinstance(calls, list)
            or not 1 <= len(calls) <= 8
        ):
            return False
        return all(
            isinstance(call, dict)
            and set(call) == {"name", "input"}
            and str(call["name"]).lower() in _READ
            and isinstance(call["input"], dict)
            and self._look(str(call["name"]).lower(), call["input"]) is None
            for call in calls
        )

    def _look(self, name: str, payload: dict):
        """None: a free read. (key, words): a read that asks. "other": not a plain read, so any
        other tool."""
        if name == _BATCH:
            return None if self._plain_batch(payload) else "other"
        if set(payload) - _KEYS[name]:
            return "other"
        for key in _TEXT:
            if payload.get(key) is not None and not isinstance(payload[key], str):
                raise ValueError(f"The input {key!r} has the wrong type.")
        if name == "read":
            # A long output (a big file, a result set) is moved by Cortex Code to its cache, and
            # the agent is told to read it there: it is what a call of this session already
            # returned. Only that session's folder and the attached files, only Read.
            target = payload.get("file_path")
            if isinstance(target, str) and any(
                folder and Path(target).resolve().is_relative_to(Path(folder).resolve())
                for folder in (self.spill, self.uploads)
            ):
                return None
            return self._place(target or "")
        raw = payload.get("path") or "."
        kind = self._place(raw)
        if kind:
            return kind
        pattern = payload.get("pattern") if name == "glob" else payload.get("include")
        if pattern and (".." in pattern or ":" in pattern or "\\" in pattern or pattern[0] == "/"):
            return self._why("odd")
        if pattern and _NAMES_SECRET.search(pattern):
            return self._why("secret")
        folder = (self.base / raw).resolve()
        return self._holds(folder, grep=name == "grep") if folder.is_dir() else None

    def _unusual(self, path: Path) -> str | None:
        """Why a change to this file is not an ordinary one, in the words that end the question."""
        if callable(self._changes):
            return self._changes(path)
        if not path.is_relative_to(self.scope):
            return "outside " + self.words["scope"]
        relative = path.relative_to(self.scope).as_posix()
        if self._changes is None or any(fnmatch(relative, pattern) for pattern in self._changes):
            return None
        return self.words["unusual"]

    def _offer(self, id: str, label: str, covers: str, *, unread: bool = False) -> dict | None:
        """The standing permission a request offers. `unread`: nobody then reads each call, and
        it says so."""
        if not self.standing:
            return None
        if unread:
            covers += " CoCo will then act without anyone reading each call."
        return {
            "id": id,
            "label": "Do not ask again for " + label,
            "until": _UNTIL,
            "covers": covers,
        }

    # ------------------------------------------------------------------ what the user is shown

    def _facts(self, tool: str, payload) -> dict | None:
        """The request to show, written from the call and never from the agent's words. None when
        the call is free. Raises ValueError for a call the app cannot interpret."""
        name = str(tool).lower()
        if not isinstance(payload, dict):
            raise ValueError("The tool input is not understood.")
        if name in _READ or name == _BATCH:
            kind = self._look(name, payload)
            if kind is None:
                return None
            if kind != "other":
                return self._read_facts(name, payload, kind)
        elif name in _LOOKUPS and self.lookups:
            action, goes, reads = _LOOKUPS[name]
            covers = f"Every use of {_human(name)}, whatever it is asked."
            return request(
                "read",
                f"Allow CoCo to {action}?",
                where=goes,
                reads=reads,
                evidence=[("Input", _json(payload))],
                pill="Allow a look-up?",
                standing=self._offer(f"tool:{name}", _human(name), covers),
            )
        elif name == "bash" and isinstance(payload.get("command"), str):
            return self._command_facts(payload)
        elif name in ("edit", "write") and all(
            isinstance(payload.get(key), str)
            for key in (("file_path", "old_string", "new_string"), ("file_path", "content"))[
                name == "write"
            ]
        ):
            return self._file_facts(name, payload)
        elif name == _SQL and self.sql:
            return self._sql_facts(payload)
        human = _human(tool)
        return request(
            "change",
            f'Allow CoCo to use the tool "{human}"?' + self.words["undo"],
            where=self.where,
            changes=f"Tool: {human}",
            evidence=[("Input", _json(payload))],
            pill="Allow a tool?",
            standing=self._offer(
                f"tool:{name}", human, f"Every use of {human}, whatever it is given."
            ),
        )

    def _read_facts(self, name: str, payload: dict, kind) -> dict:
        what = kind[1][name != "read"]
        raw = payload.get("file_path") if name == "read" else payload.get("path")
        evidence = [("Path", raw or f"(not given: {self.words['folder']})")]
        if name != "read" and payload.get("pattern"):
            evidence.append(("Pattern", payload["pattern"]))
        if name == "grep" and payload.get("include"):
            evidence.append(("Include", payload["include"]))
        evidence += _extra(
            payload, _KEYS[name] if name == "read" else {"pattern", "path", "include"}
        )
        verb = {"read": "read", "glob": "list files in", "grep": "search"}[name]
        scope = self.words["scope"]
        offer = None
        if kind[0] == "outside":
            label = self.words["elsewhere"].format(scope=scope)
            offer = self._offer(
                "elsewhere", label, self.words["elsewhere_covers"].format(scope=scope)
            )
        return request(
            "read",
            f"Allow CoCo to {verb} {what}?",
            where=self.where,
            reads=what[0].upper() + what[1:],
            evidence=evidence,
            evidence_label="Show path",
            standing=offer,
        )

    def _command_facts(self, payload: dict) -> dict:
        covers = "Any command, on this computer, whatever it does."
        standing = self._offer("commands", "commands", covers, unread=True)
        # A key beyond Cortex Code's own (a working folder, an environment) can change what the
        # line does: then it is shown whole, as a change.
        extra, line = _extra(payload, _BASH_KEYS), _line(payload)
        listed = None if extra else next((c for c in self.commands() if c.line == line), None)
        if listed:
            return request(
                "read",
                "Allow CoCo to " + listed.name[0].lower() + listed.name[1:] + "?",
                where=self.where,
                reads=listed.reads,
                evidence=[("Command", listed.line)],
                evidence_label="Show command",
                pill="Allow a command?",
                standing=standing,
            )
        lines = len(payload["command"].splitlines()) or 1
        return request(
            "change",
            "Allow CoCo to run a command on this computer?" + self.words["undo"],
            where=self.where,
            changes={
                "file": "A command on this computer",
                "note": f"{lines} lines" if lines > 1 else "",
            },
            evidence=[("Command", payload["command"]), *extra],
            evidence_label="Show command",
            pill="Allow a command?",
            standing=standing,
        )

    def _file_facts(self, name: str, payload: dict) -> dict:
        path = (self.base / payload["file_path"]).resolve()
        far = self._unusual(path) or None
        ordinary = far is None and path.is_relative_to(self.scope)
        if name == "edit":
            old, new = payload["old_string"], payload["new_string"]
            lines = max(1, len(old.splitlines()))
            verb, note = "change", f"{lines} line{'' if lines == 1 else 's'}"
            known = {"file_path", "old_string", "new_string"}
            evidence = [("Replaces", old), ("With", new), *_extra(payload, known)]
        else:
            lines, note, verb = None, "", "replace" if path.exists() else "create"
            evidence = [("New content", payload["content"])]
            evidence += _extra(payload, {"file_path", "content"})
        covers = f"Any change to any file inside {self.where}: create, change or replace."
        return request(
            "change",
            f"Allow CoCo to {verb} a file{' ' + far if far else ''}?" + self.words["undo"],
            where=self.where,
            changes={
                "file": path.relative_to(self.scope).as_posix() if ordinary else path.as_posix(),
                "lines": lines,
                "note": ", ".join(filter(None, [note, far])),
            },
            evidence=evidence,
            evidence_label="Show change",
            pill="Allow a file change?",
            standing=None if far else self._offer("files", self.words["files"], covers),
        )

    def _sql_facts(self, payload: dict) -> dict:
        sql = payload.get("sql")
        if not isinstance(sql, str):
            raise ValueError("The query is not text.")
        evidence = [("Query", sql), *_extra(payload, {"sql", "description"})]
        if _sql_reads(sql):
            covers = f"Any SQL statement that surely only reads, on {_SNOW}."
            return request(
                "read",
                "Allow CoCo to run a query on Snowflake?",
                where=_SNOW,
                reads="Data in Snowflake. It uses your account's compute",
                evidence=evidence,
                evidence_label="Show query",
                pill="Allow a query?",
                standing=self._offer("queries", "queries that only read", covers),
            )
        verbs = _sql_verbs(sql)
        covers = f"Any SQL statement, reads and changes alike, on {_SNOW}."
        return request(
            "change",
            "Allow CoCo to run a statement that can change Snowflake?" + self.words["undo"],
            where=_SNOW,
            changes={
                "file": "Snowflake: " + ", ".join(dict.fromkeys(verbs)) if verbs else "Snowflake",
                "note": f"{len(verbs)} statements" if len(verbs) > 1 else "",
            },
            evidence=evidence,
            evidence_label="Show statement",
            pill="Allow a change on Snowflake?",
            standing=self._offer("statements", "SQL statements", covers, unread=True),
        )
