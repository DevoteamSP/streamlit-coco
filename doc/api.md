# API reference: streamlit-coco

Public surface of `import streamlit_coco as st_coco`, and of `streamlit_coco.policy` and `streamlit_coco.testing`. `0.2.1`: signatures may still move. Every signature below was read from the code.

**Related:** [README](../README.md) · [Ask CoCo feature file](features/ask-coco/ask-coco.md) (the decisions and their reasons) · [Local deployment](deployment/local.md) · [SDK docs](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)

The default UI is the 0.1.9 chat family: `chat`, `panel`, `copilot_rail`, and the helpers listed with them in `streamlit_coco.__all__` (`send_prompt`, `render_transcript`, `approve_pending`, …). The floating window on this page is off until `chat` / `panel` / `copilot_rail` is called with `mini=True`, or until `ask_coco(cwd)`. `copilot_rail(..., ask=True)` adds Minimize to the rail (off by default, so a 0.1.9 rail looks the same). `own_window=False` still shows Minimize and leaves the floating window to the page: mount `ask_coco(..., on_rail=ask_restore(key_prefix))` so the window header shows Restore.

Anything not named on this page is private, including the other modules of the package. Names of `streamlit_coco.__all__` that need Streamlit (`chat`, `panel`, `copilot_rail`, `ask_coco`, `get_window`, `cwd_uploader`, `render_output_field`, `app_viewer` and the preview helpers) load it on first use. The rest imports without Streamlit.

## Contents

