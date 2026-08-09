# Release notes bank — 0.1.5

## Headline (one line)

> Upload files into the agent workspace from Streamlit — and make CoCo transcripts feel like a real product UI.

## Top 3 user-visible wins

1. **File upload into `cwd`** — `upload_to_cwd` / `cwd_uploader` / optional `chat_input_bar(..., accept_file=…)`
2. **Transcript polish** — SQL/Python highlighting, one-click Copy, `max_messages` + Load earlier
3. **Release hygiene** — Playwright UX e2e (no live CoCo in CI) + SBOM on GitHub Release

## Use cases to feature

1. Analyst drops a CSV in the sidebar; CoCo profiles it with SQL/Bash under HITL
2. Long multi-turn sessions stay usable via windowing; copy SQL out of the chat into worksheets
3. App builders ship a CoCo panel without reinventing clipboard / code fences / upload plumbing

## Learnings (candid)

- Streamlit reruns + session state force a clear start-gate and stable widget keys for upload
- Live CoCo in CI is fragile — a CoCo-free UX harness + Playwright covers the UI contract
- Empty `data-testid` markers are invisible to Playwright; prefer visible captions / text hooks
- CCv2 copy buttons are icon-only (Material `content_copy`) — use distinct `label=` for aria/tooltip when several share a view
- Compact tool cards beat raw JSON for trust; Copy SQL on tool cards complements message copy

## Quotes / soundbites

- “CoCo in Streamlit should feel like a product, not a log dump.”
- “Upload is the missing bridge between the browser and the agent workspace.”
- “Approve once · Always allow · Deny — safety by default.”

## Explicit non-goals this cut

- Live CoCo agent turns in CI
- Visual regression / Percy
- Full CCv2 legacy `chat()` e2e
- SiS-specific packaging (document later)
