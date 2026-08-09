# Spec: Tool display & user interactions

**Feature:** Tools transcript cards + HITL interactions  
**Status:** Implemented (alpha)  
**Surfaces:** `panel()` / `render_transcript()` / `render_approvals()` (primary); legacy CCv2 `chat()` (parity where practical)  
**Related:** [`doc/prd.md`](../../prd.md) FR-C3, FR-C6, FR-C7, FR-S3 (superseded), FR-S6; [`doc/roadmap.md`](../../roadmap.md)  
**Test prompts:** [`examples/testdata/prompts.json`](../../../examples/testdata/prompts.json) categories `display_*`

---

## 1. Goals

1. **No raw JSON expanders in default UX.** Tool activity is shown as meaningful cards (query, path, command, options, results).
2. **Specialized interactions** for SDK-routed / high-stakes tools (`AskUserQuestion`, approvals, SQL, file/shell mutations, plan exit).
3. **Debug escape hatch.** CoCo debug mode may reveal raw tool payloads in a collapsed expander.
4. **Stable dispatch.** Tool name matching is case- and separator-insensitive (`SQL`, `sql_execute`, `SqlExecute` → same family).

Non-goals (this revision): full Monaco diffs, custom MCP tool UIs beyond the generic meaningful card, headless programmatic UI.
(Copy-to-clipboard shipped separately via `show_copy=` / FR-S7.)


---

## 2. Definitions

| Term | Meaning |
| --- | --- |
| **Transcript tool card** | UI for a transcript item with `kind == "tool"` |
| **Interaction surface** | UI while `permission_manager` has an active pending request (`AWAITING_USER`) |
| **Debug mode** | `is_debug_mode()` — env `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG`, or `st.session_state["coco_debug"]` |
| **Family** | Logical tool group used for rendering (`sql`, `read`, `write`, `edit`, `bash`, `glob`, `grep`, `ask_user`, `exit_plan`, `generic`) |

### 2.1 Tool name normalization

```text
normalize(name) = lowercase(name) with non-alphanumeric characters removed
```

Examples: `AskUserQuestion` → `askuserquestion`, `sql_execute` → `sqlexecute`, `ExitPlanMode` → `exitplanmode`.

---

## 3. Global rules

### 3.1 Expanders

| Context | Allowed? |
| --- | --- |
| Transcript tool card (primary surface) | **Yes** — compact `st.expander` / `<details>`, **collapsed by default** |
| Tool payload / results inside the card | Shown only when the card expander is opened (still meaningful content, not raw JSON) |
| Debug mode | Optional nested collapsed expander labeled **Raw tool payload** |
| Structured output / unrelated UI | Out of scope (may still use expanders) |

### 3.2 Layout

- Tool cards use a **collapsed expander** as the primary surface (dense transcript / Copilot rail).
- Expander label: `**{FamilyLabel}** · {StatusLabel}` plus optional short meta (path, row count, pattern, match count).
- Auto-expand only when status is `error` so failures are not missed.
- Status labels: `Running` | `Completed` | `Failed` (map from `running` / `completed` / `error`).
- While a tool is `running`, show a short progress caption **inside** the expander (e.g. “Searching content…”, “Reading…”).
- **When the tool is `completed` / `error`, or the turn `result` arrives, never keep the progress caption** — show matches / result body / error instead (header status must leave `Running`).

### 3.3 Debug payload

When debug mode is on, after the meaningful card content, optionally:

```text
▾ Raw tool payload   (collapsed)
  { input, result }
```

`show_tool_details=False` suppresses large result bodies where specified per family; debug still may show raw payload.

### 3.4 Interaction vs transcript

- Active pending requests are rendered by **`render_approvals()`** (or AskUser / plan variants).
- Transcript should **not duplicate** the interactive form for the active request (`hide_active_approval` for approval items; AskUser running card stays a short “Waiting…” notice).

### 3.5 Polling

While any pending permission request is active, fragment auto-polling **pauses** so buttons / radios remain clickable (existing `panel()` behavior).

---

## 4. Family catalog

