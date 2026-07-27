# AGENTS.md — streamlit-coco

Guidance for coding agents working in this repository.

## Product

Streamlit library + optional CCv2 component for Snowflake CoCo (Cortex Code Agent SDK). Preferred UX: `panel()` + app-owned `chat_input_bar` / `st.chat_input`.

Canonical SDK docs: https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk  
Pinned rule: `.cursor/rules/coco-sdk-docs.mdc`

## Layout

- `streamlit_coco/` — library (`ui`, `session`, `permissions`, `tool_*`, `bootstrap`, …)
- `examples/` — chat, approval, structured, headless demos
- `docs/PRD.md`, `docs/api.md`, `docs/roadmap.md`, `docs/features/` — product + API + DSP N1 feature docs/checklists
- `docs/deployment/publish.md` — dual-repo sync + tag → PyPI (`streamlit-coco`)
- `CHANGELOG.md` — shipped history (not the roadmap)

**Repos:** develop in `DevoteamSP/streamlit-coco-dev`; publish from `DevoteamSP/streamlit-coco` (`make sync-release`, then tag `v*`).

## Commands

```bash
make install   # uv sync --extra dev
make check     # ruff + pytest
make audit     # pip-audit
make chat      # Streamlit demo
```

## Conventions

- Do not default-show raw JSON tool expanders; use meaningful tool cards (`docs/features/tools-display/SPEC.md`).
- Approval buttons left→right: Approve once · Always allow · Deny.
- AskUserQuestion / ExitPlanMode always go through pending HITL; never “Always allow”.
- Update `CHANGELOG.md` `[Unreleased]` for user-visible changes; update feature checklists when UX changes.
- Prefer small, focused diffs; no drive-by refactors.

## Testing

- Unit/smoke: `tests/`
- Manual UI: `docs/features/*/test-checklist.md` before release
