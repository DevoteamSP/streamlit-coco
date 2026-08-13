# Tableau → Semantic

Example app for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco): read a pile of
Tableau workbooks, surface KPI and access-rule drift, arbitrate with a human, then write
**one semantic view**, **one row access policy**, and a **Streamlit consumer** of that view
(disconnected by default — no warehouse required).

This is **not** a pixel-perfect Tableau clone and **not** chat-with-your-data. See [PRD.md](PRD.md).

## Run

From the repo root:

```bash
make install
make tableau-semantic
```

Or, from this folder (editable **repo** `streamlit-coco`; PyPI `0.1.6` also includes `copilot_rail`):

```bash
cd examples/tableau_to_semantic
uv sync
uv run streamlit run app.py
```

`make tableau-semantic` uses the repo checkout of `streamlit-coco` (so it tracks this
tree) and pulls in `streamlit-extras` (`resizable_columns` for the Copilot / Preview split).
From **`0.1.6`**, `copilot_rail()` / `preview_chars=` also ship on PyPI.

## Screens (slice 1–6)

| # | Screen | Library primitive | Needs |
|---|---|---|---|
| 1 | Load | `cwd_uploader` / fixture copy | nothing |
| 2 | Estate map | Deterministic `.twb` XML parse → Graphviz | nothing |
| 3 | KPI inventory | Deterministic calculated-field parse | nothing |
| 4 | Access-rule comparator | Copilot rail + app UI | CoCo |
| 5 | Arbitration | `request_input(schema=…)` | CoCo env optional |
| 6 | Generate | Write approval (SV + RAP) · Streamlit **Build with python** or **Build with CoCo** (save brief, then generate) · disconnected preview | CoCo for Write / CoCo generator; nothing for disconnected run |

Screens **2–3** are deterministic XML parse — no Copilot job.
Screens **4 / 6** share **one** Copilot session on the right; buttons only **queue a job**.

Screens **7–8** (question set + headless evaluation) are deferred.

### What needs a Snowflake warehouse?

| Screens | Needs |
|---|---|
| 1–3 | Nothing (Load + deterministic estate map + KPI inventory). |
| 4–5 | CoCo (CLI) for access extract + optional chat. No warehouse. |
| 6 | Nothing extra to *generate* the SQL; warehouse only to *deploy*. **Deterministic** Streamlit + disconnected preview need no account. **CoCo** generator needs the CLI. |

A contributor without a Snowflake account can run screens 1–6 against the MIT fixtures and
see real extraction + generated SQL under `out/`.

## Fixtures

Workbooks are **not** copied into this folder. Use **Load → Use MIT Tableau Server pack**,
which copies **`ts_content.twb` + `ts_users.twb`** from
[`examples/tableau_legacy/workbooks/`](../tableau_legacy/workbooks/)
(**MIT © Tableau** — attribution in that README). Those two carry the access-rule
punchline (project leader present vs dropped). The other two MIT workbooks stay in
`tableau_legacy` for reference but are not loaded by default.

Agent cwd: `examples/workspaces/tableau_to_semantic/` (gitignored).  
Artifacts: `examples/tableau_to_semantic/out/` (gitignored) — step JSON
(`estate_map.json`, `kpi_inventory.json`, `access_rules.json`, `decisions.json`),
generated SQL/YAML, and `out/streamlit_dash/` (deterministic) plus
`out/streamlit_dash_coco/` (CoCo-authored).
**Preview** (header, same right-hand slot as Copilot) runs the selected tree at
`http://127.0.0.1:8511` in disconnected mode.

## Layout

```
app.py                 entry + nav
screens/               one module per screen
contracts/             JSON Schemas for structured payloads
engine/                extract prompts, generate SQL/YAML, state
out/                   generated artifacts (gitignored)
```

Semantic view deploy SQL follows atomic-studio's
`SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` wrap — not hand-rolled `CREATE SEMANTIC VIEW` DDL.
