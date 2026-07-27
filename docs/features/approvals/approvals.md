# Tool approvals

## What

When `require_approval_for` (or allow-list enforcement) blocks a tool, `can_use_tool` pauses the worker and `render_approvals()` shows Approve once · Always allow · Deny (Deny rightmost), with a family-specific preview (path, SQL, command, etc.).

## Why

Governed Streamlit apps must not auto-run Write / Edit / Bash / SQL without an operator decision.

## How to use

1. Set `CocoOptions(require_approval_for=[...], allowed_tools=[...])`.
2. Use `panel(..., show_approvals=True)` (default) or call `render_approvals(session)`.
3. Resolve with UI buttons, or programmatically via `approve_pending` / `deny_pending`.

Demo prompts: category `approval` in `examples/testdata/prompts.json`.

## Limitations

- “Always allow” is session-scoped memory (cleared on reset); not a permanent policy store.
- AskUserQuestion and ExitPlanMode never use Always allow (dedicated UIs).
- Approval timeout defaults to 10 minutes (`approval_timeout_seconds`).

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Tools display: [`../tools-display/SPEC.md`](../tools-display/SPEC.md)
