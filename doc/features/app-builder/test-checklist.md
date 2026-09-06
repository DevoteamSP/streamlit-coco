# Feature: App Builder

**Checklist:** `doc/features/app-builder/test-checklist.md`
**App:** `examples/app_builder` (`make app-builder`)
**API:** compose `copilot_rail()` + `app_viewer()`; guidelines skills — see [`app-builder.md`](app-builder.md)
**Status:** Shipped in `0.1.8`. Automated gate (`make test-all`) passed 2026-09-06. Live CoCo golden-path sign-off still open.

## Preconditions

- [x] Feature documented in [`app-builder.md`](app-builder.md)
- [x] Demo make target exists (`make app-builder`)
- [x] Guidelines skills load in the CoCo session — three files per type: `SKILL.md`, `reference/streamlit_app.py`, `CHECKLIST.md`
- [ ] CLI + writable `CocoOptions.cwd`
- [x] `engine/profile.py` produces a profile pandas can validate without a CoCo session
- [x] Host grants no network tool to CoCo (Reads local files only). URL fetch / PDF extract is later (UC9)

## Golden path — tabular / semantic-view grounding

Flows: [`UX.md`](UX.md) UC1–UC8.

| # | Step | Expected | Pass |
| --- | --- | --- | --- |
| 1 | Welcome copy + menu **Welcome · Library · Brief · Studio · Admin**; **Open Copilot** in the header | Copilot label is explicit | |
| 2 | Welcome → Library **Create a new project** (KPI card) → **Create a new app** (name) → Brief: pick the demo pack | A named folder is created under `out/`; header shows the app name (no **New app**); returning to Library shows a **Resume** project card; deterministic profile runs, **no agent call**; Brief shows **Your brief** + sketches on the left and **Questions** on the right | |
| 2a | Library topic pills at the top: select **Local**, then **Snowflake** | Resume and Create a new project both filter; empty pills show everything | |
| 2b | Brief: change **App name** | `brief.json` / `BRIEF.md` and the header badge use the new name; `out/<slug>/` folder is unchanged | |
| 3 | Brief: review "What we found" | Metrics / grain / filters pre-filled via `infer:`; both never-inferred questions (audience, must-not) render blank | |
| 4 | Correct one inferred field, leave the rest | Correction persists; **Build this app** stays enabled once required fields are answered | |
| 5 | **Build this app** with a required field still blank | Action row is at the top of Brief; button disabled; caption names the missing question in plain language (UC5) | |
| 6 | Approve first Write (summary from brief; diff optional) | `out/<slug>/streamlit_app.py` + `brief.json` / `BRIEF.md`; Deny writes no app files (UC7) | |
| 7 | Write lands | `app_viewer` **auto-runs**, no manual Run click (UC1, §6.1a) | |
| 8 | Force a broken generation (bad column ref) | Self-check reads `.preview.log` + type `CHECKLIST.md` and attempts **one** automatic fix before the human sees Preview (§6.1a) | |
| 9 | Self-check exhausted (still red after one pass) | Falls back to manual **Fix with CoCo** exactly as `0.1.7` (UC4) | |
| 10 | "Chart by month, not week" | Edit under approval (UC3); grain in `brief.json` updated because it is a question | |
| 11 | **Regenerate** from filled brief | App rewritten from full `BRIEF.md` + confirmed profile (UC8); form still pre-filled on Resume; profile itself is **not** silently re-run | |
| 11a | Copilot **App brief** expander: edit owner brief or a type question → **Save** | `BRIEF.md` / `brief.json` update (all answers); Preview stays; no new CoCo job | |
| 11c | After Connect, empty transcript: starter buttons **List the files** / **Explain the brief** / **Suggest a change** | Hover shows the full question; click sends it and hides the starters | |
| 11b | Same expander → **Save & regenerate** | Brief saved; Build job queued; CoCo rewrites `streamlit_app.py` from the new brief (UC8) | |
| 12 | **Re-profile** (separate action) | Re-runs profiling; conflicts with confirmed answers are surfaced for reconciliation, not silently overwritten | |
| 13 | Admin: click a type card → Edit, rename, save; Create a throwaway type then Delete | Left cards select the editor; Topics \| Context and Allows \| Does not share rows; questions are tabs (add / edit / delete), not JSON; catalog CRUD persists under `types/`; delete is confirmed | |
| 13a | Admin **Guidelines skills**: edit shared `SKILL.md` and the type `SKILL.md`, save each | Files update under `types/shared/` and `types/<id>/`; next **Build this app** prompt lists those absolute paths and CoCo Reads them | |

## Later — document / URL grounding (UC9)

Out of `0.1.8`. No `doc-compare` or `urls` type in this cut. Re-enable when
those folders land.

| # | Step | Expected | Pass |
| --- | --- | --- | --- |
| 1 | Library: pick a `documents` type (doc-compare) → drop 3 sample files | Host extracts text into `out/<slug>/sources/`, each with a fetch timestamp; **no CoCo call yet** | |
| 2 | One dropped file is corrupted / unsupported | Per-source inline error (UC10); if that source is `required`, **Build** stays blocked | |
| 3 | All sources resolve | CoCo job proposes a comparison schema; rendered as the confirm form, same chrome as tabular types | |
| 4 | Confirm the proposed schema, **Build** | From here on, identical to steps 5–8 above — Write, approve, auto-run, self-check | |
| 5 | Preview | Generated app reads only `out/<slug>/sources/*`; never touches the network itself | |

## Edge cases

- [ ] Vague intent / inconclusive profile → clarifying question, not a confidently wrong app
- [ ] Deny Write — nothing written; user can retry
- [ ] Skills missing / not loaded — visible failure, not silent unconstrained generation
- [ ] Preview pointed at host app — must not happen (same rule as `app_viewer`)
- [ ] Profile pre-fills a field that is then required — user can still override every inferred value
- [ ] `ships_copilot` type (if live): generated app's embedded rail never has access to the App Builder's own session/credentials — a separate connection

## Sign-off

| Date | Tester | Result | Notes |
| --- | --- | --- | --- |
| — | — | Not run | Pending implementation |
