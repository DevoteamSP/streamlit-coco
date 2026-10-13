# Ask CoCo: the window becomes the package's interface (0.2.0)

Status: decided 2026-10-13, branch `feat/ask-coco-window`, not released. Every decision below was taken by the
implementer, with its reason, for Laurent and the client to read and overturn where they disagree. Decisions already
taken by the client are marked **(client)** and are not reopened here.

## What

Ask CoCo is a floating chat window opened from a launcher at the bottom right of the page, in front of a Cortex Code
agent. It was designed (86 frames, approved), built and verified in the Spec-First Cockpit. This migration moves it
into `streamlit-coco`, where it replaces the chat family (`chat`, `panel`, `copilot_rail` and their helpers).

```python
import streamlit as st
import streamlit_coco as st_coco

st.title("My app")
st_coco.ask_coco(".")
```

That call gives the launcher, the window and every state of the design sheet, styles and marks included.

## Why

- **One interface (client).** Laurent, author of both, prefers this presentation and these features. Two chat
  interfaces in one package would be two sets of rights, two transcripts and two test suites to keep true.
- **No regression (client).** Everything a user of 0.1.9 can do stays possible (section 3).
- **The Cockpit becomes a client like any other**, so what it proved (rights attacked as a prompt-injected agent
  would, the live-run findings on Cortex Code) is kept by one code base instead of two.

## 1. The public interface

Small on purpose: once published it binds. Everything not named in this section is private.

### 1.1 The one call

```python
coco = st_coco.ask_coco(
    cwd=".",              # the agent's working folder; the only argument a first app needs
    *,
    key="coco",           # one window per key and per browser session
    policy=None,          # a Policy, or a function (context) -> Policy; None: FolderPolicy(cwd)
    context=None,         # a function () -> dict, called when a message is sent
    features=None,        # a Features; None: Features() (comfort on, the rest off)
    prompts=None,         # first-screen prompts: [text | {"title", "text", "fill": bool}], at most three shown
    labels=None,          # {label key: text}, over streamlit_coco.labels.DEFAULT
    theme=None,           # {variable: value}, over the package's defaults
    options=None,         # a CocoOptions for model, connection, max_turns, mcp_servers, output_schema, cli_path
    on_files_changed=None,  # function ([path]) called once after the agent changed files, before the page reruns
    agent=None,           # a function (emit) -> agent; for tests and for another adapter
)
```

It returns the window's handle, and `st_coco.get_window(key="coco")` returns the same handle anywhere else on the
page:

| Member | What it does | Replaces |
|---|---|---|
| `coco.ask(label, text=None, *, key=None) -> bool` | A button of the page asks CoCo in the user's name. The thread shows `label`, CoCo receives `text`. Sent when connected, shown as waiting until then. It reruns the page once, so it belongs behind a button. A structured answer is the session's (`options=CocoOptions(output_schema=...)`) | `copilot_rail(job=…)`, `send_prompt` |
| `coco.result(key) -> dict \| None` | `{"text", "data"}` of the request sent with `coco.ask(..., key=key)`, handed over once; `data` is the session's structured output (the payload itself), else `None` | `on_structured_output`, `on_job_finished` |
| `coco.form(title, fields, *, key) -> dict \| None` | A form asked by the application, answered in the window; needs no agent and no connection. Call it on every run: it asks once per `key`. `None` until answered or skipped, then once `{"skipped": False, "values": {field id: text}}`, or `{"skipped": True, "values": {}}` when skipped; afterwards `None` again, never re-asked (a new question needs a new key) | `request_input` |
| `coco.open(drafts=None)` | Opens the window, optionally with prepared texts (one bubble each, with Copy, no agent call) | none |
| `coco.notice(text, *, action=None)` | One line in the thread in the application's words | toast of the rail |
| `coco.latest_answer -> str` | The latest answer's text, for a page that shows it elsewhere | `get_latest_assistant_text` |
| `coco.new()` / `coco.disconnect()` | End the conversation / the session | `reset_session`, `stop_session` |
| `coco.conversation` | The conversation object (view and actions as plain data), for an application that builds its own surface or runs with no browser | `render_transcript`, `approve_pending` |

*Reason for a handle and not more arguments:* what a page does to the window happens at another time and place than
where the window is mounted (a button in a page body, the window in the shell).

