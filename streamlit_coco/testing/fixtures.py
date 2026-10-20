# ruff: noqa: E501
"""View fixtures for the Ask CoCo window: one `view` (the contract of streamlit_coco/conversation.py) per state of the design sheet.

Written from the contract alone, so that the window can be built and checked before, and without, the conversation
runtime. `VIEWS` maps a state name to a view; `TYPING` and `UI` say what the window itself holds in that state (typed
text, open menu, confirmation), which is not part of a view.
"""

from __future__ import annotations

PROMPTS = [
    "Prepare this week's status report",
    "Find what is late and draft reminders",
    "Check the audit and list what to fix",
]
PROJECT = "marenval-fleet-telemetry"
LONG_PROJECT = "lormeau-regulatory-reporting-and-compliance-data-platform-phase-two-extension"
LONG_CMD = (
    'git --no-pager -C "C:/Users/someone/Desktop/Personal Workspace/Devoteam/customers/'
    + LONG_PROJECT
    + '" log -10 --oneline '
    "--format=%H%x09%an%x09%ad%x09%s --date=iso-strict --decorate=full --all --no-merges --since=2026-01-01"
)
LONG_FILE = "98_project/steering/20261009_steerco_followup_regulatory_reporting_phase_two_extension_decisions_and_actions.md"
GIT_Q = {"kind": "user", "id": "u1", "text": "What is the git status of my repository?"}
GIT_LABEL = "Look at what has changed in the project's files"
GIT_CMD = f'git --no-pager -C "C:/projects/{PROJECT}" status --short --branch'
GIT_OUT = "## main...origin/main\n M 98_project/tasks.md\n?? notes.md"
ANSWER_MD = (
    "**Overall progress.** Phase 6 of 7, 2 of 4 modules generated, 58 days remaining. Budget verdict Green.\n\n"
    "**Risks and blockers.**\n\n- M3 is 6 days late\n- R-001 is open\n- no meeting logged for 36 days\n\n"
    "**Next steps.** Camille Aubert logs the weekly meeting and moves M3 with a reason. See `98_project/risks.md` and [the guide](https://example.org/guide)."
)


def step(id, state, label, **kw):
    return {
        "kind": "step",
        "id": id,
        "state": state,
        "label": label,
        "note": kw.pop("note", None),
        "tool": kw.pop("tool", "Bash"),
        "reason": kw.pop("reason", ""),
        "input": kw.pop("input", {"command": GIT_CMD}),
        "result": kw.pop("result", ""),
        "allowed": kw.pop("allowed", False),
        "started": kw.pop("started", None),
        **kw,
    }


def view(status="ready", thread=None, **kw):
    base = {
        "status": status,
        "setup": None,
        "profiles": ["devoteam-eu"],
        "profile": "devoteam-eu",
        "error": None,
        "prompts": PROMPTS,
        "thread": thread or [],
        "request": None,
        "queue": [],
        "restore": None,
        "pill": None,
        "rev": 1,
    }
    base.update(kw)
    return base


def ask(kind="read", **kw):
    base = {
        "id": "r1",
        "kind": kind,
        "question": "Allow CoCo to look at what has changed in the project's files?",
        "where": PROJECT,
        "reads": "The list of files changed since the last share",
        "changes": None,
        "evidence_label": "Show command",
        "evidence": [{"label": "Command", "text": GIT_CMD}],
    }
    base.update(kw)
    return base


CHANGE = ask(
    "change",
    question="Allow CoCo to change a file?",
    reads=None,
    changes={"file": "specs/functional_spec.md", "lines": 3, "note": "3 lines"},
    evidence_label="Show change",
    evidence=[
        {"label": "Replaces", "text": "Phase 3 is blocked."},
        {"label": "With", "text": "Phase 3 is unblocked since 2026-10-09."},
    ],
)
S1 = step(
    "s1",
    "ok",
    "List the project files",
    tool="Glob",
    input={"pattern": "**/*.md"},
    result="24 files",
)
S2 = step(
    "s2",
    "ok",
    "Search for TODO",
    tool="Grep",
    input={"pattern": "TODO", "path": "."},
    result="3 matches",
)
S3 = step(
    "s3", "ok", "Read PROJECT.md", tool="Read", input={"file_path": "PROJECT.md"}, result="..."
)
SAY = "24 files. Now looking for **this week's reports** in `PROJECT.md`, <b>not</b> markup."


def three(folded: bool) -> list[dict]:
    """Two sections: a step no sentence introduces (shown as that step), then two steps under the sentence CoCo said."""
    return [
        {"kind": "steps", "id": "g1", "folded": folded, "summary": None, "items": [S1]},
        {"kind": "steps", "id": "g2", "folded": folded, "summary": SAY, "items": [S2, S3]},
    ]


REMINDERS = [
    {"kind": "user", "id": "u1", "text": "Draft reminders"},
    {
        "kind": "draft",
        "id": "d1",
        "title": "To Hugo Lefèvre",
        "text": "Hi Hugo, on marenval-fleet-telemetry please:\n- Your timesheet has not changed for 21 days -> update my timesheet\nThanks!",
    },
    {
        "kind": "draft",
        "id": "d2",
        "title": "To Léa Fontaine",
        "text": "Hi Léa, on marenval-fleet-telemetry please:\n- T-022: consumed 6.5 d is above the estimate of 5 d -> re-estimate the task\nThanks!",
    },
]
ANSWERED = [
    {"kind": "user", "id": "u1", "text": "Prepare this week's status report"},
    {"kind": "scope", "text": f"About {PROJECT}"},
    {"kind": "answer", "id": "a1", "text": ANSWER_MD, "streaming": False},
]
SCOPE = {"kind": "scope", "text": f"About {PROJECT}"}
RUN = [
    GIT_Q,
    SCOPE,
    {
        "kind": "steps",
        "id": "g1",
        "folded": False,
        "summary": None,
        "items": [step("s1", "run", GIT_LABEL)],
    },
]

