"""Scripted CoCo for tests, and for running an application without a Snowflake login (feature file
    1.6).

Used when STREAMLIT_COCO_AGENT=mock is set (see `conversation.agent_factory`), or directly by a
    test.
It goes through the real policy and the real agreement path (`Gate`), and really reads and changes
the files of the working folder it is connected to; nothing is simulated but the model and the
programs: a command or a SQL statement is shown and asked about, and never run.
The script is chosen by a keyword in the user's message (first match wins):

    lost       a step is running when the connection is lost (the step shows Interrupted)
    retry      fails with a timeout the first time (Try again is offered), answers normally the
        second time
    fail       reads a file that does not exist: a failing step, then an answer
    slow       a read that runs 6 s and shows 45 s elapsed (started back-dated)
    outside    reads a file outside the working folder
    forbidden  reads the folder's .env
    unlisted   runs `git push`: nothing is executed
    edit       edits the first line of the first Markdown file of the folder
    write      creates coco_note.md in the folder (also "carry out the plan")
    status     runs `git status --short`: nothing is executed
    snowflake  runs `select` on Snowflake; with the word `drop`, a statement that changes it.
               Nothing reaches Snowflake: the result is made up
    screen     answers with what the message carried of the page: the first words shown, the
        dialog, the selection
    reads      says a sentence, then Read, Glob, Grep and a batch of two reads, then an answer
    (other)    a plain streamed answer

  The states of the design sheet, checked before the keywords above:

    onechoice    a question with one choice (and "Something else")
    multichoice  a question with several choices
    ownwords     a question that is answered in one's own words only
    threeq       three questions, one at a time
    longform     a long form asked by the application (fields)
    shortplan    a plan of 4 steps to approve or decline
    longplan     a plan of 12 steps
    twowaits     a command waiting and a question behind it
    outwrite     creates a file outside the working folder: asks (a change)
    unknowntool  a tool the application does not know: asks, shown as a change
    table24      a SQL read returning a table of 24 rows
    table1240    a SQL read returning 1 240 rows (200 are sent)
    norows       a SQL read that returns no row
    structured   an answer that is data: fields, a table, the JSON
    codeblock    an answer with a fenced SQL block
    reasoning    CoCo's reasoning (sent only when the host asks)
    rawdetails   reads one file; the raw exchange rides on the events when "Raw technical details"
        is on
  With "Plan first" on, any other message is answered by what CoCo would do, and nothing is done.
  Every call that acts goes through the real policy and Gate: Allow, Decline, standing permission,
      expiry.

Also: STREAMLIT_COCO_MOCK_SETUP=package|program shows the "not installed" states;
STREAMLIT_COCO_MOCK_PROFILES=a,b lists those profiles (empty: none; default one profile, "mock");
connecting to a profile named "broken" fails (so does "denied", with a sign-in message);
STREAMLIT_COCO_MOCK_FILES="connections.toml=a,b;config.toml=c" gives several connection files (the
profiles are then those of the files); STREAMLIT_COCO_MOCK_EXPIRY=5 makes an unanswered request,
question or plan expire after 5 s instead of 10 minutes. Stop works in every script; so do Allow and
Decline. A message that starts with "Plain:" is answered plainly, whatever words it holds (a page
job's full text may hold a keyword by accident).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

from streamlit_coco.cortex import _INSTALL, _PACKAGE, data_block
from streamlit_coco.gate import EXPIRY, Gate

_PLAN4 = (
    "1. Read last week's report and the timesheets.\n2. Run the project audit.\n"
    "3. Write the report of the week.\n4. Correct the two specifications the audit flags."
)
_PLAN12 = "\n".join(
    f"{n}. {text}"
    for n, text in enumerate(
        [
            "Read last week's report.",
            "Read every timesheet of the week.",
            "Run the project audit.",
            "List the findings by owner.",
            "Read the specifications the audit flags.",
            "Correct the first specification.",
            "Correct the second specification.",
            "Write the report of the week.",
            "Draft the reminders for late timesheets.",
            "Check the report against the audit.",
            "Update the weekly note.",
            "Tell you what changed.",
        ],
        1,
    )
)
_CUSTOMERS = [
    "Aubert SA",
    "Brun Logistique",
    "Chauvet",
    "Delmas",
    "Eloy Transports",
    "Fabre",
    "Garnier",
    "Hamel",
]
_COLUMNS = ["CUSTOMER_ID", "CUSTOMER", "COUNTRY", "REVENUE_EUR"]


class _Stop(Exception):
    pass


class ScriptedAgent:
    def __init__(self, emit, delay: float = 0.04, connect_delay: float = 0.5) -> None:
        self.emit, self.delay, self.connect_delay = emit, delay, connect_delay
        self.gate = Gate(emit, float(os.environ.get("STREAMLIT_COCO_MOCK_EXPIRY") or EXPIRY))
        self._stop = threading.Event()
        self._tries = 0
        self.expiry = float(os.environ.get("STREAMLIT_COCO_MOCK_EXPIRY") or EXPIRY)
        self._slots: dict[str, dict] = {}  # question / plan id -> its slot
        self._planning = self.raw = self.reasoning = False
        self._rows = 24
        self.profile = None
        self.cwd = Path.cwd()  # the folder the agent works in: set by connect

    # ------------------------------------------------------------------ the agent's surface

    def setup(self) -> dict | None:
        missing = os.environ.get("STREAMLIT_COCO_MOCK_SETUP")
        return (
            {"missing": missing, "command": _PACKAGE if missing == "package" else _INSTALL}
            if missing
            else None
        )

    def connection_files(self) -> list[dict]:
        text = os.environ.get("STREAMLIT_COCO_MOCK_FILES")
        if not text:
            return [{"file": "connections.toml", "profiles": self.profiles()}]
        pairs = (part.partition("=") for part in text.split(";") if part.strip())
        return [
            {"file": name.strip(), "profiles": [p.strip() for p in names.split(",") if p.strip()]}
            for name, _, names in pairs
        ]

    def profiles(self) -> list[str]:
        if "STREAMLIT_COCO_MOCK_PROFILES" not in os.environ and os.environ.get(
            "STREAMLIT_COCO_MOCK_FILES"
        ):
            return [p for f in self.connection_files() for p in f["profiles"]]
        raw = os.environ.get("STREAMLIT_COCO_MOCK_PROFILES", "mock")
        return [name.strip() for name in raw.split(",") if name.strip()]

    def connect(self, profile: str, cwd: str, file: str | None = None) -> None:
        self.profile, self.cwd = profile, Path(cwd)
        wrong = file and not any(
            f["file"] == file and profile in f["profiles"] for f in self.connection_files()
        )
        message = (
            f"The profile {profile} is not in {file}."
            if wrong
            else "The profile 'broken' could not connect."
            if profile == "broken"
            else "250001 (08001): Incorrect username or password was specified."
            if profile == "denied"
            else None
        )

        def go() -> None:
            time.sleep(self.connect_delay)
            self.emit(
                {"t": "connect_failed", "message": message} if message else {"t": "connected"}
            )

        threading.Thread(target=go, daemon=True).start()

    def session_facts(self) -> list[dict]:
        return [
            {"label": label, "value": value}
            for label, value in (
                ("Connection", self.profile),
                ("Model", "scripted"),
                ("Session", "mock-session"),
                ("Program version", "mock"),
            )
            if value
        ]

    def send(self, text: str, ctx: dict, policy) -> None:
        self.gate.begin(policy)
        self._stop.clear()
        self._screen = ctx.get("screen") or {}
        threading.Thread(target=self._run, args=(text, policy), daemon=True).start()

    def decide(self, request_id: str, allow: bool, standing: bool = False) -> None:
        self.gate.answer(request_id, allow, standing)

    def revoke(self, permission_id: str) -> None:
        self.gate.revoke(permission_id)

    def _resolve(self, wait_id: str, **result) -> None:
        slot = self._slots.get(wait_id)
        if slot and not slot["event"].is_set():  # the first answer stands
            slot.update(result)
            slot["event"].set()

    def answer(self, id: str, answers) -> None:
        self._resolve(id, answers=answers if isinstance(answers, list) else [])

    def skip(self, id: str) -> None:
        self._resolve(id)

    def approve_plan(self, id: str) -> None:
        self._planning = False
        self._resolve(id, approved=True)

    def decline_plan(self, id: str, reason: str = "") -> None:
        self._resolve(id, reason=str(reason or "").strip())

    def set_planning(self, on: bool) -> None:
        self._planning = bool(on)

    def set_raw(self, on: bool) -> None:
        self.raw = bool(on)

    def set_reasoning(self, on: bool) -> None:
        self.reasoning = bool(on)

    def stop(self) -> None:
        self.gate.cancel_all()
        self._stop.set()

    def close(self) -> None:
        self.stop()

    # ------------------------------------------------------------------ the scripts

    def _run(self, text: str, policy) -> None:
        said = text.split("\n\nFiles saved for you", 1)[
            0
        ]  # the names of attached files are not words to the script
        low = (
            "" if text.startswith("Plain:") else said.lower()
        )  # a page job's text holds no keyword
        scope = self.cwd.resolve()
        outside = str(scope.parent / "outside.md")
        sheet = self._sheet(scope)
        try:
            if "lost" in low:
                self._say("I am looking at the folder.")
                self.emit(
                    {
                        "t": "tool_use",
                        "id": "toolu_lost",
                        "name": "Read",
                        "input": {"file_path": str(sheet)},
                    }
                )
                self._wait(1.5)
                self.emit({"t": "lost", "message": "The connection to Cortex Code was closed."})
                return
            if "retry" in low and not self._tries:
                self._tries += 1
                self._say("I am starting.")
                self.emit(
                    {"t": "error", "message": "Timed out waiting for Cortex Code.", "retry": True}
                )
                return
            plan = "longplan" in low or "shortplan" in low
            if (
                self._planning and not plan
            ):  # planning only: CoCo says what it would do, and does nothing (frame 54)
                self._finish(
                    "I would read the project, run the audit and then do what you asked, one step "
                    "at a time. Nothing is done yet."
                )
            elif "onechoice" in low:
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "coco",
                            "questions": [
                                self._choice(
                                    "q1",
                                    "Which week should the report cover?",
                                    ["This week", "Last week"],
                                    other="Something else",
                                )
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
            elif "multichoice" in low:
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "coco",
                            "questions": [
                                self._choice(
                                    "q1",
                                    "Who should get a reminder?",
                                    [
                                        "People with no timesheet at all",
                                        "People whose timesheet is older than 7 days",
                                        "Their project manager, in copy",
                                    ],
                                    multi=True,
                                    other="Someone else",
                                )
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
            elif "ownwords" in low:
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "coco",
                            "questions": [
                                self._choice(
                                    "q1",
                                    "What should the reminder say?",
                                    [],
                                    other="Your own words",
                                )
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
            elif "threeq" in low:
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "coco",
                            "questions": [
                                self._choice(
                                    "q1",
                                    "Which week should the report cover?",
                                    ["This week", "Last week"],
                                ),
                                self._choice(
                                    "q2",
                                    "Who should get a reminder?",
                                    ["People with no timesheet", "Their project manager"],
                                    multi=True,
                                    other="Someone else",
                                ),
                                self._choice(
                                    "q3",
                                    "How formal should they be?",
                                    ["Short and neutral", "Friendly"],
                                ),
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
            elif "longform" in low:
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "app",
                            "questions": [
                                {
                                    "id": "q1",
                                    "kind": "form",
                                    "text": "What should this week's report say?",
                                    "fields": [
                                        {
                                            "id": "w",
                                            "label": "Week",
                                            "type": "choice",
                                            "choices": [
                                                "Week 41, 6 to 12 October",
                                                "Week 40, 29 September to 5 October",
                                            ],
                                            "required": True,
                                            "value": "Week 41, 6 to 12 October",
                                        },
                                        {
                                            "id": "h",
                                            "label": "Highlights",
                                            "type": "longtext",
                                            "choices": [],
                                            "required": True,
                                            "value": "Pipeline module generated; its tests pass.",
                                        },
                                        {
                                            "id": "b",
                                            "label": "Blockers",
                                            "type": "longtext",
                                            "choices": [],
                                            "required": True,
                                            "value": "",
                                        },
                                        {
                                            "id": "n",
                                            "label": "Next steps",
                                            "type": "longtext",
                                            "choices": [],
                                            "required": True,
                                            "value": "",
                                        },
                                        {
                                            "id": "m",
                                            "label": "Mood of the customer",
                                            "type": "choice",
                                            "choices": ["Not said", "Confident", "Worried"],
                                            "required": False,
                                            "value": "Not said",
                                        },
                                        {
                                            "id": "d",
                                            "label": "Days consumed",
                                            "type": "number",
                                            "choices": [],
                                            "required": False,
                                            "value": "",
                                        },
                                    ],
                                }
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
            elif plan:
                self._say("I read the project and I propose a plan.")
                slot = self._ask(
                    "plan", {"text": _PLAN12 if "longplan" in low else _PLAN4}, "ExitPlanMode"
                )
                if slot is None:
                    self._finish("No answer came, so I did nothing.")
                elif slot.get("approved"):
                    self._say("I carry out the plan.")
                    self._call(policy, "Read", {"file_path": str(sheet)})
                    self._finish("The plan is carried out.")
                else:
                    self._finish(
                        "Understood, I will plan again."
                        + (f" You said: {slot['reason']}" if slot.get("reason") else "")
                    )
            elif "twowaits" in low:
                first = threading.Thread(
                    target=self._quietly,
                    args=(policy, "Bash", {"command": "git status --short"}),
                    daemon=True,
                )
                first.start()
                self._wait(0.5)  # the command is waiting; a question joins it
                self._answered(
                    self._ask(
                        "question",
                        {
                            "source": "coco",
                            "questions": [
                                self._choice(
                                    "q1",
                                    "Which week should the report cover?",
                                    ["This week", "Last week"],
                                )
                            ],
                        },
                        "AskUserQuestion",
                    )
                )
                first.join()
            elif "outwrite" in low:
                self._say("I write a note next to the folder.")
                done = self._call(
                    policy,
                    "Write",
                    {
                        "file_path": str(scope.parent / "coco_outside_note.md"),
                        "content": "# Note\n\nWritten by the scripted agent.\n",
                    },
                )
                self._finish("I wrote the note." if done else "Understood, I did not write it.")
            elif "unknowntool" in low:
                self._say("I use a tool of my own.")
                done = self._call(policy, "mystery_tool", {"target": "demo", "mode": "dry-run"})
                self._finish("The tool ran." if done else "Understood, I did not use it.")
            elif any(word in low for word in ("table1240", "table24", "norows")):
                self._rows = 1240 if "table1240" in low else 0 if "norows" in low else 24
                self._say("I query the customers.")
                where = " where revenue_eur > 1000000000" if not self._rows else ""
                done = self._call(
                    policy,
                    "sql_execute",
                    {
                        "sql": f"select customer_id, customer, country, revenue_eur from "
                        f"DEMO.PUBLIC.CUSTOMERS{where} order by revenue_eur desc",
                        "description": "The customers by revenue",
                    },
                )
                self._finish(
                    (
                        "No customer matches."
                        if not self._rows
                        else f"Here are the customers, {self._rows} rows."
                    )
                    if done
                    else "Understood, I did not run it."
                )
            elif "structured" in low:
                self._say("I read the status of the folder.")
                payload = {
                    "Week": "2026-W41",
                    "Phase": "6 of 7",
                    "Budget": "Green",
                    "Days remaining": 58,
                    "Risks": [
                        {
                            "ID": "R-001",
                            "RISK": "Source access not granted",
                            "OWNER": "Camille Aubert",
                        },
                        {
                            "ID": "R-004",
                            "RISK": "Milestone M3 is 6 days late",
                            "OWNER": "Hugo Lefevre",
                        },
                    ],
                }
                self.emit(
                    {
                        "t": "structured",
                        "tool_id": None,
                        "data": data_block("result-data", payload),
                        "raw": payload,
                    }
                )
                self._finish("This is the status of week 41, with its two open risks.")
            elif "codeblock" in low:
                self._finish(
                    "It reads CUSTOMERS only.\n\n```sql\nselect customer, sum(revenue_eur) as "
                    "revenue\nfrom DEMO.PUBLIC.CUSTOMERS\ngroup by customer;\n```"
                )
            elif "reasoning" in low:
                if self.reasoning:
                    self.emit(
                        {
                            "t": "reasoning",
                            "text": "The request does not say which week. I should read every "
                            "timesheet first.",
                        }
                    )
                self._finish("I looked at the timesheets first.")
            elif "rawdetails" in low:
                self._say("I read the file.")
                self._call(policy, "Read", {"file_path": str(sheet)})
                self._finish("I read the file.")
            elif "snowflake" in low:
                self._say("I look in Snowflake.")
                sql = (
                    "drop table DEMO.PUBLIC.OLD_CALLS"
                    if "drop" in low
                    else "select count(*) from DEMO.PUBLIC.CALLS"
                )
                self._call(
                    policy, "sql_execute", {"sql": sql, "description": "A query for the test"}
                )
                self._finish("Done on Snowflake.")
            elif "screen" in low:
                shown = self._screen
                self._finish(
                    "On your page: "
                    + shown.get("text", "")[:300]
                    + chr(10) * 2
                    + "Dialog: "
                    + shown.get("dialog", "")[:100]
                    + chr(10) * 2
                    + "Selected: "
                    + shown.get("selection", "")
                )
            elif "fail" in low:
                self._say("I read the file you asked for.")
                self._call(policy, "Read", {"file_path": str(scope / "does_not_exist.md")})
                self._finish("I could not read that file: it does not exist.")
            elif "slow" in low:
                self._say("I read the file; it takes a while.")
                self._call(
                    policy, "Read", {"file_path": str(sheet)}, started=time.time() - 45, wait=6
                )
                self._finish("Done, it was slow.")
            elif "outside" in low:
                self._say("I read the file.")
                done = self._call(policy, "Read", {"file_path": outside})
                self._finish("I read that file." if done else "Understood, I did not open it.")
            elif "forbidden" in low:
                self._say("I read the file.")
                done = self._call(policy, "Read", {"file_path": str(scope / ".env")})
                self._finish("I opened it." if done else "Understood, I did not open it.")
            elif "unlisted" in low:
                self._say("I push the changes.")
                done = self._call(policy, "Bash", {"command": "git push"})
                self._finish(
                    "The command was accepted. Nothing was pushed: the scripted agent never runs "
                    "it."
                    if done
                    else "Understood, I did not run it."
                )
            elif "edit" in low:
                self._say("I propose a small edit.")
                path = next((p for p in sorted(scope.glob("*.md")) if p.is_file()), None)
                old = path.read_text(encoding="utf-8").splitlines()[0] if path else ""
                if path is None or not old:
                    self._finish("There is no Markdown file to edit here.")
                else:
                    done = self._call(
                        policy,
                        "Edit",
                        {
                            "file_path": str(path),
                            "old_string": old,
                            "new_string": old + " (reviewed)",
                        },
                    )
                    self._finish("I edited the file." if done else "Understood, I did not edit it.")
            elif "write" in low or "carry out the plan" in low:
                self._say("I propose a note.")
                done = self._call(
                    policy,
                    "Write",
                    {
                        "file_path": str(scope / "coco_note.md"),
                        "content": "# Note\n\nDrafted by CoCo (scripted).\n",
                    },
                )
                self._finish(
                    "I created coco_note.md." if done else "Understood, I did not create the note."
                )
            elif "status" in low:
                self._say("I look at what has changed.")
                done = self._call(policy, "Bash", {"command": "git status --short"})
                self._finish(
                    "Here is what has changed." if done else "Understood, I did not run it."
                )
            elif "reads" in low:
                self._say("I read a few files of the folder.")
                one = str(sheet)
                self._call(policy, "Read", {"file_path": one})
                self._call(policy, "Glob", {"pattern": "*.md", "path": str(scope)})
                self._call(policy, "Grep", {"pattern": "TODO", "path": str(scope)})
                self._call(
                    policy,
                    "direct_tool_calling",
                    {
                        "tool_calls": [
                            {"name": "Read", "input": {"file_path": one}},
                            {"name": "Glob", "input": {"pattern": "*", "path": str(scope)}},
                        ]
                    },
                )
                self._finish("I read the file, listed the Markdown files and searched for TODO.")
            else:
                self._finish(f"This is a scripted answer. You wrote: {text.strip()}")
        except _Stop:
            self.emit({"t": "stopped"})
        # a script that breaks ends its turn, it does not leave the window working forever
        except Exception as error:
            self.emit({"t": "error", "message": str(error) or type(error).__name__, "retry": False})

    @staticmethod
    def _sheet(folder: Path) -> Path:
        """The file the scripts read: the first one of the folder (README.md when there is none)."""
        files = (
            sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
            if folder.is_dir()
            else []
        )
        return files[0] if files else folder / "README.md"

    def _wait(self, seconds: float) -> None:
        if self._stop.wait(seconds):
            raise _Stop

    def _say(self, text: str) -> None:
        for word in re.findall(r"\S+\s*", text):
            self._wait(self.delay)
            self.emit({"t": "text", "text": word})
        self.emit({"t": "snapshot", "text": text})

    def _finish(self, text: str) -> None:
        self._say(text)
        self.emit({"t": "result", "text": text, "error": False})

    @staticmethod
    def _choice(
        id: str, text: str, labels: list, multi: bool = False, other: str | None = None
    ) -> dict:
        return {
            "id": id,
            "text": text,
            "kind": "choice",
            "multi": multi,
            "options": [{"label": label, "description": ""} for label in labels],
            "other": {"label": other} if other else None,
        }

    def _ask(self, kind: str, body: dict, tool: str) -> dict | None:
        """A question or a plan, as the adapter reports one: the tool call, then the wait. The
        answer's slot; None when it expired."""
        tool_id, wait_id = "toolu_" + uuid.uuid4().hex[:12], uuid.uuid4().hex
        slot = self._slots[wait_id] = {"event": threading.Event()}
        self.emit({"t": "tool_use", "id": tool_id, "name": tool, "input": {}})
        self.emit({**body, "t": kind, "id": wait_id, "tool_id": tool_id})
        deadline = time.monotonic() + self.expiry
        try:
            while not slot["event"].wait(0.05):
                if self._stop.is_set():
                    raise _Stop
                if time.monotonic() > deadline:
                    self.emit({"t": "expired", "id": wait_id, "tool_id": tool_id})
                    return None
        finally:
            self._slots.pop(wait_id, None)
        self.emit(
            {"t": "tool_result", "id": tool_id, "content": "The user answered.", "error": False}
        )
        return slot

    def _answered(self, slot: dict | None) -> None:
        if slot is None:
            self._finish("No answer came, so I went on without it.")
        elif "answers" not in slot:
            self._finish("Understood, I go on without it.")
        else:
            said = [
                x
                for a in slot["answers"]
                if isinstance(a, dict)
                for x in [
                    *(a.get("picked") or []),
                    a.get("other"),
                    *(a.get("fields") or {}).values(),
                ]
                if x
            ]
            self._finish("Understood. You answered: " + "; ".join(map(str, said)) + ".")

    def _quietly(self, policy, tool: str, tool_input: dict) -> None:
        try:
            self._call(policy, tool, tool_input)
        except _Stop:
            pass

    def _call(
        self, policy, tool: str, tool_input: dict, started: float | None = None, wait: float = 0
    ) -> bool:
        """One tool call through the gate. True when it ran and succeeded."""
        tool_id = "toolu_" + uuid.uuid4().hex[:12]
        self.emit(
            {
                "t": "tool_use",
                "id": tool_id,
                "name": tool,
                "input": tool_input,
                **({"started": started} if started else {}),
            }
        )
        reason = self.gate.decide(tool, tool_input, tool_id)
        if (
            reason
        ):  # like the real CLI, the refusal comes back as a result that is not flagged as an error
            self.emit({"t": "tool_result", "id": tool_id, "content": reason, "error": False})
            return False
        self._wait(wait)
        try:
            out = self._exec(policy, tool, tool_input)
            content, data = out if isinstance(out, tuple) else (out, None)
            event = {
                "t": "tool_result",
                "id": tool_id,
                "content": content,
                "error": False,
                **({"data": data} if data is not None else {}),
            }
            if self.raw:
                event["raw"] = {
                    "request": json.dumps({"name": tool, "input": tool_input}, indent=2),
                    "result": content,
                }
            self.emit(event)
            return True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.emit({"t": "tool_result", "id": tool_id, "content": str(error), "error": True})
            return False

    def _exec(self, policy, tool: str, tool_input: dict) -> str:
        name = tool.lower()
        if name == "sql_execute":  # nothing reaches Snowflake from the scripted agent
            if not tool_input["sql"].startswith("select customer_id"):
                return "Statement executed (made up by the scripted agent): " + tool_input["sql"]
            # the adapter's way: the text, and the table (at most 200 rows sent, how many there
            # were)
            n = self._rows
            rows = [
                [
                    i + 1,
                    f"{_CUSTOMERS[i % 8]} {i + 1}",
                    ("FR", "DE", "BE")[i % 3],
                    1000 + i * 137 % 9000,
                ]
                for i in range(n)
            ]
            return f"{n} row(s) returned.", {"columns": _COLUMNS, "rows": rows[:200], "total": n}
        if name == "read":
            return Path(tool_input["file_path"]).read_text(encoding="utf-8")
        if name == "glob":
            base = Path(tool_input.get("path") or self.cwd)
            return "\n".join(
                sorted(p.relative_to(base).as_posix() for p in base.glob(tool_input["pattern"]))
            )
        if name == "grep":
            base, hits = Path(tool_input.get("path") or self.cwd), []
            for path in sorted(base.rglob("*.md")):
                for number, line in enumerate(
                    path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                ):
                    if re.search(tool_input["pattern"], line):
                        hits.append(f"{path.relative_to(base).as_posix()}:{number}:{line}")
            return "\n".join(hits[:50]) or "No match."
        if name == "write":
            path = Path(tool_input["file_path"])
            if not path.resolve().is_relative_to(
                self.cwd.resolve()
            ):  # outside the folder: only said, never written
                return (
                    f"Wrote {path.name} (made up by the scripted agent: outside the working "
                    "folder, nothing was written)"
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tool_input["content"], encoding="utf-8")
            return f"Wrote {path.name}"
        if name == "edit":
            path = Path(tool_input["file_path"])
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    tool_input["old_string"], tool_input["new_string"], 1
                ),
                encoding="utf-8",
            )
            return f"Edited {path.name}"
        if name == "bash":  # a command is shown and asked about, never run
            return "Command accepted (made up by the scripted agent: nothing was executed)"
        if name == "direct_tool_calling":
            return "\n".join(
                self._exec(policy, call["name"], call["input"]) for call in tool_input["tool_calls"]
            )
        return f"Ran {tool} (made up by the scripted agent)"