*Reason `policy` and `context` may be functions:* the Cockpit's rights depend on the project open when the message is
sent; a policy built once at mount cannot say that. The function is called once per message and its result is frozen
with the message, so navigation afterwards moves nothing.

`options` refuses `allowed_tools`, `disallowed_tools` and `require_approval_for` with a `ValueError` naming `policy`:
the window sends the program no tool list (every call reaches the gate), so those lists would be silently ignored.

### 1.2 Rights: the policy

```python
class Policy(Protocol):
    def judge(self, tool: str, payload) -> tuple[str | None, dict | None]:
        """(why the call is refused, the request to show). Both None: the call is free. Never raises."""
    def describe(self, tool: str, payload) -> str:
        """The step's name, in plain words."""
    def rights(self, granted=()) -> dict:
        """What the agent is told it may do, generated from the same rules."""
```

The request is a plain dict written by the application from the checked call, never from the agent's description:
`{kind: "read" | "change", question, where, reads, changes, evidence_label, evidence, pill, standing}`
(`pill` is what the closed launcher says: "Allow a read?").
`streamlit_coco.policy.request(...)` builds one, so a custom policy cannot misspell it.

Ready-made, in `streamlit_coco.policy`:

| Piece | What it gives |
|---|---|
| `FolderPolicy(folder, *, scope=None, commands=(), changes=None, sql=False, lookups=False, standing=False)` | The default. Reading tools inside `scope` (default: `folder`) are free; every other call asks, each time, as a change. A shell command and a file change always show their exact command or file and text; any other tool shows its whole input unless a piece below recognises it. The few sentences it writes are in `FolderPolicy.words`, for a host to replace |
| `inside(base, scope, raw) -> None \| "outside" \| "odd"` | A path placed as Cortex Code resolves it, with the Windows hardening (streams, drive-relative paths, trailing dots, device names, links followed): a spelling the app cannot place never counts as inside |
| `is_secret_name(name)` | `.env*`, `*.pem`, `*.p8`, `*.key`, `*.pfx`, `id_rsa*`, `connections.toml`, names holding `credential` or `secret`; reads and searches that would cover one ask |
| `Command(name, argv, reads, platform=sys.platform)` | One exact command line with its plain name: compared character for character, shown as a read under that name. `.line` is the line for that platform's shell, and `None` when the shell would expand an argument: such a command is never listed |
| `git_readonly(repo) -> [Command]` | status, diff and log with the options that stop a repository's own settings from running a program; none when `repo` is not a repository of its own |
| `changes=` a function `(path) -> None \| reason`, or glob patterns | Which files a change is ordinary for (default: any file inside the scope); others ask, say what is unusual and are never offered a standing permission |
| `sql=True` | A SQL call shows its exact statement, is told apart as a query (surely one reading statement) or a statement (anything else), and shows any other input (a connection, a timeout) under "Other inputs" |
| `lookups=True` | The known read-only tools of Cortex Code (object search, table lookup, semantic views, documentation, web) are shown as reads, with where the question goes |
| `standing=True` | Each request offers its family ("Commands", "File changes", "Queries", "Statements", a tool, "Reading elsewhere") as a standing permission until the conversation ends. "File changes" never covers the `.git` folder, a secret-named file or a place `flag` marks: those ask each time |

`FolderPolicy` has two documented extension points for a host with rules of its own, used by the Cockpit:
`flag(parts) -> None | (key, words)` (one more reason a place is not read freely: the Cockpit's budget files for a
member) and overriding `commands()` (commands that depend on the request: the Cockpit's audit line for the open
project).

`streamlit_coco.Gate` is the pre-tool decision that waits for the window: expiry after ten minutes as a decline, the
first answer stands, the call is judged again after Allow and must still be what was shown, standing permissions.
It is public for whoever writes another adapter; a host never needs it.

**The default is the safest, not the richest (client).** Without a policy: reading inside the working folder is
free, and every other call asks each time. The pieces that widen rights or recognise more (`commands`, `changes`,
`sql`, `lookups`, `standing`) are off until the host switches them on.

*Decision: with `sql=False` a SQL call is not refused; it asks, as a change, with its whole input.* The client's
sentence for the default is "reading inside the working folder is free and everything else asks". Refusing would be
safer still but would make the default window unable to do what `chat_app.py` does today behind an approval.