VIEWS: dict[str, dict] = {
    "empty": view(),
    "empty_project_long": view(
        prompts=[
            "Summarise what changed this week across my projects",
            "Draft reminders for late timesheets",
            "List what blocks each project and who owns it",
        ]
    ),
    "answer": view(thread=ANSWERED),
    "reminders": view(thread=REMINDERS),
    "pending": view("working", [GIT_Q, SCOPE]),
    "not_connected_one": view("not_connected", profiles=["devoteam-eu"], profile=None),
    "not_connected_several": view(
        "not_connected", profiles=["devoteam-eu", "devoteam-us", "devoteam-sandbox"], profile=None
    ),
    "not_connected_none": view("not_connected", profiles=[], profile=None),
    "not_connected_error": view(
        "not_connected",
        profiles=["devoteam-eu"],
        profile=None,
        error="Could not sign in to devoteam-eu: the password was refused.",
    ),
    "connecting": view("connecting", profile="devoteam-eu"),
    "not_installed_package": view(
        "not_installed",
        setup={"missing": "package", "command": "make cockpit"},
        profiles=[],
        profile=None,
    ),
    "not_installed_program": view(
        "not_installed",
        setup={
            "missing": "program",
            "command": "The Cortex Code program was not found on this computer. It is installed from Snowflake's documentation. Restart Cockpit afterwards.",
        },
        profiles=[],
        profile=None,
    ),
    "menu": view(thread=ANSWERED),
    "step_run": view("working", RUN),
    "step_done_dots": view(
        "working",
        [
            GIT_Q,
            SCOPE,
            {
                "kind": "steps",
                "id": "g1",
                "folded": False,
                "summary": None,
                "items": [step("s1", "ok", GIT_LABEL, result=GIT_OUT)],
            },
        ],
    ),
    "step_bad": view(
        thread=[
            GIT_Q,
            SCOPE,
            step("s1", "bad", GIT_LABEL, result="fatal: not a git repository"),
            {
                "kind": "system",
                "text": "This folder keeps no history of changes, so I could not see what changed.",
                "detail": "fatal: not a git repository (or any of the parent directories): .git",
                "action": None,
            },
        ]
    ),
    "step_refused": view(
        thread=[
            GIT_Q,
            SCOPE,
            step(
                "s1",
                "no",
                "Use snowflake_sql_execute",
                tool="snowflake_sql_execute",
                input={"sql": "select 1"},
                note="Not allowed",
                reason="CoCo cannot run SQL from the Cockpit.",
            ),
        ]
    ),
    "streaming": view(
        "working",
        [
            {"kind": "user", "id": "u1", "text": "Find the weekly reports still missing"},
            SCOPE,
            *three(False),
            {
                "kind": "answer",
                "id": "a1",
                "text": "Two projects have no weekly report for this week: **lormeau-regulatory-reporting** and",
                "streaming": True,
            },
        ],
    ),
    "folded": view(
        thread=[
            {"kind": "user", "id": "u1", "text": "Find the weekly reports still missing"},
            SCOPE,
            *three(True),
            {
                "kind": "answer",
                "id": "a1",
                "text": "Two projects have no weekly report for this week.",
                "streaming": False,
            },
        ]
    ),
    "ask_command": view("waiting", [GIT_Q, SCOPE], request=ask()),
    "ask_edit": view(
        "waiting",
        [{"kind": "user", "id": "u1", "text": "Unblock phase 3 in the spec"}, SCOPE],
        request=CHANGE,
    ),
    "ask_create": view(
        "waiting",
        [{"kind": "user", "id": "u1", "text": "Write the steering note"}, SCOPE],
        request=ask(
            "change",
            question="Allow CoCo to create a file?",
            reads=None,
            changes={"file": "98_project/steering/20261010_steerco.md", "lines": None, "note": ""},
            evidence_label="Show change",
            evidence=[
                {
                    "label": "New content",
                    "text": "# Steering committee 2026-10-10\n\n## Decisions\n- Phase 3 unblocked.",
                }
            ],
        ),
    ),
    "ask_replace": view(
        "waiting",
        [{"kind": "user", "id": "u1", "text": "Rewrite the glossary"}, SCOPE],
        request=ask(
            "change",
            question="Allow CoCo to replace a file?",
            reads=None,
            changes={"file": "specs/glossary.md", "lines": None, "note": ""},
            evidence_label="Show change",
            evidence=[{"label": "New content", "text": "# Glossary\n\n(full new content)"}],
        ),
    ),
    "ask_long_file": view(
        "waiting",
        [
            {"kind": "user", "id": "u1", "text": "Update the steerco follow-up"},
            {"kind": "scope", "text": f"About {LONG_PROJECT}"},
        ],
        request=ask(
            "change",
            question="Allow CoCo to change a file?",
            where=LONG_PROJECT,
            reads=None,
            changes={"file": LONG_FILE, "lines": 12, "note": "12 lines"},
            evidence_label="Show change",
            evidence=[{"label": "Replaces", "text": "old"}, {"label": "With", "text": "new"}],
        ),
    ),
    "ask_long_command": view(
        "waiting",
        [{"kind": "user", "id": "u1", "text": "Show the last changes"}, SCOPE],
        request=ask(
            question="Allow CoCo to look at the last changes shared?",
            where=LONG_PROJECT,
            evidence=[{"label": "Command", "text": LONG_CMD}],
        ),
    ),
    "after_allow": view(
        "working",
        [
            GIT_Q,
            SCOPE,
            {
                "kind": "steps",
                "id": "g1",
                "folded": False,
                "summary": None,
                "items": [step("s1", "run", GIT_LABEL, allowed=True)],
            },
        ],
    ),
    "after_decline": view(thread=[GIT_Q, SCOPE, step("s1", "no", GIT_LABEL, note="Declined")]),
    "expired": view(
        thread=[
            GIT_Q,
            SCOPE,
            step(
                "s1",
                "no",
                GIT_LABEL,
                note="Expired",
                reason="Not answered within ten minutes. Nothing was done.",
            ),
        ]
    ),
    "pill_request": view(
        "waiting",
        [GIT_Q, SCOPE],
        request=ask(),
        pill={"kind": "request", "label": "Allow a command?", "name": PROJECT},
    ),
    "pill_change": view(
        "waiting",
        [GIT_Q, SCOPE],
        request=CHANGE,
        pill={"kind": "request", "label": "Allow a file change?", "name": LONG_PROJECT},
    ),
    "pill_answer": view(
        thread=ANSWERED, pill={"kind": "answer", "label": "Answer ready", "name": PROJECT}
    ),
    "pill_failed": view(
        "lost",
        [GIT_Q, SCOPE, step("s1", "bad", GIT_LABEL, note="Interrupted")],
        pill={"kind": "failed", "label": "Connection lost", "name": PROJECT},
    ),
    "long_evidence": view(
        "waiting",
        [GIT_Q, SCOPE],
        request=ask(
            evidence=[
                {
                    "label": "Command",
                    "text": "\n".join(f"line {n}: " + "x" * (n * 7 % 90) for n in range(1, 60)),
                }
            ]
        ),
    ),
    "detail_open": view(
        thread=[
            GIT_Q,
            SCOPE,
            step("s1", "ok", GIT_LABEL, result=GIT_OUT, allowed=True),
            {
                "kind": "answer",
                "id": "a1",
                "text": "You changed one file and added one new file that is not shared yet.",
                "streaming": False,
            },
        ]
    ),
    "stopped": view(thread=[GIT_Q, SCOPE, step("s1", "no", GIT_LABEL, note="Stopped")]),
    "long_step": view(
        "working",
        [
            GIT_Q,
            SCOPE,
            step(
                "s1", "run", "Look at the change history of all 24 projects", started=1, elapsed=100
            ),
        ],
    ),
    "pinned": view("waiting", ANSWERED + REMINDERS + [GIT_Q, SCOPE], request=ask()),
    "lost": view(
        "lost",
        [
            GIT_Q,
            SCOPE,
            step("s1", "bad", GIT_LABEL, note="Interrupted"),
            {
                "kind": "system",
                "text": "The connection to CoCo was lost. Reconnect to go on.",
                "detail": None,
                "action": None,
            },
        ],
    ),
    "system_retry": view(
        thread=[
            GIT_Q,
            SCOPE,
            {
                "kind": "system",
                "text": "CoCo did not answer in time.",
                "detail": "TimeoutError: no event for 120 s",
                "action": "retry",
            },
        ]
    ),
    "queued": view("working", RUN + [], queue=[{"id": "q1", "text": "Then list the open risks"}]),
    "queued_waiting": view(
        "waiting",
        [GIT_Q, SCOPE],
        request=ask(),
        queue=[
            {"id": "q1", "text": "Then list the open risks"},
            {"id": "q2", "text": "And the late tasks"},
        ],
    ),
    "restore": view(thread=ANSWERED, restore="Then list the open risks", rev=7),
}
# what the window itself holds in a state (not part of a view)
TYPING = {
    "answer": "Which risks are still open?",
    "step_run": "",
    "typing_ahead": "Then list the open risks",
    "waiting_typing": "Then list the open risks",
    "lost": "A half-typed message",
}
VIEWS["typing_ahead"] = VIEWS["step_run"]
VIEWS["waiting_typing"] = VIEWS["ask_command"]
UI = {
    "menu": {"menu": True},
    "confirm_idle": {"confirm": "new"},
    "confirm_working": {"confirm": "new"},
    "confirm_request": {"confirm": "new"},
    "confirm_queue": {"confirm": "new"},
    "confirm_disc": {"confirm": "disc"},
}
VIEWS["confirm_idle"] = VIEWS["answer"]
VIEWS["confirm_working"] = VIEWS["step_run"]
VIEWS["confirm_request"] = VIEWS["ask_command"]
VIEWS["confirm_queue"] = view(
    "working",
    RUN,
    queue=[
        {"id": "q1", "text": "Then list the open risks"},
        {"id": "q2", "text": "And the late tasks"},
    ],
)
VIEWS["confirm_disc"] = VIEWS["answer"]


