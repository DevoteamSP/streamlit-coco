# streamlit-coco 0.3.1: a settings file of its own for the window's Cortex Code

Written 2026-11-18, for version 0.3.1 (0.3.0 today).

## What

A new option, `CocoOptions.settings_file`. When it is set, the Cortex Code program that the window starts reads **this settings file**, not the user's own `~/.snowflake/cortex/settings.json`. Cortex Code already has the flag for this: `cortex --config <path>`.

```python
import streamlit_coco as st_coco

st_coco.ask_coco(
    root,
    options=st_coco.CocoOptions(model="auto", settings_file="~/.my_app/coco_settings.json"),
)
```

Nothing changes for an application that does not set it.

## Why

- **A real failure.** An application session failed because the user's own Cortex settings switched on a plugin (`cortex-code-migrations`) whose hooks did not match the version of an MCP server (`migration-mcp-server`). Every tool call of the session failed. The application had nothing to do with that plugin.
- **An application needs sessions it controls.** It must be able to say: my sessions ignore the user's own Cortex plugins, hooks and environment.
- **The user's settings file holds much more than a connection and a model.** It can have `plugins`, `env`, `permissions`, `enabledInstructionPatterns` and `disableBundledSkills`. Any of them can change what a session of the application does, or break it.
- **The window gives no way to change this today.** `ask_coco(options=...)` passes to the program only `model`, `connection`, `cli_path`, `mcp_servers`, `max_turns` and `output_schema` (`cortex.py`, around line 577). The window builds its own `extra_sdk_options` and never reads the caller's.
- **The headless sessions can already do it, the window cannot.** `CocoOptions.to_sdk_options()` (`options.py`, around line 104) passes `extra_sdk_options` on, so a headless session can give `extra_args={"config": ...}`. Applications already use this for their headless runs: a small settings file with the user's connection and model only.

## How

### The option

In `streamlit_coco/options.py`, `CocoOptions` gets one field:

```python
settings_file: str | None = None  # a settings.json for the program (`cortex --config`); None: the user's own
```

- `options_hash()` includes it: another file means another session.
- `to_sdk_options()` passes it as `extra_args["config"]`, so headless sessions and `mini.py` get it too. When the caller also gives `extra_sdk_options["extra_args"]`, the two are merged; `settings_file` wins for `config`.

### The window

In `streamlit_coco/cortex.py`, where the window connects (around lines 577 to 660):

- When `host.settings_file` is set, check that the file exists. When it does not, fail the connection (a `connect_failed` event, the way the adapter already reports a failed connection; an exception would break the page's run) with a sentence in plain words: `The settings file <path> does not exist: create it, or leave settings_file empty to use your own Cortex settings.` Never start the program without it: the user would think the session is protected when it is not.
- Add it to the options the window builds itself: `extra["extra_args"] = {"config": str(Path(host.settings_file).expanduser())}`.
- Everything else stays as it is: `mode`, `can_use_tool`, the hooks, the UTF-8 `env`, and `no_mcp` when the host gives no MCP server.

### What the file holds

This is the caller's job, not the library's. A minimal file keeps the connection and the model, so the user does not have to choose them again:

```json
{
 "cortexAgentConnectionName": "my_profile",
 "sqlConnectionName": "my_profile",
 "model": "auto"
}
```

The library writes nothing, and never reads or copies the user's settings itself.

### Not asked

- A generic pass-through of any extra command-line flag. One named option is easier to check and to explain, and it cannot switch off the window's own protections.
- Choosing which settings sources to read (`--setting-sources`). It was measured that this does not change what Cortex Code loads; `--config` does.

## Tests

Automated (unit, no real program):

- `CocoOptions(settings_file=p).to_sdk_options().extra_args == {"config": p}`; merged with an `extra_args` the caller gives.
- `options_hash()` differs when only `settings_file` differs.
- The window's connect builds `extra_args={"config": <absolute path>}` when the option is set, and builds no `extra_args` when it is not (the options the window gives to `CocoSession` can be read in the existing tests of `cortex.py`).
- A missing file gives the `connect_failed` sentence above, and no program is started.
- `mini.py`'s `options_for_window` copies `CocoOptions` field by field: it keeps `settings_file` (a test holds it).
- `~` in the path is expanded.

Manual, before the tag (add a line to `doc/features/ask-coco/test-checklist.md`):

1. In `~/.snowflake/cortex/settings.json`, switch on a plugin whose hook writes a line to a file at each tool call.
2. Open an example app with `settings_file` set to a minimal file. Ask a question that reads a file: the plugin's file stays empty.
3. Remove `settings_file`: the plugin's file gets a line. This proves the option is the only difference.

Checked on 2026-11-18: Cortex Code `v1.2.45` has `--config` ("Path to a custom settings.json configuration file").

## Documents to update in streamlit-coco

- `doc/api.md`: the new field of `CocoOptions`.
- `doc/features/ask-coco/ask-coco.md`: a short section "A settings file of its own".
- `CHANGELOG.md`, `0.3.1`: "The window can start Cortex Code with a settings file of its own (`CocoOptions.settings_file`), so the user's plugins, hooks and environment do not reach the application's sessions."
- `doc/roadmap.md`: the `0.3.1` line.

## Limits

- The file **replaces** the user's settings: whatever is not in it is not read. A setting the user relies on (a theme, `disableBundledSkills`) is not applied in these sessions. That is the point, but it should be said in the docs.
- The user's own skills (`~/.snowflake/cortex/skills`) and MCP servers are not settings: this option does not change them. The window already starts with no MCP server when the host gives none.
- It needs a Cortex Code version with `--config`. Older versions refuse the flag at start; the existing start error then shows.
