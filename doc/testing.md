# Testing: streamlit-coco

How to verify a change before a merge or a release.

## Automated gates

| Gate | Command | What it covers |
| --- | --- | --- |
| Fast | `make check` | `ruff`, then the unit tests (`tests/`, without the browser tests) |
| Browser | `make e2e` | Playwright against the window on the scripted agent ([`examples/e2e_ux_harness.py`](../examples/e2e_ux_harness.py)), and the 0.1.9 chat helpers on their own harness ([`tests/e2e_classic/`](../tests/e2e_classic/)) |
| Security | `make audit` | `pip-audit --skip-editable` (dependencies only) |
| Full | `make test-all` | `check`, `e2e` and `audit` |

First-time Playwright setup:

```bash
make e2e-install   # uv sync --extra e2e, then Chromium
make e2e
```

`make e2e` uses the installed Edge when Playwright's Chromium is not installed. The harness runs with `STREAMLIT_COCO_AGENT=mock`: no Snowflake login, no live agent. CI (`.github/workflows/ci.yml`) runs the unit tests and the browser tests on every pull request to `main`.

## What the tests cover

- **Unit tests** (`tests/`): the conversation, the gate, the policy (paths, secrets, listed commands, SQL), the scripted agent, labels, attachments, `render_output_field`, uploads, the headless example, and **0.1.9 compatibility**: `test_compat_019.py` compares the current API with `tests/fixtures/api_0.1.9.json` (no name, module, member or parameter of 0.1.9 may go, move, become required or change its default; a new parameter needs a default), and `test_copilot_rail.py`, `test_rich_text.py`, `test_classic_core.py` and `test_classic_smoke.py` are the 0.1.9 tests of the chat family, kept. `tests/test_window.py` checks every fixture of `streamlit_coco.testing.VIEWS` against the conversation's contract, and runs a Node check of the window's script when Node is installed.
- **Browser tests** (`tests/e2e/`): a walk of the default window (connect, a read, Allow, Decline, queue, Take back, Stop, New conversation), the code block's copy button, "Latest exchange only", a file attached in the field and saved in `<cwd>/_coco_uploads/<id>/`, and the page's `cwd_uploader`.
- **Browser tests of the chat helpers** (`tests/e2e_classic/`): the 0.1.9 tests, unchanged, on a CoCo-free harness: SQL highlighting and the copy button, transcript windowing (**Load earlier**), and the sidebar upload into `cwd`.
- What no test covers is listed plainly, row by row, in the no-regression table of [`features/ask-coco/ask-coco.md`](features/ask-coco/ask-coco.md) (section 3).

Run the harness alone: `make e2e-harness`. Look at the window on a fixture with no server: `python -m streamlit_coco.testing.harness f38_question_choice`. Compare the window's DOM with an earlier commit: `python -m streamlit_coco.testing.domdiff --ref HEAD`.

## Live product (manual, before a release)

Needs the Cortex Code program and a Snowflake connection, and costs credits. Run [`features/ask-coco/test-checklist.md`](features/ask-coco/test-checklist.md) in a scratch folder, never in a customer repository. Then, as they apply to what changed: the checklists of [App viewer](features/app-viewer/test-checklist.md), [App Builder](features/app-builder/test-checklist.md) and [headless](features/headless/test-checklist.md). Exploratory prompts: [`examples/testdata/prompts.json`](../examples/testdata/prompts.json) (the **Test prompts** picker of `make chat`).

## Release hygiene

Before tagging (`make sync-release`, then a `v*` tag), complete the version kit under [`releases/`](releases/README.md):

1. `make test-all`
2. The live checklist, for what changed
3. A clean [`CHANGELOG.md`](../CHANGELOG.md), [`roadmap.md`](roadmap.md) and [`prd.md`](prd.md)
4. Screenshots in `releases/X.Y.Z/`; outreach in [`../doc-dev/releases/`](../doc-dev/releases/README.md)
5. Then [`deployment/publish.md`](deployment/publish.md)

## Layout

```text
tests/           unit tests (make test)
tests/e2e/       Playwright, the window (make e2e)
tests/e2e_classic/  Playwright, the 0.1.9 chat helpers (make e2e)
tests/fixtures/api_0.1.9.json  the 0.1.9 API the compatibility test holds the package to
examples/e2e_ux_harness.py
```
