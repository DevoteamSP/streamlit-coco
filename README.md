# streamlit-coco

**Built (with love) by Devoteam Snowflake Partner, brings Snowflake CoCo into Streamlit** — streaming agent UI, tool cards you can actually read, and approval gates that fit governed data apps.

[![CI](https://github.com/lletourmy/streamlit-coco/actions/workflows/ci.yml/badge.svg)](https://github.com/lletourmy/streamlit-coco/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

You own the page. CoCo owns the session. `panel()` streams the transcript; `copilot_rail()` wraps that panel as a right-rail Copilot for multipage apps. Your app keeps `st.chat_input`, metrics, and forms. Approvals pause Write / Edit / Bash / SQL until someone clicks **Approve once**, **Always allow**, or **Deny**.

![CoCo for Streamlit — streaming transcript with a Glob tool card](doc/screenshot.png)

> Alpha `0.1.7` — API may still move. Star / watch the repo if you plan to ship on it.

**Repo:** [github.com/lletourmy/streamlit-coco](https://github.com/lletourmy/streamlit-coco) *(temporary PyPI source)* · **Dev:** [streamlit-coco-dev](https://github.com/DevoteamSP/streamlit-coco-dev)  
**SDK docs:** [Cortex Code Agent SDK](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)

---

## Why this package

| Without streamlit-coco | With streamlit-coco |
| --- | --- |
| Wire CoCo yourself across Streamlit reruns | Session + fragment polling that keeps streaming |
| Raw JSON tool dumps | Meaningful cards (Glob, Grep, Read, Write, SQL, AskUser…) |
| Hope the agent behaves | `require_approval_for` + HITL UI |
| Chat-only demos | Structured callbacks into your own widgets |

Also: headless `query()` for scripts and CI, plus a legacy all-in-one `chat()` if you want built-in input.

---

## When not to use

- **You want CoCo Desktop, the CLI, or an IDE extension.** This is an embed in *your* Streamlit app — no file tree, multi-tab workspace, or full IDE.
- **The Streamlit host cannot run CoCo.** The agent is server-side (CLI on the host today; remote API is still on the roadmap). Typical Streamlit Community Cloud without that setup will not work.
- **You are not building in Python / Streamlit.** There is no TypeScript package; use the [Cortex Code Agent SDK](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk) directly.
- **You need Slack, a hosted CoCo SaaS, or a product MCP server.** Out of scope. MCP *passthrough* via `mcp_servers` already works.
- **You would not type the SQL yourself on this role.** The agent uses the Snowflake role in the connection — do not wire `ACCOUNTADMIN` into a web UI.

Alpha `0.1.7` — APIs may still move. Prefer `panel()` + your own input; `chat()` is the legacy all-in-one.

---

## Install

```bash
uv add "streamlit-coco[sdk]"
# or: pip install "streamlit-coco[sdk]"
```

From a clone (editable + tests):

```bash
make install
```

### Prerequisites

1. Python **3.10+** · Streamlit **≥ 1.53**
2. CoCo CLI on `PATH` (`cortex --version`)
3. Authenticated Snowflake connection (`~/.snowflake/connections.toml` or equivalent)
4. `cortex-code-agent-sdk` (pulled in by the `sdk` / `dev` extras)

**Full local setup:** [`doc/deployment/local.md`](doc/deployment/local.md) (CLI install, Snowflake `connections.toml`, running examples, troubleshooting).  
**API:** [`doc/api.md`](doc/api.md).

---

## Quickstart

Preferred pattern — **you own the input**; CoCo owns the session and output:

```python
import streamlit as st
import streamlit_coco as st_coco

opts = st_coco.CocoOptions(
    connection="analytics",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
)

env = st_coco.check_environment(connection=opts.connection)
if not st_coco.render_start_gate(opts, session_key="copilot", env=env):
    st.stop()

session = st_coco.get_or_create_session(opts, key="copilot")
st_coco.panel(session=session, warm_up=True, show_status=True, run_every=0.25)
st_coco.chat_input_bar(session, placeholder="Ask CoCo…")
```

- `allowed_tools` — may auto-run (enforced in Python when approvals are configured)
- `require_approval_for` — pause for Approve once · Always allow · Deny

Legacy all-in-one component (built-in input):

```python
st_coco.chat(session=session, key="coco_chat", height=560)
```

---

## Try the demos

```bash
make chat          # panel + chat input + tool cards + approvals
make cwd-upload    # upload files into agent cwd + chat
make approval      # legacy CCv2 chat
make structured    # custom structured-output panel
make headless      # asyncio query() pipeline
make backlog       # Product Backlog Desk (multipage business demo)
make bi-semantic      # Tableau / Power BI → semantic view + RAP (screens 1–6)
# make tableau-semantic is an alias for bi-semantic
```

Exploratory prompts: [`examples/testdata/prompts.json`](examples/testdata/prompts.json).  
Backlog desk: [`examples/backlog_desk/README.md`](examples/backlog_desk/README.md).  
BI → Semantic: [`examples/bi_to_semantic/README.md`](examples/bi_to_semantic/README.md).  
File upload: [`doc/features/file-upload/file-upload.md`](doc/features/file-upload/file-upload.md).

---

## Patterns you’ll use often

### Structured output → your widgets

```python
output = st.container()

def render(data: dict, result: st_coco.CocoChatResult) -> None:
    with output:
        st.dataframe(data.get("selected_features", []))

st_coco.panel(session=session, on_structured_output=render)
```

### Headless (no Streamlit UI)

```python
import asyncio
import streamlit_coco as coco

async def run():
    async for event in coco.query("Profile ANALYTICS.CUSTOMERS"):
        if event.type == "result":
            print(event.structured_output)

asyncio.run(run())
```

---

## Architecture

The agent is **server-side**. The browser only sees Streamlit widgets. `panel()` (or `copilot_rail()` around it) polls a `CocoSession` worker via `@st.fragment`; the session talks to the Cortex Code Agent SDK, which runs the `cortex` CLI against your Snowflake account. Destructive tools pause in Python (`can_use_tool`) until someone clicks Approve / Deny. Headless `query()` skips the UI and uses the same session/SDK path.

```
Browser  ──►  panel() / copilot_rail() / chat_input_bar()
                  │  @st.fragment poll (app page does not rerun)
                  ▼
             CocoSession  (thread + asyncio, transcript + pending approval)
                  │  can_use_tool → render_approvals()
                  ▼
             cortex-code-agent-sdk  ──►  cortex CLI  ──►  Snowflake CoCo + RBAC
```

Legacy `chat()` is the same session, with a CCv2 frontend instead of native widgets.

| Capability | Entry points |
| --- | --- |
| Native panel + approvals | `panel()`, `chat_input_bar()`, `render_approvals()` |
| Copilot rail (right-column Copilot) | `copilot_rail()`, `transcript_view_pills()` — [`doc/features/copilot-rail/`](doc/features/copilot-rail/) |
| App viewer (child Streamlit iframe) | `app_viewer()`, `default_fix_prompt()` — [`doc/features/app-viewer/`](doc/features/app-viewer/) |
| Tool cards & AskUser / plan UI | see [`doc/features/tools-display/`](doc/features/tools-display/) |
| Session & options | `CocoSession`, `CocoOptions`, `get_or_create_session` |
| Headless events | `query()` |
| Legacy CCv2 | `chat()` |

```
streamlit_coco/
├── ui.py            # panel(), send_prompt(), render_approvals()
├── rail.py          # copilot_rail(), transcript_view_pills()
├── viewer.py        # app_viewer()
├── app_preview.py   # child Streamlit process helpers
├── session.py       # CocoSession worker + transcript
├── permissions.py   # HITL can_use_tool gates
├── query.py         # headless query()
├── component.py     # legacy chat() CCv2 mount
└── frontend/        # static CCv2 assets
examples/            # chat, backlog desk, BI → Semantic, …
doc/                 # PRD, roadmap, feature specs
```

Full diagram and runtime notes: [`doc/prd.md`](doc/prd.md) §5 · threat-model topology: [`doc/security/threat-model.md`](doc/security/threat-model.md).  
API: [`doc/api.md`](doc/api.md). Feature checklists: [`doc/features/README.md`](doc/features/README.md).

---

## Development

```bash
make install       # uv sync --extra dev
make check         # ruff + unit/smoke (ignores tests/e2e)
make e2e-install   # Playwright + Chromium (once)
make e2e           # UX e2e vs examples/e2e_ux_harness.py
make test-all      # check + e2e + audit
make audit         # pip-audit
make format        # ruff format + fix
make build         # sdist + wheel
make sync-release  # copy tree → public clones (see doc/deployment/publish.md)
make help          # all targets
```

CI runs lint, tests, and pip-audit on every PR to `main`. Full local gate: `make test-all` ([`doc/testing.md`](doc/testing.md)).  
**Releases:** develop here (`streamlit-coco-dev`), sync + tag on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco) → PyPI ([guide](doc/deployment/publish.md)).

**Docs:** [PRD](doc/prd.md) · [API](doc/api.md) · [Roadmap](doc/roadmap.md) · [Training](doc/training/training-overview.md) · [Deployment](doc/deployment/) · [Changelog](CHANGELOG.md) · [AGENTS.md](AGENTS.md)

---

## Ownership

| Role | Name | Contact |
| --- | --- | --- |
| Asset Owner | Laurent Letourmy | laurent.letourmy@devoteam.com |
| Contributors | DevoteamSP / streamlit-coco contributors | [streamlit-coco-dev](https://github.com/DevoteamSP/streamlit-coco-dev) |

**Snow Builders level:** N0 (alpha), targeting N1. Identity sheet: [`ID.md`](ID.md).

---

## License

Apache-2.0
