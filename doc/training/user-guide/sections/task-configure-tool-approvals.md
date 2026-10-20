# I want to configure tool approvals

**For** a developer deciding which agent tools need a human in the loop · **15 min** · **a working minimal app**

You end up with a session where specific tools run automatically and others
pause for approval, resolved either through the built-in UI or
programmatically.

## Before you start

- A working minimal app ([I want to build a minimal CoCo app](task-build-a-minimal-app.html)).
- Know which tools the agent may call in your app (`Read`, `Glob`, `Grep`,
  `Edit`, `Write`, `Bash`, the SQL tool, `AskUserQuestion`, `ExitPlanMode`,
  MCP-provided tools, …) and which of them are destructive in your context.

## Steps

1. Set `allowed_tools` on `CocoOptions` for tools that should never need a
   prompt, and `require_approval_for` for tools that should always pause:

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       allowed_tools=["Read", "Glob", "Grep"],
       require_approval_for=["Edit", "Write", "Bash"],
   )
   ```

   `AskUserQuestion` and `ExitPlanMode` always pause for a decision,
   regardless of what is listed in either option.

2. Mount the panel with approvals visible (the default):

   ```python
   st_coco.panel(session, show_approvals=True)
   ```

   When the agent calls a tool matched by `require_approval_for`, the
   session's status becomes `awaiting_user` and `render_approvals()` shows
   three controls: **Approve once**, **Always allow**, **Deny**. Neither
   `AskUserQuestion` nor `ExitPlanMode` requests show **Always allow**.

3. To resolve approvals from your own UI instead of the built-in controls,
   call the low-level resolvers directly with the pending request's id (from
   `session.chat_result().pending_approval`):

   ```python
   result = session.chat_result()
   if result.pending_approval:
       request_id = result.pending_approval["request_id"]
       st_coco.approve_pending(session, request_id, always=False)
       # or: st_coco.deny_pending(session, request_id, reason="not now")
   ```

4. Optionally narrow or widen the gate at runtime by passing a callable to
   `require_approval_for` instead of a fixed list, then call
   `session.sync_options(options)` after changing it so the session picks up
   the new hash.

## Result

Tools in `allowed_tools` run without any prompt. Tools matched by
`require_approval_for` pause the run and show the three-button approval
control (or wait for `approve_pending`/`deny_pending` in a custom UI) before
executing. A denial does not execute the tool call; the agent's turn
continues from there, optionally with the reason you passed.

## Variations

- **Always allow** applies for the current session only — it is cleared on
  `session.reset()` or process restart, never written to a persisted policy.
- `permission_mode="plan"` routes tool calls through an `ExitPlanMode` flow
  instead of per-tool approval; `render_plan_banner()` shows the plan-mode
  banner and **Execute plan** call to action.
- `approval_timeout_seconds` (default `600.0`, ten minutes) controls how long
  a pending approval waits before the run fails with `ApprovalTimeoutError`.

## If it fails

- [Approval timeout](../../technical-guide/help.html#approval-timeout)
- ["Always allow" is session-scoped only](../../technical-guide/help.html#always-allow-scope)