# ====================================================================== the playground: frames 38 to 86
# One view per frame of the design sheet (ui-rebuild/design/CoCo22.dc.html, built by tools/checks/build_coco22.py), the same
# content as the frame, so that a rendered fixture can be held next to it. The contract is in utils/coco_runtime.py
# ("THE PLAYGROUND ADDITIONS"). The sheet draws some states the window reaches by a gesture (a choice made, a box ticked,
# a fold opened): GESTURES lists them per fixture for tests/coco_harness.py; the view itself never holds them.
# GESTURES steps: ["press", text, n?] click the n-th (default first) button, label, summary or menu line whose text or
# aria-label is `text`; ["type", css, text, n?]; ["attach", [[name, bytes], ...]]; ["dragover"]. CLOSED: drawn with the window shut.
RM_Q = {"kind": "user", "id": "u1", "text": "Draft reminders for late timesheets"}
RM_READ = step(
    "s1",
    "ok",
    "Read 9 files",
    tool="Read",
    input={"file_path": "98_project/timesheets/*.md"},
    result="9 files",
)
Q_WEEK = "Which week should the reminders cover?"
Q_WHO = "Who should receive them?"
WEEKS = [
    {"label": "This week", "description": "6 to 12 October"},
    {"label": "Last week", "description": "29 September to 5 October"},
    {"label": "Both weeks", "description": ""},
]
WHO = [
    {"label": "People with no timesheet at all", "description": ""},
    {"label": "People whose timesheet is older than 7 days", "description": ""},
    {"label": "Their project manager, in copy", "description": ""},
]
PLAN_Q = {
    "kind": "user",
    "id": "u1",
    "text": "Prepare this week's report and fix what the audit found",
}
PLAN4 = [
    "Read last week's report and this week's timesheets.",
    "Run the project audit.",
    "Write the report of week 41 from last week's structure.",
    "Correct the two specifications the audit flags.",
]
PLAN12 = [
    "Read last week's report.",
    "Read this week's timesheets, 9 people.",
    "Read the open risks and actions.",
    "Run the project audit.",
    "List what the audit reports, worst first.",
    "Write the report of week 41 from last week's structure.",
    "Fill the progress section from the timesheets.",
    "Fill the risks section from the register.",
    "Correct the functional specification where the audit flags it.",
    "Correct the data contract where the audit flags it.",
    "Run the audit again.",
    "Summarise what changed, file by file.",
]
SQL = (
    "SELECT customer, COUNT(*) AS orders,\n       SUM(amount_eur) AS revenue_eur\nFROM sales.orders\nWHERE order_date >= '2026-07-01'\n"
    "GROUP BY customer\nORDER BY revenue_eur DESC"
)
SQL_STEP = "Run a query on Snowflake"
JSON_STATUS = (
    '{\n  "week": "2026-W41",\n  "phase": "6 of 7",\n  "budget": "Green",\n  "days_remaining": 58,\n  "risks": [\n    {"id": "R-001", "title": "Source access not granted", "owner": "Camille Aubert"},\n'
    '    {"id": "R-004", "title": "Milestone M3 is 6 days late", "owner": "Hugo Lef\u00e8vre"}\n  ],\n  "next_step": "Log the weekly meeting."\n}'
)
CUSTOMERS = [
    ("Lormeau Assurances", "Insurance", "FR"),
    ("Clinique Saint-Aubry", "Health", "FR"),
    ("Marenval Logistique", "Transport", "BE"),
    ("Br\u00e9vent \u00c9nergie", "Energy", "FR"),
    ("Calvi\u00e8re Distribution", "Retail", "ES"),
    ("Atelier Morvan", "Industry", "FR"),
    ("Groupe Vauquelin", "Retail", "FR"),
    ("S\u00e9lune Mutuelle", "Insurance", "FR"),
    ("Port de Kerlouan", "Transport", "FR"),
    ("Tessier Fr\u00e8res", "Industry", "BE"),
    ("Banque d'Ardoise", "Banking", "LU"),
    ("Orvanne Sant\u00e9", "Health", "FR"),
]
LONG_ANSWER = (
    "**Overall progress.** Phase 6 of 7, 2 of 4 modules generated, 58 days remaining. Budget verdict Green. The pipeline module was generated on Tuesday and "
    "its tests pass; the semantic view is specified and waits for the data contract. **Risks and blockers.** M3 is 6 days late; R-001 is open; "
    "no meeting logged for 36 days. **Next steps.** Camille Aubert logs the weekly meeting and moves M3 with a reason."
)
FIX_PROMPT = (
    'The Streamlit app under `sales_dashboard/` is running and raised this exception.\n\nTraceback (most recent call last):\n  File "sales_dashboard/streamlit_app.py", line 42, in <module>\n'
    '    st.bar_chart(df, x="REGION", y="REVENUE")\nKeyError: \'REVENUE\'\n\nRead `sales_dashboard/streamlit_app.py` and nearby files. Fix the exception. After fixing, say what you changed.'
)
RAW_REQ = '{\n  "name": "Bash",\n  "status": "completed",\n  "input": {\n    "command": "git status",\n    "description": "Look at what has changed"\n  }\n}'
RAW_RES = '{\n  "result": "On branch feat/cockpit\\nYour branch is up to date with \'origin/feat/cockpit\'.\\n\\nChanges not staged for commit:\\n\\tmodified:   cockpit/pages/projects.py"\n}'
GRANTED = [
    {"id": "p1", "text": "Looks at what has changed in the files of marenval-fleet-telemetry"},
    {"id": "p2", "text": "Runs a query that only reads, on Snowflake"},
]
OPTIONS = [
    {"id": "plan", "label": "Plan first", "sub": "CoCo proposes before it acts", "on": False},
    {
        "id": "latest",
        "label": "Latest exchange only",
        "sub": "Earlier messages one click away",
        "on": True,
    },
    {"id": "shorten", "label": "Shorten long messages", "sub": "", "on": False},
    {"id": "raw", "label": "Raw technical details", "sub": "", "on": False},
]
FACTS = [
    {"label": "Account", "value": "devoteam-eu, from connections.toml"},
    {"label": "Model", "value": "auto"},
    {"label": "Works in", "value": "C:\\Users\\camille.aubert\\projects\\marenval-fleet-telemetry"},
    {"label": "Cortex Code", "value": "1.0.46"},
    {"label": "Agent SDK", "value": "1.0.7"},
    {"label": "streamlit-coco", "value": "0.1.9"},
]
STANDING = {
    "id": "sp1",
    "label": "Do not ask again for this command",
    "covers": "Looking at what has changed in the files of marenval-fleet-telemetry",
    "until": "This conversation ends, or you take it back in the menu",
}
FILES_OK = {"multi": True, "accept": [".csv", ".pdf", ".xlsx", ".md"], "max_mb": 10, "existing": []}


