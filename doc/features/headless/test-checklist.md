# Feature: Headless query & multi-turn

**Checklist:** `doc/features/headless/test-checklist.md`  
**App:** `make headless` → `examples/headless_pipeline.py`  
**API:** `streamlit_coco.query()`, `CocoSession.run()`, `CocoSession.stream()`

## Preconditions

- [x] `cortex-code-agent-sdk` installed (`[sdk]` / `[dev]` extra)
- [x] CLI on `PATH`; Snowflake connection works
- [x] No Streamlit UI required for this checklist

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Run `make headless` (or `uv run python examples/headless_pipeline.py`) | Process starts; events print / complete without Streamlit |
| 2 | Observe `query()` section | Assistant and/or tool-related events, then a `result` |
| 3 | Observe `session.run()` / `session.stream()` | Multi-turn completes; script exits cleanly |
| 4 | Optional: pending AskUser / ExitPlan auto-resolved by the example loop | No hung approval |

## Edge cases

- [x] Missing SDK → clear ImportError / install hint (unit-covered via `SDKNotInstalledError`)
- [ ] Missing CLI → `CLINotFoundError` / connection error surfaced *(not re-broken in this pass)*
- [ ] Invalid connection name → error event or exception, not silent hang *(not re-broken in this pass)*
- [x] `run(..., timeout=…)` raises `TimeoutError` when the turn never finishes (unit-covered)

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent |
| Date | 2026-07-27 |
| Build / commit | `feature/phase3-hitl-headless` (uncommitted) |
| Pass? | **Yes** — `make headless` completed: `query()` success (~18s); `session.run()` `completed` (211 events); `session.stream()` success; script asserted `streamlit` not loaded; clean exit. |
