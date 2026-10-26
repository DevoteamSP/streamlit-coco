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

Words. Every sentence the ready-made policy can put on screen comes from one table, `WORDS`, just
below: the table says, group by group, where each key shows. A host translates the policy by
giving its own words once: `FolderPolicy(folder, words={key: text})`, or a `words` dict on a
subclass. A text may hold slots in braces; the comment of its group names the ones it is given.
Six slots are given to every text: {scope}, {folder}, {except}, {also_asks}, {undo} (the host's
words for those keys) and {where} (the name of the scope's folder). A host's text that is missing,
is not text, or names a slot that does not exist never stops a call: the default sentence is used.
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

WORDS = {
    # ---- Phrases put inside the other sentences. Shown as they are: no slot is filled in them.
    "undo": " It cannot be undone.",  # ends a question that changes something: {undo}
    "scope": "the working folder",  # what reading is free in: {scope}
    "folder": "the working folder",  # where a search that names no folder looks: {folder}
    "except": "the .git folder and files that may hold secrets",  # no standing permission: {except}
    "also_asks": "Reading outside the scope, in .git or a file that may hold secrets also asks",
    "unusual": "outside what it usually changes",  # a file the `changes` patterns leave out
    "ordinary": "the files this application calls ordinary",  # what `changes` as a function lets
    # "scope" when the policy is given a `scope`. Slot: {name}, the folder's name.
    "scope_given": "the folder {name}",
    # ---- A read or a search that asks. The first eight are {what} in the question and, with a
    # capital, the "Reads" line; a host's `flag` gives its own.
    "outside_file": "a file outside {scope}",
    "outside_folder": "a folder outside {scope}",
    "odd": "a path the app cannot tell is inside {scope}",
    "git_file": "a file of the .git folder",
    "git_folder": "the .git folder",
    "secret_file": "a file that may hold secrets",
    "secret_folder": "a folder with files that may hold secrets",
    "large": "a folder too large to check for files that may hold secrets",
    "ask_read": "Allow CoCo to read {what}?",  # the question, for Read
    "ask_glob": "Allow CoCo to list files in {what}?",  # for Glob
    "ask_grep": "Allow CoCo to search {what}?",  # for Grep
    "no_path": "(not given: {folder})",  # the evidence of a search that names no folder
    # ---- A command (Bash). {name}: the listed command's name, without its capital. {count}.
    "ask_listed": "Allow CoCo to {name}?",
    "ask_command": "Allow CoCo to run a command on this computer?{undo}",
    "changes_command": "A command on this computer",  # the "Changes" line
    "lines": "{count} lines",  # the note of a command or an edit of several lines
    "one_line": "{count} line",  # the note of an edit of one line
    # ---- A file change (Edit, Write). {far}: nothing, or a space and what is unusual ("outside",
    # "unusual", or what the host's `changes` function answers).
    "ask_edit": "Allow CoCo to change a file{far}?{undo}",
    "ask_create": "Allow CoCo to create a file{far}?{undo}",
    "ask_replace": "Allow CoCo to replace a file{far}?{undo}",
    "outside": "outside {scope}",
    # ---- SQL, with `sql=True`. {verbs}: the first word of each statement. {count}.
    "where_snowflake": "Snowflake, with your account and your rights",  # the "Where" line
    "ask_query": "Allow CoCo to run a query on Snowflake?",
    "reads_query": "Data in Snowflake. It uses your account's compute",
    "ask_statement": "Allow CoCo to run a statement that can change Snowflake?{undo}",
    "changes_statement": "Snowflake: {verbs}",
    "changes_statement_none": "Snowflake",  # an empty statement
    "sql_unnamed": "STATEMENT",  # a statement that starts with no word
    "statements": "{count} statements",  # the note of several statements
    # ---- The look-up tools, with `lookups=True`. For each tool: what it does (it ends the
    # question "ask_lookup" as {action} and, with a capital, names the step), what it reads, and
    # where the question goes when that is not "where_snowflake".
    "ask_lookup": "Allow CoCo to {action}?",
    "snowflake_object_search": "search Snowflake objects",
    "snowflake_object_search_reads": "Names of objects in your Snowflake account",
    "snowflake_table_lookup": "look up a table on Snowflake",
    "snowflake_table_lookup_reads": "The description of a table in your Snowflake account",
    "semantic_view_search": "search semantic views on Snowflake",
    "semantic_view_search_reads": "Semantic views in your Snowflake account",
    "cortex_agent_search": "search Cortex agents on Snowflake",
    "cortex_agent_search_reads": "Cortex agents in your Snowflake account",
    "snowflake_product_docs": "look in Snowflake's documentation",
    "snowflake_product_docs_reads": "Pages of Snowflake's documentation",
    "snowflake_product_docs_where": "Snowflake's documentation service: your question leaves "
    "this computer",
    "snowflake_connections_list": "list your Snowflake connections",
    "snowflake_connections_list_reads": "The names of your Snowflake connections",
    "snowflake_connections_list_where": "Your Snowflake connections file; the list goes to "
    "Cortex Code",
    "web_search": "search the web",
    "web_search_reads": "Search results from the web",
    "web_search_where": "The web: your search words leave this computer",
    "web_fetch": "fetch a web page",
    "web_fetch_reads": "A page from the web",
    "web_fetch_where": "The web: the address below is called from this computer",
    # ---- Any other tool. {tool}: its name, in words.
    "ask_tool": 'Allow CoCo to use the tool "{tool}"?{undo}',
    "changes_tool": "Tool: {tool}",
    "unknown_tool": "unknown tool",  # {tool} for a tool without a name
    # ---- The few words the closed launcher shows.
    "pill_read": "Allow a read?",
    "pill_change": "Allow a change?",  # only `request()` without a `pill`
    "pill_lookup": "Allow a look-up?",
    "pill_command": "Allow a command?",
    "pill_file": "Allow a file change?",
    "pill_query": "Allow a query?",
    "pill_statement": "Allow a change on Snowflake?",
    "pill_tool": "Allow a tool?",
    # ---- The evidence: the button that opens it, then the label of each exact text.
    "show_input": "Show input",
    "show_path": "Show path",
    "show_command": "Show command",
    "show_change": "Show change",
    "show_query": "Show query",
    "show_statement": "Show statement",
    "label_path": "Path",
    "label_pattern": "Pattern",
    "label_include": "Include",
    "label_other": "Other inputs",  # the inputs the request does not show elsewhere
    "label_input": "Input",
    "label_command": "Command",
    "label_replaces": "Replaces",
    "label_with": "With",
    "label_content": "New content",
    "label_query": "Query",
    # ---- The standing permission, with `standing=True`: the tick, until when, what it covers.
    # {what} in "tick" is one of the six below, or a tool's name.
    "tick": "Do not ask again for {what}",
    "until": "Until this conversation ends, or you take it back in the menu",
    "unread": " CoCo will then act without anyone reading each call.",  # ends two "covers"
    "tick_commands": "commands",
    "files": "changes in this folder",
    "elsewhere": "reading outside {scope}",
    "tick_queries": "queries that only read",
    "tick_statements": "SQL statements",
    "covers_commands": "Any command, on this computer, whatever it does.",
    # {what}: "files_any", "files_matching" or "ordinary", by what `changes` is
    "covers_files": "Any change to {what}, except {except}: create, change or replace.",
    "files_any": "any file inside {where}",
    "files_matching": "the files inside {where} that match {patterns}",
    "covers_elsewhere": "Reading and searching outside {scope}, except {except}.",
    "covers_queries": "Any SQL statement that surely only reads, on {snowflake}.",
    "covers_statements": "Any SQL statement, reads and changes alike, on {snowflake}.",
    "covers_lookup": "Every use of {tool}, whatever it is asked.",
    "covers_tool": "Every use of {tool}, whatever it is given.",
    # ---- The name of a step (`describe`). {path}, {pattern}, {count}, {verbs}, {tool}.
    "step_read": "Read {path}",
    "step_glob": "List {pattern}",
    "step_glob_all": "List files",  # a Glob without a pattern
    "step_grep": 'Search for "{pattern}"',
    "step_batch": "Read {count} files",
    "step_edit": "Change {path}",
    "step_create": "Create {path}",
    "step_replace": "Replace {path}",
    "step_command": "Run a command",
    "step_query": "Run a query on Snowflake",
    "step_statement": "Run on Snowflake: {verbs}",
    "step_tool": "Use {tool}",
    # ---- Why a call is refused, shown on its step. {key}: the name of the input.
    "refused_input": "The tool input is not understood.",
    "refused_request": "This request is not understood.",
    "refused_type": "The input {key!r} has the wrong type.",
    "refused_query": "The query is not text.",
    # ---- What the agent is told it may do (`rights`). {path}: the folder of the scope.
    "rights_scope": "{scope} ({path})",
    "rights_free": "Read, Glob, Grep (and a batch of 1 to 8 of them) inside the scope; always "
    "give full paths. A long output that was moved to a file of this session may be read where "
    "the tool says it is",
    "rights_asked": "Everything else, each time, and the user sees the exact call and answers: "
    "any Bash command, Edit or Write anywhere, sql_execute, the Snowflake and web tools, any "
    "other tool. {also_asks}",
    "rights_refused": "Nothing, for what it is. Only an input the app cannot read is refused "
    "(not an object, {unread})",
    "rights_unread": "a path that is not text",
    "rights_unread_sql": "a path or a query that is not text",
    "rights_also_read": "Read, Glob and Grep there are free as inside the scope. Edit and Write "
    "there are asked, as outside the scope",
    # ---- The commands of `git_readonly(repo, words)`: the name, then what it reads.
    "git_status": "Look at what has changed in the files",
    "git_status_reads": "The list of changed files and the branch",
    "git_diff": "Show the changes not shared yet",
    "git_diff_reads": "The text of the changes not shared yet",
    "git_log": "Look at the last changes shared",
    "git_log_reads": "The ten latest changes shared",
}
_GIVEN = ("scope", "folder", "except", "also_asks", "undo")  # the phrases every text is given

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
# What a read that asks is: the keys of WORDS for a read, and for a search.
_WHY = {
    "outside": ("outside_file", "outside_folder"),
    "odd": ("odd", "odd"),
    "git": ("git_file", "git_folder"),
    "secret": ("secret_file", "secret_folder"),
    "large": ("large", "large"),
}
# The look-up tools of Cortex Code and the web: reads, and the key of where the question goes.
_LOOKUPS = {
    "snowflake_object_search": "where_snowflake",
    "snowflake_table_lookup": "where_snowflake",
    "semantic_view_search": "where_snowflake",
    "cortex_agent_search": "where_snowflake",
    "snowflake_product_docs": "snowflake_product_docs_where",
    "snowflake_connections_list": "snowflake_connections_list_where",
    "web_search": "web_search_where",
    "web_fetch": "web_fetch_where",
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
    evidence_label: str | None = None,
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
                    (default: WORDS["show_input"])
    pill            the few words the closed launcher shows (default: WORDS["pill_read"] or
                    WORDS["pill_change"])
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
        "pill": pill or WORDS["pill_read" if kind == "read" else "pill_change"],
        "evidence_label": evidence_label or WORDS["show_input"],
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


def _word(words, key: str) -> str:
    """The host's text for this key, as it is; the default when it is missing or is not text."""
    text = words.get(key) if isinstance(words, dict) else None
    return text if isinstance(text, str) else WORDS[key]


def git_readonly(repo, words: dict | None = None) -> list[Command]:
    """status, diff and log of one repository, as commands that only read. None when `repo` is
    not a repository of its own: git would climb to a parent repository and report its files.
    `words`: the host's words for their names and what they read (the "git_" keys of WORDS)."""
    repo = Path(repo)
    if not (repo / ".git").exists():
        return []
    # A repository can name programs for git to run (core.fsmonitor, a signature check, a pager,
    # an external diff, a textconv): these lines switch each one off, and take no lock, so a
    # "read-only" command writes nothing in .git.
    git = ("git", "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false")
    git += ("-c", "log.showSignature=false", "-C", repo.resolve().as_posix())
    listed = {
        "git_status": ("status", "--short", "--branch"),
        "git_diff": ("diff", "--no-ext-diff", "--no-textconv"),
        "git_log": ("log", "-10", "--oneline"),
    }
    return [
        Command(_word(words, key), (*git, *rest), _word(words, key + "_reads"))
        for key, rest in listed.items()
    ]


def _json(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _human(tool) -> str:
    return re.sub(r"[_\-\s]+", " ", str(tool)).strip()


def _line(payload: dict) -> str:
    # not str.strip(): it drops Unicode spaces the shell keeps
    return str(payload.get("command", "")).strip(" \t\r\n")


def _sql_verbs(sql: str) -> list[str]:
    """The first word of each statement ("" when it starts with none). Not a parser: it only
    names what is asked."""
    parts = [part.strip() for part in sql.split(";") if part.strip()]
    return [re.match(r"[A-Za-z]*", part).group().upper() for part in parts]


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

    also_read   folders read freely besides the scope, with the same care (.git, secret names,
                odd spellings, `flag`, searches, links followed). Reading only: a change there
                is a change outside the scope
    commands    `Command`s: a call that is exactly one of these lines is shown as a read
    changes     which files a change is ordinary for: a function (resolved path) -> None, or the
                words that end the question ("outside the working folder"); or glob patterns,
                compared with the path from the scope ("*" crosses folders). Default: the scope
    sql         a SQL call shows its exact statement and is told apart as a query (surely one
                reading statement) or a statement (anything else)
    lookups     the known read-only tools of Cortex Code are shown as reads
    standing    each request offers its family as a standing permission. "File changes" covers
                only what `changes` calls ordinary, and never a place a read asks for (.git, a
                secret name, what `flag` marks): those are asked each time
    words       the host's words, over the defaults: {key of WORDS: text}
    where       what the request's "Where" line says (default: the name of the scope's folder);
                the managed agent has no folder here: `where=SANDBOX_WHERE`

    A host with rules of its own subclasses it: `flag` (one more reason a place is not read
    freely), `commands` (commands that depend on the request) and `words`.
    """

    # The words a host may replace: `words=`, or a new dict on the instance or the subclass.
    words = WORDS

    def __init__(
        self,
        folder,
        *,
        scope=None,
        also_read=(),
        commands=(),
        changes=None,
        sql: bool = False,
        lookups: bool = False,
        standing: bool = False,
        words: dict | None = None,
        where: str | None = None,
    ) -> None:
        self.base = Path(folder)  # the agent's working folder
        self.scope = Path(scope or folder).resolve()
        if isinstance(also_read, (str, os.PathLike)):
            also_read = (also_read,)
        self.also = [(self.base / place).resolve() for place in also_read]
        self.where = where or Path(scope or folder).name or self.scope.name
        if words:
            self.words = {**self.words, **words}
        if scope is not None:
            self.words = {**self.words, "scope": self._say("scope_given", name=self.where)}
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
        path, from the scope (or from the `also_read` folder that holds it). None, or (a key of
        your own, the words): the words are what a read asks for ("a draft"), or a pair when a
        search needs its own ("a draft", "a folder with drafts"). A search of a folder that holds
        such a file asks too."""
        return None

    def commands(self) -> list[Command]:
        """The listed commands for this request."""
        return [command for command in self._commands if command.line]

    # ------------------------------------------------------------------ the words

    def _word(self, key: str) -> str:
        return _word(self.words, key)

    def _say(self, key: str, /, **slots) -> str:
        """The host's sentence for this key, its slots filled. The default sentence when the
        host's cannot be filled (a slot that does not exist, a stray brace): never an error."""
        slots = {"where": self.where, **{name: self._word(name) for name in _GIVEN}, **slots}
        try:
            return self._word(key).format(**slots)
        except Exception:  # a host's text must not stop a call
            return WORDS[key].format(**slots)

    def _tool(self, tool) -> str:
        return _human(tool) or self._word("unknown_tool")

    def _extra(self, payload: dict, known: set) -> list[tuple[str, str]]:
        rest = {key: value for key, value in payload.items() if key not in known}
        return [(self._word("label_other"), _json(rest))] if rest else []

    def _verbs(self, sql: str) -> list[str]:
        return [verb or self._word("sql_unnamed") for verb in _sql_verbs(sql)]

    # ------------------------------------------------------------------ the three questions

    def judge(self, tool: str, payload) -> tuple[str | None, dict | None]:
        """(why the call is refused, the request to show). Never raises. Both None: free."""
        try:
            return None, self._facts(tool, payload)
        except ValueError as error:
            return str(error), None
        except Exception:  # whatever the system says about a path, the call does not run
            return self._word("refused_request"), None

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
            return self._say("step_read", path=shown(target))
        if name == "glob":
            pattern = str(payload.get("pattern") or "")
            if not pattern:
                return self._word("step_glob_all")
            listed = shown(pattern) if _ROOTED.match(pattern) else pattern
            return self._say("step_glob", pattern=listed)
        if name == "grep":
            return self._say("step_grep", pattern=payload.get("pattern", ""))
        if name == _BATCH:
            calls = payload.get("tool_calls")
            return self._say("step_batch", count=len(calls) if isinstance(calls, list) else 0)
        if name == "edit":
            return self._say("step_edit", path=shown(target))
        if name == "write":
            key = "step_replace" if (self.base / str(target)).exists() else "step_create"
            return self._say(key, path=shown(target))
        if name == "bash":
            line, unlisted = _line(payload), self._word("step_command")
            return next((c.name for c in self.commands() if c.line == line), unlisted)
        if name == _SQL and self.sql:
            sql = str(payload.get("sql") or "")
            if _sql_reads(sql):
                return self._word("step_query")
            return self._say("step_statement", verbs=", ".join(dict.fromkeys(self._verbs(sql))))
        if name in _LOOKUPS and self.lookups:
            action = self._word(name)
            return action[:1].upper() + action[1:]
        return self._say("step_tool", tool=self._tool(tool))

    def rights(self, granted=()) -> dict:
        """What the agent may do for this request, in words: sent with every message. `granted`:
        what currently runs without asking."""
        unread = self._word("rights_unread_sql" if self.sql else "rights_unread")
        rights = {
            "scope": self._say("rights_scope", path=self.scope.as_posix()),
            "without_asking": self._say("rights_free"),
            "asked": self._say("rights_asked"),
            "refused": self._say("rights_refused", unread=unread),
            "running_without_asking_now": list(granted),
        }
        # shown as reads; the rest of Bash as changes
        listed = [{"name": c.name, "line": c.line} for c in self.commands() if c.line]
        if listed:
            rights["commands"] = listed
        if self.also:
            rights["also_read_without_asking"] = {
                "folders": [place.as_posix() for place in self.also],
                "how": self._say("rights_also_read"),
            }
        return rights

    # ------------------------------------------------------------------ what is free, what asks

    def _why(self, key: str) -> tuple[str, tuple[str, str]]:
        return key, (self._say(_WHY[key][0]), self._say(_WHY[key][1]))

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

    def _root(self, path: Path) -> Path | None:
        """The folder read freely that holds this resolved path: the scope or an `also_read`."""
        return next((root for root in (self.scope, *self.also) if path.is_relative_to(root)), None)

    def _place(self, raw: str):
        """None when the place is read freely (inside the scope or an `also_read` folder, and
        ordinary); else (key, words). Raises when the system cannot resolve it."""
        if _spelling(raw):
            return self._why("odd")
        path = (self.base / raw).resolve()
        root = self._root(path)
        parts = path.relative_to(root or path.anchor).parts
        return self._flag(parts, host=bool(root)) or (None if root else self._why("outside"))

    def _holds(self, folder: Path, *, grep: bool):
        """A search returns lines or names of the files it covers and Cortex Code gives no way to
        filter them: the kind of the first file it would cover that a direct read asks for
        (secrets by name for a Grep; what the host flags for both)."""
        base, seen = folder.relative_to(self._root(folder)).parts, 0
        for top, dirs, files in os.walk(folder):
            if grep:
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _NOT_SEARCHED]
                files = [f for f in files if not f.startswith(".")]
            else:
                dirs[:] = [d for d in dirs if d.lower() != ".git"]
            dirs.sort()  # the first place found must not depend on the filesystem's listing order
            seen += len(files)
            if seen > _WALK_LIMIT:
                return self._why("large")
            here = base + Path(top).relative_to(folder).parts
            for name in sorted(files):
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
                raise ValueError(self._say("refused_type", key=key))
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
            return self._say("outside")
        relative = path.relative_to(self.scope).as_posix()
        if self._changes is None or any(fnmatch(relative, pattern) for pattern in self._changes):
            return None
        return self._word("unusual")

    def _offer(self, id: str, what: str, covers: str, *, unread: bool = False) -> dict | None:
        """The standing permission a request offers. `unread`: nobody then reads each call, and
        it says so."""
        if not self.standing:
            return None
        return {
            "id": id,
            "label": self._say("tick", what=what),
            "until": self._word("until"),
            "covers": covers + (self._word("unread") if unread else ""),
        }

    # ------------------------------------------------------------------ what the user is shown

    def _facts(self, tool: str, payload) -> dict | None:
        """The request to show, written from the call and never from the agent's words. None when
        the call is free. Raises ValueError for a call the app cannot interpret."""
        name = str(tool).lower()
        if not isinstance(payload, dict):
            raise ValueError(self._word("refused_input"))
        if name in _READ or name == _BATCH:
            kind = self._look(name, payload)
            if kind is None:
                return None
            if kind != "other":
                return self._read_facts(name, payload, kind)
        elif name in _LOOKUPS and self.lookups:
            human = _human(name)
            return request(
                "read",
                self._say("ask_lookup", action=self._word(name)),
                where=self._word(_LOOKUPS[name]),
                reads=self._word(name + "_reads"),
                evidence=[(self._word("label_input"), _json(payload))],
                evidence_label=self._word("show_input"),
                pill=self._word("pill_lookup"),
                standing=self._offer(f"tool:{name}", human, self._say("covers_lookup", tool=human)),
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
        human = self._tool(tool)
        return request(
            "change",
            self._say("ask_tool", tool=human),
            where=self.where,
            changes=self._say("changes_tool", tool=human),
            evidence=[(self._word("label_input"), _json(payload))],
            evidence_label=self._word("show_input"),
            pill=self._word("pill_tool"),
            standing=self._offer(f"tool:{name}", human, self._say("covers_tool", tool=human)),
        )

    def _read_facts(self, name: str, payload: dict, kind) -> dict:
        what = kind[1][name != "read"]
        raw = payload.get("file_path") if name == "read" else payload.get("path")
        evidence = [(self._word("label_path"), raw or self._say("no_path"))]
        if name != "read" and payload.get("pattern"):
            evidence.append((self._word("label_pattern"), payload["pattern"]))
        if name == "grep" and payload.get("include"):
            evidence.append((self._word("label_include"), payload["include"]))
        evidence += self._extra(
            payload, _KEYS[name] if name == "read" else {"pattern", "path", "include"}
        )
        offer = None
        if kind[0] == "outside":
            covers = self._say("covers_elsewhere")
            offer = self._offer("elsewhere", self._say("elsewhere"), covers)
        return request(
            "read",
            self._say("ask_" + name, what=what),
            where=self.where,
            reads=what[:1].upper() + what[1:],
            evidence=evidence,
            evidence_label=self._word("show_path"),
            pill=self._word("pill_read"),
            standing=offer,
        )

    def _command_facts(self, payload: dict) -> dict:
        covers = self._say("covers_commands")
        standing = self._offer("commands", self._word("tick_commands"), covers, unread=True)
        # A key beyond Cortex Code's own (a working folder, an environment) can change what the
        # line does: then it is shown whole, as a change.
        extra, line = self._extra(payload, _BASH_KEYS), _line(payload)
        listed = None if extra else next((c for c in self.commands() if c.line == line), None)
        if listed:
            return request(
                "read",
                self._say("ask_listed", name=listed.name[:1].lower() + listed.name[1:]),
                where=self.where,
                reads=listed.reads,
                evidence=[(self._word("label_command"), listed.line)],
                evidence_label=self._word("show_command"),
                pill=self._word("pill_command"),
                standing=standing,
            )
        lines = len(payload["command"].splitlines()) or 1
        return request(
            "change",
            self._say("ask_command"),
            where=self.where,
            changes={
                "file": self._word("changes_command"),
                "note": self._say("lines", count=lines) if lines > 1 else "",
            },
            evidence=[(self._word("label_command"), payload["command"]), *extra],
            evidence_label=self._word("show_command"),
            pill=self._word("pill_command"),
            standing=standing,
        )

    def _file_facts(self, name: str, payload: dict) -> dict:
        path = (self.base / payload["file_path"]).resolve()
        far = self._unusual(path) or None
        ordinary = far is None and path.is_relative_to(self.scope)
        if name == "edit":
            old, new = payload["old_string"], payload["new_string"]
            lines = max(1, len(old.splitlines()))
            ask, note = "ask_edit", self._say("one_line" if lines == 1 else "lines", count=lines)
            known = {"file_path", "old_string", "new_string"}
            evidence = [(self._word("label_replaces"), old), (self._word("label_with"), new)]
        else:
            lines, note, ask = None, "", "ask_replace" if path.exists() else "ask_create"
            known = {"file_path", "content"}
            evidence = [(self._word("label_content"), payload["content"])]
        evidence += self._extra(payload, known)
        # A standing permission never covers a place a read asks for: with one, an agent that
        # a file it read has turned could rewrite a hook or a credentials file unseen.
        place = self._place(payload["file_path"])
        asked = far or (place and place[0] != "outside")
        return request(
            "change",
            self._say(ask, far=f" {far}" if far else ""),
            where=self.where,
            changes={
                "file": path.relative_to(self.scope).as_posix() if ordinary else path.as_posix(),
                "lines": lines,
                "note": ", ".join(filter(None, [note, far])),
            },
            evidence=evidence,
            evidence_label=self._word("show_change"),
            pill=self._word("pill_file"),
            standing=None if asked else self._offer("files", self._word("files"), self._covers()),
        )

    def _covers(self) -> str:
        """What the "File changes" standing permission covers: no more than `changes` does."""
        if self._changes is None:
            what = self._say("files_any")
        elif callable(self._changes):
            what = self._word("ordinary")
        else:
            what = self._say("files_matching", patterns=", ".join(self._changes))
        return self._say("covers_files", what=what)

    def _sql_facts(self, payload: dict) -> dict:
        sql = payload.get("sql")
        if not isinstance(sql, str):
            raise ValueError(self._word("refused_query"))
        snowflake = self._word("where_snowflake")
        label = self._word("label_query")
        evidence = [(label, sql), *self._extra(payload, {"sql", "description"})]
        if _sql_reads(sql):
            covers = self._say("covers_queries", snowflake=snowflake)
            return request(
                "read",
                self._say("ask_query"),
                where=snowflake,
                reads=self._word("reads_query"),
                evidence=evidence,
                evidence_label=self._word("show_query"),
                pill=self._word("pill_query"),
                standing=self._offer("queries", self._word("tick_queries"), covers),
            )
        verbs = self._verbs(sql)
        named = self._say("changes_statement", verbs=", ".join(dict.fromkeys(verbs)))
        covers = self._say("covers_statements", snowflake=snowflake)
        return request(
            "change",
            self._say("ask_statement"),
            where=snowflake,
            changes={
                "file": named if verbs else self._word("changes_statement_none"),
                "note": self._say("statements", count=len(verbs)) if len(verbs) > 1 else "",
            },
            evidence=evidence,
            evidence_label=self._word("show_statement"),
            pill=self._word("pill_statement"),
            standing=self._offer("statements", self._word("tick_statements"), covers, unread=True),
        )
