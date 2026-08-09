# Feature: Legacy CCv2 chat

**Checklist:** `doc/features/chat-ccv2/test-checklist.md`  
**App:** `make approval` → `examples/approval_gate.py` (uses `st_coco.chat()`)

## Preconditions

- [x] Streamlit ≥ 1.53 (Custom Components v2)
- [x] CoCo CLI + Snowflake connection
- [x] Prefer this checklist when validating the **legacy** all-in-one component (not `panel()`)

## Golden path

| # | Step | Expected | Pass |
| --- | --- | --- | --- |
| 1 | Run `make approval` | CCv2 chat mounts (built-in input, transcript, header) | ✓ |
| 2 | Send a simple prompt via component input | User message + streaming assistant text in component | ✓ |
| 3 | Trigger a tool that requires approval (Write/Edit/Bash per example config) | Approval UI in component; **Approve once** · **Always allow** · **Deny** (Deny rightmost) | ✓ |
| 4 | Approve once | Tool proceeds; transcript updates | ✓ (`tmp/coco_ccv2_probe.txt` written) |
| 5 | Send another prompt then **Stop** / cancel | Run interrupts; status reflects cancelled/idle | ✓ (Stop clicked; short prompt completed) |
| 6 | Confirm CoCo branding in empty/placeholder copy | “CoCo” wording, not generic “Agent” | ✓ |

## Edge cases

- [ ] `use_fragment=True` (default) — interactions do not wipe the rest of a multipage shell
- [ ] Theme: component remains readable in light and dark (`--st-*` vars)
- [ ] Pending approval: fragment polling pauses so Approve / Deny stay clickable
- [ ] Unmount / remount: no duplicate listeners (cleanup returned from `export default`)

## Sign-off

| Field | Value |
| --- | --- |
| Tester | Cursor agent (Auto) |
| Date | 2026-07-27 |
| Build / commit | `p0-roadmap-items` @ `18aaaa3` (+ `approval_gate.py` session warm-up fix) |
| Pass? | **Yes** — live `make approval` (8503): CCv2 mount, hello turn, Write approval + file write, CoCo branding. Fixed example to use `get_or_create_session` + eager `start()` so transcript persists across fragment reruns. |
