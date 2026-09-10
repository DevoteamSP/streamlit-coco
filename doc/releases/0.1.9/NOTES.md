# Release notes bank — 0.1.9

Freeform. Feed LinkedIn / Medium / GitHub Release.

## Headline (one line)

> Pick the Snowflake connections TOML in the Copilot rail — not only `connections.toml`.

## Top 3 user-visible wins

1. **Config file + Connection** selectboxes on one row in the connection popover
2. **Any `~/.snowflake/*.toml`** — a single file is used whatever its name; several files are listed
3. **`toml_file=`** sets the default; helpers `list_snowflake_connections()` / `list_snowflake_toml_files()`

## Use cases to feature

1. Laptop with both `connections.toml` and legacy `config.toml`
2. A custom-named profile file (`team.toml`) as the only Snowflake config

## Learnings (candid)

- Snowflake CLI still authenticates by connection *name*; the rail only chooses which file to list profiles from.
- Passing a full `connections=` list froze the popover to one file. Extras (e.g. `st.secrets`) are prepended; names always come from the selected TOML.
- Two `st.selectbox` in `st.columns(2)` beat a segmented control in the popover: labels stay readable, both controls share one row.

## Quotes / soundbites

- “Config file on the left. Connection on the right.”
- “One TOML? We use it, whatever you named it.”

## Explicit non-goals this cut

- Changing how the Cortex CLI / SDK resolves the connection (still the profile name)
- API mode / no-CLI (`0.2.0`)
- Backlog Desk still has its own connection popover (not `copilot_rail()`)
