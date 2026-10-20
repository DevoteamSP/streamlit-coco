# Case 2 — Intermediate: approval gates and a Copilot rail in a real app

**Level:** Intermediate — your data / a real job, less guided. **Time:**
45–60 min.

## Context

A rail beside your own pages is the shape `copilot_rail()` is built for:
`examples/backlog_desk/` (file/JSON-backed, no SQL) and
`examples/bi_to_semantic/` (Tableau/Power BI → semantic view) both wire it
into an existing multipage app rather than replacing the app with a chat
window. This case asks you to do the same against a real workflow, with
checkpoints instead of click-by-click instructions.

## Goal

Configure a `CocoOptions` with `require_approval_for` for a workflow that
actually mutates something, and embed `copilot_rail()` as a right column
next to an existing (or the bundled) multipage app.

## Data

**Yours, or a stand-in.** If you have a multipage Streamlit app you already
run, use it. If not, use `examples/backlog_desk/` as the stand-in "your
data": file-backed tickets, epics, and releases under
`examples/backlog_desk/data/{epics,tickets,releases,policies}` — real files
you can inspect with `git diff` after CoCo edits them. `examples/bi_samples/`
(MIT-licensed Tableau/Power BI fixture packs) is the alternative stand-in if
you would rather follow the BI → Semantic shape.

## Checkpoints

1. **Pick your surface.** Identify one page in your app (or
   `examples/backlog_desk/`'s Ticket page) where a mutating action currently
   has no human-in-the-loop safeguard, or where you want an agent to draft
   something a person reviews before it lands.

2. **Define `CocoOptions` for that workflow.** Separate the tools that can
   run unattended (read-only exploration: `Read`, `Glob`, `Grep`) from the
   tools that must pause (`Edit`, `Write`, `Bash`, and `SQL` if your workflow
   touches Snowflake). Put the first set in `allowed_tools` and the second in
   `require_approval_for` — they should not overlap for the same tool.
   *Checkpoint: you can state, for each tool your workflow could invoke,
   which list it belongs in and why.*

3. **Scope one session to the page.** Use `get_or_create_session(opts,
   key=...)` with a key specific to this workflow, and decide when it should
   reset — `copilot_rail()` does not reset itself on a `cwd` or schema
   change; the caller owns that lifecycle decision. *Checkpoint: you know
   exactly which user action should trigger `reset_session(...)`.*

4. **Wire `copilot_rail()` in.** Add it as the right column of your layout,
   following the `examples/backlog_desk/` pattern (opened from a header
   button, closed with **Close**) or the `examples/bi_to_semantic/` pattern
   (a connection popover next to the rail). Reference
   `doc/features/copilot-rail/copilot-rail.md` in the repo for the full
   parameter list (`job=`, `on_job_sent=`, `on_job_finished=`,
   `example_questions=`, `toml_file=`). *Checkpoint: the rail opens and
   closes without rerunning the rest of your page.*

5. **Queue a real job and watch it get gated.** Trigger the mutating action
   from your page (a `status="queued"` job, or a direct chat prompt) and
   confirm `require_approval_for` pauses it with **Approve once** / **Always
   allow** / **Deny**, not with a silent write. *Checkpoint: you can point at
   the exact line in your `CocoOptions` that caused the pause.*

6. **Keep the transcript usable.** Open the rail's Display config popover
   (`:material/display_settings:`) and adjust **Last messages** / **First n
   characters** so a long session stays readable in the rail's width.

## Expected result

- Copilot sits in a right column beside your existing page content — the
  page itself is never replaced by a full-screen chat.
- The mutating action you picked in step 1 now pauses for an explicit
  Approve/Deny decision before it runs.
- You can explain, without re-reading the code, why each tool in your
  workflow is either auto-run or approval-gated.

## Where to look if stuck

- Approval gate not firing, or firing for the wrong tool:
  [`help.html#always-allow-scope`](../technical-guide/help.html#always-allow-scope).
- Approval banner sitting unanswered until it times out:
  [`help.html#approval-timeout`](../technical-guide/help.html#approval-timeout).
- Something in the workflow behaves unexpectedly and the tool cards alone
  do not explain why: enable `STREAMLIT_COCO_DEBUG=1` and re-run — see
  [`help.html#debug-mode-not-showing-payloads`](../technical-guide/help.html#debug-mode-not-showing-payloads)
  if the raw payload still does not appear.