def section(id, items, summary=None, folded=False):
    return {"kind": "steps", "id": id, "folded": folded, "summary": summary, "items": items}


def plan_text(items):
    return "\n".join(f"{n}. {text}" for n, text in enumerate(items, 1))


def waiting(wait, thread, status="waiting", **kw):
    """A view with something waiting: `wait` is the waiting block (`request` mirrors it when it is an agreement request)."""
    return view(status, thread, wait={"more": None, **wait}, **kw)


def request_wait(req, more=None):
    return {"id": req["id"], "kind": "request", "more": more}


def choice(id, text, options, multi=False, other="Something else"):
    return {
        "id": id,
        "text": text,
        "kind": "choice",
        "multi": multi,
        "options": options,
        "other": {"label": other} if other else None,
    }


def question(*questions, source="coco", more=None):
    return {
        "id": "n1",
        "kind": "question",
        "more": more,
        "source": source,
        "questions": list(questions),
    }


def plan(items, more=None):
    return {"id": "n2", "kind": "plan", "more": more, "text": plan_text(items)}


def form_field(id, label, type="text", value="", required=True, choices=()):
    return {
        "id": id,
        "label": label,
        "type": type,
        "choices": list(choices),
        "required": required,
        "value": value,
    }


def table(id, columns, rows, total=None, label=None):
    return {
        "id": id,
        "label": label,
        "columns": [{"name": n, "kind": k} for n, k in columns],
        "rows": rows,
        "total": total,
    }


