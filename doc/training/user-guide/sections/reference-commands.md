# Command reference

Every `make` target in the repo's `Makefile` that a user of the library runs
directly. There is no `[project.scripts]` entry — all commands go through
`make`.

## `make install`

Synopsis: `make install`

Installs the package with its `dev` extras, editable, via `uv`
(`uv sync --extra dev`). `make sync` is an alias for the same target.

Output: an editable install in the active virtual environment.

## `make run`

Synopsis: `make run [EXAMPLE=<path>]`

| Variable | Default | Effect |
|---|---|---|
| `EXAMPLE` | `examples/chat_app.py` | The example script to run |

Runs the given example with `streamlit run`. Output: the app opens in the
default browser on the next free Streamlit port.

## `make chat`

Synopsis: `make chat`

Runs `examples/chat_app.py` — the preferred-pattern demo. See
[I want to run the example apps](task-run-the-example-apps.html) and
[Example apps reference](reference-examples.html).

## `make approval`

Synopsis: `make approval`

Runs `examples/approval_gate.py` — the legacy CCv2 `chat()` demo.

## `make structured`

Synopsis: `make structured`

Runs `examples/structured_output.py` — the `output_schema` /
`on_structured_output` demo.

## `make headless`

Synopsis: `make headless`

Runs `examples/headless_pipeline.py` from a terminal, no Streamlit involved.
Output: streamed event text in the terminal.

## `make cwd-upload`

Synopsis: `make cwd-upload`

Runs `examples/cwd_upload_chat.py` — the file-upload demo.

## `make backlog`

Synopsis: `make backlog`

Runs the Product Backlog Desk (`examples/backlog_desk/`) — a multipage,
file/JSON-backed demo with a right-rail Copilot. Output files land under
`examples/backlog_desk/data/`; see [Outputs](outputs.html).

## `make bi-semantic`

Synopsis: `make bi-semantic`

Runs BI → Semantic (`examples/bi_to_semantic/`). `make tableau-semantic` is a
deprecated alias for the same target. Output files land under
`examples/bi_to_semantic/out/`; see [Outputs](outputs.html).

## `make app-builder`

Synopsis: `make app-builder`

Runs App Builder (`examples/app_builder/`). Output files land under
`examples/app_builder/out/<slug>/`; see [Outputs](outputs.html).

## `make e2e-harness`

Synopsis: `make e2e-harness`

Runs the CoCo-free UX harness (`examples/e2e_ux_harness.py`) used by the
Playwright end-to-end suite — no live agent involved.

## `make test`

Synopsis: `make test`

Runs the unit/smoke test suite: `pytest tests/ --ignore=tests/e2e -v`.

## `make lint`

Synopsis: `make lint`

Runs `ruff check .`.

## `make format`

Synopsis: `make format`

Runs `ruff format . && ruff check --fix .`.

## `make check`

Synopsis: `make check`

Runs `make lint` then `make test`.

## `make e2e-install`

Synopsis: `make e2e-install`

Installs the `e2e` extra and the Chromium browser for Playwright. Run once
before the first `make e2e`.

## `make e2e`

Synopsis: `make e2e`

Runs the Playwright UX end-to-end suite (`tests/e2e`, marker `e2e`) against
`make e2e-harness`.

## `make audit`

Synopsis: `make audit`

Runs `pip-audit --skip-editable` — a dependency vulnerability scan.

## `make test-all`

Synopsis: `make test-all`

Runs `make check` + `make e2e` + `make audit` — the full automated gate.

## Other targets (maintainer-facing)

These targets exist for cutting and publishing a release rather than for
using the library day to day; they are covered in the Technical Guide
`upgrade-and-release.html`, not repeated here:

| Target | Effect |
|---|---|
| `make build` | Build sdist + wheel into `dist/` (`uv build`) |
| `make publish` | Upload `dist/` to PyPI (`uv publish`) |
| `make sync-release` | Sync the release tree to `../streamlit-coco` (`DRY_RUN=1` / `COMMIT=1` / `PUSH=1`) |
| `make clean` | Remove caches and build artifacts |
| `make adoption-stats` / `make adoption-chart` | Collect/rebuild PyPI and GitHub traffic metrics under `doc-dev/metrics/` — not part of this guide's scope |
