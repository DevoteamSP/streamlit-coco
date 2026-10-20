# Getting started

## Access and prerequisites

- Python >=3.10, a virtual environment, and Streamlit >=1.55.
- A Snowflake account with Cortex Code access, and a connection configured in
  `~/.snowflake/connections.toml` (or the legacy `~/.snowflake/config.toml`).
  This library never stores or logs credentials itself — authentication is
  delegated to the CoCo CLI, the SDK, and the OS-level Snowflake config.
- The `cortex` CLI reachable on `PATH`, or `CORTEX_CODE_CLI_PATH` set to its
  location.

Installation and CLI setup are covered step by step in Enablement
[`setup.html`](../../enablement/setup.html) — follow that page first if you
have not installed `streamlit-coco` yet. This page assumes installation is
done and picks up from a working checkout.

## First run

1. Confirm the environment is ready before writing any app code:

   ```python
   import streamlit_coco as st_coco

   env = st_coco.check_environment()
   print(env.ready, env.sdk_installed, env.cli_ok, env.snowflake_config_found)
   ```

   `check_environment()` never raises — it always returns a `CocoEnvironment`,
   so a `False` here means something to fix, not a crash. See
   [Concepts](concepts.html#cocoenvironment) and
   [API reference](reference-api.html) for every field.

2. Run the first-party demo to see a working app before writing your own:

   ```bash
   make chat
   ```

   This runs `examples/chat_app.py` — the preferred integration pattern
   (`check_environment` → `render_start_gate` → `get_or_create_session` →
   `panel()` + `chat_input_bar()`) in the smallest working form. Details and
   the other example apps are in
   [I want to run the example apps](task-run-the-example-apps.html).

3. Build your own minimal app from the same pattern:
   [I want to build a minimal CoCo app](task-build-a-minimal-app.html).

## You're done when…

- `check_environment().ready` is `True` for the connection you intend to use.
- `make chat` opens a browser tab showing the CoCo panel, and a prompt you
  type gets a streamed response.
- You can point to the four calls of the preferred pattern
  (`check_environment` → `render_start_gate` → `get_or_create_session` →
  `panel()`) in `examples/chat_app.py` and explain what each one does.

If `check_environment()` reports a problem, or the app gets stuck before a
response appears, see
[FAQ](faq.html) or
[`help.html`](../../technical-guide/help.html) in the Technical Guide.
