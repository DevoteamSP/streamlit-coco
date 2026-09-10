# Roadmap — streamlit-coco

Living plan. Product detail: `[doc/prd.md](prd.md)`. Shipped history: `[CHANGELOG.md](../CHANGELOG.md)`.

**Status:** Alpha `0.1.9` ([pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/)). Rail TOML picker shipped. Next: API mode.  
**Publisher:** temporary Trusted Publisher on `[lletourmy/streamlit-coco](https://github.com/lletourmy/streamlit-coco)`; public tree also synced to `[DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)`.  
**Last updated:** 2026-09-10  
**This cut:** `[releases/0.1.9/](releases/0.1.9/)`  
**Next cuts:** `0.2.0` local API (no CLI) → `0.2.5` Streamlit in Snowflake → `0.3.0` Native App

> **Before every release:** complete `[releases/X.Y.Z/CHECKLIST.md](releases/README.md)` (CHANGELOG, this roadmap, PRD, screenshots, [public issues](https://github.com/DevoteamSP/streamlit-coco/issues)) and outreach under `[../doc-dev/releases/](../doc-dev/releases/README.md)`, then `[deployment/publish.md](deployment/publish.md)`.

**Regularly check version of sdk:** at `[CoCo Python SDK](https://pypi.org/project/cortex-code-agent-sdk/)`

---



## Now — toward `0.2.0`


| Priority | Item | Ref |
| -------- | ---- | --- |
| P0 | **API mode** — `CocoOptions.mode="api"` + Snowflake Sandbox; CLI optional | [#4](https://github.com/DevoteamSP/streamlit-coco-dev/issues/4) · [remote-api](features/remote-api/remote-api.md) |


Manual checklists: `[doc/features/README.md](features/README.md)` — re-run before the next tag.

---



## v0.1.7 — Community sample apps

Shipped in `0.1.7`. First-party examples, not the API-mode cut. Publisher switch and FR-S2 stay on `0.2.0`.


| Item                                                                                              | Ref                                                                      |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ✅ Rename Tableau → Semantic to **BI → Semantic**; Load Tableau **or** Power BI                    | `examples/bi_to_semantic`, `make bi-semantic`                            |
| ✅ MIT Power BI pack + `pbixray` as the primary `.pbix` reader                                     | `[examples/bi_samples/powerbi/](../examples/bi_samples/powerbi/)`        |
| ✅ Screen 4: colliding table contracts (`Fact` / `Scenario` / `Date`) — public samples have no RLS | [BRIEF](../examples/bi_to_semantic/BRIEF-powerbi-fixtures.md)            |
| ✅ Streamlit App Viewer (`app_viewer()`)                                                           | `[features/app-viewer/app-viewer.md](features/app-viewer/app-viewer.md)` |


---



## v0.1.8 — App Builder + rail UX

Shipped `2026-09-06`. First-party example + rail knobs. Publisher switch and FR-S2 stay on `0.2.0`.


| Item | Status | Ref |
| ---- | ------ | --- |
| App Builder host — Welcome · Library · Brief · Studio · Admin; named apps; topic pills; Admin CRUD (questions as tabs) | ✅ | `[features/app-builder/](features/app-builder/app-builder.md)` · `make app-builder` |
| Profile step + `infer:` — deterministic pandas for tabular / semantic-view (KPI demo fixture). Agent-run profile for documents/URLs (UC9) is later. | ✅ tabular / semantic-view | [UX §4](features/app-builder/UX.md) · `engine/profile.py` |
| Guidelines skills — shared pack + per-type `SKILL.md`; KPI has reference app + `CHECKLIST.md` + one automatic self-check pass after Write | ✅ | `types/shared/` · `types/semantic-kpis/` · [UX §6.1a](features/app-builder/UX.md) |
| Live types — KPI presentation, Data quality, Call transcription, Meeting recap, Prompt library, CSV explorer. `doc-compare` and every `urls` type are later. | ✅ | [UX §5.3](features/app-builder/UX.md#53-catalog-content) |
| Example questions on the Copilot rail — after Connect, starter buttons (`title` + `question`); hover shows the full question; click sends that text to CoCo (or fills the chat input when `deferred=`). Hidden after the first turn or while a job is present. | ✅ | `[features/copilot-rail/](features/copilot-rail/copilot-rail.md)` · [`example_questions`](api.md#copilot_railsession--titlecopilot--) |
| Display config popover — icon-only Material button (`:material/display_settings:`); Last messages / First *n* characters pills + sliders; fragment-rerun keeps the popover open. Helper: `transcript_display_config()` | ✅ | `[features/copilot-rail/](features/copilot-rail/copilot-rail.md)` · [`transcript_display_config`](api.md) |


---



## v0.1.8.1 — Deferred example questions

Shipped `2026-09-07`. Patch on the `0.1.8` rail starters. Publisher switch and FR-S2 stay on `0.2.0`.


| Item | Status | Ref |
| ---- | ------ | --- |
| `copilot_rail(..., deferred=True)` — click copies the question into the chat input and does not run it. Per-item `deferred` on `{title, question}` (or a 3-tuple). Default remains send-on-click. | ✅ | `[features/copilot-rail/](features/copilot-rail/copilot-rail.md)` · [`deferred`](api.md#copilot_railsession--titlecopilot--) |
| BI → Semantic opts in (`deferred=True`). App Builder still sends on click. | ✅ | `make bi-semantic` |


---



## v0.1.9 — Connections TOML picker

Shipped `2026-09-10`. Rail connection popover can choose which Snowflake TOML to list. Publisher switch and FR-S2 stay on `0.2.0`.


| Item | Status | Ref |
| ---- | ------ | --- |
| `copilot_rail(..., toml_file=)` — Config file + Connection selectboxes on one row. Lists `~/.snowflake/*.toml`. A single file is used whatever its name. | ✅ | `[features/copilot-rail/](features/copilot-rail/copilot-rail.md)` · [`toml_file`](api.md#copilot_railsession--titlecopilot--) |
| Helpers `list_snowflake_connections()`, `list_snowflake_toml_files()`, `resolve_snowflake_config_path()`. App Builder / BI → Semantic use the picker. | ✅ | `make app-builder` · `make bi-semantic` |


---



## Use cases

Two lists, kept apart:

1. **Library / product UCs** — PRD §4.2 (`panel()`, pipeline builder, headless, …).
2. **App Builder session UCs** (UC1–UC10) — [UX.md](features/app-builder/UX.md) §2. Managed there, not here.

Product-shaped ideas (examples, RFCs, later catalogue types) live in this table. Tracker is the [public repo](https://github.com/DevoteamSP/streamlit-coco/issues). Do not file new issues until confirmed.


| Idea | Status | Home |
| ---- | ------ | ---- |
| Prompt library player (local or GitHub) | In `0.1.8` catalogue (local; GitHub source later) | `types/prompt-library` |
| Dashboard builder on a semantic view + agent client | Partial — KPI type is the dashboard slice; in-app agent is `ships_copilot` (later) | `types/semantic-kpis` · [UX §5.5](features/app-builder/UX.md) |
| Data quality solutions builder | In `0.1.8` catalogue | `types/data-quality` |
| Migration wizard | First-party slice shipped (`0.1.6` Tableau, `0.1.7` Power BI). Full cockpit still RFC. | `make bi-semantic` · [#10](https://github.com/DevoteamSP/streamlit-coco/issues/10) |
| FinOps costs explorer | Later catalogue card (`warehouse-spend`). Public example still open. | [UX §5.3](features/app-builder/UX.md#53-catalog-content) · [#5](https://github.com/DevoteamSP/streamlit-coco/issues/5) |
| Incident / query triage | Unscheduled example | [#6](https://github.com/DevoteamSP/streamlit-coco/issues/6) |
| Multi-persona workspaces | Unscheduled example | [#7](https://github.com/DevoteamSP/streamlit-coco/issues/7) |
| Napkin to App | Out of `0.1.8` (sketches *on* a type brief are in). RFC. | [#9](https://github.com/DevoteamSP/streamlit-coco/issues/9) |
| Self-extending app | Later | [#11](https://github.com/DevoteamSP/streamlit-coco/issues/11) |
| Native App skills marketplace / distribution | Later (`0.3.0`). One issue, not two. | [#12](https://github.com/DevoteamSP/streamlit-coco/issues/12) |

---



## v0.2.0 — API mode, local Streamlit (no CoCo CLI)

`streamlit run` on a laptop or VM. The SDK talks to the Snowflake Agent API (`mode="api"`). Bash / Read / Write run in **Snowflake Sandbox**, not on the host. The `cortex` CLI is not required.


| Item                                                                             | Ref                                                                                                      |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Wire `CocoOptions.mode="api"` + `snowflake_sandbox` through session / start gate | [#4](https://github.com/DevoteamSP/streamlit-coco-dev/issues/4)                                          |
| Env probe: CLI optional when API mode is set                                     | `[check_environment](../streamlit_coco/diagnostics.py)`                                                  |
| Feature doc + checklist                                                          | [remote-api](features/remote-api/remote-api.md)                                                          |
| Map `cwd` / uploads onto the sandbox workspace (`/workspace`, V-stage)           | [file-upload](features/file-upload/file-upload.md)                                                       |
| Least-privilege role documentation (SEC-02)                                      | [threat-model](security/threat-model.md)                                                                 |
| Approval audit log persistence (SEC-01)                                          | [threat-model](security/threat-model.md) · [#15](https://github.com/DevoteamSP/streamlit-coco/issues/15) |


CLI mode stays supported for local installs that already have `cortex` on `PATH`.

---



## v0.2.5 — API mode from Streamlit in Snowflake

Same Agent API + sandbox, but the Streamlit process **is** Snowflake (SiS). No CLI install, no laptop `connections.toml` — identity is the current Snowflake session.


| Item                                                     | Ref                                                   |
| -------------------------------------------------------- | ----------------------------------------------------- |
| SiS auth (current-user / session; not a PAT profile)     | PRD §8                                                |
| Start gate / env probe that does not require a local CLI | —                                                     |
| Deployment guide: Streamlit in Snowflake                 | [deployment/](deployment/README.md)                   |
| Session isolation for multi-user SiS apps                | [threat-model](security/threat-model.md) § scenario 3 |


---



## v0.3.0 — API mode from a Native App

Packaged Snowflake Native App: the consumer runs the Streamlit UI in their account; CoCo executes via API mode under the app’s granted privileges.


| Item                                                                | Ref             |
| ------------------------------------------------------------------- | --------------- |
| Application package + Streamlit UI that starts CoCo in `mode="api"` | —               |
| Provider / consumer privilege model for Agent API + sandbox         | —               |
| Skills marketplace / skills distribution inside the Native App      | Use cases above |


---



## Later



### App Builder — beyond `0.1.8`

- [ ] **Agent-run interview** replacing (or supplementing) the confirm-the-profile step — deliberately deferred out of `0.1.8`, not rejected. Wrong shape for `tabular`/`semantic_view` types today (a parser is faster and does not hallucinate a column name; see `[app-builder-v2.md](../doc-dev/briefs/app-builder-v2.md)` and [UX §9](features/app-builder/UX.md)); becomes the right shape once `documents`/`urls` types are live and users want to correct a proposed comparison schema by talking instead of through a form. Needs first: a no-CoCo fallback so room demos without an agent still work, `request_input(schema=…)` so interview answers land in `brief.json` as structured data, and the transcript persisted into the filled brief so **Regenerate** stays reproducible. See [UX §11](features/app-builder/UX.md) for the full design.
- [ ] `ships_copilot` — a generated app that embeds its own `copilot_rail()`, so the owner keeps shaping it after it leaves the builder. Scope to one type once the base catalogue is solid ([UX §5.5](features/app-builder/UX.md)).
- [ ] **Document comparison** (`doc-compare`) and the first `urls` type (`page-watch`) — UC9 host-fetch + comparison schema ([UX §6.1b](features/app-builder/UX.md)).
- [ ] Round out the later catalogue — spend explorer (`ACCOUNT_USAGE`), exception queue (write-back), feedback themes, invoice exceptions, docs tour, research digest ([UX §5.3](features/app-builder/UX.md)).



### Streaming & transcript UX

- [ ] Theming / a11y pass (native `panel()` transcript; keyboard traps, ARIA) — [#13](https://github.com/DevoteamSP/streamlit-coco/issues/13)
- [ ] Auto-scroll while streaming; stop when the user scrolls up — [#2](https://github.com/DevoteamSP/streamlit-coco/issues/2)



### Platform & packaging

- [x] Community sample apps (≥ 3) — Backlog Desk (`0.1.0`) + BI → Semantic (`0.1.6` / `0.1.7`) + App Builder (`0.1.8`)
- [ ] Docker / Kubernetes deployment guide — [#8](https://github.com/DevoteamSP/streamlit-coco/issues/8)
- [ ] Snowpark Container Services (SPCS) deployment guide — [#8](https://github.com/DevoteamSP/streamlit-coco/issues/8)
- [ ] Extend CoCo-free Playwright e2e coverage — [#14](https://github.com/DevoteamSP/streamlit-coco/issues/14)

---



## Out of scope (for now)

- Full IDE workspace
- MCP *product* servers (MCP passthrough via `mcp_servers` works today)
- Sub-agents
- Slack integration

---



## Success checks (90 days post-launch)

Public surface: [DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) · [pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/)  
Snapshot **2026-09-06** ([pypistats](https://pypistats.org/packages/streamlit-coco)): **506** downloads last month · **2** GitHub stars.


| Metric                    | Target                  | Current (2026-09-06)                                                          |
| ------------------------- | ----------------------- | ----------------------------------------------------------------------------- |
| PyPI downloads            | 500+ / month            | 506 last month (8 last day · 63 last week)                                    |
| GitHub stars              | 50+                     | 2 ([DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)) |
| Time-to-first-working-app | < 30 min via quickstart | —                                                                             |
| Community examples        | ≥ 3                     | 3 first-party (Backlog Desk, BI → Semantic, App Builder)                  |


