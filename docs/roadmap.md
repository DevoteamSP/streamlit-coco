# Roadmap — streamlit-coco

Living plan. Product detail: [`docs/PRD.md`](PRD.md). Shipped history: [`CHANGELOG.md`](../CHANGELOG.md).

**Status:** Alpha `0.1.0` — Phase 3 (HITL / headless / text renderer) shipped. Remaining release gate: tag + PyPI.  
**Last updated:** 2026-07-27

Preferred UX: native `panel()`; CCv2 applies to legacy `chat()`.

---

## Next — ship `0.1.0`

| Priority | Item | Notes |
| --- | --- | --- |
| P0 | Tag + PyPI publish `0.1.0` `streamlit-coco[sdk]` | Sync → [`streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco); tag `v*`; see [`docs/deployment/publish.md`](deployment/publish.md) |
| P2 | Deployment docs (Docker, SPCS) | Container + Snowflake topologies |

Manual checklists: [`docs/features/README.md`](features/README.md) — re-run before release.

---

## Later — polish & platform

- [ ] Theming / a11y pass (native `panel()` transcript)
- [ ] Richer markdown / SQL highlighting (FR-S6)
- [ ] Optional `max_messages` truncation + “load earlier”
- [ ] SPCS-oriented guide and sample image
- [ ] Community sample apps (≥ 3)
- [ ] Automated UI / e2e tests (promote checklists beyond manual N1)
- [ ] Packaged CCv2 via official component-template (only if still needed)

---

## Out of scope (for now)

Remote agent proxy; browser-side CoCo / managed SaaS; full IDE workspace; Slack/MCP products (MCP passthrough via `mcp_servers` works); file upload into `cwd`.

---

## Sequencing

```text
✅ Phase 3 — HITL, headless stream/run, text renderer
      ↓
Sync → streamlit-coco → tag v0.1.0 → PyPI   ← remaining
      ↓
UX polish, optional packaged CCv2
```

---

## Success checks (90 days post-launch)

| Metric | Target |
| --- | --- |
| PyPI downloads | 500+ |
| GitHub stars | 50+ |
| Time-to-first-working-app | < 30 min via quickstart |
| Open P0 “streaming broken on rerun” | 0 for 30 days |
| Community examples | ≥ 3 |
