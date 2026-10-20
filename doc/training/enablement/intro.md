# Introduction

## What streamlit-coco is

`streamlit-coco` is a Python/Streamlit library that embeds Snowflake's Cortex
Code Agent SDK ("CoCo") into a Streamlit app: a right-rail or full-panel
Copilot, human-in-the-loop approval gates for destructive tools, a live
preview of an app CoCo just wrote, structured output into your own widgets,
and a headless `query()` / `CocoSession` API for scripts and CI.

PyPI package: `streamlit-coco`. Current version: **0.1.9** (alpha — the API
may still move). Python 3.10+, Streamlit 1.55+. License: Apache-2.0.

## The problem it addresses

Wiring the CoCo SDK into a Streamlit app by hand means building, from
scratch: session state that survives Streamlit reruns, streaming render of
the agent transcript, readable tool cards instead of raw JSON tool dumps, and
an approval flow for anything the agent could write, edit, or execute.
`streamlit-coco` provides that plumbing as a set of composable functions
(`panel()`, `chat_input_bar()`, `copilot_rail()`, `render_approvals()`, …) so
an app author writes the page and the options, not the session bridge.

## Who this is for

Consultants and engineers who need to add a CoCo-based Copilot to a Streamlit
app on a Snowflake account with Cortex Code access. It assumes basic Python
and enough Streamlit familiarity to read `st.container` / `st.session_state`
code — the library hides most of the session-management plumbing, so deep
Streamlit expertise is not required.

## Learning objectives

After this track you will be able to:

1. Explain what `streamlit-coco` does, and when it applies versus using the
   CoCo CLI or the SDK directly (see the README's "When not to use" section).
2. Install the library, connect it to a Snowflake account, and run each
   bundled example app (`make chat`, `make backlog`, `make bi-semantic`, `make
   headless`, …).
3. Build a Streamlit app using the preferred pattern — `panel()` +
   `chat_input_bar()` — with `require_approval_for` configured so destructive
   tools pause for a human decision.
4. Configure `CocoOptions` for a real workflow and embed `copilot_rail()`
   into an existing multipage app.
5. Diagnose a session that fails to connect or a tool that will not run,
   using `check_environment()`, `STREAMLIT_COCO_DEBUG`, and the Technical
   Guide's [help reference](../technical-guide/help.html).

## Time estimate

| Module | Time |
| --- | --- |
| `intro.md` (this page) | 10 min |
| [`setup.md`](setup.html) | 20–30 min |
| [`guided-tour.md`](guided-tour.html) | 20–30 min |
| [`hands-on.md`](hands-on.html) — 6 exercises | 120–150 min |
| [`demo-guide.md`](demo-guide.html) — read-through + one dry run | 30–40 min |
| **Enablement total** | **~3.5–4.5 hours** |

The training cases ([`01-simple`](../training/01-simple.html),
[`02-intermediate`](../training/02-intermediate.html),
[`03-advanced`](../training/03-advanced.html)) are a separate track, budgeted
20–30, 45–60, and 30–45 minutes respectively.

## Prerequisites

- Python 3.10+ and `uv` installed locally.
- A Snowflake account with **Cortex Code access**, and a working
  `~/.snowflake/connections.toml` (legacy `config.toml` also works) — or the
  Snowflake CLI's default connection.
- The **CoCo CLI** (`cortex`) installed and reachable on `PATH` (verify with
  `cortex --version`), or a path you can set via `CORTEX_CODE_CLI_PATH`.
- Git access to the development repository
  (`github.com/DevoteamSP/streamlit-coco-dev`) if you plan to run the
  bundled examples, or just `pip install "streamlit-coco[sdk]"` if you only
  need the published package.
- Nothing beyond that: no dedicated Snowflake warehouse is required to work
  through this track — the examples default to read-only sample data or
  disconnected fixtures.
