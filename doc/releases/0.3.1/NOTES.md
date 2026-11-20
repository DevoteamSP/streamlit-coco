# Release notes bank — 0.3.1

## Headline (one line)

> Your application's CoCo sessions can ignore the user's own Cortex plugins and hooks: `CocoOptions(settings_file=...)`.

## Top 3 user-visible wins

1. **`settings_file`** — `ask_coco(root, options=CocoOptions(settings_file="~/.my_app/coco_settings.json"))` starts Cortex Code with `--config`, so the file replaces the user's `~/.snowflake/cortex/settings.json` for the application's sessions. A missing file fails the connection with a sentence; it never starts an unprotected session.
2. **One tick covers a batch of edits** — edits Cortex Code sends in one call are judged one by one, so *Do not ask again for changes in this folder* works instead of asking every time.
3. **A cleaner window** — the full-page conversation uses the whole width; a table or a list said before a call is a message, not a flat line; bold text that holds code shows without its stars; the last message of a turn no longer shows twice.

## Learnings (candid)

- The trigger was a real failure: a user's own plugin (hooks that did not match an MCP server version) made every tool call of an unrelated application fail. An application needs sessions it controls.
- `--setting-sources` was measured and does not change what Cortex Code loads; `--config` does.
- `uv lock` on a current uv rewrites the whole lock (revision 3 to 5, markers dropped); the cut changed only the `streamlit-coco` version line in each lock.

## Explicit non-goals this cut

- A generic pass-through of any command-line flag.
- The user's own skills and MCP servers: they are not settings, and the option does not change them.
