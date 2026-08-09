# Roadmap — streamlit-coco

Living plan. Product detail: [`doc/prd.md`](prd.md). Shipped history: [`CHANGELOG.md`](../CHANGELOG.md).

**Status:** Alpha **`0.1.5`** on PyPI ([pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/)).  
**Publisher:** temporary Trusted Publisher on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco); public tree also synced to [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco).  
**Last updated:** 2026-08-09

> **Before every release:** complete [`releases/X.Y.Z/CHECKLIST.md`](releases/README.md) (CHANGELOG, this roadmap, PRD, screenshots) and outreach under [`../doc-dev/releases/`](../doc-dev/releases/README.md), then [`deployment/publish.md`](deployment/publish.md).

> **Regularly check version of sdk:** at [`CoCo Python SDK`](https://pypi.org/project/cortex-code-agent-sdk/)

---

## Now

| Priority | Item | Ref |
| --- | --- | --- |
| P0 | Remote CoCo APIs — harden / ship (`mode="api"`) | [#4](https://github.com/DevoteamSP/streamlit-coco-dev/issues/4); [remote-api](features/remote-api/remote-api.md) |
| P1 | Switch PyPI publisher back to `DevoteamSP/streamlit-coco` when the org is validated | [publish.md](deployment/publish.md) |
| P2 | Auto-scroll to bottom while running; pause if user scrolls up (FR-S2) | — |

Manual checklists: [`doc/features/README.md`](features/README.md) — re-run before the next tag.

---

## Use Cases ideas

- App Builder
- Prompt library player (local or github)
- Dashboard Builder (on Semantic View) + Agent client
- Native App "skills marketplace"
- Native App for skills distribution
- Data Quality solutions builder
- Migration wizard
- FinOps costs explorer
- Incident / query triage
- Multi-persona workspaces

## Next — v0.2.0

| Item | Ref |
| --- | --- |
| Approval audit log persistence (SEC-01) | — |
| Least-privilege role documentation (SEC-02) | — |
| Deployment docs (Docker, SPCS) | [deployment/](deployment/README.md); PRD §8 / G6 |
| API-mode sandbox upload (extend cwd upload) | [file-upload](features/file-upload/file-upload.md) |

---

## Later

### Streaming & transcript UX
- [ ] Auto-scroll to bottom while running; pause if user scrolls up (FR-S2)
- [x] Richer markdown / SQL highlighting (FR-S6) — shipped in `0.1.5`
- [x] Copy-to-clipboard on assistant messages and tool results (FR-S7) — shipped in `0.1.5`
- [x] Optional `max_messages` truncation + “load earlier” (FR-ST4) — shipped in `0.1.5`
- [ ] Theming / a11y pass (native `panel()` transcript; keyboard traps, ARIA)

### Platform & packaging
- [ ] Packaged CCv2 via Vite / `asset_dir` (PRD §14.7; optional if still needed)
- [ ] Community sample apps (≥ 3)
- [x] SBOM generation in release workflow (SEC-04) — shipped in `0.1.5`
- [x] Automated UI / e2e tests (Playwright + CoCo-free harness; `make e2e`) — shipped in `0.1.5`

---

## Out of scope (for now)

- Full IDE workspace
- MCP *product* servers (MCP passthrough via `mcp_servers` works today)
- Sub-agents
- Slack integration

---

## Success checks (90 days post-launch)

Public surface: [DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) · [pypi.org/project/streamlit-coco](https://pypi.org/project/streamlit-coco/)  
Snapshot **2026-08-09** ([pypistats](https://pypistats.org/packages/streamlit-coco)): **107** downloads last month · **2** GitHub stars.

| Metric | Target | Current (2026-08-09) |
| --- | --- | --- |
| PyPI downloads | 500+ / month | 107 last month (6 last day · 107 last week) |
| GitHub stars | 50+ | 2 ([DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)) |
| Time-to-first-working-app | < 30 min via quickstart | — |
| Open P0 "streaming broken on rerun" | 0 for 30 days | — |
| Community examples | ≥ 3 | — |
