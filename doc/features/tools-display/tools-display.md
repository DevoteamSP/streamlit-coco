# Tools display & user interactions

## What

Transcript tool calls render as compact expanders (collapsed by default; open on errors) with meaningful bodies (Glob, Grep, Read, Write, Edit, Bash, SQL, AskUserQuestion, ExitPlanMode, generic). Interactive HITL covers approvals, AskUserQuestion (radio / Other… / Submit), and ExitPlanMode (Approve plan / Reject). Raw JSON payloads appear only in CoCo debug mode.

## Why

Operators need to see *what* the agent is doing (query, path, command) and answer clarifying questions without digging through expanders.

## How to use

1. Prefer `panel()` + transcript mode (`show_tool_details=True`).
2. Enable **Settings** → **CoCo debug mode** only when inspecting raw payloads.
3. For ExitPlanMode: set `permission_mode="plan"` (chat demo: **Settings** → **Plan mode** + Reset session).
4. Drive coverage with `display_*` prompts in `examples/testdata/prompts.json`.

## Limitations

- Unified Monaco-style diffs are not shipped; **unified text diffs** (`difflib`) are shown on Edit/Write approval and transcript cards (Before/After fallback if empty).
- MCP / unknown tools get a scalar field summary, not a custom UI.
- CCv2 `chat()` has card parity; full AskUser interaction is native `panel()` path.

## Related

- Spec: [`SPEC.md`](SPEC.md)
- Checklist: [`test-checklist.md`](test-checklist.md)
