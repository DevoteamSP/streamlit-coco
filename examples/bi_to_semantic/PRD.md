# PRD — `bi_to_semantic`

**Status:** Ships in streamlit-coco **`0.1.7`** as **BI → Semantic** (Tableau + Power BI; Tableau path first shipped in `0.1.6`)
**Owner:** Laurent Letourmy
**Kind:** streamlit-coco example app (public, ships in `examples/`)
**Last updated:** 2026-08-14

> An example app that reads Tableau workbooks and/or Power BI reports, shows what
> is actually inside them, and moves the KPI logic and the access rules down into
> Snowflake — one semantic view, one row access policy — then generates a Streamlit
> app that **must** consume that view (live via `SEMANTIC_VIEW(...)`, or disconnected
> on sample frames).
>
> **Demo packs:** Tableau `ts_content` + `ts_users` (MIT — project-leader branch
> present vs dropped). Power BI `Customer Profitability Sample (auto)` +
> `Corporate Spend` (MIT © Microsoft — colliding `Fact` / `Scenario` / `Date`).
> The full MIT Tableau set of four remains under `examples/tableau_legacy/`.

---

## 1. Why this example exists

`streamlit-coco` needs an example that is not a chat window. The library's real
argument is that an agent can be embedded in an app, **act** on things, and be
governed while doing it. That argument needs a use case where the acting matters and
the governance is the point.

Reading a BI estate is that use case, for three reasons:

1. **The source is unmodelled.** A `.twb` is XML on disk; a Power BI project is
   TMDL + JSON (or a `.pbix` ZIP). Neither is in a semantic view, catalogue, or
   warehouse. Snowflake Intelligence cannot see it. The only way in is an agent
   with `Read` / `Glob` / `Grep` — which is exactly what CoCo is — plus a
   deterministic parser for the demo packs.
2. **The output is a platform object**, not a document. `CREATE SEMANTIC VIEW` and
   `CREATE ROW ACCESS POLICY` are code. They can be reviewed, approved, diffed, and
   tested.
3. **Every stage has a genuine reason to use a different library primitive.** That is
   what makes it an example of the library rather than an app that happens to import it.

### Non-goals

- **Not a pixel-perfect Tableau or Power BI clone.** Screen 6 emits a Streamlit *consumer* of the
  semantic view (same dashboards, different rendering). Viz-for-viz fidelity is out of
  scope; binding every query to `SEMANTIC_VIEW(...)` is in scope.
- **Not a modelling methodology.** No domains, no maturity model, no operating model.
  The app produces two Snowflake objects, a Streamlit consumer, and (later) a test suite.
- **Not a chat-with-your-data app.** That is Snowflake Intelligence's job. This app
  produces the semantic view that *makes* Snowflake Intelligence work — and a Streamlit
  app that is forced to use it.
- **Not production tooling.** It is an example. It is allowed to be opinionated and
  narrow.

---

## 2. The argument the app has to make on screen

> Your KPI definitions and your access rules are not in your platform.
> They are in your dashboards, duplicated, and they no longer agree with each other.

Two findings carry it, both measured on the bundled fixtures:

**KPI drift.** `AdventureWorksDW-InternetSales` defines `Margin %`,
`Avg Order Value`, `Discount Rate` as workbook-local calculated fields. Every workbook
carries its own copy of the truth.

**Access-rule drift — the stronger finding.** The four Tableau Server workbooks each
implement a `User Filter` calculated field. They are *not* copies:

| Workbook | Access rule | Length |
|---|---|---|
| `ts_content` | server admin → site admin → project owner → **project leader** → item owner | 1256 |
| `ts_web_requests` | same shape, bound to different columns (`[name (system_users) #2]`) | 1253 |
| `ts_events` | admins merged into one concatenated string; project owner via an opaque `Calculation_1139973721156337666`; **no project-leader branch** | 1050 |
| `ts_users` | **shortest** — project owner and project leader dropped; last rule changes meaning to "the user being described" | 934 |

A Project Leader can see a row in one dashboard and not in another. Nobody can find
that out without diffing four XML files by hand. **This is real, unmodified content
published by Tableau — not a scenario built to make the point.**

---

## 3. Fixtures

| Estate | Carries | Licence | Ships publicly |
|---|---|---|---|
| `examples/tableau_legacy/workbooks/` — 4 × `.twb`, Tableau Server ops | the access-rule argument; 98 calculated fields, 20 duplicated across workbooks, 14 with divergent formulas | **MIT © Tableau** — attribution in the folder | **Yes** |
| `examples/powerbi_legacy/` — Customer Profitability + Corporate Spend `.pbix` | colliding `Fact` / `Scenario` / `Date` on the Obvience `IP` warehouse; no RLS in public MIT samples | **MIT © Microsoft** — attribution in the folder | **Yes** |
| AdventureWorks Tableau workbooks | the KPI argument — `Margin %`, `Avg Order Value`, `Discount Rate` | **Unverified** — community-sourced | **No, until cleared** |

