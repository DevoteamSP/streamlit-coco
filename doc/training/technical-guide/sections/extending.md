# Extending

One section per extension point the repo actually exposes.

## Pluggable text renderer (`text_renderer=`)

`panel()`, `render_transcript()`, and `render_output_field()`
(`streamlit_coco/ui.py`, `streamlit_coco/display.py`) accept `text_renderer=`
so an app can render assistant/user text with any Streamlit text API, or a
custom callable, instead of the hardcoded `st.markdown` default.

**Named values:** `"markdown"` (default), `"write"`, `"text"`, `"caption"`,
`"code"` (also accepts `st.*`-prefixed names). Passing an unknown name
raises a `ValueError` listing the known names.

**Callable form:** pass any `Callable[[str], None]`-shaped function — it is
invoked with the message text.

**Files to touch:**
- `streamlit_coco/text_renderer.py` — the name → callable resolution table.
  Add a new named value here if extending the built-in set.
- Call sites in `streamlit_coco/ui.py` (`panel`) and `streamlit_coco/display.py`
  (`render_transcript`, `render_output_field`) already thread `text_renderer`
  through; a new renderer only needs to be registered once.

**Regenerate / verify step:** run `examples/chat_app.py` (`make chat`) with
the new renderer passed explicitly and confirm assistant/user text renders
as expected; no build step is needed since this is pure Python.

**Tests to add:** extend `doc/features/text-renderer/test-checklist.md`
with the new named value, and add a case to the relevant unit test file
covering renderer resolution (there is no dedicated
`test_text_renderer.py` in the current tree — check `tests/` for the
closest existing coverage before adding a new file).

## Tool family / tool name dispatch

`streamlit_coco/tool_names.py` maps a raw tool name to a `ToolFamily` enum
(`ASK_USER`, `SQL`, `READ`, `WRITE`, `EDIT`, `BASH`, `GLOB`, `GREP`,
`EXIT_PLAN`, `GENERIC`) via `tool_family(name)`, using a normalized
(lowercased, separator-stripped) lookup table. Any tool name that does not
match a known family — including MCP tools — falls through to `GENERIC` and
gets a generic tool card instead of a family-specific one.

**Files to touch:**
- `streamlit_coco/tool_names.py` — add the tool's normalized name(s) to
  `_FAMILY_BY_NORMALIZED`, and add a case to `family_label()` if it needs a
  dedicated header label instead of the raw tool name.
- `streamlit_coco/tool_cards.py` / `streamlit_coco/tool_extract.py` — add
  the family-specific card rendering and any input/diff/SQL extraction the
  new family needs. A family left unregistered here still renders (via the
  `GENERIC` fallback); registering it only changes how it is displayed.

**Regenerate / verify step:** run a chat demo (`make chat`) with a prompt
that exercises the new tool and confirm the tool card renders with the
expected family label and preview instead of the generic fallback.

**Tests to add:** a case in the unit tests covering `tool_family()` /
`family_label()` for the new tool name (see the existing tool-family
coverage pattern in `tests/`), and an NDJSON fixture under
`tests/fixtures/ndjson/` if the new family needs event-normalization
coverage in `test_ndjson_fixtures.py`.

## App Builder `types/<id>/` catalog and skill packs

Each App Builder app type is a folder under `examples/app_builder/types/`:

```text
types/<id>/
  type.json          catalog card: id, name, icon, users, needs,
                      needs_snowflake, topics, grounding_kind, brief
                      (context, enables, does_not, questions)
  SKILL.md            optional — type-specific layout + data rules,
                      read by CoCo via add_dirs when generating the app
  reference/           optional — supporting reference material for SKILL.md
  CHECKLIST.md          optional — self-check list the generate prompt
                      runs against once after a Write, before stopping
types/shared/SKILL.md   generation rules for every type (no type.json —
                      not a catalog card); every Build/regenerate prompt
                      tells CoCo to read this file plus the type's own
                      SKILL.md (both mounted via add_dirs)
```

This is a content-level extension point: adding a type does not require a
Python code change, only a new `types/<id>/` folder (or using the Admin
screen's type editor, which writes the same files).

**Files to touch:**
- `examples/app_builder/types/<id>/type.json` — required; follow the shape
  of an existing type (e.g. `types/call-transcription/type.json`) for the
  `brief.questions` structure and the `grounding_kind` values
  (`tabular` / `semantic_view` / `documents` / `urls`) that decide whether
  the profile step is a deterministic pandas parser
  (`examples/app_builder/engine/profile.py`) or a CoCo job.
- `examples/app_builder/types/<id>/SKILL.md` — optional but expected for a
  real type; without it, CoCo generates only against the shared rules.
- `examples/app_builder/engine/paths.py` — no change needed; `TYPES_DIR`
  already points at `types/`, so a new folder is picked up automatically.

**Regenerate / verify step:** `make app-builder`, open Library, confirm the
new type card appears (filtered correctly by its `topics`), fill a brief,
and Build — confirm the generated `streamlit_app.py` follows the new
`SKILL.md`'s rules and (if a `CHECKLIST.md` is present) that the generate
prompt self-checks against it once.

**Tests to add:** a case in `test_app_builder_catalog.py` covering the new
`type.json` parses and validates against the catalog card fields the
Library/Brief/Admin pages read; a case in `test_app_builder_profile.py` if
`grounding_kind` triggers a new deterministic profile path.

## Adding a new example app

The established pattern for a rail-based example (as in
`examples/bi_to_semantic/` and `examples/app_builder/`) composes
`copilot_rail()` for the Copilot and `app_viewer()` for a live preview of
whatever CoCo writes, wired together through `on_fix` / job queueing — see
[architecture](architecture.html#example-app-orchestration).

**Files to touch:**
- `examples/<name>/` — new folder with its own `app.py` (or multipage
  `app_pages/`), following the composition pattern of an existing example
  closest to the new one's shape (`backlog_desk/` for a no-SQL rail
  example; `bi_to_semantic/` or `app_builder/` for a rail + preview
  example).
- `Makefile` — add a `<name>:` target that runs the new example (mirror an
  existing target, e.g. `bi-semantic:`), add it to `.PHONY`, and add a line
  to `help`.
- `doc/deployment/local.md` §5 and `doc/testing.md` — add the new `make`
  target to the examples table so it is discoverable from the docs that
  already list them.

**Regenerate / verify step:** `make <name>` runs and reaches a usable
screen; if the example uses `app_viewer()`, confirm the preview port does
not collide with an existing example's fixed port (chat/backlog examples
do not use `app_viewer`; `bi_to_semantic` uses `:8511`/`:8512`;
`app_builder` uses `:8513`).

**Tests to add:** at minimum a smoke test parallel to `test_smoke.py`'s
coverage of the existing examples, and a feature-doc checklist under
`doc/features/<feature>/test-checklist.md` if the example exercises new
UI behavior rather than only recomposing existing primitives.
