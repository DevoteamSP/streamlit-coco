# Feature: Tool approvals

**Checklist:** `doc/features/approvals/test-checklist.md`  
**App:** `make chat` (or `make approval`)  
**Prompts:** `examples/testdata/prompts.json` (category `approval`)

## Preconditions

- [x] **Settings** → **Requires approval** includes `Write`, `Edit`, `Bash` (demo defaults)
- [x] **Settings** → **Auto-allowed** includes read-only tools (`Read`, `Glob`, `Grep`)
- [x] Session started and **CoCo ready**

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Send `write-approval` | Approval card for **Write**; buttons left→right: **Approve once** · **Always allow Write** · **Deny** |
| 2 | Click **Deny** (rightmost) | Tool denied; agent continues or explains; no file written (or clearly aborted) |
| 3 | Send `write-approval` again → **Approve once** | Write runs once; next Write should prompt again |
| 4 | Send `always-allow-path` → **Always allow Write** | First write succeeds with approval |
| 5 | Send `always-allow-followup` | Second Write **does not** re-prompt (session Always allow) |
| 6 | Send `bash-approval` → Approve once | Bash runs after approval; output visible in tool card |
| 7 | Send `bash-destructive-deny` → **Deny** | Dangerous command not executed |
| 8 | Send `mixed-approval-chain` | Glob auto-runs; Write pauses for approval |
| 9 | While approval pending, confirm polling pauses enough to click buttons | Buttons stay clickable (no stuck grey loop) |
| 10 | Start a Write approval, then **Stop CoCo** / cancel | Pending approval clears or denies cleanly; session usable |

## Edge cases

- [x] Tool only in approval list (not in auto) still prompts and can run — Write/Bash/Edit defaults
- [ ] Overlap: tool in both auto + approval → approval wins — not exercised this pass
- [x] After **Settings** → **Reset session**, Always-allow memory is cleared — Write re-prompted after reset

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent (Auto) |
| Date | 2026-07-26 |
| Build / commit | `p0-roadmap-items` @ `18aaaa3` |
| Pass? | **Yes** — golden path 1–10 live (`make chat`): Deny / Approve once / Always allow Write (+ follow-up no re-prompt) / Bash approve with output / Bash destructive Deny / Glob auto then Write gate / buttons stable while pending / Stop clears pending Write. Edge: Reset clears Always allow. Overlap (auto∩approval) not run. |
