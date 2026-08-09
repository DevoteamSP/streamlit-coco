# Testing — streamlit-coco

How to verify changes before merge / release.

## Automated gates

| Gate | Command | What it covers |
| --- | --- | --- |
| Fast | `make check` | `ruff` + unit/smoke (`tests/`, ignores browser e2e) |
| UX browser | `make e2e` | Playwright vs CoCo-free harness ([`examples/e2e_ux_harness.py`](../examples/e2e_ux_harness.py)) |
| Security | `make audit` | `pip-audit` |
| Full automated | `make test-all` | `check` + `e2e` + `audit` |

First-time Playwright setup:

```bash
make e2e-install   # uv sync --extra e2e + Chromium
make e2e
```

CI (`.github/workflows/ci.yml`) runs **unit** and **e2e** on every PR to `main`. E2e does **not** call a live CoCo agent.

### What the browser suite covers

- Fenced SQL/Python highlighting (`st.code`)
- Clipboard **Copy** on assistant messages
- Sidebar `cwd_uploader` → `_uploads/`
- `max_messages` truncation + **Load earlier**

Run the harness alone: `make e2e-harness`.

## Live product (manual, pre-release)

Requires Cortex CLI + Snowflake connection. Sign the feature checklists under [`doc/features/`](features/README.md).

Suggested order:

1. `make cwd-upload` → [`features/file-upload/test-checklist.md`](features/file-upload/test-checklist.md)
2. `make chat` → [`features/panel/test-checklist.md`](features/panel/test-checklist.md) (includes copy / highlight / windowing UX notes)
3. Tools + approvals → [`features/tools-display/test-checklist.md`](features/tools-display/test-checklist.md), [`features/approvals/test-checklist.md`](features/approvals/test-checklist.md)
4. Optional: `make structured`, `make headless`, `make approval` (CCv2)

Exploratory prompts: [`examples/testdata/prompts.json`](../examples/testdata/prompts.json) (chat sidebar **Test prompts**).

## Release hygiene

Before tagging (`make sync-release` / `v*`), complete the version kit under [`releases/`](releases/README.md) (e.g. [`releases/0.1.5/CHECKLIST.md`](releases/0.1.5/CHECKLIST.md)):

1. `make test-all`
2. Manual checklist pass for touched features
3. Clean [`CHANGELOG.md`](../CHANGELOG.md) + [`roadmap.md`](roadmap.md) + [`prd.md`](prd.md)
4. Screenshots in [`releases/X.Y.Z/`](releases/README.md); outreach in [`../doc-dev/releases/`](../doc-dev/releases/README.md)
5. Then follow [`deployment/publish.md`](deployment/publish.md)

## Layout

```text
tests/           unit + smoke (default make test)
tests/e2e/       Playwright UX (make e2e)
examples/e2e_ux_harness.py
```