**Open decision (blocks the public release, not the demo):** either clear the
AdventureWorks workbooks' licence, or author two small business workbooks on the
AdventureWorks schema in-house. If authored in-house, say so in the article and in this
README — a real estate for the access-rule finding, an authored one to illustrate KPI
drift. Readers forgive fabricated material that is announced; they do not forgive
finding out.

The reconstructed Snowflake schema for the Tableau Server estate already exists in
`examples/tableau_legacy/sql/` — 28 tables, 509 columns, 26 foreign keys, ~221 000
synthetic rows, loaded and integrity-checked.

---

## 4. Screens

Eight screens, each with one reason to exist and one library primitive to demonstrate.

### Screen 1 — Load

Drop `.twb` / `.twbx` / `.pbix` / `.pbit` files, or pick a bundled fixture pack
(Tableau MIT or Microsoft Power BI).

- **Primitive:** `cwd_uploader()` / `upload_to_cwd()` (shipped 0.1.5).
- **Agent:** none. Deterministic.
- **Out:** files in the agent's `cwd`.

### Screen 2 — Estate map

A visual of what is in the pile: entities, joins between them, and which workbook
touches what. This screen is why someone opens the app.

- **Primitive:** agent with `Read` / `Glob` / `Grep`, **structured output** routed into
  the app's own widgets — not a text transcript.
- **Agent emits:**
  ```
  { "tables": [{name, columns:[{name, type}]}],
    "joins":  [{left_table, left_column, right_table, right_column, workbooks:[...]}],
    "workbook_usage": [{workbook, tables:[...], worksheets:int, dashboards:int}] }
  ```
- **Shows:** graph of entities and joins; tables touched by more than one workbook
  highlighted — that overlap is what a shared semantic view is for.

### Screen 3 — KPI inventory

Every calculated field, grouped by name, with conflicts surfaced.

- **Primitive:** structured output, batched over workbooks.
- **Agent emits:**
  ```
  { "metrics": [{ name, workbooks:[...], definitions:[{workbook, formula, aggregation}],
                  is_conflicting: bool, plain_english: str }] }
  ```
- **Shows:** a table sorted so conflicts come first. `plain_english` is the
  re-documentation — the thing nobody has ever written down.

### Screen 4 — Access-rule comparator

**The screen that makes people sit up.** The `User Filter` implementations side by
side, common branches greyed, divergences coloured.

- **Primitive:** structured output + app-owned rendering. No agent chat visible.
- **Agent emits:**
  ```
  { "access_rules": [{ workbook, branches: [{ condition, grants_to, source_columns:[...] }],
                       plain_english: str }],
    "divergences": [{ branch, present_in:[...], absent_from:[...], consequence: str }] }
  ```
- **Shows:** four columns, one per workbook. Each row is a branch of the rule.
  `consequence` is rendered as plain text under the table — *"a Project Leader sees
  this content in ts_content and not in ts_users."*

### Screen 5 — Arbitration

The human decides. One metric at a time, one access branch at a time.

- **Primitive:** `request_input` with multi-field `schema=` — the human-in-the-loop
  primitive, used for a judgement call rather than a permission.
- **Per metric:** pick the canonical formula (or write one), name it, confirm the
  plain-English definition.
- **Per access branch:** keep / drop / merge, and say why.
- **Out:** a decision record. Every downstream artifact traces back to a decision made
  here, and the app shows that provenance.

### Screen 6 — Generate (two steps)

**Step 1 — Semantic view + row access policy.** Emit the two Snowflake objects.

- **Primitive:** **`Write` approval with unified diff preview** — the agent proposes
  the DDL, the human reads a diff, and approves or denies.
- **Artifacts:**
  - `semantic_view.yaml` / `semantic_view.sql` — Cortex Analyst model wrapped in
    `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` (atomic-studio syntax; do not re-derive).
  - `row_access_policy.sql` — one policy expressing the arbitrated rule, plus
    `ALTER TABLE … ADD ROW ACCESS POLICY`.
- **The point to make visible:** the rule that lived in the BI layer now lives once,
  below it, and applies to every consumer — Tableau, Snowflake Intelligence,
  notebooks, **and the Streamlit app in step 2**.

**Step 2 — Streamlit app for selected dashboards / report pages.** Migrate the chosen
dashboards into a Streamlit app that is a **mandatory consumer of the generated
semantic view**.

