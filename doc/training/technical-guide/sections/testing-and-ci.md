# Testing and CI

## Test tree

```text
tests/            unit + smoke (default `make test`; 17 files)
tests/e2e/         Playwright UX e2e (conftest.py + 3 UX specs)
examples/e2e_ux_harness.py   CoCo-free harness the e2e suite drives
```

Notable unit test files: `test_core.py`, `test_errors.py`, `test_upload.py`,
`test_copilot_rail.py`, `test_app_viewer.py`, `test_snowflake_toml.py`,
`test_ndjson_fixtures.py`, `test_backlog_desk.py`,
`test_bi_to_semantic_parse.py`, `test_app_builder_catalog.py`,
`test_app_builder_profile.py`, `test_rich_text.py`, `test_smoke.py`.

## How to run each gate

| Gate | Command | Covers |
|---|---|---|
| Fast | `make check` | `ruff check .` + `pytest tests/ --ignore=tests/e2e -v` |
| UX browser | `make e2e` | Playwright against `examples/e2e_ux_harness.py` — no live CoCo agent. First time: `make e2e-install` (installs the `[e2e]` extra + Chromium). |
| Security | `make audit` | `pip-audit --skip-editable` |
| Full automated | `make test-all` | `check` + `e2e` + `audit` |

The browser suite covers: fenced SQL/Python highlighting, clipboard **Copy**
on assistant messages, sidebar `cwd_uploader` → `_uploads/`, and
`max_messages` truncation + **Load earlier**.

Manual/live checklists (need a real CoCo CLI + Snowflake connection) live
under `doc/features/<feature>/test-checklist.md`, indexed from
`doc/features/README.md`. Suggested run order: file-upload → panel →
tools-display / approvals → optional structured / headless / approval
(CCv2) / bi-semantic.

## What CI actually gates

`.github/workflows/ci.yml` — on every push to `main` and every pull request
targeting `main`:

- `test` job: `ruff check .`, then `pytest tests/ --ignore=tests/e2e -v`,
  then `pip-audit --skip-editable` (this last step is
  `continue-on-error: true` — non-blocking until a clean baseline is set).
- `e2e` job: installs the `[e2e]` extra and Chromium, then
  `pytest tests/e2e -m e2e -v`. No live CoCo agent is called.

`.github/workflows/security.yml` — on pull requests to `main`, pushes to
`main`, and weekly (Monday 06:00 UTC):

- `gitleaks` job: installs the Gitleaks CLI binary (not
  `gitleaks-action@v2`, which needs a `GITLEAKS_LICENSE` for GitHub
  organization repos) and runs `gitleaks git --verbose --redact
  --exit-code 1 .`.
- `pip-audit` job: `pip-audit --skip-editable` (also
  `continue-on-error: true`).

**CodeQL does not run in this repo's CI.** See
[security](security.html#ci-security-posture-current) for why, and do not
add a CodeQL job assumption when reasoning about this repo's gates.

`.github/workflows/release.yml` runs only on `v*` tag pushes: builds
sdist+wheel, generates the SBOM, and publishes to PyPI (skipped for
pre-release tag suffixes). See [upgrade-and-release](upgrade-and-release.html).

## What to add with a change

- A test for new behavior: a unit test under `tests/` for library code, or
  a Playwright spec under `tests/e2e/` for UX behavior the browser suite
  should catch (fenced code, clipboard, upload, transcript windowing are
  the existing precedent).
- A manual checklist entry under `doc/features/<feature>/test-checklist.md`
  when the change touches a UI feature that needs a live CoCo CLI +
  Snowflake connection to verify (existing features each have their own
  checklist file — add rows to the relevant one, or create a new
  `doc/features/<feature>/` folder for a genuinely new feature, following
  the existing files' `## Preconditions` / `## Golden path` / `## Sign-off`
  shape).
- A `CHANGELOG.md` entry under `[Unreleased]` — `Added` / `Changed` /
  `Fixed` / `Security` as appropriate. Security fixes always go under
  `Security`, never `Fixed`.
