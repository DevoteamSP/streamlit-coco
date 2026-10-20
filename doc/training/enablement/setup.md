# Setup

Get the development repository running locally and verify you are ready for
the [guided tour](guided-tour.html) and the [hands-on exercises](hands-on.html).
Full reference: [`doc/deployment/local.md`](../../deployment/local.md) — this
page is the condensed, training-specific path through it.

## Required accounts and permissions

- A Snowflake account with **Cortex Code access**. Ask your asset owner if
  you do not have one for training — a shared/sandbox connection may be
  available.
- Git access to `DevoteamSP/streamlit-coco-dev` (the development repository).
  If you only need the published package, `pip install "streamlit-coco[sdk]"`
  from PyPI is enough and you can skip step 1 below.

## 1. Clone and install

```bash
git clone https://github.com/DevoteamSP/streamlit-coco-dev.git
cd streamlit-coco-dev
make install     # uv sync --extra dev
```

Verify the package imports and check the version:

```bash
uv run python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

## 2. Install and verify the CoCo CLI

```bash
cortex --version
```

If it is not on `PATH`, either install it or point at the binary:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

`CocoOptions(cli_path=...)` also works, in code, as an alternative to the
environment variable.

## 3. Set up a Snowflake connection

Create or confirm `~/.snowflake/connections.toml`:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema as needed
```

Legacy `~/.snowflake/config.toml` is also detected. When `connection` is
omitted in `CocoOptions`, the SDK uses the Snowflake CLI's default
connection.

## 4. Environment check (no agent started yet)

```bash
uv run python -c "
import streamlit_coco as st_coco
env = st_coco.check_environment(connection='analytics')
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
"
```

`env.ready` should print `True`. If not, see the troubleshooting table in
[`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting)
before continuing.

## 5. Run the test suite

```bash
make check    # ruff + unit/smoke pytest (excludes tests/e2e)
```

All tests should pass. This confirms your Python environment matches CI.

## 6. Run your first demo

```bash
make chat
```

A browser tab opens with the `panel()` + `chat_input_bar()` demo
(`examples/chat_app.py`). Type a prompt — for example *"What tables are
available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"* — and confirm you see a
streaming response with at least one tool card.

## Verification checklist — you're ready when...

- [ ] `uv run python -c "import streamlit_coco as c; print(c.__version__)"` prints `0.1.9`
- [ ] `cortex --version` succeeds
- [ ] `check_environment(...).ready` is `True`
- [ ] `make check` passes with no failures
- [ ] `make chat` opens a working app and you get a streamed response with at least one tool card

If every box is checked, move on to [`guided-tour.md`](guided-tour.html).

## Troubleshooting quick reference

| Symptom | Fix |
| --- | --- |
| `SDKNotInstalledError` | `make install` again, or `pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | Install the CLI; set `CORTEX_CODE_CLI_PATH` |
| `CocoConnectionError` | Fix `connections.toml`; test with `cortex --version` and the Snowflake CLI directly |
| Session stuck on "Starting CoCo…" | Check terminal logs; set `STREAMLIT_COCO_DEBUG=1` |

Full table: [`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting).
The Technical Guide has the complete reference:
[`help.html`](../technical-guide/help.html).