def money(n):
    return f"{n:,}".replace(",", " ")


def customers(count, wide=False):
    rows = []
    for i in range(count):
        name, segment, country = CUSTOMERS[i % len(CUSTOMERS)]
        orders, revenue = 1530 - (i % 15) * 97, 412600 - (i % 15) * 27350
        rows.append(
            [
                name,
                segment,
                country,
                money(orders),
                money(revenue),
                money(revenue // orders),
                f"{1.2 + (i * 7 % 5) * 0.6:.1f} %",
                f"2026-09-{30 - (i % 15) * 2:02d}",
            ]
            if wide
            else [name, money(orders), money(revenue)]
        )
    return rows


COLS3 = [("CUSTOMER", "text"), ("ORDERS", "number"), ("REVENUE_EUR", "number")]
COLS8 = [
    ("CUSTOMER", "text"),
    ("SEGMENT", "text"),
    ("COUNTRY", "text"),
    ("ORDERS", "number"),
    ("REVENUE_EUR", "number"),
    ("AVG_BASKET_EUR", "number"),
    ("RETURN_RATE", "number"),
    ("LAST_ORDER", "number"),
]


def data(id, *, tables=(), title=None, fields=(), json=None):
    return {
        "type": "data",
        "id": id,
        "title": title,
        "fields": list(fields),
        "tables": list(tables),
        "json": json,
    }


def sql_step(id="s1", **kw):
    return step(id, "ok", SQL_STEP, tool="sql_execute", input={"sql": SQL}, **kw)


SQL_Q = {"kind": "user", "id": "u1", "text": "Who bought the most last quarter?"}
SQL_ASK = ask(
    question="Allow CoCo to run a query on Snowflake?",
    where="Snowflake, with your account and your rights",
    reads="The table SALES.ORDERS, with your role ANALYST_EU",
    evidence_label="Show query",
    evidence=[{"label": "Query", "text": SQL}],
)
WIDE_ANSWER = {
    "kind": "answer",
    "id": "a1",
    "text": "Five customers make 61\u00a0% of the revenue.",
    "streaming": False,
}
GIT_ASK55 = ask(
    question="Allow CoCo to look at what has changed in your project files?",
    reads="The files of marenval-fleet-telemetry",
    evidence=[{"label": "Command", "text": "git status"}],
)
GIT_ASK56 = {**GIT_ASK55, "standing": STANDING}
STATUS_Q = {"kind": "user", "id": "u1", "text": "Give me this week's status"}
STATUS_DATA = data(
    "d1",
    title="Weekly status",
    json=JSON_STATUS,
    fields=[
        {"label": "Week", "value": "2026-W41"},
        {"label": "Phase", "value": "6 of 7"},
        {"label": "Budget", "value": "Green"},
        {"label": "Days remaining", "value": "58"},
        {"label": "Next step", "value": "Log the weekly meeting."},
    ],
    tables=[
        table(
            "t2",
            [("ID", "text"), ("RISK", "text"), ("OWNER", "text")],
            [
                ["R-001", "Source access not granted", "Camille Aubert"],
                ["R-004", "Milestone M3 is 6 days late", "Hugo Lef\u00e8vre"],
            ],
            label="Risks",
        )
    ],
)

VIEWS.update(
    {
        # ---- questions
        "f38_question_choice": waiting(
            question(choice("q1", Q_WEEK, WEEKS)), [RM_Q, section("g1", [RM_READ])]
        ),
        "f39_question_picked": waiting(
            question(choice("q1", Q_WEEK, WEEKS)),
            [RM_Q, section("g1", [RM_READ])],
            queue=[{"id": "q1", "text": "Then list the open risks"}],
        ),
        "f40_question_other": waiting(question(choice("q1", Q_WEEK, WEEKS)), [RM_Q]),
        "f41_question_multi": waiting(
            question(choice("q1", Q_WHO, WHO, multi=True, other="Someone else")), [RM_Q]
        ),
        "f42_question_several": waiting(
            question(
                choice("q1", Q_WEEK, WEEKS),
                choice("q2", Q_WHO, WHO, multi=True, other="Someone else"),
                choice(
                    "q3",
                    "How formal should they be?",
                    [
                        {"label": "Short and neutral", "description": ""},
                        {"label": "Friendly", "description": ""},
                    ],
                ),
            ),
            [RM_Q],
        ),
        "f43_question_form": waiting(
            question(
                {
                    "id": "q1",
                    "kind": "form",
                    "text": "What should this week's report say?",
                    "fields": [
                        form_field(
                            "w",
                            "Week",
                            "choice",
                            "Week 41, 6 to 12 October",
                            choices=[
                                "Week 41, 6 to 12 October",
                                "Week 40, 29 September to 5 October",
                            ],
                        ),
                        form_field(
                            "h",
                            "Highlights",
                            "longtext",
                            "Pipeline module generated; its tests pass.",
                        ),
                        form_field(
                            "b",
                            "Blockers",
                            "longtext",
                            "Access to the source system is still not granted.",
                        ),
                        form_field("n", "Next steps", "longtext", ""),
                        form_field(
                            "m",
                            "Mood of the customer",
                            "choice",
                            "Not said",
                            False,
                            ["Not said", "Confident", "Worried"],
                        ),
                        form_field("d", "Days consumed", "number", "", False),
                    ],
                },
                source="app",
            ),
            [{"kind": "user", "id": "u1", "text": "Prepare this week's status report"}],
        ),
        "f44_question_answered": view(
            "working",
            [
                RM_Q,
                section("g1", [RM_READ]),
                {"kind": "asked", "id": "n1", "text": Q_WEEK, "note": None},
                {"kind": "user", "id": "u2", "text": "This week"},
                section(
                    "g2",
                    [
                        step(
                            "s2",
                            "run",
                            "Read 4 files",
                            tool="Read",
                            input={"file_path": "98_project/timesheets/*.md"},
                        )
                    ],
                ),
            ],
        ),
        "f45_question_skipped": view(
            "working",
            [
                RM_Q,
                section("g1", [RM_READ]),
                {"kind": "asked", "id": "n1", "text": Q_WEEK, "note": "Skipped"},
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "I will cover this week, the one still open.",
                    "streaming": True,
                },
            ],
        ),
        "f46_question_pill": waiting(
            question(choice("q1", Q_WEEK, WEEKS)),
            [RM_Q, section("g1", [RM_READ])],
            pill={"kind": "question", "label": "A question for you", "name": PROJECT},
        ),
        # ---- plans
        "f47_plan_mode": view(
            "working",
            [
                PLAN_Q,
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "run",
                            "Read 4 files",
                            tool="Read",
                            input={"file_path": "98_project/weeklies/*.md"},
                        )
                    ],
                ),
            ],
            mode={"planning": True, "can_carry_out": False},
        ),
        "f48_plan_presented": waiting(plan(PLAN4), [PLAN_Q]),
        "f49_plan_long": waiting(plan(PLAN12), [PLAN_Q]),
        "f50_plan_decline": waiting(plan(PLAN4), [PLAN_Q]),
        "f51_plan_approved": view(
            "working",
            [
                PLAN_Q,
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "ok",
                            "The plan you approved",
                            tool=None,
                            input={},
                            blocks=[{"type": "text", "text": plan_text(PLAN4)}],
                        )
                    ],
                ),
                section(
                    "g2",
                    [
                        step(
                            "s2",
                            "run",
                            "Read last week's report",
                            tool="Read",
                            input={"file_path": "98_project/weeklies/20261002_weekly.md"},
                        )
                    ],
                ),
            ],
        ),
        "f52_plan_declined": view(
            "working",
            [
                PLAN_Q,
                step(
                    "s1",
                    "no",
                    "The plan CoCo proposed",
                    tool=None,
                    input={},
                    note="Declined",
                    blocks=[{"type": "text", "text": plan_text(PLAN4)}],
                ),
                {
                    "kind": "user",
                    "id": "u2",
                    "text": "Only the report. Leave the specifications alone.",
                },
            ],
            mode={"planning": True, "can_carry_out": False},
        ),
        "f53_plan_pill": waiting(
            plan(PLAN4),
            [PLAN_Q],
            pill={"kind": "plan", "label": "A plan to approve", "name": PROJECT},
        ),
        "f54_plan_answer": view(
            "ready",
            [
                PLAN_Q,
                {
                    "kind": "answer",
                    "id": "a1",
                    "streaming": False,
                    "text": "I would read last week's report and the timesheets, run the audit, write the report of week 41, then correct the two specifications the audit flags.",
                },
            ],
            mode={"planning": True, "can_carry_out": True},
        ),
        "f55_two_wait": waiting(
            request_wait(GIT_ASK55, {"count": 2, "next": "question"}), [GIT_Q], request=GIT_ASK55
        ),
        # ---- standing permission
        "f56_standing_offer": waiting(request_wait(GIT_ASK56), [GIT_Q], request=GIT_ASK56),
        "f58_standing_granted": view(
            "working",
            [
                GIT_Q,
                {
                    "kind": "system",
                    "id": "y1",
                    "text": "CoCo no longer asks before it looks at what has changed in these files.",
                    "detail": None,
                    "action": {"label": "Ask again"},
                },
                section("g1", [step("s1", "run", GIT_LABEL, allowed=True)]),
            ],
            granted=GRANTED[:1],
        ),
        "f59_standing_later": view(
            "ready",
            [
                {"kind": "user", "id": "u1", "text": "And now, anything new?"},
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "ok",
                            GIT_LABEL,
                            result="On branch feat/cockpit\nnothing to commit, working tree clean",
                            standing=True,
                        )
                    ],
                ),
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "Nothing has changed since this morning.",
                    "streaming": False,
                },
            ],
            granted=GRANTED[:1],
        ),
        "f60_menu_all": view("ready", ANSWERED, options=OPTIONS, granted=GRANTED, session=FACTS),
        # ---- data
        "f62_table": view(
            "ready",
            [
                SQL_Q,
                section("g1", [sql_step(note="24 rows")]),
                {
                    **WIDE_ANSWER,
                    "blocks": [data("d1", tables=[table("t1", COLS3, customers(24), total=24)])],
                },
            ],
        ),
        "f63_query_result": view(
            "ready",
            [
                SQL_Q,
                section(
                    "g1",
                    [
                        sql_step(
                            note="24 rows",
                            allowed=True,
                            blocks=[
                                data("d1", tables=[table("t1", COLS3, customers(24), total=24)])
                            ],
                        )
                    ],
                ),
            ],
        ),
        "f64_query_none": view(
            "ready",
            [
                {"kind": "user", "id": "u1", "text": "Any order above 1 million euros?"},
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "ok",
                            SQL_STEP,
                            tool="sql_execute",
                            note="No rows",
                            allowed=True,
                            input={
                                "sql": "SELECT order_id, customer, amount_eur\nFROM sales.orders\nWHERE amount_eur > 1000000"
                            },
                        )
                    ],
                ),
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "No order went above 1 million euros last quarter.",
                    "streaming": False,
                },
            ],
        ),
        "f65_larger": view(
            "ready",
            [
                SQL_Q,
                section("g1", [sql_step(note="1 240 rows")]),
                {
                    **WIDE_ANSWER,
                    "blocks": [
                        data("d1", tables=[table("t1", COLS8, customers(200, True), total=1240)])
                    ],
                },
            ],
        ),
        "f67_data_answer": view(
            "ready",
            [
                STATUS_Q,
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "",
                    "streaming": False,
                    "blocks": [STATUS_DATA],
                },
            ],
        ),
        "f69_code": view(
            "ready",
            [
                {"kind": "user", "id": "u1", "text": "Write the query for revenue by customer"},
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "It reads SALES.ORDERS only.\n\n```sql\n" + SQL + "\n```",
                    "streaming": False,
                },
            ],
        ),
        # ---- files
        "f70_attach": view(attach=FILES_OK),
        "f71_files_chosen": view("ready", ANSWERED, attach=FILES_OK),
        "f73_files_sent": view(
            "working",
            [
                {
                    "kind": "user",
                    "id": "u1",
                    "text": "Compare these with last week",
                    "files": ["timesheets_2026-W41.csv", "steering_notes.pdf"],
                },
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "run",
                            "Read timesheets_2026-W41.csv",
                            tool="Read",
                            input={"file_path": "_uploads/timesheets_2026-W41.csv"},
                        )
                    ],
                ),
            ],
            attach=FILES_OK,
        ),
        "f74_drop": view("ready", ANSWERED, attach=FILES_OK),
        # ---- requests sent by the page
        "f75_page_request": view(
            "working",
            [
                {
                    "kind": "user",
                    "id": "u1",
                    "text": "Fix the error in the sales dashboard",
                    "full": FIX_PROMPT,
                },
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "run",
                            "Read sales_dashboard/streamlit_app.py",
                            tool="Read",
                            input={"file_path": "sales_dashboard/streamlit_app.py"},
                        )
                    ],
                ),
            ],
        ),
        "f76_page_before_connect": view(
            "not_connected",
            [],
            profiles=["devoteam-eu", "devoteam-us"],
            profile=None,
            prompts=[],
            queue=[
                {
                    "id": "q1",
                    "text": "Build the sales dashboard",
                    "note": "Sent when you connect",
                    "full": None,
                }
            ],
        ),
        "f77_page_result": view(
            "ready",
            [
                {"kind": "user", "id": "u1", "text": "Map the Tableau estate"},
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "ok",
                            "Read 4 files",
                            tool="Read",
                            input={"file_path": "_uploads/*.twb"},
                        )
                    ],
                    summary="Reading the four workbooks.",
                    folded=True,
                ),
                {
                    "kind": "answer",
                    "id": "a1",
                    "text": "Four workbooks, 31 measures, 6 of them defined twice.",
                    "streaming": False,
                },
                {
                    "kind": "system",
                    "id": "y1",
                    "text": "The result is on the page, under Estate map.",
                    "detail": None,
                    "action": {"label": "Show it"},
                },
            ],
        ),
        "f78_prompt_fill": view(
            prompts=[
                {
                    "title": "Count the rows of a table",
                    "text": "Count the rows of SALES.ORDERS",
                    "fill": True,
                },
                *PROMPTS[1:],
            ]
        ),
        # ---- display and session
        "f79_latest_only": view("ready", ANSWERED, options=OPTIONS, hidden=12),
        "f80_shortened": view(
            "ready",
            [
                {"kind": "user", "id": "u0", "text": "And last week?"},
                {"kind": "answer", "id": "a0", "text": LONG_ANSWER, "streaming": False},
                *ANSWERED,
            ],
            options=[{**o, "on": o["id"] == "shorten"} for o in OPTIONS],
        ),
        "f82_connecting": view(
            "connecting", [], profile="devoteam-eu", prompts=[], type_ahead=True
        ),
        "f83_connect_failed": view(
            "not_connected",
            [],
            profiles=["devoteam-eu", "devoteam-us"],
            profile="devoteam-eu",
            prompts=[],
            problem="Snowflake refused the sign-in. Try again, or choose another account.",
            error="250001 (08001): Failed to connect to DB: xy12345.eu-west-1.snowflakecomputing.com:443. Incorrect username or password was specified.",
        ),
        "f84_profile_files": view(
            "not_connected",
            [],
            profiles=["devoteam-eu", "devoteam-us", "legacy-prod"],
            profile=None,
            prompts=[],
            profile_files=[
                {"file": "connections.toml", "profiles": ["devoteam-eu", "devoteam-us"]},
                {"file": "config.toml", "profiles": ["legacy-prod"]},
            ],
        ),
        "f85_raw_details": view(
            "ready",
            [
                GIT_Q,
                section(
                    "g1",
                    [
                        step(
                            "s1",
                            "ok",
                            GIT_LABEL,
                            result=GIT_OUT,
                            raw={"request": RAW_REQ, "result": RAW_RES},
                        )
                    ],
                ),
                {"kind": "answer", "id": "a1", "text": "You changed one file.", "streaming": False},
            ],
            options=[{**o, "on": o["id"] == "raw"} for o in OPTIONS],
        ),
        "f86_reasoning": view(
            "working",
            [
                RM_Q,
                section(
                    "g1",
                    [
                        {
                            "kind": "reasoning",
                            "id": "r1",
                            "text": "The request does not say which week. The open week is 41; nine people are staffed. I should read every timesheet before asking who is late.",
                        },
                        RM_READ,
                    ],
                    summary="Looking at the timesheets first.",
                ),
            ],
        ),
    }
)
# frames that are the same view as another, reached by a gesture
VIEWS["f57_standing_ticked"] = VIEWS["f56_standing_offer"]
VIEWS["f61_granted_list"] = VIEWS["f60_menu_all"]
VIEWS["f66_larger_request"] = waiting(
    request_wait(SQL_ASK),
    [
        SQL_Q,
        section("g1", [sql_step(note="24 rows")]),
        {
            **WIDE_ANSWER,
            "blocks": [data("d1", tables=[table("t1", COLS8, customers(24, True), total=24)])],
        },
    ],
    request=SQL_ASK,
)
VIEWS["f68_data_json"] = VIEWS["f67_data_answer"]
VIEWS["f72_file_refused"] = VIEWS["f71_files_chosen"]
VIEWS["f81_session_details"] = VIEWS["f60_menu_all"]
GESTURES: dict[str, list[list]] = {
    "f39_question_picked": [["press", "This week"]],
    "f40_question_other": [
        ["press", "Something else"],
        ["type", "textarea.ag-oth", "Only the two weeks of the autumn break"],
    ],
    "f41_question_multi": [
        ["press", "People with no timesheet at all"],
        ["press", "Their project manager, in copy"],
    ],
    "f42_question_several": [
        ["press", "This week"],
        ["press", "Next"],
        ["press", "People whose timesheet is older than 7 days"],
    ],
    "f50_plan_decline": [
        ["press", "Decline"],
        ["type", "textarea.in", "Only the report. Leave the specifications alone."],
    ],
    "f57_standing_ticked": [["press", "Do not ask again for this command"]],
    "f59_standing_later": [["press", GIT_LABEL]],
    "f60_menu_all": [["press", "CoCo menu"]],
    "f61_granted_list": [["press", "CoCo menu"], ["press", "Without asking"]],
    "f63_query_result": [["press", SQL_STEP]],
    "f64_query_none": [["press", SQL_STEP]],
    "f65_larger": [["press", "Open larger"]],
    "f66_larger_request": [["press", "Open larger"]],
    "f68_data_json": [["press", "Show as JSON"]],
    "f69_code": [["press", "Copy code"]],
    "f71_files_chosen": [
        ["attach", [["timesheets_2026-W41.csv", 48000], ["steering_notes.pdf", 1200000]]]
    ],
    "f72_file_refused": [
        [
            "attach",
            [
                ["timesheets_2026-W41.csv", 48000],
                ["steering_recording.mp4", 86000000],
                ["budget_export.xlsb", 20000],
            ],
        ]
    ],
    "f74_drop": [["dragover"]],
    "f75_page_request": [["press", "Show full request"]],
    "f78_prompt_fill": [["press", "Count the rows of a table"]],
    "f81_session_details": [["press", "CoCo menu"], ["press", "Session details"]],
    "f84_profile_files": [["press", "Snowflake profile"]],
    "f85_raw_details": [["press", GIT_LABEL]],
    "f86_reasoning": [["press", "What CoCo considered"]],
}
CLOSED = {"f46_question_pill", "f53_plan_pill"}
TYPING.update(
    {
        "f71_files_chosen": "Compare these with last week",
        "f72_file_refused": "Compare these with last week",
    }
)
# states the contract allows and the sheet does not draw (no frame number): kept so that the validator and the window meet them
VIEWS["files_sending"] = view(
    "working",
    [
        {
            "kind": "user",
            "id": "u1",
            "text": "Compare these with last week",
            "files": ["timesheets_2026-W41.csv", "steering_notes.pdf"],
            "sending": 2,
        }
    ],
    attach=FILES_OK,
)
VIEWS["question_expired"] = view(
    "ready", [RM_Q, {"kind": "asked", "id": "n1", "text": Q_WEEK, "note": "Expired"}]
)
VIEWS["question_cancelled"] = view(
    "ready", [RM_Q, {"kind": "asked", "id": "n1", "text": Q_WEEK, "note": "Cancelled"}]
)
VIEWS["plan_expired"] = view(
    "ready",
    [
        PLAN_Q,
        step(
            "s1",
            "no",
            "The plan CoCo proposed",
            tool=None,
            input={},
            note="Expired",
            reason="Not answered within ten minutes. Nothing was done.",
            blocks=[{"type": "text", "text": plan_text(PLAN4)}],
        ),
    ],
)


# The frames of the playground are drawn by a host that switched everything on (Features.all()):
# its views say the page may be read for the context of a message (view key `page_text`).
_ALL_ON = {"files_sending", "question_expired", "question_cancelled", "plan_expired"}
for _name, _view in VIEWS.items():
    if (_name[:1] == "f" and _name[1:2].isdigit()) or _name in _ALL_ON:
        _view["page_text"] = True


def assert_same_shape(test, actual, expected, path: str = "view") -> None:
    """For the runtime packages: a view the conversation produced has the shape of the fixture of its frame. Same keys at every
    level, same type for every value that is not None (ids, texts and numbers differ), lists compared item by item as far as both go."""
    if isinstance(expected, dict):
        test.assertIsInstance(actual, dict, path)
        test.assertEqual(set(actual), set(expected), path)
        for key in expected:
            assert_same_shape(test, actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        test.assertIsInstance(actual, list, path)
        for number, (one, other) in enumerate(zip(actual, expected)):
            assert_same_shape(test, one, other, f"{path}[{number}]")
    elif actual is not None and expected is not None:
        test.assertIs(type(actual), type(expected), path)
