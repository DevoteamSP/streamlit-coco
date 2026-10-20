# Install

One deployment target ships today: **local** — Streamlit, the CoCo CLI, and
the Snowflake connection config all on the same host. Streamlit in Snowflake
(SiS) and SPCS install paths are not implemented in this repo today. They
appear only as scope in [security](security.html#threat-model-summary)
(threat-model context) and in the project roadmap, not as something you can
install.

## Prerequisites matrix

| Requirement | Version | Why |
|---|---|---|
| Python | 3.10+ | `requires-python = ">=3.10"` in `pyproject.toml` |
| Streamlit | >=1.55 | `streamlit-coco` declares `streamlit>=1.55` as its only hard dependency |
| CoCo CLI (`cortex`) | reachable on `PATH`, or `CORTEX_CODE_CLI_PATH` set | The SDK spawns it as a subprocess; the library does not vendor it |
| `cortex-code-agent-sdk` | >=1.0.7 | Installed via the `[sdk]` extra; the library talks to CoCo through this SDK |
| Snowflake connection | one profile in `~/.snowflake/connections.toml` (or legacy `config.toml`) | The CLI/SDK authenticate through this file; the library never stores credentials |

## Local install — ordered steps

### 1. Install the package

```bash
pip install "streamlit-coco[sdk]"
```

or, from a clone (contributors on `streamlit-coco-dev`):

```bash
git clone https://github.com/DevoteamSP/streamlit-coco.git
cd streamlit-coco
make install   # uv sync --extra dev
```

Verify:

```bash
python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

### 2. Install the CoCo CLI

The Cortex Code Agent SDK spawns the CoCo CLI (`cortex`) as a subprocess. It
must be installed and reachable on the same machine as the Streamlit app.

Verify:

```bash
cortex --version
```

If it is not on `PATH`:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

(or pass `cli_path=` on `CocoOptions` — see
[configuration](configuration.html)).

### 3. Configure a Snowflake connection

Create or update `~/.snowflake/connections.toml`:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
```

Legacy `~/.snowflake/config.toml` is also detected. See
[security](security.html#roles-and-grants) for the role this connection
should use.

Verify (probes SDK, CLI, and config without starting an agent):

```python
import streamlit_coco as st_coco

env = st_coco.check_environment(connection="analytics")
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
```

For a script that should fail fast instead of returning a status object:

```python
st_coco.require_environment(connection="analytics")
```

### 4. Run an example app

```bash
make chat
```

Verify: the browser opens on the chat demo and the start gate ("Start CoCo
Chat") shows SDK / CLI / Snowflake status as green before you click it. See
[operations](operations.html) for the full list of `make` targets that run
example apps.

## What is not installable today

- **Streamlit in Snowflake (SiS)** — no install path exists in this repo.
  SiS appears only as deployment context in the threat model, not as a
  supported target.
- **SPCS** — same: threat-model scope, not an install target.
- **Native App** — no `manifest.yml` / `snowflake.yml` in the repo; there is
  nothing to install as a Native App.
