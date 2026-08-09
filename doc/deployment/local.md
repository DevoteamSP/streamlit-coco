# Local deployment

Run **streamlit-coco** on your laptop or VM with the CoCo CLI and Snowflake credentials on the same host as Streamlit.

**Related:** [README quickstart](../../README.md) · [PRD §8](../prd.md) · SPCS / Docker (Next on [roadmap](../roadmap.md))

---

## 1. Python environment

**Requirements:** Python **3.10+**, Streamlit **≥ 1.53**.

### Install from PyPI (when published)

```bash
uv add "streamlit-coco[sdk]"
# or: pip install "streamlit-coco[sdk]"
```

The `[sdk]` extra pulls in `cortex-code-agent-sdk`.

### Install from a clone (editable + dev tools)

```bash
# Public / install-from-source
git clone https://github.com/DevoteamSP/streamlit-coco.git
cd streamlit-coco
# Contributors developing the library: clone streamlit-coco-dev instead
make install   # uv sync --extra dev
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

In Streamlit apps, use the built-in start gate:

```python
env = st_coco.check_environment(connection=opts.connection)
if not st_coco.render_start_gate(opts, session_key="copilot", env=env):
    st.stop()
```

The gate shows SDK / CLI / Snowflake status and only starts the session after you click **Start CoCo Chat**.

---

## 5. Run the examples

From the repo root (after `make install`):

| Command | App | What it exercises |
| --- | --- | --- |
| `make chat` | `examples/chat_app.py` | Preferred `panel()` + `chat_input_bar`, tool cards, approvals |
| `make approval` | `examples/approval_gate.py` | Legacy CCv2 `chat()` |
| `make structured` | `examples/structured_output.py` | Structured output callback |
| `make headless` | `examples/headless_pipeline.py` | `query()` without Streamlit UI |
| `make backlog` | `examples/backlog_desk/` | Multipage product backlog desk (file-backed, no SQL) + right-rail Copilot |

Or run Streamlit directly:

```bash
uv run streamlit run examples/chat_app.py
```

Exploratory prompts: [`examples/testdata/prompts.json`](../../examples/testdata/prompts.json) (use the **Test prompts** sidebar in `make chat`).

---

## 6. Minimal app skeleton

```python
import streamlit as st
import streamlit_coco as st_coco

opts = st_coco.CocoOptions(
    connection="analytics",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
)

env = st_coco.check_environment(connection=opts.connection)
if not st_coco.render_start_gate(opts, session_key="copilot", env=env):
    st.stop()

session = st_coco.get_or_create_session(opts, key="copilot")
st_coco.panel(session=session, warm_up=True, show_status=True, run_every=0.25)
st_coco.chat_input_bar(session, placeholder="Ask CoCo…")
```

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SDKNotInstalledError` | Missing Python SDK | `pip install streamlit-coco[sdk]` or `make install` |
| `CLINotFoundError` | `cortex` not on PATH | Install CLI; set `CORTEX_CODE_CLI_PATH` |
| `CLIProbeError` | Binary exists but `--version` fails | Reinstall CLI; check permissions |
| `CocoConnectionError` | Bad connection name or auth | Fix `connections.toml`; test with Snowflake CLI |
| Session stuck on **Starting CoCo…** | CLI or network issue | Check terminal logs; enable debug (`STREAMLIT_COCO_DEBUG=1`) |
| Input disabled after boot | `SessionNotReadyError` / ERROR status | Fix environment; reset session from sidebar |

Run the test suite locally:

```bash
make check   # ruff + pytest (includes NDJSON fixture regression tests)
```

---

## 8. What local deployment does *not* cover

- **Streamlit Community Cloud** — CoCo needs subprocess + CLI on the host; often not available.
- **PCS** — documented in a follow-up (roadmap P2).

For production topologies, see [`doc/roadmap.md`](../roadmap.md).
