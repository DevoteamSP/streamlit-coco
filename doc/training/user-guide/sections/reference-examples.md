# Example apps reference

Each first-party example app under `examples/`, what it demonstrates, how to
run it, and what it needs. See [Command reference](reference-commands.html)
for the underlying `make` targets and [Outputs](outputs.html) for the files
each one produces.

## `chat_app.py`

Run with `make chat`. Demonstrates the preferred integration pattern:
`check_environment()` → `render_start_gate()` → `get_or_create_session()` →
`panel()` + `chat_input_bar()`. Its sidebar includes a test-prompt runner
backed by `examples/testdata/prompts.json`. Needs a Snowflake connection with
Cortex Code access.

## `approval_gate.py`

Run with `make approval`. Demonstrates the legacy CCv2 `chat()` all-in-one
widget instead of `panel()` — useful as a reference for apps still on the
older API. Needs a Snowflake connection.

## `structured_output.py`

Run with `make structured`. Demonstrates `output_schema` plus
`on_structured_output`, routing the agent's JSON into a widget instead of
chat text. Needs a Snowflake connection.

## `headless_pipeline.py`

Run with `make headless`. Pure async Python with no Streamlit import; drives
`query()` and `CocoSession` from a terminal, each in its own event loop.
Needs a Snowflake connection; produces no browser UI.

## `cwd_upload_chat.py`

Run with `make cwd-upload`. Demonstrates `chat_input_bar(accept_file=...)`
and `cwd_uploader()` — browser uploads written into the agent's `cwd`. Needs
a Snowflake connection for the agent turns; the upload mechanics themselves
do not.

## `backlog_desk/`

Run with `make backlog`. A multipage Product Backlog Desk: file/JSON-backed
(no SQL), with Board / Epic / Ticket / Release pages and a right-rail
Copilot opened from a header **Copilot** button or an action link (closed
with **Close** — it is not a navigation page). Its Copilot ships four
prompt-based skills (not `.cortex/skills/` orchestration skills): Summarize
sprint, Draft release notes (approval-gated), Propose ticket update
(approval-gated), Check definition of done. Data lives under
`data/{epics,tickets,releases,policies}`. This is the first-party example of
a rail embedded in a non-SQL, non-chat product. Needs a Snowflake connection
for the Copilot; the Board/Epic/Ticket/Release pages themselves read only
local JSON.

## `bi_to_semantic/`

Run with `make bi-semantic` (alias: `make tableau-semantic`, deprecated).
Reads Tableau (`.twb`/`.twbx`) and/or Power BI (`.pbix`/`.pbit`) workbooks,
surfaces KPI and access-rule drift, arbitrates disagreements through
`request_input(schema=...)`, and writes one semantic view, one row access
policy, and a generated Streamlit consumer app (disconnected by default, no
warehouse required to view it). Six screens: Welcome, 1 Load, 2 Estate map
(deterministic parse), 3 KPI inventory (deterministic), 4 Access-rule
comparator (Power BI parsed locally; Tableau parsed via CoCo), 5 Arbitration
(`request_input`), 6 Generate (Write approval + preview). Screens 2 and 3
need no CoCo agent or warehouse; screen 4's Tableau path and screen 6 do.
Sample fixtures (MIT-licensed Tableau Server pack and Power BI Obvience
pack) live under `examples/bi_samples/`. The agent's `cwd` for this example
is `examples/workspaces/bi_to_semantic/` (gitignored). Preview: a Python
(deterministic) consumer on `127.0.0.1:8511` and a CoCo-authored consumer on
`:8512`, both via `app_viewer()`. JSON Schemas for the intermediate
artifacts live under `examples/bi_to_semantic/contracts/`. See
[Outputs](outputs.html) for exact file names.

## `app_builder/`

Run with `make app-builder`. Guided Streamlit-app generation for business
users. Pages: Welcome, Library (Resume and Create-a-new-project cards, with
a topic-pill filter), Brief (a free-text brief and sketches, or typed
questions), Studio (Build this app / regenerate; Open Copilot; Open Preview;
an App brief expander with Save / Save & regenerate), Admin (type CRUD and
guideline-skill editors). Each app type is `types/<id>/type.json` (its
catalog card) plus an optional `types/<id>/SKILL.md` (with `reference/` and
`CHECKLIST.md`) that CoCo reads via `add_dirs`; `types/shared/SKILL.md`
holds the generation rules common to every type and is not itself a catalog
card. The locked live type set is: KPI presentation, Data quality, Call
transcription, Meeting recap, Prompt library, CSV explorer — each declares a
`grounding_kind` (`tabular` / `semantic_view` / `documents` /
`urls`) that decides whether its profile step is a deterministic pandas
parser (`engine/profile.py`) or a CoCo job. Documents and URLs are fetched by
the host application, never by the CoCo session itself — no network tool is
granted to it. Generated output lands under `examples/app_builder/out/<slug>/`
(`brief.json`, `BRIEF.md`, `sketches/`, `streamlit_app.py`); preview runs on
port 8513. Needs a Snowflake connection for any type using a CoCo-driven
profile step or for Studio's Build/regenerate step.