- **Primitive:** two generators, same contract. With **2 · Streamlit app**
  selected, a **How to build** segmented control sits beside the step control
  (**Python · faster** / **CoCo · enhanced**). The matching builder is full
  width. Step and build mode persist when Copilot opens. CoCo: **Save Brief**
  writes `out/streamlit_dash_coco/BRIEF.md`; **Generate with CoCo** stays
  disabled until that file matches the editor. Reopening the app reloads the
  saved brief from disk. If the CoCo tree has more than one `.md` file
  (`BRIEF.md`, `README.md`, …), pills switch which file the editor shows.
- **Picker:** pills of Tableau dashboards. Caption shows dashboard / worksheet
  counts and the semantic view FQN.
- **Generated trees:**
  - `out/streamlit_dash/` — Python-built app
  - `out/streamlit_dash_coco/` — CoCo-authored app (same contract, different UI)
  Each tree:
  - `streamlit_app.py` — dashboard UI
  - `sv.py` — `SEMANTIC_VIEW(...)` SQL builder; live vs disconnected
  - `spec.json` — provenance (decision ids, view FQN, selected dashboards)
  - `data/disconnected.json` — sample frames with the *shape* of the view
  - `semantic_view.yaml` — copy of the step-1 model
- **Disconnected mode (default):** the app runs with no warehouse and no credentials.
  Every widget still *claims* the semantic view; values come from sample frames.
  This is how a contributor without Snowflake sees the migrated UX.
- **Live mode:** `st.connection("snowflake")` + `SELECT * FROM SEMANTIC_VIEW(...)`
  only. Never `SELECT` from base tables. If live fails, the UI says so — it does
  not silently query `USERS` / `HISTORICAL_EVENTS`.
- **Run on the fly:** **Preview** (header) can sit beside Copilot (preview |
  Copilot). The split uses `streamlit_extras.resizable_columns`. Chrome is
  `st_coco.app_viewer()` (mode pills stay in the example). **Full width**
  hides the wizard when Copilot is closed. **Run** starts `streamlit run` on
  `127.0.0.1:8511` (Python) or `:8512` (CoCo), disconnected or live, and embeds it in that panel; **Stop** /
  **Open**. If the preview log shows an uncaught exception, **Fix with CoCo**
  queues `default_fix_prompt`. Building with python opens Preview automatically. The pane previews
  whichever generator is selected (**Python · faster** / **CoCo · enhanced**).
- **Disconnected studio:** for the Python-built app, the Preview panel renders
  the layout inline on sample frames until **Run**. CoCo's layout is only visible
  via **Run** (iframe).
- **The point to make visible:** the dashboard is no longer the source of truth.
  It is a client of the same objects Snowflake Intelligence will use.

### Screen 7 — Question set

Generate the test suite from the semantic view, using the **published** `question.yaml`
specification (*Testing Snowflake Intelligence at Scale*, §3).

- **Primitive:** structured output, batched.
- **Emits** one YAML per question with `id`, `question`, `expected_behavior`,
  `category`, `tags`, `expected_rules`, `evaluation.expected_tools`,
  `evaluation.expected_output.validates`.
- **Must include `should_decline` questions.** A question that tries to read a row the
  caller is not entitled to is how the row access policy gets tested. Without these the
  suite proves nothing about governance.

### Screen 8 — Evaluation

Run the suite and score it.

- **Primitive:** **headless `query()` / `session.run()` — no Streamlit in the loop.**
  This is the screen that matters most to a library audience: the same session API runs
  outside the UI, so the suite runs in CI.
- **Shows:** pass / fail per question, per `expected_rule`; `should_decline` questions
  reported separately, because a governance failure is not the same class of problem as
  a wrong number.
- **Emits:** a JSON report a CI job can consume.

---

## 5. What runs without a Snowflake account

Screens 1–7 read files and produce files. Screen 8 needs Cortex and a warehouse.

State this plainly in the README, the way the e2e harness does. A contributor without a
Snowflake account should be able to run most of the app on the MIT fixtures and see
real output.

| Screens | Needs |
|---|---|
| 1–5 | CoCo (CLI or API mode) for access extract; estate/KPI/arbitration are local. No warehouse. |
| 6 step 1 | Nothing extra to *generate*; a warehouse to *deploy*. |
| 6 step 2 | Nothing for the **deterministic** + **disconnected** preview. CoCo CLI for the **CoCo** generator. Warehouse + deployed view for **live**. |
| 7 | CoCo. |
| 8 | Snowflake account, Cortex, deployed semantic view. |

---

## 6. Layout

```
examples/bi_to_semantic/
├── README.md              what it is, what runs without an account
├── PRD.md                 this file
├── app.py                 entry point + nav
├── screens/               one module per screen
├── contracts/             JSON Schemas for every structured-output payload
├── engine/
│   ├── extract.py         prompts + parsing for screens 2–4
│   ├── generate.py        semantic view + row access policy
│   ├── streamlit_app_gen.py  BI dashboards → Streamlit consumer
│   └── evaluate.py        headless question-set runner (deferred)
└── out/                   generated artifacts (gitignored)
    ├── streamlit_dash/      Python-built migrated app
    └── streamlit_dash_coco/ CoCo-authored migrated app
```

