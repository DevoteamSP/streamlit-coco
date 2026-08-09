# Feature: Tools display & user interactions

**Checklist:** `doc/features/tools-display/test-checklist.md`  
**Spec:** [`SPEC.md`](SPEC.md)  
**App:** `make chat`  
**Prompts:** `examples/testdata/prompts.json` — prefer categories `display_*`

## Preconditions

- [x] Session started and **CoCo ready**
- [x] **Settings** → **CoCo debug mode** is **off** for the default path
- [x] Enable tools in sidebar as needed (SQL for SQL cases; Write/Edit/Bash for approvals)
- [ ] For ExitPlan prompts: **Settings** → enable **Plan mode**, then **Reset session** — not run this pass

## Golden path (one prompt per family)

| # | Category / prompt id | Expected | Pass |
| --- | --- | --- | --- |
| 1 | `display_glob` / `display-glob-basic` | Glob as **collapsed** expander + paths inside — **no JSON expander** | |
| 2 | `display_grep` / `display-grep-basic` | Grep collapsed expander + matches meta in label | |
| 3 | `display_read` / `display-read-readme` | Read collapsed expander; content when opened | |
| 4 | `display_write` / `display-write-approval` | Approval: path + content; Approve once | ✓ |
| 5 | `display_edit` / `display-edit-approval` | Approval: Before / After (after write) | ✓ |
| 6 | `display_bash` / `display-bash-safe` | Approval: bash code block | ✓ (via approvals bash path) |
| 7 | `display_sql` / `display-sql-context` | SQL code + result table/text (SQL enabled) | — not run (SQL not in default allowed tools) |
| 8 | `display_sql` / `display-sql-approval` | SQL in **Requires approval**; query shown on gate | — not run |
| 9 | `display_ask_user` / `display-ask-single` | Radio + Other… + Submit (not Approve once) | — not run |
| 10 | `display_ask_user` / `display-ask-other` | Other… text required before Submit | — not run |
| 11 | `display_ask_user` / `display-ask-multi` | Multiselect UI | — not run |
| 12 | `display_exit_plan` / `display-plan-exit` | **Approve plan** · **Reject** (Approve leftmost; Plan mode on) | — not run |
| 13 | `display_debug` / `display-debug-raw` | Debug on → collapsed **Raw tool payload** | — not run |
| 14 | While any approval/question pending | Buttons stay clickable (polling paused) | ✓ (approvals sign-off) |

## Extra coverage

- [ ] `display-write-deny` / `display-bash-deny` — Deny path — bash deny covered in approvals
- [ ] `display-ask-cancel` — Cancel AskUserQuestion
- [ ] `display-plan-reject` — Reject plan with feedback
- [ ] `display-mixed-auto-then-write` — Glob auto + Write gate — covered in approvals #8
- [ ] `display-glob-emptyish` — empty match list renders cleanly

## Edge cases

- [ ] `sql_execute` / `SQL` name variants both use SQL card (live agent naming)
- [x] Always allow never offered for AskUserQuestion / ExitPlanMode — unit tests
- [ ] Unknown MCP tool shows scalar field summary, not open JSON expander

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent (Auto) |
| Date | 2026-07-27 |
| Build / commit | `p0-roadmap-items` @ `18aaaa3` (+ example fixes unstaged) |
| Pass? | **Yes (core)** — live `make chat`: Glob/Grep/Read cards; Write + Edit Before/After approval UX; no default JSON expanders on tool cards. Bash approval card covered via approvals checklist. SQL / AskUser / ExitPlan / debug families not run this pass (enable SQL + plan/debug in Settings for follow-up). |
