# Ask CoCo: the window becomes the package's interface (0.2.0)

Status: released in `0.2.0` (2026-10-20); the window is opt-in. The 0.1.9 chat family
(`chat`, `panel`, `copilot_rail`) is the default again. Pass `mini=True` to one of those, or call
`ask_coco(cwd)`, to mount the floating window. The sheet below is the other developer's record of
the window; where it says the chat family is removed, the code on this branch keeps it.

Original status: decided 2026-10-13, branch `feat/ask-coco-window`. Every decision below was taken by the
implementer, with its reason, for Laurent and the client to read and overturn where they disagree. Decisions already
taken by the client are marked **(client)** and are not reopened here.

At hand-over this file was checked against the code. What it changed is marked **[changed]**; the list of what the
first draft got wrong is in section 7. Where the two disagree, the code is the truth for signatures.

## What

Design deliverable: [canvas and consultation guide](design/README.md), with all 86 frames and the two host-page views.

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
| `coco.ask(label, text=None, *, key=None) -> bool` | A button of the page asks CoCo in the user's name. The thread shows `label`, CoCo receives `text` (`label` when none). `key` defaults to `label` **[changed]**. Sent when connected, shown as waiting until then. It reruns the page once, so it belongs behind a button: called on every run it would loop **[changed]**. A structured answer is the session's (`options=CocoOptions(output_schema=...)`) | `copilot_rail(job=…)`, `send_prompt` |
| `coco.result(key) -> dict \| None` | `{"text", "data"}` of the request sent with `coco.ask(..., key=key)`, `None` until it has finished, handed over once; `data` is the session's structured output (the payload itself), else `None` | `on_structured_output`, `on_job_finished` |
| `coco.form(title, fields, *, key) -> dict \| None` | A form asked by the application, answered in the window; needs no agent and no connection. Call it on every run: it asks once per `key`. `None` until answered or skipped, then once `{"skipped": False, "values": {field id: text}}`, or `{"skipped": True, "values": {}}` when skipped; afterwards `None` again, never re-asked (a new question needs a new key). It reruns the page when it first asks **[changed]** | `request_input` |
| `coco.open(drafts=None)` | Opens the window, optionally with prepared texts (one bubble each, with Copy, no agent call) | none |
| `coco.notice(text, *, action=None)` | One line in the thread in the application's words | toast of the rail |
| `coco.latest_answer -> str` | The latest answer's text, for a page that shows it elsewhere | `get_latest_assistant_text` |
| `coco.new()` / `coco.disconnect()` | End the conversation / the session | `reset_session`, `stop_session` |
| `coco.conversation` | The conversation object (view and actions as plain data), for an application that builds its own surface or runs with no browser | `render_transcript`, `approve_pending` |

**[changed] What a host must know about the calls:**

