# Case 3 — Advanced: a session that never connects

**Level:** Advanced — something breaks, you diagnose alone. **Time:** 30–45
min.

## Context

This case is based on a symptom documented in the library's own
troubleshooting references (not a hypothetical): a session that boots the
UI correctly but never leaves the connecting state. You will not be told the
root cause up front — the same symptom can come from more than one layer of
the stack, and part of the exercise is working out which one.

## Goal

Diagnose, without being told the cause, why a CoCo session does not become
ready — and fix it — using the same tools `check_environment()` itself uses
internally, not guesswork.

## Data

**Your own local environment.** No special Snowflake objects are needed;
this is purely an environment/connectivity diagnosis. Use whichever example
app you already have working from earlier exercises (`examples/chat_app.py`
via `make chat`, or your own app from
[Case 1](01-simple.html) / [Case 2](02-intermediate.html)).

## Symptoms

This is everything you are given. Do not assume the cause from this list
alone — confirm it.

- You run `make chat` (or your own app built on the quickstart pattern).
- The start gate renders normally and shows its SDK/CLI/Snowflake probe.
- You click **Start CoCo Chat**.
- The panel's status line stays on a connecting state; the transcript area
  shows a persistent "Starting CoCo…" and never progresses.
- The chat input stays disabled.
- No error banner appears in the UI itself.

## Steps

1. **Reproduce it.** If your own environment does not currently show this
   symptom, you can still work through the diagnostic method below — the
   goal is the method, not necessarily forcing a live repro.

2. **Turn on debug output.** Set `STREAMLIT_COCO_DEBUG=1` (or `COCO_DEBUG=1`)
   and re-run. Read the terminal, not just the browser — look for anything
   printed after "Starting CoCo…".

3. **Bypass the UI.** In a Python shell, call `check_environment()` directly
   with the same `connection=` value your app uses, and print every field:
   `sdk_installed`, `sdk_version`, `cli_path`, `cli_version`,
   `snowflake_config_file`, `connection_hint`. Do not stop at the first
   field that looks wrong — read all of them; more than one can be off at
   once.

4. **Map what you found to a typed error.** `streamlit_coco.errors` defines
   one exception class per failure layer (missing SDK, CLI not found, CLI
   present but not responding, no Snowflake config, bad connection/auth,
   session that never reaches ready). For whichever field(s) looked wrong in
   step 3, work out which of those classes `require_environment()` would
   have raised instead of `check_environment()`'s silent probe — that is
   your diagnosis.

5. **Fix the specific layer you found**, then repeat the repro path (start
   gate → **Start CoCo Chat**) and confirm the session now reaches a ready
   state and answers a prompt.

## Expected result

- You can name the specific layer that was broken (SDK, CLI on `PATH`, CLI
  responding to `--version`, Snowflake config present, or connection/auth)
  using `check_environment()`'s own fields, not by trial and error on the
  UI.
- After the fix, the same repro path leaves the connecting state, the chat
  input enables, and a prompt streams back a normal response with a tool
  card.

## Where to look if stuck

Start here, then branch based on what `check_environment()` told you:

- [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  — the general symptom and how to read the debug output.
- [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error)
  — if `check_environment()` reached the CLI but the connection/auth is bad.
- [`help.html#cli-not-found`](../technical-guide/help.html#cli-not-found) /
  [`help.html#cli-probe-failed`](../technical-guide/help.html#cli-probe-failed)
  — if `cli_path` or `cli_version` looked wrong.
- [`help.html#snowflake-config-not-found`](../technical-guide/help.html#snowflake-config-not-found)
  — if `snowflake_config_file` was empty.
- [`help.html#session-not-ready`](../technical-guide/help.html#session-not-ready)
  — if every `check_environment()` field looked fine but the session still
  never reaches ready.