### 1.3 Features

```python
st_coco.Features(
    queue=True, steps=True, motion=True, copy=True,          # comfort: on
    page_text=False,        # each message carries the text the page shows (more data leaves the browser)
    page_exclude=(),        # CSS selectors left out of that text
    attachments=None,       # Attachments(multi=True, accept=[...], max_mb=10): files saved in the working folder
    planning=False,         # the menu offers "Plan first"
    display=(),             # which menu switches exist: "latest", "shorten", "raw"
    session_details=False,  # the menu offers Session details
    reasoning=False,        # CoCo's reasoning as a fold among the steps
    download_csv=False,     # Download CSV in the wider table view
)
st_coco.Features.all()      # everything on: the playground
```

**Everything is optional for the host (client).** A feature appears only when the host supplies its data or
switches it on; a host that uses none sees no trace of it. Standing permission is not here: it is a right, so it is
the policy's (`standing=True`). Questions and plans from CoCo have no switch: the agent decides to ask, and an
unanswerable question would block it.

### 1.4 Context

`context()` returns a plain dict of what the application knows when the message leaves. It is data for the agent and
for a policy function, never authorisation. Three keys have a meaning for the window, all optional:

| Key | Meaning |
|---|---|
| `scope` | `{"name", "folder"}`: what the request is about. The thread says "About <name>" when it changes; a request shows it as "where" |
| `instructions` | text added to what the agent is asked in every request |
| `user` | `{"name", "language"}` |

Everything else is passed to the agent as facts. The window adds `screen` (page text, open dialog, selection) only
when `Features.page_text` is on, and `rights` from the policy.

### 1.5 Labels and theme

