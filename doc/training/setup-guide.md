# Setup Guide — streamlit-coco

Get the dev repo running locally and verify you're ready for the hands-on lab.
Full reference: [`doc/deployment/local.md`](../deployment/local.md) — this guide is the
condensed, training-specific path through it.

## 1. Clone and install

```bash
git clone https://github.com/DevoteamSP/streamlit-coco-dev.git
cd streamlit-coco-dev
make install     # uv sync --extra dev
```

Verify the package imports and check the version:

```bash
uv run python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.6
```

## 2. Install and verify the CoCo CLI

```bash
cortex --version
```

If it's not on `PATH`, either install it or point at the binary:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

## 3. Set up a Snowflake connection

Create or confirm `~/.snowflake/connections.toml`:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema as needed
```

You need an account with **Cortex Code access**. Ask the asset owner if you don't have one
for training — a shared/sandbox connection may be available.

## 4. Environment check (no agent started yet)

```bash
uv run python -c "
import streamlit_coco as st_coco
env = st_coco.check_environment(connection='analytics')
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
"
```

`env.ready` should print `True`. If not, see the troubleshooting table in
[`doc/deployment/local.md` §7](../deployment/local.md#7-troubleshooting) before continuing.

## 5. Run the test suite

```bash
make check    # ruff + pytest (includes NDJSON fixture regression tests)
```

All tests should pass. This confirms your Python environment matches CI.

## 6. Run your first demo

```bash
make chat
```

A browser tab opens with the `panel()` + chat input demo. Type a prompt (e.g. *"What
tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*) and confirm you see a streaming
response with tool cards.

## Verification checklist — you're ready when...

- [ ] `uv run python -c "import streamlit_coco as c; print(c.__version__)"` prints `0.1.6`
- [ ] `cortex --version` succeeds
- [ ] `check_environment(...).ready` is `True`
- [ ] `make check` passes with no failures
- [ ] `make chat` opens a working app and you get a streamed response with at least one tool card
- [ ] You can locate `doc/features/README.md` (feature index) and `doc/marketing/demo.md` (demo script) in the repo

If every box is checked, move on to [`hands-on-lab.md`](hands-on-lab.md).

## Troubleshooting quick reference

| Symptom | Fix |
| --- | --- |
| `SDKNotInstalledError` | `make install` again, or `pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | Install the CLI, set `CORTEX_CODE_CLI_PATH` |
| `CocoConnectionError` | Fix `connections.toml`; test with `cortex --version` and Snowflake CLI directly |
| Session stuck on "Starting CoCo…" | Check terminal logs; set `STREAMLIT_COCO_DEBUG=1` |

Full table: [`doc/deployment/local.md` §7](../deployment/local.md#7-troubleshooting).
