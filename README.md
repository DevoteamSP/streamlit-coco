# streamlit-coco

**Built by Devoteam Snowflake Partner.** Ask CoCo for Streamlit: a floating chat window, in front of a Snowflake coding agent, that you add to your own application with one call. You say what the agent may do alone and what it must ask first. The window shows each request in plain words, with the exact command, file text or SQL statement one click away, and every decision can be written to an audit log.

[![CI](https://github.com/lletourmy/streamlit-coco/actions/workflows/ci.yml/badge.svg)](https://github.com/lletourmy/streamlit-coco/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> `0.3.0` (alpha, the API may still move). The default interface is still the 0.1.9 chat family (`chat`, `panel`, `copilot_rail`); the floating window is opt-in (`mini=True` on those calls, or `ask_coco(cwd)`). **New and experimental:** Snowflake's managed coding agent runs in the same window with no `cortex` program, files attached in the window go to the sandbox, and `AuditLog` records who allowed what. The managed agent rests on a public-preview SDK (`snowflake-cortex-agent-sdk` 0.0.x). Details: [`doc/features/ask-coco/ask-coco.md`](doc/features/ask-coco/ask-coco.md).

**Repo:** [github.com/lletourmy/streamlit-coco](https://github.com/lletourmy/streamlit-coco) *(temporary PyPI source)* · **Dev:** [streamlit-coco-dev](https://github.com/DevoteamSP/streamlit-coco-dev)
**SDK docs:** [Cortex Agent SDK](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent-sdk/cortex-agent-sdk) · [Cortex Code Agent SDK](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)

---

## What you get

- A launcher at the bottom right of the page, and a window that opens from it. The window is the whole interface: connect, ask, watch the steps, answer requests.
- **Rights written as code**, in one object (a `Policy`). The default is the safest: reading inside the working folder is free, everything else asks, each time.
- Every request names what it is about and shows the exact text of what would run.
- **Two real agents behind the same window**, the same policy and the same Allow and Decline: the Cortex Code program on the server, or Snowflake's managed coding agent in a Snowflake sandbox (experimental).
- An **audit log**: one JSON line per decision, with who, when and the exact command shown.
- Buttons of your own page can ask CoCo something in the user's name, and read the answer back.
- A scripted agent (`STREAMLIT_COCO_AGENT=mock`) so you can build and test with no Snowflake login.
- Headless `query()` and `CocoSession` for scripts and CI.

## Which agent

| | Cortex Code program | Managed agent (experimental) | Scripted |
| --- | --- | --- | --- |
| Runs | on the Streamlit server, in your working folder | in a Snowflake sandbox | in the page's process |
| Needs | the `cortex` program on the `PATH`, a Snowflake profile | a Snowflake profile and a role (or a token), outbound HTTPS to the account | nothing |
| Files it sees | the working folder | what you mount (workspace, stage) and what the user attaches, before the first message | none |
| Rights | the policy judges every call | the policy judges every call the server asks about; the role of the session is the limit | the policy shows and asks, nothing runs |
| Use | `ask_coco(".")` | `ask_coco(".", agent=managed_agent(options))` | `STREAMLIT_COCO_AGENT=mock` |

## When not to use

- **You want CoCo Desktop, the CLI, or an IDE extension.** This is an embed in your Streamlit application. It has no file tree and no editor.
- **The Streamlit host can run neither agent.** The Cortex Code program needs a host that can run it; the managed agent needs outbound HTTPS to your Snowflake account and a login. Streamlit Community Cloud without one of those will not work. (Streamlit in Snowflake is planned, not shipped.)
- **You are not building in Python and Streamlit.** There is no TypeScript package. Use the [Cortex Agent SDK](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent-sdk/cortex-agent-sdk) directly.
- **You would not type the SQL yourself on this role.** The agent uses the Snowflake role of the connection. Do not wire `ACCOUNTADMIN` into a web page: give it the least role that works ([threat model, section 8](doc/security/threat-model.md)).

---

## Install

```bash
uv add "streamlit-coco[sdk]"
# or: pip install "streamlit-coco[sdk]"
```

From a clone (editable, with the tests): `make install`.

Needs:

1. Python 3.10 or later, Streamlit 1.55 or later.
2. For the Cortex Code agent: the Cortex Code program on the `PATH` (`cortex --version`), a Snowflake connection (`~/.snowflake/connections.toml` or `config.toml`), and `snowflake-cortex-agent-sdk` (the `sdk` extra, pinned `>=0.0.3,<0.1`). The window says what is missing and how to fix it.
3. For the managed agent: no `cortex` program; a profile and a role to log in with, and the same `sdk` extra. See [The managed agent](#the-managed-agent-experimental).
4. For a scripted agent: nothing more. See below.

Full local setup: [`doc/deployment/local.md`](doc/deployment/local.md). Every public name: [`doc/api.md`](doc/api.md).

---

## First application: show the window

Save this as `app.py`.

```python
import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="My app")
st.title("My app")
st.write("Open Ask CoCo with the launcher at the bottom right of the page.")

# One call: the launcher and the window. CoCo works in this folder.
st_coco.ask_coco(".")
```

Run it without a Snowflake login, on the scripted agent:

```bash
STREAMLIT_COCO_AGENT=mock streamlit run app.py        # PowerShell: $env:STREAMLIT_COCO_AGENT="mock"
```

What happens: click **Ask CoCo** (bottom right), then **Connect mock**. Type a message and press Enter. The scripted agent answers: "This is a scripted answer. You wrote: ..." This was run in Edge on Streamlit 1.65.0.

Without the variable, the same file talks to a real Cortex Code agent. The window offers your Snowflake connections and connects when the user presses **Connect**. Nothing starts before that.

`ask_coco(cwd)` is the only call a first application needs. The argument is the agent's working folder. A relative path (like `"."`) is taken from the folder the Streamlit server was started in, not from the folder of the script. The package checks that the working folder exists and is a directory before connecting, and raises `CocoError` otherwise. It does not create the folder: create it first. It returns a handle; see [Talk to the window](#talk-to-the-window).

---

## Second application: your own rights

The agent may list one command, change Markdown files, and run SQL. Each of those still asks first, unless it is a read. Save this as `app_rights.py`.

```python
import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco import policy

st.set_page_config(page_title="My app with rights")
st.title("My app with rights")
st.write("Reading in this folder is free. Everything else asks first.")

# One command, written exactly as the agent must type it. It is shown as a read.
status = policy.Command(
    name="Look at what has changed",
    argv=("git", "status", "--short"),
    reads="The list of changed files",
)

rights = policy.FolderPolicy(
    ".",
    commands=[status],  # this exact line is a read, under its plain name
    changes="*.md",  # changing a Markdown file is ordinary; any other file is flagged
    sql=True,  # a SQL call shows its exact statement
)

st_coco.ask_coco(".", policy=rights)
```

Run it the same way, from a folder that holds a `README.md`:

```bash
STREAMLIT_COCO_AGENT=mock streamlit run app_rights.py
```

Connect, then type these words. The scripted agent picks its script from a keyword:

| Type | What the window shows |
| --- | --- |
| `status` | A request to look at what has changed: **Allow CoCo to look at what has changed?** It is a read. **Show command** opens the exact line, `git status --short`. |
| `edit` | A request to change a file: **Allow CoCo to change a file?** It says `README.md`, one line. **Show change** opens the text. |
| `snowflake drop` | A request to run a statement that can change Snowflake. It says `DROP`. **Show statement** opens `drop table DEMO.PUBLIC.OLD_CALLS`. |

If you type while a request waits, the message is queued behind it ("Queued", with **Take back**) and is sent after Allow or Decline. Nothing runs until the user presses **Allow**; **Decline** ends the call. The scripted agent never runs the command or reaches Snowflake: it only shows and asks. With a real agent the same policy decides, and **Allow** runs the call.

What each argument did:

- `commands=[status]`: a call whose command is exactly this line is a read, named "Look at what has changed". Any other command asks as a change, with its whole line.
- `changes="*.md"`: a change to a Markdown file is ordinary. A change to any other file asks too, and says it is unusual. Try `changes="docs/*.md"` and the `edit` request is flagged: "outside what it usually changes", with the full path.
- `sql=True`: a SQL call shows its exact statement. A statement that surely only reads is a query. Anything else is a statement that can change Snowflake.

The scripted agent makes only its own fixed calls (`git status --short`, an edit of the first Markdown file, `coco_note.md`), so it cannot try every rule you write. More switches (`standing`, `lookups`, `also_read`, `git_readonly`) are in [`doc/api.md`](doc/api.md). A runnable version with a standing permission is `examples/approval_gate.py`.

---

## The managed agent (experimental)

Snowflake's managed coding agent, through the Cortex Agent SDK. It runs in a Snowflake sandbox: no `cortex` program, no working folder. It takes the same window, the same policy and the same Allow and Decline.

```python
import streamlit as st

import streamlit_coco as st_coco
from streamlit_coco.policy import FolderPolicy

# Logs in with the connector: do it once per session, never on every rerun.
if "managed" not in st.session_state:
    st.session_state.managed = st_coco.options_from_connection(
        "my_profile",       # a profile of ~/.snowflake
        role="PUBLIC",      # the agent works with this role's rights: the least that works
    )
options = st.session_state.managed

st_coco.ask_coco(
    ".",
    agent=st_coco.managed_agent(options),
    connection=options.label,
    policy=FolderPolicy(".", words=st_coco.SANDBOX_WORDS, where=st_coco.SANDBOX_WHERE),
)
```

`make managed` runs a complete example (profile and role form, then the window).

- **Always asks.** The run is created with `permission_policy="always_ask"`; it is not an option. Only the user's Allow becomes the server's one-call "Allow this command". The server's own "Allow all bash for this session" is never chosen.
- **The server decides what it asks about.** A command it rates risky pauses the run and reaches your policy; one it rates harmless (`echo hello`) runs unasked. The role of the session, not the window, is the real limit: give it the least rights that work.
- **No local folder.** `cwd` is only the policy's and is never sent. The agent works on what you mount (`workspace_mounts`, `stage_mounts`, `stage_skills`) and on what the user attaches.
- **Attach a file.** `Features(attachments=st_coco.Attachments())` with `options_from_connection(..., upload_stage="DB.SCHEMA.STAGE")`: each file goes to a folder of this conversation on that stage, mounted at `/uploads`, and is removed with the conversation. Files go in **before the first message** (the sandbox reads the stage once); a later one is refused with a sentence that says so.
- **Probe without the program:** `check_environment(managed=True)`.
- **Not available:** the agent's own questions and plans (Cortex Code's tools), planning only.

Skills on a stage and a chat with one chosen skill: `make skills-hub`, and the same as a Snowflake Native App on Snowpark Container Services: [`examples/skills_hub_native/`](examples/skills_hub_native/DEPLOY.md), which also holds a prompt for Cortex Code that asks for your parameters and deploys it ([`COCO_PROMPT.md`](examples/skills_hub_native/COCO_PROMPT.md)).

---

## Who allowed what: the audit log

```python
audit = st_coco.AuditLog("logs/coco-audit.jsonl", who=lambda: st.user.get("email"))
st_coco.ask_coco(".", audit=audit)
```

One line per call that asked the user, was covered by a standing permission, or was refused: `time`, `who`, `agent`, `tool`, `decision` (`allowed`, `declined`, `expired`, `refused`, `standing`, `revoked`) and the exact command, SQL or path the user was shown, with what looks like a credential replaced by `[redacted]` (`AuditLog(redact=...)` to change it, `None` to turn it off; a secret that looks like nothing, such as a plain `-p hunter2`, is **not** caught). A second line, `decision: "outcome"`, says whether an allowed call `succeeded`, `failed`, was `not_run` or got `no_result`. Reads inside the working folder that run without a question are not logged. The file is readable by its owner only; it is not tamper-proof (ship it to storage the app cannot rewrite if that matters). The library cannot know who answers: give `who`. See [`doc/api.md`](doc/api.md#the-audit-log).

---

## Talk to the window

`ask_coco` returns the window's handle. `st_coco.get_window()` returns the same handle anywhere else on the page.

```python
import streamlit as st

import streamlit_coco as st_coco

coco = st_coco.ask_coco(".", prompts=["List the files here"])

if st.button("Summarise this folder"):  # ask() reruns the page: keep it behind a button
    coco.ask("Summarise this folder", "Read the files here and say what they are for.", key="sum")

done = coco.result("sum")  # None until finished, then {"text", "data"}, once
if done:
    st.write(done["text"])
```

| Call | What it does |
| --- | --- |
| `coco.ask(label, text, key=...)` | A button of your page asks CoCo in the user's name. The thread shows `label`. |
| `coco.result(key)` | The finished answer of that request: `{"text", "data"}`, handed over once. |
| `coco.form(title, fields, key=...)` | A form your application asks, answered in the window. No agent needed. |
| `coco.notice(text)` | One line in the thread, in your words. |
| `coco.open()`, `coco.new()`, `coco.disconnect()` | Open the window, end the conversation, end the session. |
| `coco.latest_answer` | The text of the latest answer, for a page that shows it elsewhere. |

Other arguments of `ask_coco`: `features` (what the window offers: attachments, display switches, window places), `context` (what your page knows when a message is sent), `labels` (every sentence, to translate), `theme` (colours, font), `options` (model, connection, structured output), `agent`, `audit`, `on_files_changed`, `on_layout` and `split` (the page makes room when the window is attached to an edge). All of them are in [`doc/api.md`](doc/api.md).

---

## Try the demos

```bash
make simple-chat   # panel, a test-prompt picker, rights as pills
make modern-chat   # Copilot rail, floating window, or both
make approval      # a listed command, a file rule, SQL, a standing permission
make structured    # a result handed to the page as data
make cwd-upload    # files attached in chat, and an uploader on the page
make headless      # asyncio query() and a Conversation answered in code
make managed       # the managed agent: profile and role, then the window (experimental)
make skills-hub    # skills on a stage, a chat with one chosen skill (experimental)
make backlog       # Product Backlog Desk: a multipage application
make bi-semantic   # Tableau / Power BI to semantic view
make app-builder   # App Builder: type library, brief, Preview
```

Each Streamlit demo has an **Ask CoCo** control (Off / On) in the sidebar. Off keeps that page's chat, panel, or Copilot rail. On leaves Ask CoCo minimized until **Minimize** on that CoCo, which hides it and opens the window. **Restore** in the window closes it and brings the rail or chat back.

To run them with no login: `STREAMLIT_COCO_AGENT=mock make simple-chat` (PowerShell: set `$env:STREAMLIT_COCO_AGENT` first); `make skills-hub` shows its sample skills on a scripted chat. `make chat` still launches the simple demo.

Exploratory prompts: [`examples/testdata/prompts.json`](examples/testdata/prompts.json).
Backlog Desk: [`examples/backlog_desk/README.md`](examples/backlog_desk/README.md) · BI to Semantic: [`examples/bi_to_semantic/README.md`](examples/bi_to_semantic/README.md) · App Builder: [`examples/app_builder/README.md`](examples/app_builder/README.md) · Skills shop: [`examples/skills_hub/README.md`](examples/skills_hub/README.md) · Skills shop as a Native App: [`examples/skills_hub_native/DEPLOY.md`](examples/skills_hub_native/DEPLOY.md).

---

## Architecture

The agent is not in the browser. The browser sees one Streamlit component.

```text
Browser  ──►  Ask CoCo window (one component, in a fragment)
                  │  one action at a time; the page does not rerun
                  ▼
             Conversation   (thread, steps, requests, queue: plain data)
                  │  every call the agent asks about reaches the Gate
                  ▼
             Gate + Policy  (free, asks, or refused; waits for Allow / Decline; writes the audit log)
                  ▼
             an agent  (backend.py: one surface, three agents)
                  ├── Cortex adapter ──►  Cortex Agent SDK (cortexcode) ──►  Cortex Code program ──►  Snowflake
                  ├── Managed agent  ──►  Cortex Agent SDK ──►  Snowflake's coding agent (sandbox)
                  └── Scripted agent (tests, demos, no login)
```

All three go through the same Conversation, Policy and Gate. Only the model and the programs are replaced.

```text
streamlit_coco/
├── window.py        # ask_coco(), get_window(), the handle
├── conversation.py  # the contract between the window and the agent (read its docstring)
├── policy.py        # Policy, FolderPolicy, Command, git_readonly, request, inside
├── gate.py          # the decision that waits for Allow / Decline
├── audit.py         # AuditLog
├── backend.py       # AgentBackend: what an agent is
├── cortex.py        # the Cortex Code adapter
├── managed.py       # the managed agent: ManagedOptions, managed_agent, options_from_connection
├── features.py      # Features, Attachments
├── labels.py        # every sentence of the window, by key
├── testing/         # scripted agent, scripted client of the managed agent, fixtures, harness
├── static/          # the window's script, styles and font
├── session.py       # CocoSession (headless)
├── query.py         # query() (headless)
├── viewer.py        # app_viewer()
└── uploader.py      # cwd_uploader()
examples/            # demos
doc/                 # API, feature files, checklists
```

Notes: [`doc/prd.md`](doc/prd.md) · threat model: [`doc/security/threat-model.md`](doc/security/threat-model.md) · feature files: [`doc/features/README.md`](doc/features/README.md).

---

## Headless

```python
import asyncio
import streamlit_coco as coco

async def run():
    async for event in coco.query("Profile ANALYTICS.CUSTOMERS"):
        if event.type == "result":
            print(event.structured_output)

asyncio.run(run())
```

`query()` and `CocoSession` use the Cortex Code program.

---

## Development

```bash
make install       # uv sync --extra dev
make check         # ruff and the unit tests (not the browser tests)
make e2e-install   # Playwright and Chromium, once
make e2e           # browser tests of the window, on the scripted agent and a scripted managed client
make test-all      # check, e2e and the dependency audit
make format        # ruff format and fix
make build         # sdist and wheel
make help          # every target
```

`make e2e` uses the installed Edge when Playwright's Chromium is not installed. No automated test calls a live agent. Process: [`doc/testing.md`](doc/testing.md). Live checks before a release (Cortex Code and the managed agent): [`doc/features/ask-coco/test-checklist.md`](doc/features/ask-coco/test-checklist.md).

Releases: develop here, sync and tag on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco) for PyPI ([guide](doc/deployment/publish.md)).

**Docs:** [API](doc/api.md) · [Ask CoCo feature file](doc/features/ask-coco/ask-coco.md) · [PRD](doc/prd.md) · [Roadmap](doc/roadmap.md) · [Threat model](doc/security/threat-model.md) · [Deployment](doc/deployment/) · [Changelog](CHANGELOG.md) · [AGENTS.md](AGENTS.md)

---

## Ownership

| Role | Name | Contact |
| --- | --- | --- |
| Asset Owner | Laurent Letourmy | laurent.letourmy@devoteam.com |
| Asset Contributor | Alentz Joseph | alentz.joseph@devoteam.com |

**Snow Builders level:** N0 (alpha), targeting N1. Identity sheet: [`ID.md`](ID.md).

---

## License

Apache-2.0
