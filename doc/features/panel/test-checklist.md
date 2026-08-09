# Feature: Panel + chat input

**Checklist:** `doc/features/panel/test-checklist.md`  
**App:** `make chat` → `examples/chat_app.py`  
**Prompts:** `examples/testdata/prompts.json` (categories `tools_auto`, `streaming`, `multi_turn`)

## Preconditions

- [ ] `uv sync --extra dev` (or `make install`)
- [ ] `cortex --version` works; Snowflake connection configured
- [ ] Fresh browser session (or **Back to start** then **Start CoCo Chat**)

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Open landing; confirm env blocks (SDK, CLI, Snowflake config) | Green/ready status; no session started yet |
| 2 | Click **Start CoCo Chat** | Soft “Starting CoCo” status; then **CoCo ready** caption |
| 3 | Confirm chat input is usable after ready | Input enabled; placeholder is ask-prompt (not stuck disabled) |
| 4 | Send test prompt `glob-project` or type a short question | User message appears; status “CoCo is working”; streaming text |
| 5 | Wait for completion | Status returns to ready; transcript keeps history |
| 6 | Open **Settings** → toggle **Transcript / Field** | Output mode switches without killing session |
| 7 | While a long prompt runs (`stop-friendly`), click **Stop CoCo** | Run cancels / stops; UI recoverable |
| 8 | Change a sidebar control (e.g. Settings popover) during idle | Rest of app does not needlessly clear transcript |
| 9 | **Settings** → **Reset session** | Transcript cleared; warm-up reconnects |
| 10 | **Settings** → **Back to start** | Returns to landing gate; no live worker |

## Panel UX (copy / highlight / windowing)

Automated coverage: `make e2e` (fixture harness). Live CoCo checks below with `make chat`.

| # | Step | Expected |
| --- | --- | --- |
| U1 | Ask for a SQL or Python snippet (fenced) | Assistant reply shows highlighted `st.code` blocks (not plain fences only) |
| U2 | Click the **copy** icon on an assistant message | Icon switches to check briefly; paste matches message text |
| U3 | Long session with `max_messages` set (or harness) | Caption “N earlier messages hidden”; **Load earlier** reveals older turns |

## Edge cases

- [ ] Start with missing CLI → failed boot messaging; input disabled only on hard error
- [ ] Send prompt during `CONNECTING` → queued / handled without crash
- [ ] Rapid double-send → no event-loop / queue errors

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent (Auto) |
| Date | 2026-07-25 |
| Build / commit | `p0-roadmap-items` (CCv2 register-once + live `make chat`) |
| Pass? | **Yes** — steps 1–5 verified live (env gate → Start → ready → send prompt → assistant reply). Steps 6–10 / edge cases not fully exercised in this pass. |