### 4.1 `ask_user` — AskUserQuestion

**Names:** `AskUserQuestion`, `ask_user_question`, …

**Transcript card**

| Status | Display |
| --- | --- |
| `running` | Info: “Waiting for your answer — {headers}” |
| `completed` | Caption: “Answered — {headers}” (no JSON) |
| `error` | Error: “Question cancelled or failed — {headers}” |

**Interaction** (always; never auto-allow / never “Always allow”)

- Info banner: CoCo needs input.
- Per question: header + question text.
- Options → radio (single) or multiselect (multi).
- Always append **Other…** unless an Other/free-form option already exists.
- Free-form / **Something else** / **Other** choices are always shown **last** (even if the agent listed them mid-list).
- Selecting Other… reveals a required text field.
- Actions: **Submit answers** (allow with `updated_input={questions, answers}`) · **Cancel** (deny, rightmost).
- Submit disabled until every question has a valid answer.

**Permission routing:** Always `create_request` in `can_use_tool` before any allowlist check.

---

### 4.2 `sql` — SQL / sql_execute

**Names:** `SQL`, `sql_execute`, `SqlExecute`, `sql_query`, …

**Transcript card**

- Header: `SQL · {status}` + row count when completed.
- Body: `st.code(sql, language="sql")` from `query` / `command` / `sql` / `statement` / `text` (nested `input`/`arguments`/`params` allowed).
- Completed: parse result into rows → `st.dataframe`; else plain text (truncate > 4k chars); empty → “Query returned no rows.”
- Failed: `st.error` with message.
- Running: “Executing query…”

**Interaction (when approval required)**

- Warning: wants to run SQL.
- Show SQL code block.
- Approve once / Always allow / Deny (SQL preview shown).

---

### 4.3 `read`

**Names:** `Read`

**Transcript card**

- Header: `Read · {status}` · `` `{path}` ``
- Running: “Reading file…”
- Completed: show content as `st.code` if looks like code/text (truncate long), or caption “Read N chars”
- Failed: error message from result

**Path keys:** `path`, `file_path`, `filePath`, `filename`

**Interaction:** show path (and optional preview of intent); standard approval buttons.

---

### 4.4 `write`

**Names:** `Write`

**Transcript card**

- Header: `Write · {status}` · path
- Body: content preview in `st.code` (language guessed from extension; default `text`), truncated
- Running: “Writing file…”
- Failed: error

**Content keys:** `content`, `new_str`, `newString`, `text`

**Interaction:** path + content preview + Approve once / Always allow / Deny.

---

### 4.5 `edit`

**Names:** `Edit`

**Transcript card**

- Header: `Edit · {status}` · path
- Body: show **Before** / **After** (or old_string / new_string) as two code blocks — not a raw expander
- Running: “Applying edit…”
- Failed: error

**Keys:** path as above; `old_string`/`oldString`, `new_string`/`newString`

**Interaction:** path + before/after or **unified diff** preview + approval buttons.

---

### 4.6 `bash`

**Names:** `Bash`

**Transcript card**

- Header: `Bash · {status}`
- Body: `st.code(command, language="bash")`
- Completed: stdout/stderr / result text in `st.text` (truncated)
- Running: “Running command…”
- Failed: error

**Command keys:** `command`, `cmd`

**Interaction:** command code block + approval buttons.

---

### 4.7 `glob`

**Names:** `Glob`

**Transcript card**

- Header: `Glob · {status}` · pattern
- Completed: compact caption (`N files`); path list only in debug mode
- Running: “Searching files…”

**Keys:** `pattern`, `glob_pattern`, `glob`

**Interaction:** show pattern; approval if required.

---

### 4.8 `grep`

**Names:** `Grep`

**Transcript card**

- Header: `Grep · {status}` · pattern · optional path
- Completed: compact caption (`N matches`) — **no full match dump** in the card (preview only in debug mode)
- Running: “Searching content…”

**Keys:** `pattern`, `regex`; path keys as Read; optional `path`/`glob`

**Interaction:** pattern (+ path) + approval if required.

---

### 4.9 `exit_plan` — ExitPlanMode

