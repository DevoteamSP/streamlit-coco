# Outputs

Every file or artifact `streamlit-coco` or its example apps produce, what it
contains, and where it lands.

## Uploaded files

Produced by: `upload_to_cwd()`, `cwd_uploader()`, or
`chat_input_bar(accept_file=...)` — see
[I want to add file uploads](task-add-file-uploads.html).

Lands at: `<CocoOptions.cwd>/_uploads/` (the subdirectory name is
configurable via `subdir`/`upload_subdir`).

Read it: it is a plain copy of the file the user uploaded, under its
original (validated) name; any agent tool reading from `cwd` can see it
directly.

## App Builder build output

Produced by: the Studio page's **Build this app** / **regenerate** action in
`examples/app_builder/`.

Lands at: `examples/app_builder/out/<slug>/`, containing `brief.json` (the
structured brief), `BRIEF.md` (the human-readable brief, editable and
re-loadable in the CoCo editor), `sketches/` (any uploaded sketches), and
`streamlit_app.py` (the generated app).

Read it: `streamlit_app.py` is a runnable Streamlit script; `BRIEF.md` is the
source of truth for what was asked for, and is what **Save & regenerate**
writes before queuing a new CoCo turn.

## BI → Semantic intermediate artifacts

Produced by: screens 2 through 5 of `examples/bi_to_semantic/`.

Lands at: `examples/bi_to_semantic/out/`, containing `estate_map.json`
(screen 2), `kpi_inventory.json` (screen 3), `access_rules.json` (screen 4),
and `decisions.json` (screen 5's arbitration record).

Read it: each file matches its JSON Schema under
`examples/bi_to_semantic/contracts/` (`estate_map.schema.json`,
`kpi_inventory.schema.json`, `access_rules.schema.json`); `decisions.json`
records what the reviewer chose at each arbitration point in screen 5.

## BI → Semantic generated output

Produced by: screen 6 (Generate) of `examples/bi_to_semantic/`, after the
Write approval.

Lands at: `examples/bi_to_semantic/out/streamlit_dash/` (the deterministic
consumer) and `examples/bi_to_semantic/out/streamlit_dash_coco/` (the
CoCo-authored consumer), alongside the generated semantic view SQL/YAML and
row access policy.

Read it: both consumer directories are runnable Streamlit apps, previewed
via `app_viewer()` on ports 8511 (deterministic) and 8512 (CoCo-authored).
The semantic view and row access policy files are the SQL/YAML to review
before applying them to a Snowflake account.

## Backlog Desk Copilot writes

Produced by: the Backlog Desk Copilot's Edit/Write skills (Draft release
notes, Propose ticket update), both approval-gated.

Lands at: `examples/backlog_desk/data/tickets/` (updated ticket JSON) and
`examples/backlog_desk/data/releases/` (release notes Markdown).

Read it: ticket JSON follows the same shape the Board/Epic/Ticket pages
already read; release notes are plain Markdown.

## `app_viewer()` child-process files

Produced by: any call to `app_viewer(app_dir, ...)`.

Lands at: inside the previewed `app_dir` itself — `.preview.log`,
`.preview.pid`, `.preview.port`.

Read it: `.preview.log` is the child Streamlit process's stdout/stderr, used
by the "Fix with CoCo" flow's log-tail; `.preview.pid` and `.preview.port`
identify the running child process. There is only one preview per `app_dir`
at a time — never point `app_dir` at the app hosting the viewer itself.

## Release build artifacts

Produced by: `make build` (maintainer-facing, see
[Command reference](reference-commands.html)).

Lands at: `dist/` — an sdist and a wheel.

Read it: these are the files `make publish` uploads to PyPI; not produced by
normal library use.
