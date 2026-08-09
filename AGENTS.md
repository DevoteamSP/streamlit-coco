# AGENTS.md — streamlit-coco

Guidance for coding agents working in this repository.

## Product

Streamlit library + optional CCv2 component for Snowflake CoCo (Cortex Code Agent SDK). Preferred UX: `panel()` + app-owned `chat_input_bar` / `st.chat_input`.

Canonical SDK docs: https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk  
Pinned rule: `.cursor/rules/coco-sdk-docs.mdc`

## Layout

- `streamlit_coco/` — library (`ui`, `session`, `permissions`, `tool_*`, `bootstrap`, …)
- `examples/` — chat, approval, structured, headless demos
- `doc/prd.md`, `doc/api.md`, `doc/roadmap.md`, `doc/features/` — product + API + DSP N1 feature docs/checklists
- `doc/releases/X.Y.Z/` — public release kit (checklist, screenshots)
- `doc-dev/` — **dev-only** docs (never synced to public `streamlit-coco`); includes `doc-dev/releases/X.Y.Z/` outreach (LinkedIn, Medium, community)
- `doc/deployment/publish.md` — dual-repo sync + tag → PyPI (`streamlit-coco`)
- `CHANGELOG.md` — shipped history (not the roadmap)

**Repos:** develop in `DevoteamSP/streamlit-coco-dev`; publish from `lletourmy/streamlit-coco` (`make sync-release`, then tag `v*`) until DevoteamSP is PyPI-validated.

## Commands

```bash
make install   # uv sync --extra dev
make check     # ruff + unit/smoke (ignores tests/e2e)
make e2e       # Playwright UX vs examples/e2e_ux_harness.py
make audit     # pip-audit
make test-all  # check + e2e + audit
make chat      # Streamlit demo
```

Full test process: [`doc/testing.md`](doc/testing.md).

## Conventions

- Do not default-show raw JSON tool payloads; use meaningful compact tool expanders (`doc/features/tools-display/SPEC.md`).
- Approval buttons left→right: Approve once · Always allow · Deny.
- AskUserQuestion / ExitPlanMode always go through pending HITL; never “Always allow”.
- Update `CHANGELOG.md` `[Unreleased]` for user-visible changes; update feature checklists when UX changes.
- **Before cutting a release:** complete `doc/releases/X.Y.Z/CHECKLIST.md` + outreach in `doc-dev/releases/X.Y.Z/`, then `doc/deployment/publish.md`. Do not tag until the public kit docs/QA sections are done.
- Prefer small, focused diffs; no drive-by refactors.

## Testing

- Unit/smoke: `tests/` (see `make check`)
- Browser UX e2e: `tests/e2e/` (`make e2e-install` once, then `make e2e`)
- Manual / live CoCo: `doc/features/*/test-checklist.md` before release
- Process overview: [`doc/testing.md`](doc/testing.md)
