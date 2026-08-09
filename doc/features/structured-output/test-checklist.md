# Feature: Structured output

**Checklist:** `doc/features/structured-output/test-checklist.md`  
**Apps:** `make structured` (`examples/structured_output.py`), `make chat`  
**Prompts:** `examples/testdata/prompts.json` (`structured-json`)

## Preconditions

- [x] Live CoCo CLI + Snowflake connection
- [x] For callback path: run `examples/structured_output.py`
- [ ] For inline path: `make chat` with transcript mode — not run this pass

## Golden path

| # | Step | Expected | Pass |
| --- | --- | --- | --- |
| 1 | In chat app, send `structured-json` | Agent Reads `pyproject.toml`; reply is JSON-shaped (inline panel if no callback) | — deferred to chat follow-up |
| 2 | Run `make structured` | Custom `on_structured_output` renders via app widgets (not only raw JSON dump) | ✓ after example fix |
| 3 | Complete a turn with `output_schema` set on `CocoOptions` | `result.structured_output` populated; callback/container fires once per result | ✓ JSON matches schema in live turn |
| 4 | Confirm mutual exclusivity | When callback/container is set, default inline JSON panel is skipped | ✓ (callback set; transcript shows assistant JSON, not inline expander) |
| 5 | Second structured turn in same session | New result renders; no duplicate sticky render of the previous payload | — not run |

## Edge cases

- [ ] Non-dict structured payload → wrapped or shown safely
- [ ] Failed turn / error result → no false-positive structured render
- [ ] Fragment remount does not re-fire callback for the same result id

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent (Auto) |
| Date | 2026-07-27 |
| Build / commit | `p0-roadmap-items` @ `18aaaa3` (+ `structured_output.py` session/fragment fixes) |
| Pass? | **Yes (core)** — live `make structured` (8502): `output_schema` turn returns `{name, version, requires_python, dependencies}` for `pyproject.toml`; Read tool card + assistant JSON; custom pipeline panel via `on_structured_output` (fixed: `get_or_create_session`, `pipeline` slot, `use_fragment=False`). Chat inline `structured-json` + second-turn dedupe not run this pass. |