- `streamlit_coco.labels.DEFAULT` is one table of every sentence the window and the conversation write, in English,
  by key. `labels=` overrides any of them; a translation is a dict. Texts written by a policy (the request's
  question, a command's plain name) are the policy's own.
- The theme is a set of CSS variables with the sheet's values as defaults: `accent`, `on-accent`, `surface`, `text`,
  `muted`, `border`, `danger`, `font`, `radius`, and `avoid` (selectors of the page the launcher must not cover).
  The default font is Montserrat, shipped in the package under its OFL licence; `theme={"font": "inherit"}` uses the
  host's.

*Reason for shipping a font:* "same presentation by default" (client). The sheet is set in Montserrat; without it
the window's measures (pills as wide as their label) differ from the approved frames.

### 1.6 Testing

`streamlit_coco.testing`: `ScriptedAgent` (goes through the real policy and the real gate, one keyword per state of
the sheet), `VIEWS` (one view per frame), `harness` (one HTML file that mounts the real window on any view, no
server). Setting `STREAMLIT_COCO_AGENT=mock` runs any application on the scripted agent, with no Snowflake login.

### 1.7 What stays public from 0.1.9, unchanged

`CocoOptions`, `CocoSession`, `query`, `CocoEvent`, `events_to_dataframe`, the errors, `check_environment` and the
Snowflake file helpers, `upload_to_cwd`, `cwd_uploader`, `app_viewer` and the preview helpers, `tool_family`,
`is_sql_tool`, `is_ask_user_question`, `is_exit_plan_mode`.

## 2. The migration sheet: what each old public name becomes

| 0.1.9 | 0.2.0 | What to change in an application |
|---|---|---|
| `chat(...)` | removed | `ask_coco(cwd)` |
| `panel(session, ...)` | removed | `ask_coco(cwd)`; the window owns its session |
| `copilot_rail(session, ...)` | removed | `ask_coco(cwd, prompts=[...])`; `job=` becomes `coco.ask(label, text)`; `on_connect` / `on_disconnect` are not needed |
| `chat_input_bar` | removed | the window's field; `accept_file=` becomes `Features(attachments=Attachments(...))` |
| `send_prompt(session, text)` | removed | `coco.ask(label, text)` |
| `render_start_gate` | removed | nothing starts before the user presses Connect in the window |
| `render_environment_status` | removed | the window says what is missing; Session details shows versions when all is well. `check_environment()` stays for a page of your own |
| `render_session_status` | removed | the launcher's arc and pill, the steps |
| `render_transcript` | removed | the window's thread; `coco.conversation.view()` for a surface of your own |
| `render_approvals` | removed | the window's request, written from your policy |
| `approve_pending` / `deny_pending` | removed | `coco.conversation.act({"type": "allow" \| "decline", "id": ...})`; headless: the same on a `Conversation` |
| `render_plan_banner` | removed | the planning strip, with `Features(planning=True)` |
| `request_input` | removed | `coco.form(title, fields, key=...)` |
| `transcript_display_config`, `transcript_view_pills` | removed | `Features(display=("latest", "shorten"))` |
| `render_output_field` | kept, first argument is the handle | `render_output_field(coco, text_renderer=...)` |
| `get_latest_assistant_text(session)` | removed | `coco.latest_answer` |
| `get_or_create_session`, `reset_session`, `stop_session` | removed | the window owns its session; `coco.new()`, `coco.disconnect()` |
| `is_debug_mode` | removed | `Features(display=("raw",))` |
| `CocoOptions.allowed_tools`, `.disallowed_tools`, `.require_approval_for` | kept for `CocoSession` and `query`; refused by `ask_coco` | a `policy` |
| `show_tool_details=False`, `show_copy=False`, `show_thinking=True` | `Features(steps=False)`, `Features(copy=False)`, `Features(reasoning=True)` | |
| `text_renderer=` on `panel` | on `render_output_field` only | the window draws Markdown itself |
| `cwd_uploader`, `upload_to_cwd`, `app_viewer`, preview helpers | kept | nothing; `on_fix=` calls `coco.ask("Fix with CoCo", prompt)` |
| `CocoSession`, `query`, events, errors, diagnostics | kept | nothing |

## 3. The no-regression table

Rows are those of the inventory (`COCO_PACKAGE_FEATURES.md` section 1). Example codes: **CA** `chat_app.py`, **AG**
`approval_gate.py`, **SO** `structured_output.py`, **UP** `cwd_upload_chat.py`, **AB** `app_builder`, **BD**
`backlog_desk`, **BI** `bi_to_semantic`. "Proof" is filled in at hand-over with the check that was run.

| # | Capability | After the migration | Proved by |
|---|---|---|---|
| 1 | Type, send, see the answer arrive | window | CA |
| 2 | Thinking before the first word | window (dots) | CA |
| 3 | Stop a run | window | CA |
| 4 | Type while connecting or working | window, wider: queued, can be taken back | CA, UP |
| 5 | Formatted answers, fenced code | window | CA |
| 6 | Copy answer, code, table, JSON; copy off | window; `Features(copy=False)` | CA |
| 7 | One card per tool call | window (steps) | all |
| 8 | SQL result as a table with its row count | window (data block) | CA, BI |
| 9 | File change as before / after | window ("Show change") | CA, AB |
| 10 | Tool detail on or off | `Features(steps=...)` | CA |
| 11 | Approve once / Deny with a preview | window (Allow / Decline) | AG |
| 12 | Always allow | policy `standing=True` | AG |
| 13 | Unanswered request refused after 10 minutes | gate ("Expired") | unit test |
| 14 | A question from CoCo | window | CA (scripted) |
| 15 | A form asked by the application | `coco.form` | BI |
| 16 | Plan mode | `Features(planning=True)` | CA |
| 17 | Switch plan mode on | menu line | CA |
| 18 | Structured output | `options=CocoOptions(output_schema=...)`, `coco.ask(label, text, key=...)` then `coco.result(key)`, data block | SO, BI |
| 19 | Attach files in the field | `Features(attachments=...)` | UP |
| 20 | Uploader on the page | `cwd_uploader`, unchanged | UP, BI |
| 21 | Example questions, sending or filling | `prompts=` | AB, BI |
| 22 | Jobs queued by the application | `coco.ask` | AB, BI |
| 23 | Skill picker | page form of the example, then `coco.ask` | BD |
| 24 | Test-prompt picker | sidebar of the example, then `coco.ask` | CA |
| 25 | Last messages / first n characters | `Features(display=("latest", "shorten"))` | AB, BI |
| 26 | Output mode "Field" | "Latest exchange only"; in the page: `render_output_field` | CA |
| 27 | Debug mode | `Features(display=("raw",))` | CA |
| 28 | Thinking shown | `Features(reasoning=True)` | unit test (0.1.9 showed nothing) |
| 29 | Start gate | nothing starts before Connect | CA, UP |
| 30 | Environment status | window when missing; Session details when well | CA |
| 31 | Connection: file, profile, connect, disconnect | window | AB, BD, BI |
| 32 | Starting, failed start | window | scripted |
| 33 | Status, model, session facts | steps, pill, Session details | CA |
| 34 | Clear chat, reset, close | New conversation, Minimise, Disconnect | all |
| 35 | Which tools run without asking (pills) | sidebar of the example, building a `FolderPolicy` | CA |
| 36 | App preview | `app_viewer`, unchanged; Fix through `coco.ask` | AB, BI |
| 37 | "CoCo is cooking", "Awaiting approval" on the page | launcher's arc and pill | AB |
| 38 | A result handed to the page | `coco.result`, `coco.notice` | BI, SO |
| 39 | Host texts | `labels=`, `prompts=` | AB, BI |

## 4. Floor versions

| Dependency | Required | Verified on | Below the floor |
|---|---|---|---|
| Python | 3.10 | 3.12 | pip refuses the install |
| Streamlit | the lowest version on which the harness and the package's browser tests pass, found by running them from 1.53 upward; written in `pyproject.toml` | 1.64.0 | pip refuses the install. If an older Streamlit is forced, `ask_coco` raises one `CocoError` naming the version needed, before drawing anything |
| Cortex Code Agent SDK | 1.0.7 | 1.0.7 | pip refuses the install |
| Cortex Code program | none enforced | read from 1.1.104 | A program cannot be pinned from a Python package. The rights fail safe: a tool or an input the policy does not know asks, as a change, with its whole input. Session details show the program's version; the documentation says which one was read |

*Reason for finding the Streamlit floor by a run and not by reading release notes:* the window uses the new component
API in a fragment, with isolated styles; only a run says whether a version holds it.

## 5. How the Cockpit depends on the package before a release

The package is not pushed, so the Cockpit cannot pin a version or a commit address. `make cockpit` installs a wheel
built from this branch and committed in `spec-first/cockpit/vendor/`, and `COCO_PKG=<path>` on the command line
installs a working copy instead (for whoever develops both). Someone who switches to the Cockpit's branch gets
everything with `make cockpit`, as today. At the release the wheel is deleted and the line becomes
`streamlit-coco[sdk]==0.2.0`.

*Rejected:* a path to a sibling checkout (breaks for anyone without it); copying the package's source into the
Cockpit (the two would drift, which is what this migration ends).

## 6. Left out, and why

- **`CocoSession`'s own approval list is not removed.** `require_approval_for` and the session's permission manager
  still work for `CocoSession` and `query` used without the window. The window does not use them. *Reason:* removing
  them rewrites the session for no user-visible gain; headless scripts keep working unchanged apart from the two
  removed top-level names.
- **No French labels shipped.** The table and the override exist; a translation is a host's dict. The Cockpit is in
  English.
- **Moving or resizing the window, a conversation that survives a browser reload, a list of past conversations.**
  Out of scope in the Cockpit's feature file, unchanged here.
- **A second agent or provider.** `agent=` is the seam; only the Cortex adapter and the scripted agent exist.
- **MCP servers stay off unless `options.mcp_servers` is given.** Their calls then ask like any unknown tool. Not
  verified live.
- **The design sheet does not change**, and no frame is added for the package's own examples.
- **No release, tag or publication.** Version `0.2.0.dev0` on the branch.

## Limitations

- Verified on the scripted agent only. The live run needs a Snowflake login and is listed in
  [`test-checklist.md`](test-checklist.md).
- One window per page: two `ask_coco` calls with different keys draw two launchers at the same place.
- The window ignores the system's reduced-motion setting **(client)**; `Features(motion=False)` restores it.
- With the keyboard, Allow and Decline are reached with Shift+Tab from the field; a request that arrives under a
  Streamlit dialog cannot be clicked until the dialog is closed.

## Related

- The feature as decided for the Cockpit, every state and its reason: `spec-first/doc/features/cockpit-ask-coco.md`.
- The contract between window and conversation: the docstring of `streamlit_coco/conversation.py`.
- Checklist: [`test-checklist.md`](test-checklist.md).