- `ask` and `form` rerun the page. `ask` belongs behind a button.
- A page button runs after `ask_coco(cwd)` in the script, so a button that changes the folder takes a second run to take effect.
- `options` is read when a session connects, and the object given on the first run of a browser session is the one used. A new object on a later run is ignored. `cwd`, `policy`, `prompts`, `features`, `context`, `theme` and the `window.*` labels are read on every run; the `agent.*` labels, once.
- A policy function that raises falls back to the default folder policy, and the error is logged.
- Files attached in the field are saved when the message is sent, in `<cwd>/_coco_uploads/<id>/`, and the policy lets the agent read those files only.
- A relative `cwd` is resolved from the folder the server was started in. The package neither creates the folder nor checks it exists; with the scripted agent a missing folder connects and reads fail as failed steps.
- While a request waits, what is typed is queued behind it ("Queued", "Take back") until Allow or Decline.
- `get_window(key)` raises `CocoError` until `ask_coco` has run with that key in this browser session.

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
| `FolderPolicy(folder, *, scope=None, also_read=(), commands=(), changes=None, sql=False, lookups=False, standing=False)` | The default. Reading tools inside `scope` (default: `folder`) are free; every other call asks, each time, as a change. A shell command and a file change always show their exact command or file and text; any other tool shows its whole input unless a piece below recognises it. The few sentences it writes are in `FolderPolicy.words`, for a host to replace |
| `also_read=` folders | Read freely besides the scope, with the same hardening (a guidelines folder, an output folder). Reading only: a change there asks as outside the scope |
| `inside(base, scope, raw) -> None \| "outside" \| "odd"` | A path placed as Cortex Code resolves it, with the Windows hardening (streams, drive-relative paths, trailing dots, device names, links followed): a spelling the app cannot place never counts as inside |
| `is_secret_name(name)` | `.env*`, `*.pem`, `*.p8`, `*.key`, `*.pfx`, `id_rsa*`, `connections.toml`, names holding `credential` or `secret`; reads and searches that would cover one ask |
| `Command(name, argv, reads, platform=sys.platform)` | One exact command line with its plain name: compared character for character, shown as a read under that name. `.line` is the line for that platform's shell, and `None` when the shell would expand an argument: such a command is never listed |
| `git_readonly(repo) -> [Command]` | status, diff and log with the options that stop a repository's own settings from running a program; none when `repo` is not a repository of its own |
| `changes=` a function `(path) -> None \| reason`, or glob patterns | Which files a change is ordinary for (default: any file inside the scope); others ask, say what is unusual and are never offered a standing permission |
| `sql=True` | A SQL call shows its exact statement, is told apart as a query (surely one reading statement: shown as a read, "Allow a query?") or a statement (anything else: shown as a change) **[changed]**, and shows any other input (a connection, a timeout) under "Other inputs" |
| `lookups=True` | The known read-only tools of Cortex Code (object search, table lookup, semantic views, documentation, web) are shown as reads, with where the question goes |
| `standing=True` | Each request offers its family as a standing permission until the conversation ends. The offer reads "Do not ask again for" followed by: commands; changes in this folder; queries that only read; SQL statements; the tool's name; reading outside the working folder **[changed]**. "File changes" never covers the `.git` folder, a secret-named file or a place `flag` marks: those ask each time |

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
    queue=True, steps=True, motion=True, copy=True,          # comfort: on (steps=False keeps failed and refused steps)
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