**Names:** `ExitPlanMode`, `exit_plan_mode`, …

**Transcript card**

- Header: `Plan · {status}`
- Body: plan markdown/text in bordered card

**Interaction** (always route through pending when `can_use_tool` is installed)

- Title: Approve plan to leave plan mode?
- Show `plan` (and optional `question`) as markdown/text
- Actions: **Approve plan** (allow; optional `updated_input.message`) · **Reject** (deny, optional reason text, rightmost)
- No “Always allow”

**Permission routing:** Always `create_request` (like AskUserQuestion). Never add to `always_allowed_tools`.

---

### 4.10 `generic` — unknown / MCP tools

**Transcript card**

- Header: `{ToolName} · {status}`
- Body: human summary of up to 6 scalar input fields (key → short value); skip huge blobs
- Result: short text/caption if scalar/string; if large structured data, show “Result received (N keys)” and only dump JSON in debug
- **Never** default to an open JSON expander

**Interaction:** warning with tool name + meaningful input summary + standard approval buttons; raw JSON only in debug.

---

## 5. Approval chrome (shared)

For mutable / gated tools (not AskUser / ExitPlan):

| Button | Behavior |
| --- | --- |
| Approve once | `PermissionResultAllow` (optional `updated_input`) |
| Always allow {Tool} | Allow + session memory for that tool name (not AskUser / ExitPlan) |
| Deny | `PermissionResultDeny` (rightmost) |

Left → right order in the UI: **Approve once** · **Always allow** · **Deny**.

SQL / Write / Edit / Bash / generic follow this pattern when pending.

---

## 6. Parameters & debug

| API | Behavior |
| --- | --- |
| `panel(..., show_tool_details=True)` | Show result bodies for specialized cards (tables, content previews) |
| `show_tool_details=False` | Headers + primary input (SQL/command/path) only; skip large results |
| `render_approvals(..., show_tool_input=None)` | `None` → follow debug mode for raw payload expander |
| `is_debug_mode()` | Gates raw payload expanders |

---

## 7. CCv2 parity

Legacy component should:

- Detect AskUser / SQL families (already partially done)
- Prefer compact cards over `<details>` JSON for Read/Write/Edit/Bash/Glob/Grep/generic
- Full interactive AskUser remains native `panel()` path (CCv2 may show “answer in host UI” notice if pending)

---

## 8. Acceptance criteria

1. Default demo path never opens a tool **JSON expander** for SQL, AskUser, Read, Write, Edit, Bash, Glob, Grep.
2. AskUser always shows radio/Other/Submit; never Approve once for that tool.
3. SQL shows code + table/text result.
4. Write/Edit/Bash approval shows path/content/command, not only the tool name.
5. Debug checkbox reveals raw payloads without changing the primary card.
6. Unit tests cover name normalization, SQL parse, family dispatch, AskUser/ExitPlan forced pending.
7. Manual checklist under `doc/features/tools-display/test-checklist.md` passes on a live session.

---

## 9. Implementation map

| Module | Responsibility |
| --- | --- |
| `streamlit_coco/tool_names.py` | normalize + family detection |
| `streamlit_coco/ask_user.py` | AskUser helpers (existing) |
| `streamlit_coco/sql_tool.py` | SQL helpers (existing) |
| `streamlit_coco/tool_cards.py` | Transcript card renderers per family |
| `streamlit_coco/ui.py` | Interaction surfaces (approvals, AskUser, ExitPlan) |
| `streamlit_coco/permissions.py` | Forced pending for AskUser + ExitPlan |
| `streamlit_coco/display.py` | Dispatch transcript items → tool_cards |
| `streamlit_coco/frontend/main.js` | CCv2 card parity |

---

## 10. Revision history

| Date | Change |
| --- | --- |
| 2026-07-23 | Initial full spec (no default tool expanders; family catalog + HITL) |
| 2026-07-31 | Compact transcript: tool cards are collapsed expanders; auto-open on error |
| 2026-07-23 | Implemented in library; `display_*` prompt pack + Plan mode toggle in chat demo |
