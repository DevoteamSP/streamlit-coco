# Test prompts

Dataset: [`prompts.json`](prompts.json) (v2)

Use the **Test prompts** section in the chat app sidebar (`make chat`) to filter by category and **Send test prompt** one at a time.

Full UX rules: [`doc/features/tools-display/SPEC.md`](../../doc/features/tools-display/SPEC.md).

## Categories (tools-display)

Prefer these when validating the P0 tools-display work:

| Category | Family | What to look for |
|----------|--------|------------------|
| `display_glob` | Glob | Pattern header + path list card (no JSON expander) |
| `display_grep` | Grep | Pattern (+ path) + match lines |
| `display_read` | Read | Path + content preview |
| `display_write` | Write | Approval shows path + content; Deny / Approve / Always |
| `display_edit` | Edit | Approval shows Before / After |
| `display_bash` | Bash | Command in bash code block |
| `display_sql` | SQL | SQL code + table/text; enable SQL in **Settings** |
| `display_ask_user` | AskUserQuestion | Radio / multi / Other… / Submit (not Approve once) |
| `display_exit_plan` | ExitPlanMode | Enable **Plan mode** in **Settings** first |
| `display_mixed` | multi | Several card types in one turn |
| `display_debug` | any | Turn **CoCo debug mode** on in **Settings** → Raw tool payload |

## Other categories

| Category | What it exercises |
|----------|-------------------|
| `tools_auto` | Glob / Grep / Read without approval |
| `approval` | Write / Edit / Bash gates, Deny, Always allow |
| `tools_sql` | SQL tool (enable SQL in **Settings** first) |
| `clarification` | Ambiguous asks / AskUserQuestion |
| `streaming` | Long answers / Stop mid-run |
| `structured` | JSON-shaped replies |
| `multi_turn` | Session memory across two prompts |
| `permissions` | Allow-list denial messaging |

Each prompt has `expects` tags (e.g. `card:sql`, `approval:Write`, `no_json_expander`) as a manual checklist — not automated assertions.

## Suggested run order (tools-display)

1. `display_glob` → `display_grep` → `display_read` (auto tools)
2. `display_write` → `display_edit` → `display_bash` (approvals)
3. Enable SQL → `display_sql`
4. `display_ask_user` (try Other… and Cancel)
5. Enable Plan mode → Reset session → `display_exit_plan`
6. Toggle debug → `display_debug`