| Section | Names |
| --- | --- |
| [The window](#the-window) | `ask_coco`, `get_window`, the handle |
| [Rights](#rights-streamlit_cocopolicy) | `policy`, `Policy`, `FolderPolicy`, `Command`, `git_readonly`, `request`, `inside`, `is_secret_name`, `Gate` |
| [Features](#features) | `Features`, `Attachments` |
| [Context](#context) | the keys of `context()` |
| [Labels and theme](#labels-and-theme) | `labels=`, `theme=` |
| [Callbacks](#callbacks) | every function you hand to the package |
| [The conversation](#the-conversation) | `coco.conversation`, the contract |
| [Page helpers](#page-helpers) | `render_output_field`, `cwd_uploader`, `upload_to_cwd`, `list_cwd_uploads`, `format_upload_prompt`, `sanitize_upload_name`, `DEFAULT_*`, `UploadedPath`, `app_viewer` and the preview helpers |
| [Options and session](#options-and-session) | `CocoOptions`, `CocoSession`, `CocoRunStatus`, `CocoChatResult`, `get_session` |
| [Headless](#headless) | `query`, `CocoEvent`, `events_to_dataframe` |
| [Environment and errors](#environment-and-errors) | `check_environment`, `require_environment`, `CocoEnvironment`, the Snowflake file helpers, the exceptions |
| [Tool helpers](#tool-helpers) | `tool_family`, `is_sql_tool`, `is_ask_user_question`, `is_exit_plan_mode` |
| [Testing](#testing) | `STREAMLIT_COCO_AGENT=mock`, `ScriptedAgent`, `VIEWS`, `harness`, `domdiff` |

---

## The window

### `ask_coco`

```python
def ask_coco(
    cwd: str | Path = ".",
    *,
    key: str = "coco",
    policy=None,
    context: Callable[[], dict] | None = None,
    features=None,
    prompts: list | None = None,
    labels: dict[str, str] | None = None,
    theme: dict[str, str] | None = None,
    options=None,
    on_files_changed: Callable[[list], Any] | None = None,
    agent: Callable | None = None,
    connection: str | None = None,
    on_rail: Callable[[], Any] | None = None,
) -> Window: ...
```

Mounts the launcher (bottom right) and the window, and returns the handle. Call it once per page run. It is cheap to call on every run: it keeps one conversation per `key` and per browser session.

| Argument | What it is |
| --- | --- |
| `cwd` | The agent's working folder, and the base of relative paths. A relative `cwd` is resolved from the folder the Streamlit server was started in (`~` is expanded). The folder must exist and be a directory; otherwise `ask_coco` raises `CocoError` before connecting, with either the real or scripted agent. The package does not create it. Changing it between runs ends the conversation and says why in the thread. |
| `key` | One window per key and per browser session. Two keys draw two launchers at the same place. |
| `policy` | A [`Policy`](#rights-streamlit_cocopolicy), or a function `(context) -> Policy` called once per message. `None` means `FolderPolicy(cwd)`. A function that raises falls back to that default, and the error is logged. |
| `context` | A function `() -> dict`, called when a message is sent. See [Context](#context). |
| `features` | A [`Features`](#features). `None` means `Features()`. |
| `prompts` | First-screen prompts. Each is a text, or `{"title", "text", "fill": bool}`. At most three are shown, only on the first screen. `fill: True` puts the text in the field instead of sending it. |
| `labels` | `{label key: text}` over [`labels.DEFAULT`](#labels-and-theme). May change between runs under the same key without resetting the conversation; existing thread text keeps its original language. |
| `theme` | `{variable: value}` over the defaults. See [Labels and theme](#labels-and-theme). |
| `options` | A [`CocoOptions`](#cocooptions): `model`, `connection`, `max_turns`, `mcp_servers`, `output_schema`, `cli_path`. The object you pass on the first run of a browser session is the one used, and it is read when a session connects. It refuses `allowed_tools`, `disallowed_tools` and `require_approval_for` with a `ValueError` that names `policy`. |
| `on_files_changed` | A function `([path]) -> Any`. See [Callbacks](#callbacks). |
| `agent` | A function `(emit) -> agent`, for tests and for another adapter. `None` gives the Cortex adapter, or the scripted agent when `STREAMLIT_COCO_AGENT=mock`. |
| `connection` | Snowflake profile name. When the window is not connected yet, it connects with this profile. The Copilot rail passes the profile it is already using, so Minimize does not ask you to connect again. |
| `on_rail` | A function `() -> None`. When set, the window header shows **Restore**. Using it calls the function, then reruns the page. `copilot_rail` uses it to bring its column back after Minimize. |

Raises `CocoError` before drawing anything when Streamlit is older than 1.55 or `cwd` does not name an existing directory.

What the call reads on each run: `cwd`, `policy`, `prompts`, `on_files_changed`, `features`, `context`, `labels` and `theme`. What it reads once per browser session: `options`, and the `agent.*` entries of `labels`.

### `get_window`

```python
def get_window(key: str = "coco") -> Window: ...
```

The handle of the window mounted with this key in this browser session. Raises `CocoError` when `ask_coco` has not run yet with that key.

### The handle

`ask_coco` and `get_window` return a `Window`. It holds only the key.

| Member | What it does |
| --- | --- |
| `coco.key -> str` | The key. |
| `coco.ask(label, text=None, *, key=None) -> bool` | A button of your page asks CoCo in the user's name. The thread shows `label`; CoCo receives `text` (`label` when `text` is `None`). `key` defaults to `label`. Sent at once when connected, shown as waiting until then. Returns `False` when the message was refused. It reruns the page once, so call it behind a button, never on every run. |
| `coco.result(key) -> dict \| None` | `{"text", "data"}` of the request sent with `coco.ask(..., key=key)`. `None` until it has finished. Handed over once. `data` is the structured output when the session has an `output_schema`, else `None`. While the request is pending, the window reruns the page when it ends, so your page can show the line. |
| `coco.form(title, fields, *, key) -> dict \| None` | A form your application asks, answered in the window. It needs no agent and no connection. Call it on every run: it asks once per `key`. It returns `None` until answered or skipped, then once `{"skipped": False, "values": {field id: text}}`, or `{"skipped": True, "values": {}}`. Afterwards it returns `None` again and never re-asks: a new question needs a new key. It reruns the page when it first asks. |
| `coco.open(drafts=None)` | Opens the window. `drafts` is a list of texts or `(title, text)` pairs, one bubble each, with Copy and no agent call. |
| `coco.notice(text, *, action=None)` | One line in the thread, in your words. `action` is `{"label", "then"}`: a button, and the function it runs on the server when pressed. |
| `coco.latest_answer -> str` | The text of the latest answer, `""` when none. |
| `coco.new()` | Ends the conversation. |
| `coco.disconnect()` | Ends the session. |
| `coco.conversation` | The [conversation object](#the-conversation). |

`fields` of a form are dicts `{"id", "label"?, "type"?, "choices"?, "required"?, "value"?}`. `type` is `text`, `longtext`, `number` or `choice`.

Notes:

- `ask` and `form` rerun the page. A page button runs after `ask_coco(cwd)`, so a button that changes the folder takes a second run to take effect.
- `result` needs the same key you gave `ask` (the label, when you gave none).

---

## Rights: `streamlit_coco.policy`

```python
from streamlit_coco import policy      # also st_coco.policy
```

Public names: `Policy`, `FolderPolicy`, `Command`, `git_readonly`, `request`, `inside`, `is_secret_name`. Pure Python: no Streamlit, no SDK.

Nothing is refused for what it is. A reading tool (Read, Glob, Grep, or a batch of up to eight of them) inside the scope is free. Every other call asks, each time, unless a standing permission covers it. Only a call the app cannot interpret is refused: an input that is not an object, a path that is not text, a path the system cannot resolve.

### `Policy`

A protocol. `FolderPolicy` is one; you may write your own.

```python
class Policy(Protocol):
    def judge(self, tool: str, payload) -> tuple[str | None, dict | None]: ...
    def describe(self, tool: str, payload) -> str: ...
    def rights(self, granted=()) -> dict: ...
```

| Method | What it returns |
| --- | --- |
| `judge(tool, payload)` | `(why the call is refused, the request to show)`. Both `None`: the call is free. Never raises. |
| `describe(tool, payload)` | The step's name, in plain words. |
| `rights(granted=())` | What the agent is told it may do, generated from the same rules. |

A policy may also define `exit_note(tool, input, content)`: it recognises a call that ran and exited non-zero for what it found, which the thread then shows as done.

### `request`

```python
def request(
    kind: str,                  # "read" or "change"
    question: str,
    *,
    where: str,
    reads: str | None = None,
    changes=None,               # a few words, or {"file", "lines", "note"}
    evidence=(),                # (label, exact text) pairs
    evidence_label: str = "Show input",
    pill: str | None = None,    # default "Allow a read?" or "Allow a change?"
    standing: dict | None = None,  # {"id", "label", "covers", "until"}
) -> dict: ...
```

Builds the plain dict the window shows: `{kind, question, where, reads, changes, evidence_label, evidence, pill, standing}`. It raises `ValueError` for a request that is not a read or a change, a change that says nothing about what changes, a read that says it changes something, or a standing permission with the wrong keys. Write it from the checked call, never from the agent's own description.

### `FolderPolicy`

```python
class FolderPolicy:
    def __init__(self,     folder,
        *,
        scope=None,
        also_read=(),
        commands=(),
        changes=None,
        sql: bool = False,
        lookups: bool = False,
        standing: bool = False,
    ): ...
```

The default policy: reading inside `scope` (default `folder`) is free, every other call asks, each time. A shell command and a file change always show their exact command, or file and text. Any other tool shows its whole input.

| Argument | What it does |
| --- | --- |
| `folder` | The agent's working folder. |
| `scope` | The folder reading is free in. Default: `folder`. |
| `also_read` | A folder, or several, read freely besides the scope, with the same care (`.git`, secret names, odd spellings, searches, links followed). Reading only: a change there asks as outside the scope. |
| `commands` | A list of [`Command`](#command). A call whose command is exactly one of them is shown as a read. |
| `changes` | Which files a change is ordinary for. Glob patterns (a string or a list, compared with the path from the scope; `*` crosses folders), or a function `(resolved path) -> None \| reason`. Default: any file inside the scope. Other files ask, say what is unusual, and are never offered a standing permission. |
| `sql` | A SQL call shows its exact statement, and is told apart: a query (surely one reading statement) is a read, anything else is a change. Any other input (a connection, a timeout) shows under "Other inputs". With `sql=False` a SQL call asks as a change with its whole input. |
| `lookups` | The known read-only tools of Cortex Code (Snowflake object search, table lookup, semantic view and Cortex agent search, Snowflake documentation, connection list, web search, web fetch) are shown as reads, with where the question goes. |
| `standing` | Each request offers its family as a standing permission until the conversation ends. The offer reads "Do not ask again for ...": commands; changes in this folder; queries that only read; SQL statements; one tool; reading outside the scope. File changes never include the `.git` folder, a secret-named file, or a place `flag` marks: those ask each time. |

Attributes: `words` (a dict of the few sentences it writes, for a host to replace: `undo`, `scope`, `folder`, `large`, `unusual`, `files`, `elsewhere`, `except`, `ordinary`, `also_asks`), `base`, `scope`, `where`, `spill`, `uploads`.

Extension points, for a host with rules of its own:

| Method | Use |
| --- | --- |
| `flag(parts) -> None \| (key, words)` | One more reason a place inside the scope is not read freely. `parts` are the names of the path from the scope. |
| `commands() -> list[Command]` | The listed commands for this request. Override it when they depend on the request. |

### `Command`

```python
class Command:
    def __init__(self, name: str, argv: tuple[str, ...], reads: str, platform: str = sys.platform): ...
```

One exact command line with its plain name, compared character for character and shown as a read under `name`. `reads` says what it reads. Only for a command that surely changes nothing.

`Command.line` is the line as the shell of that platform is given it (PowerShell on `win32`). It is `None` when the shell would expand an argument (`$name` or a backtick inside double quotes; a backslash too on other shells). Such a command is never listed.

### `git_readonly`

```python
def git_readonly(repo) -> list[Command]: ...
```

`status`, `diff` and `log` of one repository, written with the options that stop the repository's own settings from running a program, and that take no lock. It returns `[]` when `repo` is not a repository of its own (git would climb to a parent repository and report its files).

### `inside`

```python
def inside(base, scope, raw) -> str | None: ...
```

`None` when the path `raw`, placed as Cortex Code resolves it (relative to `base`, links followed), is inside `scope`. Otherwise `"outside"`, or `"odd"` for a spelling the app cannot place: a stream, a drive-relative path, a trailing dot or space, a device name, a path the system cannot resolve. Never raises. It does not look at what the file is: see `is_secret_name`.

### `is_secret_name`

```python
def is_secret_name(name: str) -> bool: ...
```

True for `.env*`, `*.pem`, `*.p8`, `*.key`, `*.pfx`, `id_rsa*`, `connections.toml`, and any name that holds `credential` or `secret`. Reads and searches that would cover one ask.

### `Gate`

```python
class Gate:
    def __init__(self, emit, expiry: float = 600): ...
```

The pre-tool decision that waits for the window. It is public for whoever writes another adapter. A host never needs it. `decide(tool, tool_input, tool_id)` blocks and returns `None` to allow, or the reason. An unanswered request expires after `expiry` seconds as a decline, the first answer stands, the call is judged again after Allow and must still be what was shown, and a standing permission lasts until the conversation ends. Methods: `begin(policy, *, new_conversation=False)`, `granted()`, `revoke(permission_id)`, `answer(request_id, allow, standing=False)`, `agreed(tool, tool_input)`, `cancel_all()`.

---

## Features

```python
class Features:
    def __init__(self,     queue: bool = True,
        steps: bool = True,
        motion: bool = True,
        copy: bool = True,
        page_text: bool = False,
        page_exclude: tuple[str, ...] = (),
        attachments: Attachments | None = None,
        planning: bool = False,
        display: tuple[str, ...] = (),
        session_details: bool = False,
        reasoning: bool = False,
        download_csv: bool = False,
    ): ...

# Features.all() builds one with everything on: the playground
```

A feature appears only when you switch it on or supply its data. A host that uses none sees no trace of any.

| Field | What it does |
| --- | --- |
| `queue` | The user may type while CoCo works, connects, or while a request waits for Allow or Decline: the message is queued behind it ("Queued") and can be taken back ("Take back"). Off: Send is unavailable meanwhile and what was typed stays in the field. |
| `steps` | One card per tool call. Off: only failed and refused steps stay, and the sentences CoCo said. |
| `motion` | The window's animation. It ignores the system's reduced-motion setting. |
| `copy` | Copy on answers, code and tables. |
| `page_text` | Each message carries the text the page shows (more data leaves the browser). |
| `page_exclude` | CSS selectors left out of that text. |
| `attachments` | An `Attachments`: the field accepts files. |
| `planning` | The menu offers "Plan first". |
| `display` | Menu switches that exist: `"latest"` (Latest exchange only), `"shorten"` (Shorten long messages), `"raw"` (Raw technical details). Any other value raises `ValueError`. |
| `session_details` | The menu offers Session details. |
| `reasoning` | CoCo's reasoning, as a fold among the steps. |
| `download_csv` | Download CSV in the wider table view. |

Standing permission is not here: it is a right, so it is the policy's (`standing=True`). Questions and plans from CoCo have no switch.

### `Attachments`

```python
class Attachments:
    def __init__(self, multi: bool = True, accept: tuple[str, ...] | list[str] = (".csv", ".tsv", ".txt", ".md", ".json", ".pdf", ".xlsx", ".docx"), max_mb: float = 10): ...
```

Files attached in the field are saved when the message is sent, in `<cwd>/_coco_uploads/<id>/`, and named to the agent. The policy lets the agent read those files and only those. An empty `accept` list accepts any type.

---

## Context

`context()` returns a plain dict of what your application knows when the message leaves. It is data for the agent and for a policy function, never authorisation. The conversation copies it when a message is sent; navigation afterwards changes nothing.

| Key | Meaning |
| --- | --- |
| `scope` | `{"name", "folder"}`: what the request is about. The thread says "About <name>" when it changes. A request shows it as "where". |
| `instructions` | Text added to what the agent is asked in every request. |
| `user` | `{"name", "language"}`. |

Every other key is passed to the agent as a fact. The window adds `screen` (`{"text", "dialog", "selection"}`) only when `Features.page_text` is on, and `rights` from the policy.

---

## Labels and theme

### Labels

`streamlit_coco.labels.DEFAULT` is one table of every sentence the window and the conversation write, in English, by key. Print the keys with:

```bash
python -c "from streamlit_coco.labels import DEFAULT; print(*DEFAULT, sep='\n')"
```

Key naming:

| Key | Who writes it |
| --- | --- |
| `window.<area>.<name>` | The browser side. Areas: `launcher`, `dialog`, `header`, `thread`, `field`, `common`, `time`, `first`, `data`, `confirm`, `standing`, `question`, `files`, `plan`, `session`, `request`, `step`, `footer`, `wait`, `queue`, `announce`, `menu`, `page`, and `offline`. |
| `agent.<name>` | The conversation, in Python: notes ("Allowed by you"), pills, menu options, attach messages, problem texts. |
| any other prefix | Free for your own sentences. Nothing reads them but you. |

Rules:

- `{name}` is a slot the writer fills. A text with a slot the writer does not know is shown as it is.
- `_one` and `_other` suffixes (`rows_one`, `rows_other`) are the singular and the plural, because a translation may not form a plural by adding an "s".
- A value may start or end with a space or a colon where the sentence is read after a prefix ("You: ").
- Texts a policy writes (a request's question, a command's plain name) are not in the table. They are the policy's own. Translate them in your policy.
- `agent.setup_package` is empty by default. A host that installs the package another way puts its own command there.

To translate, pass a dict. Keys you leave out stay in English.

```python
import streamlit_coco as st_coco

st_coco.ask_coco(".", labels={
    "window.field.placeholder": "Demandez à CoCo",
    "window.launcher.label": "Demander à CoCo",
    "agent.note_declined": "Refusé",
})
```

`window.*` labels are read on every run. The `agent.*` entries are read when the window is first mounted in a browser session.

### Theme

`theme={name: value}` sets CSS variables of the window (`--coco-<name>`). The window sits in an isolated shadow root: your page's styles do not reach it, and it does not touch yours.

| Name | Default | What it is |
| --- | --- | --- |
| `accent` | `#5498FF` | The brand colour: launcher, Send, focus ring. |
| `on-accent` | `#16181D` | Text and marks on the accent. |
| `surface` | `#FFFFFF` | The window's background. |
| `text` | `#3C3C3A` | Body text. |
| `muted` | `#6E6E6B` | Secondary text. |
| `border` | `#E8E6E1` | Lines and borders. |
| `danger` | `#F8485E` | Decline, errors. |
| `font` | `Montserrat, system-ui, sans-serif` | Font stack. The package ships Montserrat under its OFL licence. `"inherit"` uses your page's font. |
| `radius` | `1rem` | Corner radius of the window. |
| `avoid` | none | A CSS selector list: parts of your page the launcher must not cover (a fixed footer, an action bar). |

Everything else derives from these or from `1rem`, the page's own text size.

---

## Callbacks

Every function you hand to the package, and when it is called.

| Where | Signature | Called |
| --- | --- | --- |
| `ask_coco(policy=...)` | `(context: dict) -> Policy` | Once per message. The result is frozen with the message. Raising falls back to `FolderPolicy(cwd)`. |
| `ask_coco(context=...)` | `() -> dict` | When a message is sent, and when `coco.ask` sends one. |
| `ask_coco(on_files_changed=...)` | `(paths: list) -> Any` | Once after the agent changed files, before the page reruns. Clear your caches here. An exception is logged and does not stop the page. |
| `ask_coco(agent=...)` | `(emit) -> agent` | When the conversation starts. |
| `coco.notice(action={"label", "then"})` | `then() -> Any` | On the server, when the user presses the button. |
| `policy.FolderPolicy(changes=...)` | `(path) -> None \| reason` | For each file change. |
| `policy.FolderPolicy.flag` | `(parts) -> None \| (key, words)` | For each path read. |
| `app_viewer(on_fix=...)` | `(traceback_or_log: str) -> None` | When Fix is pressed. Usually calls `coco.ask("Fix with CoCo", prompt)`. |
| `app_viewer(on_close=...)` | `() -> None` | When Close is pressed. |
| `app_viewer(title_extra=...)` | `() -> None` | When the title row is drawn. |

---

## The conversation

`coco.conversation` is the conversation object. It is plain data in and out: the window reads `view()` and sends one action at a time. Use it to build a surface of your own, or to run with no browser (see `examples/headless_pipeline.py`). The class is `streamlit_coco.conversation.Conversation`; it is not in `__all__`. The docstring of that module is the contract: every key of the view and every action, with its shape.

```python
from streamlit_coco.conversation import Conversation

conv = Conversation(cwd, policy=None, features=None, prompts=None, labels=None,
                    agent=None, on_files_changed=None)
```

| Member | What it does |
| --- | --- |
| `conv.view() -> dict` | The whole state as plain data. Call it once per run: it hands `restore` over once. |
| `conv.act(action, context=None)` | One action. |
| `conv.drain() -> bool` | Applies what the agent reported. `True` when files of the working folder changed. |
| `conv.busy -> bool` | True while something can still arrive. Poll while it is. |
| `conv.set_cwd(cwd)` | A new working folder. It ends the conversation when a session works in another one. |
| `conv.add_drafts([(title, text)])` | Bubbles with Copy, no agent call. |
| `conv.request_from_page(label, text, context, key=None) -> bool` | What `coco.ask` calls. |
| `conv.result_for(key)` | What `coco.result` calls. |
| `conv.ask_form(key, title, fields)`, `conv.form_result(key)` | What `coco.form` calls. |
| `conv.notice(text, label=None, then=None)` | What `coco.notice` calls. |
| `conv.close()` | Ends the agent. |

Actions (`{"type": ...}`): `send` (`text`, `files`, `screen`), `prompt` (`text`), `stop`, `allow` (`id`), `decline` (`id`), `unqueue` (`id`), `new`, `connect` (`profile`, `file`), `disconnect`, `reconnect`, `retry`, `seen`, `answer`, `skip`, `approve_plan`, `decline_plan`, `carry_out`, `revoke`, `set`, `show_earlier`, `system_action`. The `id` of `allow` and `decline` is the `id` of `view()["request"]`.

Status values of the view: `not_installed`, `not_connected`, `connecting`, `ready`, `working`, `waiting`, `lost`.

To answer requests in code, read `view()["request"]` (the dict your policy wrote) and send `{"type": "allow", "id": ...}` or `{"type": "decline", "id": ...}`:

```python
view = conv.view()
if view["request"]:
    verdict = "allow" if view["request"]["kind"] == "read" else "decline"
    conv.act({"type": verdict, "id": view["request"]["id"]})
```

An agent (the `agent=` seam) is an object the conversation drives and that reports plain events (`connected`, `text`, `tool_use`, `tool_result`, `result`, `refused`, ...). The events and the methods it offers are listed in the docstrings of `conversation.py` and `cortex.py`.

---

## Page helpers

### `render_output_field`

```python
def render_output_field(coco, container=None, *, label: str = "CoCo output", text_renderer=None) -> None: ...
```

Shows the latest answer of the window `coco` in your page, as text only: no tool cards, no copy button, no status line. It looks again every second. `text_renderer` is `"markdown"` (default), `"write"`, `"text"`, `"code"`, `"caption"`, or a callable `(text) -> None`.

### `cwd_uploader`

```python
def cwd_uploader(
    target: CocoSession | CocoOptions | str,
    *, label="Upload into agent workspace", subdir="_uploads", overwrite="error",
    accept_multiple_files=True, file_type=None, max_bytes=10485760,
    key="coco_cwd_uploader", show_inventory=True,
) -> list[UploadedPath]: ...
```

`st.file_uploader` plus `upload_to_cwd`, for your own page or sidebar. Returns what was written on this run. `target` is the folder (text), a `CocoOptions` (its `cwd`) or a `CocoSession`. It lives in `streamlit_coco.uploader`. For files attached in the window's field, use `Features(attachments=...)` instead.

### Upload helpers

| Name | What it is |
| --- | --- |
| `upload_to_cwd(target, files, *, subdir="_uploads", overwrite="error", max_bytes=10485760, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS) -> list[UploadedPath]` | Writes browser uploads (or `(name, bytes)` tuples) under `cwd/subdir`. `overwrite` is `"error"`, `"replace"` or `"skip"`. Raises `CwdUploadError` for a bad name, a type not allowed, a payload too large, a `subdir` that escapes the folder, or an overwrite conflict. |
| `list_cwd_uploads(target, *, subdir="_uploads") -> list[Path]` | Files already in the folder. |
| `format_upload_prompt(paths, *, user_text="", intro=...) -> str` | A prompt text that names the saved files. |
| `sanitize_upload_name(filename) -> str` | A safe file name (path parts stripped). |
| `UploadedPath` | A frozen record: `path`, `relative`, `name`, `bytes_written`, `overwritten`, `skipped`. |
| `DEFAULT_ALLOWED_EXTENSIONS` | A `frozenset` of extensions. |
| `DEFAULT_MAX_BYTES` | `10485760`. |
| `DEFAULT_UPLOAD_SUBDIR` | `"_uploads"`. |

### `app_viewer` and the preview helpers

```python
def app_viewer(
    app_dir: str | Path, *, key="coco_app_viewer", port=None, address="127.0.0.1", env=None,
    iframe_height=520, show_fix=True, on_fix=None, on_close=None, title_extra=None,
    title="Preview", script_name="streamlit_app.py",
) -> None: ...
```

A preview column: Run, Stop, Open, **Fix with CoCo**, then an iframe of a child `streamlit run` of the folder `app_dir`. Never point it at your own application. The child is another origin: Fix reads `.preview.log`, not the iframe. `port=None` takes the first free port in 8511 to 8520. Wire `on_fix` to `coco.ask("Fix with CoCo", st_coco.default_fix_prompt(trace, app_dir))`.

Streamlit-free helpers: `start_app_preview(app_dir, *, port=None, address="127.0.0.1", env=None, script_name="streamlit_app.py") -> str`, `stop_app_preview(app_dir)`, `preview_running(app_dir) -> bool`, `preview_url(app_dir, *, address="127.0.0.1") -> str | None`, `last_preview_exception(app_dir) -> str | None`, `preview_log_tail(app_dir, *, n=40) -> str`, `default_fix_prompt(traceback, app_dir) -> str`.

---

## Options and session

### `CocoOptions`

Your configuration, converted to the SDK's `CortexCodeAgentOptions` by `to_sdk_options()`. Used by `ask_coco(options=...)`, `CocoSession` and `query`.

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `connection` | `str \| None` | `None` | Snowflake connection name. |
| `cwd` | `str` | `"."` | Working folder for a `CocoSession` or `query`. `ask_coco` takes its folder from its own `cwd` argument. |
| `model` | `str \| None` | `None` | Prefer `"auto"` when set. |
| `allowed_tools` | `list[str]` | `[]` | `CocoSession` and `query` only. `ask_coco` refuses it: use a `policy`. |
| `disallowed_tools` | `list[str]` | `[]` | Same. |
| `permission_mode` | `str` | `"default"` | For example `"plan"`. |
| `profile` | `str \| None` | `None` | SDK profile. |
| `cli_path` | `str \| None` | `None` | Path of the Cortex Code program (`CORTEX_CODE_CLI_PATH` also works). |
| `mcp_servers` | `dict` | `{}` | MCP servers, forwarded to the SDK. Their calls ask like any unknown tool. |
| `hooks` | `dict` | `{}` | SDK hooks. |
| `require_approval_for` | `list[str] \| Callable` | `[]` | `CocoSession` and `query` only. `ask_coco` refuses it. |
| `output_schema` | `dict \| None` | `None` | JSON Schema for a structured answer. It comes back through `coco.result(key)["data"]`. |
| `max_turns` | `int \| None` | `None` | Cap on agent turns. |
| `approval_timeout_seconds` | `float` | `600.0` | Wait for an approval in a `CocoSession`. |
| `extra_sdk_options` | `dict` | `{}` | Passed to the SDK's options, for example `add_dirs`. |

Methods: `options_hash() -> str`, `to_sdk_options(*, can_use_tool=None)` (raises `SDKNotInstalledError` when the SDK is missing), `auto_allow_tools() -> list[str]`, `tools_requiring_approval()`.

### `CocoSession`

```python
class CocoSession:
    def __init__(self, *, options: CocoOptions | None = None, key: str | None = None): ...
```

A multi-turn session on a background thread, for scripts, tests and your own surfaces. The window does not use it: the window owns its own session.

| Member | Notes |
| --- | --- |
| `start()` | Connect the worker. |
| `ensure_ready(timeout=120.0)` | Wait until ready. Raises `SessionNotReadyError`. |
| `send(prompt)` | Queue a turn. Raises `SessionStartError` or `SessionNotReadyError` on a boot failure. |
| `await run(prompt, *, timeout=None) -> CocoChatResult` | One turn, until it completes. |
| `stream()` | Async iterator of `CocoEvent`. |
| `execute_plan(*, mode="default", prompt="Execute the approved plan.")`, `set_permission_mode(mode)` | Leave plan mode. |
| `cancel()`, `close()`, `reset()` | Stop the turn, shut down the worker, clear everything. |
| `chat_result() -> CocoChatResult` | A snapshot. |
| `is_running`, `is_ready`, `is_connecting`, `needs_polling` | State flags. |
| `messages`, `get_transcript_snapshot()`, `get_revision()` | The transcript and its revision. |
| `last_error`, `init_info`, `structured_output` | Diagnostics and the last structured payload. |
| `permission_manager` | The coordinator of the session's own approvals. |
| `add_event_listener(callback)` | `callback(CocoEvent)` on each event. |
| `sync_options(options)` | Apply options. The worker restarts if their hash changed. |
| `set_show_structured_inline(value)` | Whether the result JSON is appended to the transcript. |

A `CocoSession` has its own approval list (`require_approval_for`, `allowed_tools`). Answer its requests with `session.permission_manager.resolve(request_id, *, approved, always=False, reason=None, updated_input=None) -> bool`, and find the pending one with `session.permission_manager.active_pending()`. The window does not use this path.

### `CocoRunStatus`

A `str` enum: `idle`, `connecting`, `ready`, `running`, `awaiting_user`, `completed`, `error`, `cancelled`.

### `CocoChatResult`

A snapshot of a session: `last_prompt`, `last_result` (`CocoEvent | None`), `pending_approval` (`dict | None`), `structured_output`, `events` (`list[CocoEvent]`), `status` (`CocoRunStatus`).

### `get_session`

```python
def get_session(key: str) -> CocoSession | None: ...
```

Looks a session up in the process registry (sessions created with `key=`).

---

## Headless

### `query`

```python
async def query(prompt: str, *, options: CocoOptions | None = None, output_schema: dict | None = None) -> AsyncIterator[CocoEvent]: ...
```

A single turn. Drain the whole iterator: an early `break` can leave the SDK's cancel scopes unclean. Raises `SDKNotInstalledError` or `QueryError`.

```python
async def main():
    async for event in st_coco.query("Profile CUSTOMERS", options=st_coco.CocoOptions(cwd=".")):
        if event.type == "result":
            print(event.structured_output)
```

For several turns use a `CocoSession`. For rights that match the window's, run a `Conversation` with a policy and answer its requests in code (see [The conversation](#the-conversation) and `examples/headless_pipeline.py`).

### `CocoEvent`

A normalised, JSON-serialisable event (`to_dict`, `from_dict`). Common `type` values: `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error`. Fields: `type`, `id`, `text`, `delta`, `name`, `tool_use_id`, `input`, `content`, `is_error`, `request_id`, `tool_name`, `tool_input`, `subtype`, `duration_ms`, `structured_output`, `cost_usd`, `message`, `code`, `metadata`.

### `events_to_dataframe`

```python
def events_to_dataframe(events: list[CocoEvent]) -> DataFrame: ...
```

Flattens events for an audit view. Needs pandas.

---

## Environment and errors

### `check_environment`

```python
def check_environment(*, connection=None, cli_path=None, toml_file=None) -> CocoEnvironment: ...
```

Probes without starting an agent. Does not raise. The window does this itself and says what is missing; use it for a page of your own.

`CocoEnvironment` fields: `sdk_installed`, `sdk_version`, `cli_path`, `cli_version`, `snowflake_config_file`, `connection_hint`, `toml_file`. Properties: `ready`, `cli_ok`, `snowflake_config_found`, `snowflake_config_display`, `snowflake_config_missing_label`.

### `require_environment`

```python
def require_environment(*, connection=None, cli_path=None, toml_file=None, require_snowflake_config=False) -> CocoEnvironment: ...
```

Like `check_environment`, but raises a typed error when the SDK or the program (and, if asked, the Snowflake file) is missing.

### Snowflake file helpers

| Name | What it does |
| --- | --- |
| `list_snowflake_toml_files() -> list[Path]` | `*.toml` files in `~/.snowflake/`, `connections.toml` then `config.toml` first. |
| `list_snowflake_connections(toml_file=None) -> list[str]` | Profile names of that file. A bare name is read under `~/.snowflake/`. |
| `resolve_snowflake_config_path(toml_file=None, *, must_exist=True) -> Path \| None` | The path of the file in use. |
| `default_snowflake_connection_name(toml_file=None) -> str \| None` | The default connection name. |

### Exceptions

```text
CocoError
├── SDKNotInstalledError          (also ImportError)
├── CLINotFoundError
├── CLIProbeError
├── SnowflakeConfigNotFoundError
├── CocoConnectionError
├── SessionStartError
├── SessionNotReadyError
├── ApprovalTimeoutError          (also TimeoutError)
├── QueryError
└── CwdUploadError
```

Catch `CocoError` for application-level handling; use a subclass for a specific recovery.

---

## Tool helpers

| Function | Role |
| --- | --- |
| `tool_family(tool_name) -> ToolFamily` | Maps a tool name to its family. |
| `is_sql_tool(tool_name) -> bool` | SQL and `sql_execute` spellings. |
| `is_ask_user_question(tool_name) -> bool` | AskUserQuestion spellings. |
| `is_exit_plan_mode(tool_name) -> bool` | ExitPlanMode. |

---

## Testing

`streamlit_coco.testing` runs and checks the window with no Snowflake login. Importing it needs neither Streamlit nor the conversation; `ScriptedAgent` is read on first use.

### `STREAMLIT_COCO_AGENT=mock`

Set it in the environment and any application runs on the scripted agent. The mock is chosen only by this variable. The window then offers a profile named `mock`: press **Connect mock**.

| Variable | Effect |
| --- | --- |
| `STREAMLIT_COCO_MOCK_SETUP=package` or `program` | Shows the "not installed" states. |
| `STREAMLIT_COCO_MOCK_PROFILES=a,b` | Lists those profiles (empty: none; default: one, `mock`). A profile named `broken` fails to connect; `denied` fails with a sign-in message. |
| `STREAMLIT_COCO_MOCK_FILES="connections.toml=a,b;config.toml=c"` | Several connection files. |
| `STREAMLIT_COCO_MOCK_EXPIRY=5` | An unanswered request, question or plan expires after 5 seconds instead of 10 minutes. |

### `ScriptedAgent`

```python
from streamlit_coco.testing import ScriptedAgent


class ScriptedAgent:
    def __init__(self, emit, delay: float = 0.04, connect_delay: float = 0.5): ...
```

It goes through the real policy and the real gate, and really reads and changes the files of its working folder. Nothing is simulated but the model and the programs: a command or a SQL statement is shown and asked about, and never run. Pass it to `ask_coco(agent=lambda emit: ScriptedAgent(emit))` or to a `Conversation`.

The scripted agent only ever emits its own fixed calls, so it cannot exercise every rule a host writes. The one command it asks for is `git status --short`: another command listed in `FolderPolicy(commands=...)` cannot be tried with it. `edit` changes the first Markdown file of the folder and `write` creates `coco_note.md`: a rule about other file types shows only as "not ordinary" on those two files. To see that, narrow `changes` (for example `changes="docs/*.md"`): the request then says "outside what it usually changes" and names the full path.

The script is chosen by a keyword in the user's message (first match wins). A message that starts with `Plain:` is answered plainly whatever words it holds.

| Keyword | Script |
| --- | --- |
| `lost` | A step is running when the connection is lost. |
| `retry` | Fails with a timeout the first time (Try again is offered), answers the second time. |
| `fail` | Reads a file that does not exist: a failing step, then an answer. |
| `slow` | A read that runs 6 s and shows 45 s elapsed. |
| `outside` | Reads a file outside the working folder. |
| `forbidden` | Reads the folder's `.env`. |
| `unlisted` | Runs `git push`. Nothing is executed. |
| `edit` | Edits the first line of the first Markdown file of the folder. |
| `write` | Creates `coco_note.md` in the folder (also "carry out the plan"). |
| `status` | Runs `git status --short`. Nothing is executed. |
| `snowflake` | Runs a `select`. With the word `drop`, a statement that changes Snowflake. The result is made up. |
| `screen` | Answers with what the message carried of the page. |
| `reads` | Says a sentence, then Read, Glob, Grep and a batch of two reads, then an answer. |
| (other) | A plain streamed answer. |

States of the design sheet, checked before the keywords above: `onechoice`, `multichoice`, `ownwords`, `threeq`, `longform`, `shortplan`, `longplan`, `twowaits`, `outwrite`, `unknowntool`, `table24`, `table1240`, `norows`, `structured`, `codeblock`, `reasoning`, `rawdetails`. With "Plan first" on, any other message is answered by what CoCo would do, and nothing is done. Stop, Allow, Decline, standing permission and expiry work in every script.

### Fixtures

```python
from streamlit_coco.testing import VIEWS
```

`VIEWS` maps a state name to a `view` of the conversation, one per frame of the design sheet (for example `ask_command`, `f43_question_form`, `f62_table`). Each has the shape of `Conversation.view()`. They are for tests that need a state with no conversation running.

### Harness and domdiff

```bash
python -m streamlit_coco.testing.harness f38_question_choice 48 [--out FILE] [--width 460] [--height 780] [--rem 14.4] [--shot FILE.png]
python -m streamlit_coco.testing.domdiff [--ref HEAD] [--only REGEX]
```

`harness` writes one HTML file that mounts the real window on any fixture, with no server. Open it with Playwright (the installed Edge), wait for `window.__cocoReady`, and read what the window sent in `frames[n].__actions`. `domdiff` compares the window's DOM at a commit with the working copy and exits with status 1 when anything differs. It needs Playwright and the installed Edge.

---

## Package metadata

```python
st_coco.__version__  # "0.2.1"
```