`Features(steps=False)` hides the cards of steps that went well and keeps the failed and refused ones, and the sentences CoCo said **[changed]**. `display` accepts only `latest`, `shorten` and `raw`; another value raises `ValueError`.

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
  The default font is Montserrat, shipped in the package under its OFL licence; `theme={"font": "inherit"}` is meant to use the
  host's. **Observed 2026-10-20 on Streamlit 1.60.0:** the window's host element does not pass the page font down (it renders in the browser's serif), so name the page's font instead, as `examples/modern_chat` does (roadmap).

**[changed]** Defaults: `accent` #5498FF, `on-accent` #16181D, `surface` #FFFFFF, `text` #3C3C3A, `muted` #6E6E6B, `border` #E8E6E1, `danger` #F8485E, `font` Montserrat, system-ui, sans-serif, `radius` 1rem, `avoid` none.

*Reason for shipping a font:* "same presentation by default" (client). The sheet is set in Montserrat; without it
the window's measures (pills as wide as their label) differ from the approved frames.

### 1.6 Testing

`streamlit_coco.testing`: `ScriptedAgent` (goes through the real policy and the real gate, one keyword per state of
the sheet), `VIEWS` (one view per frame), `harness` (one HTML file that mounts the real window on any view, no
server). Setting `STREAMLIT_COCO_AGENT=mock` runs any application on the scripted agent, with no Snowflake login.

### 1.7 What stays public from 0.1.9, unchanged

`CocoOptions`, `CocoSession`, `CocoRunStatus`, `CocoChatResult`, `get_session`, `query`, `CocoEvent`,
`events_to_dataframe`, the errors, `check_environment`, `require_environment`, `CocoEnvironment` and the Snowflake file
helpers, `upload_to_cwd`, `list_cwd_uploads`, `format_upload_prompt`, `sanitize_upload_name`, the `DEFAULT_*` upload
constants, `UploadedPath`, `cwd_uploader` (in `uploader.py`), `render_output_field` (takes the handle; shows text
only), `app_viewer` and the preview helpers, `tool_family`, `is_sql_tool`, `is_ask_user_question`,
`is_exit_plan_mode` **[changed]**.

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
| `render_output_field` | kept, first argument is the handle; shows the text only (no tool cards, copy button or status line) | `render_output_field(coco, text_renderer=...)` |
| `get_latest_assistant_text(session)` | removed | `coco.latest_answer` |
| `get_or_create_session`, `reset_session`, `stop_session` | removed | the window owns its session; `coco.new()`, `coco.disconnect()` |
| `is_debug_mode` | removed | `Features(display=("raw",))` |
| `CocoOptions.allowed_tools`, `.disallowed_tools`, `.require_approval_for` | kept for `CocoSession` and `query`; refused by `ask_coco` | a `policy` |
| `show_tool_details=False`, `show_copy=False`, `show_thinking=True` | `Features(steps=False)`, `Features(copy=False)`, `Features(reasoning=True)` | |
| `text_renderer=` on `panel` | on `render_output_field` only | the window draws Markdown itself |
| `cwd_uploader` (now in `uploader.py`), `upload_to_cwd`, `app_viewer`, preview helpers | kept | nothing; `on_fix=` calls `coco.ask("Fix with CoCo", prompt)` |
| `CocoSession`, `query`, events, errors, diagnostics | kept | nothing. A `CocoSession`'s own approvals are answered with `session.permission_manager.resolve(request_id, approved=...)` |
| `CocoRunStatus`, `CocoChatResult`, `get_session` | kept | nothing |
| `CocoEvent`, `events_to_dataframe`, `CocoOptions` | kept | nothing, apart from the three refused lists above |
| `check_environment`, `require_environment`, `CocoEnvironment`, `list_snowflake_toml_files`, `list_snowflake_connections`, `resolve_snowflake_config_path`, `default_snowflake_connection_name` | kept | nothing |
| the exceptions (`CocoError` and its subclasses) | kept | nothing |
| `upload_to_cwd`, `list_cwd_uploads`, `format_upload_prompt`, `sanitize_upload_name`, `UploadedPath`, `DEFAULT_ALLOWED_EXTENSIONS`, `DEFAULT_MAX_BYTES`, `DEFAULT_UPLOAD_SUBDIR` | kept | nothing |
| `start_app_preview`, `stop_app_preview`, `preview_running`, `preview_url`, `last_preview_exception`, `preview_log_tail`, `default_fix_prompt` | kept | nothing |
| `tool_family`, `is_sql_tool`, `is_ask_user_question`, `is_exit_plan_mode` | kept | nothing |
| (new) `ask_coco`, `get_window`, `Features`, `Attachments`, `Gate`, `policy` | added | see section 1 |

## 3. The no-regression table

Rows are those of the inventory (`COCO_PACKAGE_FEATURES.md` section 1). "Proved by" names a test (file and name) or an
example that exists in this repository **[changed]**. A test file is `tests/test_<name>.py`; **e2e** is `tests/e2e/`, run by
`make e2e` in Edge on the scripted agent. "Not proved" means no test and no recorded run covers it. An example named
alone is code that shows the feature; no test runs it. Nothing here was proved against a live Cortex Code agent: see
[`test-checklist.md`](test-checklist.md).

| # | Capability | After the migration | Proved by |
|---|---|---|---|
| 1 | Type, send, see the answer arrive | window | e2e `test_walk_of_the_default_window` |
| 2 | Thinking before the first word | window (dots) | not proved: no test or run looks at the dots |
| 3 | Stop a run | window | e2e walk (Stop); `test_scripted` `test_stop_while_a_request_is_pending` |
| 4 | Type while connecting or working | window, wider: queued, can be taken back | e2e walk (Queued, Take back); `test_extras` `test_typed_ahead_waits_for_the_connection` |
| 5 | Formatted answers, fenced code | window | fenced code: e2e `test_code_block_has_its_own_copy`; Markdown formatting is not proved |
| 6 | Copy answer, code, table, JSON; copy off | window; `Features(copy=False)` | answer and code: e2e `test_code_block_has_its_own_copy`; table, JSON and copy off: not proved |
| 7 | One card per tool call | window (steps) | `test_conversation` `test_a_step_is_named_by_the_policy_and_keeps_tool_input_and_result`; e2e walk |
| 8 | SQL result as a table with its row count | window (data block) | `test_extras` `test_a_query_result_becomes_a_step_block_with_its_count`; `test_scripted` `test_sql_results_are_tables_and_a_standing_permission_covers_the_next_query` |
| 9 | File change as before / after | window ("Show change") | `test_scripted` `test_an_edit_of_an_existing_file_shows_the_change` |
| 10 | Tool detail on or off | `Features(steps=...)` | `test_conversation` `test_steps_off_keeps_the_sentences_and_what_failed_but_not_the_cards` |
| 11 | Approve once / Deny with a preview | window (Allow / Decline) | e2e walk (Allow, Decline); `test_gate` `test_the_hook_waits_for_the_window_then_returns_an_explicit_decision` |
| 12 | Always allow | policy `standing=True` | `test_gate` `test_an_allow_with_the_tick_grants_the_family_and_says_so`; `test_waits` `test_allow_with_standing_passes_the_family_on_and_the_grant_is_listed_and_said` |
| 13 | Unanswered request refused after 10 minutes | gate ("Expired") | `test_gate` `test_a_request_left_unanswered_expires_as_a_decline` |
| 14 | A question from CoCo | window | `test_scripted` `test_a_question_with_one_choice_is_answered_and_kept_in_the_thread` |
| 15 | A form asked by the application | `coco.form` | `test_window` `FormTest`; `test_scripted` `test_a_long_form_is_answered_with_its_fields`. The `coco.form` call itself is used by `examples/bi_to_semantic`; no test runs it |
| 16 | Plan mode | `Features(planning=True)` | `test_scripted` `test_a_plan_is_approved_then_carried_out_and_declined_with_a_reason` |
| 17 | Switch plan mode on | menu line | `test_scripted` `test_plan_first_answers_without_acting_and_carry_out_goes_on` |
| 18 | Structured output | `options=CocoOptions(output_schema=...)`, `coco.ask(label, text, key=...)` then `coco.result(key)`, data block | `test_window` `test_result_keeps_the_key_asked_while_pending_and_hands_over_once`; `test_scripted` `test_structured_answers_code_and_raw_details`. `examples/structured_output.py` is run by no test, and the real `output_schema` path is live only |
| 19 | Attach files in the field | `Features(attachments=...)` | e2e `test_attached_file_lands_in_the_folder`; `test_extras` `test_a_file_is_saved_in_the_working_folder_and_named_to_the_agent` |
| 20 | Uploader on the page | `cwd_uploader`, unchanged | e2e `test_page_cwd_uploader`; `tests/test_upload.py` |
| 21 | Example questions, sending or filling | `prompts=` | sending: `test_conversation` `test_prompts_are_at_most_three_and_only_on_the_first_screen`; filling: only the fixture `f78_prompt_fill`, not proved in the browser |
| 22 | Jobs queued by the application | `coco.ask` | `test_extras` `test_a_request_before_connecting_waits_then_goes_and_its_result_is_handed_once` |
| 23 | Skill picker | page form of the example, then `coco.ask` | `examples/backlog_desk` only; `test_backlog_desk` tests the skill data, not the window: not proved |
| 24 | Test-prompt picker | sidebar of the example, then `coco.ask` | `examples/chat_app.py` only: not proved |
| 25 | Last messages / first n characters | `Features(display=("latest", "shorten"))` | latest: e2e `test_latest_exchange_only`; `test_extras` `test_latest_only_hides_earlier_messages_and_show_earlier_brings_them_back`; shorten: not proved |
| 26 | Output mode "Field" | "Latest exchange only"; in the page: `render_output_field` | `test_display` `test_render_output_field_shows_latest_answer`; e2e `test_latest_exchange_only` |
| 27 | Debug mode | `Features(display=("raw",))` | `test_extras` `test_raw_details_reach_steps_only_when_on_and_the_agent_is_told` |
| 28 | Thinking shown | `Features(reasoning=True)` | `test_scripted` `test_reasoning_is_sent_and_shown_only_when_the_host_asks` (0.1.9 showed nothing) |
| 29 | Start gate | nothing starts before Connect | `test_conversation` `test_nothing_is_sent_when_not_connected`; e2e (the walk connects first) |
| 30 | Environment status | window when missing; Session details when well | `test_conversation` `test_not_installed_and_not_connected_and_connecting_and_ready`; `test_scripted` `test_setup_and_profiles_states_can_be_reached` |
| 31 | Connection: file, profile, connect, disconnect | window | `test_extras` `test_connect_passes_the_chosen_file_and_a_restart_keeps_it`; `test_conversation` `test_disconnect_ends_the_conversation`. A real connection: live checklist only |
| 32 | Starting, failed start | window | `test_conversation` `test_connect_failed_says_why_and_stays_not_connected`; `test_scripted` `test_a_connection_fails_with_a_message_and_a_wrong_file_is_said` |
| 33 | Status, model, session facts | steps, pill, Session details | `test_scripted` `test_session_details_and_the_connection_files`; `test_extras` `test_session_facts_without_secrets_only_when_ready_and_asked_for` |
| 34 | Clear chat, reset, close | New conversation, Minimise, Disconnect | New conversation: e2e walk; Disconnect: `test_conversation` `test_disconnect_ends_the_conversation`; Minimise: not proved |
| 35 | Which tools run without asking (pills) | sidebar of the example, building a `FolderPolicy` | `examples/chat_app.py` (`PillPolicy`) only: not proved |
| 36 | App preview | `app_viewer`, unchanged; Fix through `coco.ask` | helpers: `tests/test_app_viewer.py`; the Fix wiring through `coco.ask` (`examples/app_builder`, `examples/bi_to_semantic`): not proved |
| 37 | "CoCo is cooking", "Awaiting approval" on the page | launcher's arc and pill | the pill in the view: `test_conversation` `test_answer_pill_until_seen`; the arc drawn in the browser: not proved |
| 38 | A result handed to the page | `coco.result`, `coco.notice` | `test_window` `test_result_keeps_the_key_asked_while_pending_and_hands_over_once`; `test_extras` `test_a_notice_button_runs_its_function_once` |
| 39 | Host texts | `labels=`, `prompts=` | `test_window` `test_a_host_override_reaches_the_window_and_the_conversation`; `test_conversation` `test_prompts_are_at_most_three_and_only_on_the_first_screen` |

## 4. Floor versions

| Dependency | Required | Verified on | Below the floor |
|---|---|---|---|
| Python | 3.10 | 3.12 | pip refuses the install |
| Streamlit | 1.55, written in `pyproject.toml` **[changed]** | the window: a five-line app on 1.53.0 and 1.65.0; the package: the browser tests on 1.55.0 and 1.60.0, the unit tests on 1.60.0 (on 1.55.0 all but three `AppTest` mounts of the window pass; those need 1.59). `copilot_rail` needs `st.popover(key=)`, new in 1.55, so 1.53 and 1.54 are below the floor | pip refuses the install. If an older Streamlit is forced, `ask_coco` raises one `CocoError` naming the version needed, before drawing anything |
| Cortex Code Agent SDK | 1.0.7, an optional extra: `streamlit-coco[sdk]` **[changed]** | 1.0.7 | Not installed: the window says so and shows the command; the scripted agent still works |
| Cortex Code program | none enforced | read from 1.1.104 | A program cannot be pinned from a Python package. The rights fail safe: a tool or an input the policy does not know asks, as a change, with its whole input. Session details show the program's version; the documentation says which one was read |

*Reason for finding the Streamlit floor by a run and not by reading release notes:* the window uses the new component
API in a fragment, with isolated styles; only a run says whether a version holds it. 1.53 is the lowest version tried for the window alone; the package as a whole needs 1.55 (the rail).

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
  still work for `CocoSession` and `query` used without the window; answer them with
  `session.permission_manager.resolve(request_id, approved=...)`. The window does not use them. *Reason:* removing
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
- **No public tag or PyPI upload in the design pass.** `0.2.0` was later cut in the development repo only (2026-10-14), still without a public tag.

## 7. Where the first draft disagreed with the code

Found when this file was checked against the code (the code stands; the text above is corrected):

- The standing permission's labels were written "Commands", "File changes", "Queries", "Statements", "Reading elsewhere".
  The code writes "Do not ask again for commands / changes in this folder / queries that only read / SQL statements /
  the tool's name / reading outside the working folder".
- A SQL query is shown as a read ("Allow a query?"); only a statement is a change.
- The Agent SDK was said to be required by pip. It is an optional extra (`streamlit-coco[sdk]`).
- The Streamlit row said 1.64.0 was verified and that a run found the floor. Only 1.53.0 and 1.65.0 were driven.
- `coco.ask`'s `key` defaults to `label` (the table said `None`).
- `cwd_uploader` was listed without its module (`uploader.py`); `Gate`, `CocoRunStatus`, `CocoChatResult` and
  `get_session` were missing from the public lists; `render_output_field` was not said to show text only.

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
