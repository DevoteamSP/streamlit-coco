# Testing: streamlit-coco

How to verify a change before a merge or a release.

## Automated gates

| Gate | Command | What it covers |
| --- | --- | --- |
| Fast | `make check` | `ruff`, then the unit tests (`tests/`, without the browser tests) |
| Browser | `make e2e` | Playwright against the window on the scripted agent ([`examples/e2e_ux_harness.py`](../examples/e2e_ux_harness.py)), the window on the managed agent over a scripted stream of Snowflake's client ([`examples/e2e_managed_harness.py`](../examples/e2e_managed_harness.py)), and the 0.1.9 chat helpers on their own harness ([`tests/e2e_classic/`](../tests/e2e_classic/)) |
| Security | `make audit` | `pip-audit --skip-editable` (dependencies only) |
| Full | `make test-all` | `check`, `e2e` and `audit` |

First-time Playwright setup:

```bash
make e2e-install   # uv sync --extra e2e, then Chromium
make e2e
```

`make e2e` uses the installed Edge when Playwright's Chromium is not installed. The harness runs with `STREAMLIT_COCO_AGENT=mock`: no Snowflake login, no live agent. CI (`.github/workflows/ci.yml`) runs the unit tests and the browser tests on every pull request to `main`.

## What the tests cover

- **Unit tests** (`tests/`): the conversation, the gate, the policy (paths, secrets, listed commands, SQL), the scripted agent, labels, attachments, `render_output_field`, uploads, the headless example, and **compatibility with released versions**: `test_compat_019.py`, `test_compat_022.py` and `test_compat_030.py` compare the current API with `tests/fixtures/api_0.1.9.json`, `api_0.2.2.json` and `api_0.3.0.json` (no name, module, member or parameter of those releases may go, move, become required or change its default; a new parameter needs a default; the 0.2.2 snapshot holds what 0.2.0 to 0.2.2 added, such as `ask_coco`, `Features` and `get_window`), and `test_copilot_rail.py`, `test_rich_text.py`, `test_classic_core.py` and `test_classic_smoke.py` are the 0.1.9 tests of the chat family, kept. `tests/test_window.py` checks every fixture of `streamlit_coco.testing.VIEWS` against the conversation's contract, and runs a Node check of the window's script when Node is installed.
- **Browser tests** (`tests/e2e/`): a walk of the default window (connect, a read, Allow, Decline, queue, Take back, Stop, New conversation), the code block's copy button, "Latest exchange only", a file attached in the field and saved in `<cwd>/_coco_uploads/<id>/`, and the page's `cwd_uploader`; the managed window (`test_managed_window.py`: its first screen, a command that asks in the sandbox, Allow, Decline, the audit log, a file that goes to the stage); the window's places (`test_window_layout.py`): attach left or right, full page, the switches, the page callback and `split`, the hint after 750 ms, the title bar over the page's header.
- **Browser tests of the chat helpers** (`tests/e2e_classic/`): the 0.1.9 tests, unchanged, on a CoCo-free harness: SQL highlighting and the copy button, transcript windowing (**Load earlier**), and the sidebar upload into `cwd`.
- What no test covers is listed plainly, row by row, in the no-regression table of [`features/ask-coco/ask-coco.md`](features/ask-coco/ask-coco.md) (section 3).

Run the harness alone: `make e2e-harness`. Look at the window on a fixture with no server: `python -m streamlit_coco.testing.harness f38_question_choice`. Compare the window's DOM with an earlier commit: `python -m streamlit_coco.testing.domdiff --ref HEAD`.

## Live product (manual, before a release)

Needs the Cortex Code program (rows 1 to 20) or a Snowflake account with the Cortex Agent API (rows 21 to 33), and costs credits. Run [`features/ask-coco/test-checklist.md`](features/ask-coco/test-checklist.md) in a scratch folder, never in a customer repository. Then, as they apply to what changed: the checklists of [App viewer](features/app-viewer/test-checklist.md), [App Builder](features/app-builder/test-checklist.md) and [headless](features/headless/test-checklist.md). Exploratory prompts: [`examples/testdata/prompts.json`](../examples/testdata/prompts.json) (the **Test prompts** picker of `make chat`).

## Release hygiene

Before tagging (`make sync-release`, then a `v*` tag), complete the version kit under [`releases/`](releases/README.md):

1. `make test-all`
2. The live checklist, for what changed
3. A clean [`CHANGELOG.md`](../CHANGELOG.md), [`roadmap.md`](roadmap.md) and [`prd.md`](prd.md); a new `tests/fixtures/api_X.Y.Z.json` and `test_compat_*` for the release (see `tests/api_snapshot.py`)
4. Screenshots in `releases/X.Y.Z/`; outreach in [`../doc-dev/releases/`](../doc-dev/releases/README.md)
5. Then [`deployment/publish.md`](deployment/publish.md)

## Layout

```text
tests/           unit tests (make test)
tests/e2e/       Playwright, the window (make e2e)
tests/e2e_classic/  Playwright, the 0.1.9 chat helpers (make e2e)
tests/fixtures/api_0.1.9.json, api_0.2.2.json, api_0.3.0.json  the released APIs the compatibility tests hold the package to
examples/e2e_ux_harness.py
examples/e2e_managed_harness.py
```