On a new Streamlit session, screens 2–5 hydrate from `out/*.json` if those files
exist (estate map, KPI inventory, access rules, decisions). A saved
`out/streamlit_dash_coco/BRIEF.md` is loaded back into the CoCo brief editor.
Workbooks already in the workspace are listed on Load without copying again.

Fixtures are **not** copied here — Tableau pack points at
`examples/tableau_legacy/workbooks/`; Power BI pack at `examples/powerbi_legacy/`.

---

## 7. Demo script — 8 minutes

Fixture: **`ts_content` + `ts_users`** (MIT pack subset — clearest access divergence).

| # | Beat | Say |
|---|---|---|
| 1 | Show one `.twb` as raw XML. Two seconds. | *"This is what nobody opens."* |
| 2 | Load the two-workbook pack. Estate map appears. | *"Two dashboards, one model underneath — they just never agreed to share it."* |
| 3 | KPI inventory. Point at a duplicated definition. | *"Every dashboard carries its own copy of the truth."* |
| 4 | **Access comparator.** Let it land. | *"Same User Filter name. Project Leader is in ts_content and gone from ts_users. Tableau's own published content."* |
| 5 | Arbitrate one metric and one access branch. Deny the agent's first proposal on purpose. | *"No — that branch matters, keep it. This is why it doesn't run alone."* |
| 6 | Generate step 1. Read the diff. Approve. | *"One definition. One policy. Below the BI layer."* |
| 6b | Generate step 2. Build with python (Preview rail opens). Then CoCo: save brief → generate. Run disconnected in the Preview panel. | *"Same view, two clients — one written in Python, one the agent wrote. Neither talks to base tables."* |
| 7 | Deploy, then ask the question in Snowflake Intelligence. | *"It answers. And it's the same number, whoever asks."* |
| 8 | Run the suite. Show the scoreboard, including a `should_decline` pass. | *"And here's the proof it stays true tomorrow."* |

**Deliberately deny one proposal at beat 5.** A demo that goes perfectly reads as
scripted; a demo that gets corrected in front of the room reads as real — and it
demonstrates the approval gate better than any explanation.

**End on the scoreboard, not on the answer.** The answer proves it works. The
scoreboard proves it is engineering.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Beat 7 fails live — the generated semantic view does not answer | Rehearse on **both** estates. Have the deployed view pre-created as a fallback and say so if used. |
| The estate map is visually weak — a boring graph kills screen 2 | Screen 2 is the reason people open the app. Design it first, not last. |
| Agent output is unstable across runs | Every structured payload is schema-validated; the app renders from the payload, never from free text. |
| AdventureWorks licence unresolved | Ship publicly with the MIT estate only; author the business workbooks in-house. |
| Reads as a consulting tool | No domains, no archetypes, no maturity model. Two Snowflake objects, one Streamlit consumer, a test report. |
| Streamlit preview collides with the wizard port | Python preview is **8511**, CoCo is **8512** — neither uses 8501. |

---

## 9. Acceptance criteria

1. Runs from a clean clone against the bundled MIT fixtures, screens 1–7, with no
   Snowflake warehouse.
2. Screen 4 shows the two access rules (`ts_content` vs `ts_users`) and names at least one concrete divergence in
   plain English (project leader).
3. Screen 6 step 1 produces a semantic view and a row access policy that deploy without
   manual editing.
4. Screen 6 step 2 can write a Streamlit app two ways: **Build with python**
   (`out/streamlit_dash/`) and **Build with CoCo** (save brief →
   `out/streamlit_dash_coco/BRIEF.md`, then generate). Both query only via `SEMANTIC_VIEW(...)` in live
   mode, and run in **disconnected** mode with no Snowflake account. **Run**
   starts the selected tree on a local port.
5. Screen 8 runs headless — a CI job can invoke it with no Streamlit process — and
   emits a machine-readable report.
6. At least one `should_decline` question in the generated suite exercises the row
   access policy and passes.
7. Every generated artifact traces back to a decision made on screen 5.

---

## 10. Related

- Fixtures and reconstructed schema: [`../tableau_legacy/README.md`](../tableau_legacy/README.md)
- Power BI MIT pack: [`../powerbi_legacy/README.md`](../powerbi_legacy/README.md)
- Question specification: *Testing Snowflake Intelligence at Scale — A Question-Driven
  Validation Framework*, [DevoteamSP/public](https://github.com/DevoteamSP/public)
- Semantic view generation: `atomic-studio` (existing generator — reuse, do not rewrite)
- Library primitives: [`doc/features/`](../../doc/features/) — file-upload, approvals,
  structured-output, headless, [copilot-rail](../../doc/features/copilot-rail/copilot-rail.md)
