# Local deployment

Run **streamlit-coco** on your laptop or VM with the CoCo CLI and Snowflake credentials on the same host as Streamlit.

**Related:** [README quickstart](../../README.md) · [PRD §8](../prd.md) · SPCS / Docker (Next on [roadmap](../roadmap.md))

---

## 1. Python environment

**Requirements:** Python **3.10+**, Streamlit **≥ 1.55**.

### Install from PyPI (when published)

```bash
uv add "streamlit-coco[sdk]"
# or: pip install "streamlit-coco[sdk]"
```

The `[sdk]` extra pulls in `snowflake-cortex-agent-sdk`.

### Install from a clone (editable + dev tools)

```bash
# Public / install-from-source
git clone https://github.com/DevoteamSP/streamlit-coco.git
cd streamlit-coco
# Contributors developing the library: clone streamlit-coco-dev instead
uv sync --extra dev   # uv sync --extra dev
```

Verify the package:

```bash
uv run python -c "import streamlit_coco as c; print(c.__version__)"
```

---

## 2. CoCo CLI (`cortex`)

The Cortex Code Agent SDK spawns the **CoCo CLI** as a subprocess. It must be installed and reachable on the same machine as your Streamlit app.

```bash
cortex --version
```

If the binary is not on `PATH`, set:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

Or pass `cli_path=` in `CocoOptions`.

Official SDK docs: [Cortex Code Agent SDK](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)

---

## 3. Snowflake connection

CoCo uses your Snowflake CLI connection config. Create or update:

```text
~/.snowflake/connections.toml
```

Example (adjust account, user, and auth for your org):

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema as needed
```

Legacy `~/.snowflake/config.toml` is also detected.

Pass the connection name to the library:

```python
opts = st_coco.CocoOptions(connection="analytics", cwd=".")
```

When `connection` is omitted, the SDK uses the Snowflake CLI default connection.

---

## 4. Environment check (before starting CoCo)

Probe SDK, CLI, and config **without** starting an agent:

```python
import streamlit_coco as st_coco

env = st_coco.check_environment(connection="analytics")
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
```

For scripts that should fail fast:

```python
st_coco.require_environment(connection="analytics")
```

Typed errors (`SDKNotInstalledError`, `CLINotFoundError`, …) replace opaque runtime failures — see `streamlit_coco.errors`.

In a Streamlit application you need not call it: the Ask CoCo window checks the environment itself, says what is missing and how to fix it, and starts nothing before the user presses **Connect**. Call `check_environment()` for a page of your own.

---

## 5. Run the examples

From the repo root (after `uv sync --extra dev`):

| Command | App | What it exercises |
| --- | --- | --- |
| `uv run --extra dev python -m streamlit run examples/chat_app.py` | `examples/chat_app.py` | The window, a test-prompt picker, rights as pills |
| `uv run --extra dev python -m streamlit run examples/approval_gate.py` | `examples/approval_gate.py` | A listed command, a file rule, SQL, a standing permission |
| `uv run --extra dev python -m streamlit run examples/structured_output.py` | `examples/structured_output.py` | A structured result handed to the page (`coco.result`) |
| `uv run --extra dev python -m streamlit run examples/cwd_upload_chat.py` | `examples/cwd_upload_chat.py` | Files attached in the window, and an uploader on the page |
| `uv run --extra dev python examples/headless_pipeline.py` | `examples/headless_pipeline.py` | `query()`, a `CocoSession` and a `Conversation` without Streamlit |
| `uv run --directory examples/backlog_desk --project ../.. python -m streamlit run streamlit_app.py` | `examples/backlog_desk/` | Multipage product backlog desk (file-backed, no SQL) |

No login yet? Set `STREAMLIT_COCO_AGENT=mock` (PowerShell: `$env:STREAMLIT_COCO_AGENT="mock"`) and any of them runs on a scripted agent.

Or run Streamlit directly:

```bash
uv run streamlit run examples/chat_app.py
```

Exploratory prompts: [`examples/testdata/prompts.json`](../../examples/testdata/prompts.json) (use the **Test prompts** sidebar in `uv run --extra dev python -m streamlit run examples/chat_app.py`).

---

## 6. Minimal app skeleton

```python
import streamlit as st
import streamlit_coco as st_coco

st.title("My app")
st_coco.ask_coco(".")  # the agent works in this folder; reading is free, everything else asks
```

The rights, the features and the two applications of the README: [`README.md`](../../README.md) and [`doc/api.md`](../api.md).

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SDKNotInstalledError` | Missing Python SDK | `pip install streamlit-coco[sdk]` or `uv sync --extra dev` |
| `CLINotFoundError` | `cortex` not on PATH | Install CLI; set `CORTEX_CODE_CLI_PATH` |
| `CLIProbeError` | Binary exists but `--version` fails | Reinstall CLI; check permissions |
| `CocoConnectionError` | Bad connection name or auth | Fix `connections.toml`; test with Snowflake CLI |
| The window stays on **Connecting** or shows a problem | CLI or network issue | Read the problem text in the window and **Try again**; check the terminal log; **Session details** (with `Features(session_details=True)`) shows versions |
| The window says the package or the program is not installed | SDK or Cortex Code missing | Run the command the window shows, or `pip install streamlit-coco[sdk]` |

Run the test suite locally:

```bash
uv run --extra dev ruff check . && uv run --extra dev python -m pytest tests/ --ignore=tests/e2e --ignore=tests/e2e_classic   # ruff + pytest (includes NDJSON fixture regression tests)
```

---

## 8. What local deployment does *not* cover

- **Streamlit Community Cloud** — CoCo needs subprocess + CLI on the host; often not available.
- **PCS** — documented in a follow-up (roadmap P2).

For production topologies, see [`doc/roadmap.md`](../roadmap.md).
