# Feature docs & test plans

Manual golden-path checklists (DSP N1). Run before releases; link from PRs that touch the feature.

Narrative docs follow DSP §9 (What / Why / How / Limitations). Checklists are the executable sign-off.

Package API (all public exports): [`../api.md`](../api.md).

## Index

| Feature | Narrative | Checklist | Preferred prompts / app |
| --- | --- | --- | --- |
| Panel + chat input | [panel/panel.md](panel/panel.md) | [panel/test-checklist.md](panel/test-checklist.md) | `make chat`; `tools_auto`, `streaming` |
| Tool approvals | [approvals/approvals.md](approvals/approvals.md) | [approvals/test-checklist.md](approvals/test-checklist.md) | category `approval` |
| Tools display + HITL | [tools-display/tools-display.md](tools-display/tools-display.md) ([SPEC](tools-display/SPEC.md)) | [tools-display/test-checklist.md](tools-display/test-checklist.md) | categories `display_*` |
| Structured output | [structured-output/structured-output.md](structured-output/structured-output.md) | [structured-output/test-checklist.md](structured-output/test-checklist.md) | `make structured`; `structured-json` |
| Headless query / multi-turn | [headless/headless.md](headless/headless.md) | [headless/test-checklist.md](headless/test-checklist.md) | `make headless` |
| Pluggable text renderer | [text-renderer/text-renderer.md](text-renderer/text-renderer.md) | [text-renderer/test-checklist.md](text-renderer/test-checklist.md) | `panel(..., text_renderer=…)` |
| Legacy CCv2 chat | [chat-ccv2/chat-ccv2.md](chat-ccv2/chat-ccv2.md) | [chat-ccv2/test-checklist.md](chat-ccv2/test-checklist.md) | `make approval` |

## Suggested run order (release)

1. **panel** → 2. **approvals** → 3. **tools-display** → 4. **structured-output** → 5. **headless** → 6. **text-renderer** → 7. **chat-ccv2**

Approval / plan button order (left → right): **Approve once** · **Always allow** · **Deny** (Deny rightmost). AskUser: **Submit** · **Cancel**. Plan: **Approve plan** · **Reject**.

Exploratory prompts: [`examples/testdata/`](../../examples/testdata/).

## Last automated verification

| Suite | Result | Notes |
| --- | --- | --- |
| `uv run pytest tests/` | **31 passed** (2026-07-25) | Unit + smoke; includes CCv2 register-once |
| `make headless` / `examples/headless_pipeline.py` | **Pass** (2026-07-27) | Multi-turn `run()` + `stream()`; no Streamlit import; signed off in [`headless/test-checklist.md`](headless/test-checklist.md) |
| UI golden path — panel | **Pass (core)** (2026-07-25) | Signed off in [`panel/test-checklist.md`](panel/test-checklist.md) — steps 1–5 live |
| UI golden path — approvals | **Pass** (2026-07-26) | Signed off in [`approvals/test-checklist.md`](approvals/test-checklist.md) — golden path 1–10 live |
| UI golden path — tools-display | **Pass (core)** (2026-07-27) | [`tools-display/test-checklist.md`](tools-display/test-checklist.md) — Glob/Grep/Read/Write/Edit live; SQL/AskUser/plan/debug deferred |
| UI golden path — structured-output | **Pass (core)** (2026-07-27) | [`structured-output/test-checklist.md`](structured-output/test-checklist.md) — `make structured` + `output_schema` live |
| UI golden path — chat-ccv2 | **Pass** (2026-07-27) | [`chat-ccv2/test-checklist.md`](chat-ccv2/test-checklist.md) — `make approval` live |

