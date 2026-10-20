# Data and contracts

## `CocoEvent`

`streamlit_coco/messages.py` defines `CocoEvent`, the normalized,
JSON-serializable event the library produces from SDK/NDJSON messages. Every
event carries `to_dict()` / `CocoEvent.from_dict()` for round-tripping.

Fields:

| Field | Type | Notes |
|---|---|---|
| `type` | `str` | `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `id` | `str` | UUID, generated per event |
| `text` | `str \| None` | Assistant/thinking text |
| `delta` | `str \| None` | Streaming delta text |
| `name` | `str \| None` | Tool name (on tool-use events) |
| `tool_use_id` | `str \| None` | Correlates a tool result to its tool-use event |
| `input` | `dict \| None` | Tool input |
| `content` | `Any` | Raw content payload |
| `is_error` | `bool \| None` | Tool result error flag |
| `request_id` | `str \| None` | Permission request id |
| `tool_name` | `str \| None` | Tool name on permission-request events |
| `tool_input` | `dict \| None` | Tool input on permission-request events |
| `subtype` | `str \| None` | Event subtype |
| `duration_ms` | `int \| None` | Turn/tool duration, when the SDK provides it |
| `structured_output` | `Any` | Structured output payload, when present |
| `cost_usd` | `float \| None` | Cost, when the SDK provides it |
| `message` | `str \| None` | Free-text message (system/error events) |
| `code` | `str \| None` | Error code |
| `metadata` | `dict` | Free-form extra fields |

`events_to_dataframe(events)` (needs `pandas`) flattens a list of
`CocoEvent` into a `DataFrame` for inspection or logging.

## JSON Schema contracts — `examples/bi_to_semantic/contracts/`

Three JSON Schema files constrain the structured outputs the BI → Semantic
example asks CoCo (and its own deterministic parsers) to produce. Each is a
draft 2020-12 schema with `additionalProperties: false`:

| File | Purpose |
|---|---|
| `estate_map.schema.json` | Shape of `estate_map.json` — tables, columns, joins, and per-workbook usage discovered from the Tableau/Power BI estate |
| `kpi_inventory.schema.json` | Shape of `kpi_inventory.json` — metric names, the workbooks that define them, their definitions, a conflict flag, and a plain-English description |
| `access_rules.schema.json` | Shape of `access_rules.json` — per-workbook access-rule branches and divergences, in plain English |

These files are not reproduced here; read them directly under
`examples/bi_to_semantic/contracts/` when building against the shape they
enforce. Because they carry a `$schema` draft URI, they are exactly the kind
of contract file that trips
[help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)
if passed to `CocoOptions.output_schema` unmodified — the library strips
`$schema` / `$id` before forwarding to the SDK, so passing these files as-is
through `CocoOptions.output_schema` is safe; only a caller that reimplements
that stripping needs to be careful.

## App Builder `brief.json` / `BRIEF.md`

Each App Builder project under `examples/app_builder/out/<slug>/` carries:

- `brief.json` — the machine-readable brief: type id, owner-entered context,
  the type's declared questions and their answers.
- `BRIEF.md` — the same brief rendered as Markdown, the form CoCo reads
  (mounted via `add_dirs`) when writing or regenerating the app. The Studio
  page's **Save** and **Save & regenerate** actions write `BRIEF.md` from
  the current form state before queuing CoCo — see
  [help.html#app-builder-brief-overwrite-race](../help.html#app-builder-brief-overwrite-race)
  for the ordering bug this fixed in `0.1.8`.
- `sketches/` — optional attached sketch images for the brief.
- `streamlit_app.py` — the generated (or demo-scaffold) consumer app, once
  built.

There is no JSON Schema file for `brief.json` in the repo; its shape is
implicitly defined by `types/<id>/type.json`'s `brief.questions` list plus
the fixed top-level fields the App Builder engine writes
(`examples/app_builder/engine/paths.py` locates these files under
`OUT_DIR = examples/app_builder/out/`).

## Upload subdirectory contract (`_uploads/`)

`upload_to_cwd()` (`streamlit_coco/upload.py`) writes browser uploads under
`<CocoOptions.cwd>/_uploads/` by default (`DEFAULT_UPLOAD_SUBDIR =
"_uploads"`). The contract it enforces on every write:

- Filenames are sanitized to a basename only (`sanitize_upload_name`) —
  path separators and unsafe characters are stripped; `.`/`..` and empty
  names are rejected.
- The destination directory is resolved and checked to be inside `cwd`
  (`subdir` must be relative and must not contain `..`).
- Extension allowlist: `DEFAULT_ALLOWED_EXTENSIONS`, a fixed frozenset of
  safe document/data extensions (see the constant in `streamlit_coco/upload.py`
  for the exact list) — rejects anything outside it unless a caller passes
  its own `allowed_extensions`.
- Size limit: `DEFAULT_MAX_BYTES = 10 * 1024 * 1024` (10 MiB) unless a
  caller overrides `max_bytes`.
- Overwrite policy is explicit per call: `"error"` (default for
  `upload_to_cwd` — raises `CwdUploadError` if the file exists), `"replace"`
  (default for `chat_input_bar`'s `upload_overwrite`), or `"skip"`.

Each successful write returns an `UploadedPath` (`path`, `relative`, `name`,
`bytes_written`, `overwritten`, `skipped`).

## Versioning

There is no separate schema-versioning scheme for `CocoEvent`, the BI → Semantic
JSON Schemas, or the App Builder brief shape. All of them version with the
package: `pyproject.toml`'s `version` field and `CHANGELOG.md` are the only
record of when a contract's shape changed (see the `0.1.6` and `0.1.8` `Fixed`
entries in [help](../help.html) for examples of contract-adjacent fixes). A
breaking change to any of these shapes is a package-version event, not an
independently versioned schema.
