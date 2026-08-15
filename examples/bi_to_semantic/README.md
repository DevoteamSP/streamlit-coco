# BI → Semantic

Example app for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco): read a pile of
**Tableau** workbooks and/or **Power BI** reports, surface KPI and access-rule drift,
arbitrate with a human, then write **one semantic view**, **one row access policy**,
and a **Streamlit consumer** of that view (disconnected by default — no warehouse
required).

This is **not** a pixel-perfect BI clone and **not** chat-with-your-data. See [PRD.md](PRD.md).

## Run

From the repo root:

```bash
make install
make bi-semantic
```

`make tableau-semantic` is a deprecated alias for the same target.

Or, from this folder (editable **repo** `streamlit-coco`; PyPI `0.1.7` includes `app_viewer` + `copilot_rail`):

```bash
cd examples/bi_to_semantic
uv sync
uv run streamlit run app.py
```

`make bi-semantic` uses the repo checkout of `streamlit-coco` (so it tracks this
tree) and pulls in `streamlit-extras` (`resizable_columns` for the Copilot / Preview split).
From **`0.1.6`**, `copilot_rail()` / `preview_chars=` ship on PyPI. From **`0.1.7`**, so does `app_viewer()`.

## Screens (Welcome + slice 1–6)

| # | Screen | Library primitive | Needs |
|---|---|---|---|
| — | Welcome | orientation (what / what happens / how) | nothing |
| 1 | Load | `cwd_uploader` / fixture copy | nothing |
| 2 | Estate map | Deterministic Tableau `.twb` XML and/or Power BI `.pbix` → Graphviz | nothing |
| 3 | KPI inventory | Deterministic calculated fields / DAX measures | nothing |
| 4 | Access-rule comparator | Power BI table contracts (or RLS) parsed locally; Tableau User Filters via Copilot | CoCo for Tableau |
| 5 | Arbitration | `request_input(schema=…)` | CoCo env optional |
| 6 | Generate | Write approval (SV + RAP) · Streamlit **Build with python** or **Build with CoCo** (save brief, then generate) · disconnected preview | CoCo for Write / CoCo generator; nothing for disconnected run |

Screens **2–3** are deterministic parse — no Copilot job.
Screens **4 / 6** share **one** Copilot session on the right; buttons only **queue a job**.

Screens **7–8** (question set + headless evaluation) are deferred.

### What needs a Snowflake warehouse?

| Screens | Needs |
|---|---|
| 1–3 | Nothing (Load + deterministic estate map + KPI inventory). |
| 4–5 | CoCo (CLI) for Tableau access extract + optional chat. Power BI table contracts need no agent. No warehouse. |
| 6 | Nothing extra to *generate* the SQL; warehouse only to *deploy*. **Deterministic** Streamlit + disconnected preview need no account. **CoCo** generator needs the CLI. |

A contributor without a Snowflake account can run screens 1–6 against the bundled
fixtures and see real extraction + generated SQL under `out/`.

## Fixtures

Sources are **not** copied into this folder until you load a pack.

| Pack | Button | Punchline | Licence |
|---|---|---|---|
| Tableau Server | **Use MIT Tableau Server pack** | `ts_content.twb` + `ts_users.twb` — project-leader User Filter present vs dropped | **MIT © Tableau** — [`examples/tableau_legacy/`](../tableau_legacy/) |
| Power BI Obvience | **Use MIT Power BI pack** | `Customer Profitability Sample (auto).pbix` + `Corporate Spend.pbix` — same `Fact` / `Scenario` / `Date` names, none agree | **MIT © Microsoft** — [`examples/powerbi_legacy/`](../powerbi_legacy/) |

Uploads accept `.twb` / `.twbx` and `.pbix` / `.pbit` (plus TMDL / `report.json` fragments).

Agent cwd: `examples/workspaces/bi_to_semantic/` (gitignored).  
Artifacts: `examples/bi_to_semantic/out/` (gitignored) — step JSON
(`estate_map.json`, `kpi_inventory.json`, `access_rules.json`, `decisions.json`),
generated SQL/YAML, and `out/streamlit_dash/` (deterministic) plus
`out/streamlit_dash_coco/` (CoCo-authored).
**Preview** (header) runs the selected tree in disconnected mode: Python at
`http://127.0.0.1:8511`, CoCo at `http://127.0.0.1:8512`. Copilot and Preview
can open together; Preview is `st_coco.app_viewer()` and **Fix with CoCo** queues a job.

## Layout

```
app.py                 entry + nav
screens/               one module per screen
contracts/             JSON Schemas for structured payloads
engine/                extract prompts, Tableau + Power BI parse, generate SQL/YAML, state
out/                   generated artifacts (gitignored)
```

Semantic view deploy SQL follows atomic-studio's
`SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` wrap — not hand-rolled `CREATE SEMANTIC VIEW` DDL.
