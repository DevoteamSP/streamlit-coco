# Roadmap — streamlit-coco

Living plan. Product detail: [`doc/prd.md`](prd.md). Shipped history: [`CHANGELOG.md`](../CHANGELOG.md).

**Status:** Alpha **`0.1.7`** prepared ([pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/) still shows `0.1.6` until the tag).  
**Publisher:** temporary Trusted Publisher on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco); public tree also synced to [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco).  
**Last updated:** 2026-08-15  
**This cut:** [`releases/0.1.7/`](releases/0.1.7/)  
**Next cuts:** **`0.1.8`** App Builder → **`0.2.0`** local API (no CLI) → **`0.2.5`** Streamlit in Snowflake → **`0.3.0`** Native App

> **Before every release:** complete [`releases/X.Y.Z/CHECKLIST.md`](releases/README.md) (CHANGELOG, this roadmap, PRD, screenshots) and outreach under [`../doc-dev/releases/`](../doc-dev/releases/README.md), then [`deployment/publish.md`](deployment/publish.md).

> **Regularly check version of sdk:** at [`CoCo Python SDK`](https://pypi.org/project/cortex-code-agent-sdk/)

---

## Now — toward `0.1.8`

| Priority | Item | Ref |
| --- | --- | --- |
| P0 | **App Builder** for business users, including guidelines skills | — |

Manual checklists: [`doc/features/README.md`](features/README.md) — re-run before the next tag.

---

## v0.1.7 — Community sample apps

Shipped this cut. First-party examples, not the API-mode cut. Publisher switch and FR-S2 stay on `0.2.0`.

| Item | Ref |
| --- | --- |
| ✅ Rename Tableau → Semantic to **BI → Semantic**; Load Tableau **or** Power BI | `examples/bi_to_semantic`, `make bi-semantic` |
| ✅ MIT Power BI pack + `pbixray` as the primary `.pbix` reader | [`examples/powerbi_legacy/`](../examples/powerbi_legacy/) |
| ✅ Screen 4: colliding table contracts (`Fact` / `Scenario` / `Date`) — public samples have no RLS | [BRIEF](../examples/bi_to_semantic/BRIEF-powerbi-fixtures.md) |
| ✅ Streamlit App Viewer (`app_viewer()`) | [`features/app-viewer/app-viewer.md`](features/app-viewer/app-viewer.md) |

---

## v0.1.8 — App Builder

| Item | Ref |
| --- | --- |
| App Builder for business users, including guidelines skills | — |

---

## Use Cases ideas

- Prompt library player (local or github)
- Dashboard Builder (on Semantic View) + Agent client
- Native App "skills marketplace" (needs `0.3.0`)
- Native App for skills distribution (needs `0.3.0`)
- Data Quality solutions builder
- Migration wizard
- FinOps costs explorer
- Incident / query triage
- Multi-persona workspaces

---

## v0.2.0 — API mode, local Streamlit (no CoCo CLI)

`streamlit run` on a laptop or VM. The SDK talks to the Snowflake Agent API (`mode="api"`). Bash / Read / Write run in **Snowflake Sandbox**, not on the host. The `cortex` CLI is not required.

| Item | Ref |
| --- | --- |
| Wire `CocoOptions.mode="api"` + `snowflake_sandbox` through session / start gate | [#4](https://github.com/DevoteamSP/streamlit-coco-dev/issues/4) |
| Env probe: CLI optional when API mode is set | [`check_environment`](../streamlit_coco/diagnostics.py) |
| Feature doc + checklist | [remote-api](features/remote-api/remote-api.md) |
| Map `cwd` / uploads onto the sandbox workspace (`/workspace`, V-stage) | [file-upload](features/file-upload/file-upload.md) |
| Least-privilege role documentation (SEC-02) | [threat-model](security/threat-model.md) |
| Approval audit log persistence (SEC-01) | [threat-model](security/threat-model.md) |

CLI mode stays supported for local installs that already have `cortex` on `PATH`.

---

## v0.2.5 — API mode from Streamlit in Snowflake

Same Agent API + sandbox, but the Streamlit process **is** Snowflake (SiS). No CLI install, no laptop `connections.toml` — identity is the current Snowflake session.

| Item | Ref |
| --- | --- |
| SiS auth (current-user / session; not a PAT profile) | PRD §8 |
| Start gate / env probe that does not require a local CLI | — |
| Deployment guide: Streamlit in Snowflake | [deployment/](deployment/README.md) |
| Session isolation for multi-user SiS apps | [threat-model](security/threat-model.md) § scenario 3 |

---

## v0.3.0 — API mode from a Native App

Packaged Snowflake Native App: the consumer runs the Streamlit UI in their account; CoCo executes via API mode under the app’s granted privileges.

| Item | Ref |
| --- | --- |
| Application package + Streamlit UI that starts CoCo in `mode="api"` | — |
| Provider / consumer privilege model for Agent API + sandbox | — |
| Skills marketplace / skills distribution inside the Native App | Use cases above |

---

## Later

### Streaming & transcript UX
- [ ] Theming / a11y pass (native `panel()` transcript; keyboard traps, ARIA)

### Platform & packaging
- [ ] Community sample apps (≥ 3 contributed) — Backlog Desk (`0.1.0`) + BI → Semantic (`0.1.6` Tableau, **`0.1.7`** Power BI) + App Builder (`0.1.8`)
- [ ] Docker / Kubernetes deployment guide
- [ ] Snowpark Container Services (SPCS) deployment guide

---

## Out of scope (for now)

- Full IDE workspace
- MCP *product* servers (MCP passthrough via `mcp_servers` works today)
- Sub-agents
- Slack integration

---

## Success checks (90 days post-launch)

Public surface: [DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) · [pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/)  
Snapshot **2026-08-14** ([pypistats](https://pypistats.org/packages/streamlit-coco)): **319** downloads last month · **2** GitHub stars.

| Metric | Target | Current (2026-08-14) |
| --- | --- | --- |
| PyPI downloads | 500+ / month | 319 last month (83 last day · 224 last week) |
| GitHub stars | 50+ | 2 ([DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)) |
| Time-to-first-working-app | < 30 min via quickstart | — |
| Community examples | ≥ 3 | 2 first-party (Backlog Desk, BI → Semantic) |
