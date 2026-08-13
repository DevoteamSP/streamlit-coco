# Release notes bank — 0.1.6

## Headline (one line)

> CoCo as a product copilot — a reusable right rail, a Tableau → Semantic example, and a consultant training pack.

## Top 3 user-visible wins

1. **`copilot_rail()`** — connection, queued jobs, compact transcript pills, Cancel-on-title-row; `preview_chars=` on `panel()`
2. **Tableau → Semantic** — `make tableau-semantic`: estate / KPI / access drift → semantic view + RAP + Streamlit consumer, with Preview sharing the Copilot slot
3. **Training pack** — `doc/training/` + workshop W01 so a second consultant can demo and build unassisted

## Use cases to feature

1. Multipage wizard queues CoCo jobs from the left; the rail streams, pauses for HITL, and hides Cancel when the turn ends
2. Tableau Server workbooks disagree on a User Filter; the app surfaces the drift and Writes one semantic view + one row access policy
3. Enablement: setup → lab (including optional Tableau) → 12-minute demo → quiz

## Learnings (candid)

- Streamlit widget keys vs `persist_state`: do not write a `text_area` / pills key after the widget exists; Save Brief writes the file and reruns
- Job chrome belongs on the rail title row; stale-job handling must live inside the polling fragment or Cancel never hides
- Lazy `__getattr__` must not cache UI callables — a hot-reload of `copilot_rail` otherwise keeps the old signature
- `streamlit_extras.resizable_columns` is enough for Copilot vs Preview; a custom CCv2 split was overkill
- A BI estate with *disagreeing* RLS rules is a better Copilot demo than a chat window

## Quotes / soundbites

- “CoCo in Streamlit should sit in the product, not replace the page.”
- “The rail is generic. The Tableau app is the proof.”
- “Approve once · Always allow · Deny — safety by default, even when the agent Writes a semantic view.”

## Explicit non-goals this cut

- Pixel-perfect Tableau clone
- Live CoCo agent turns in CI
- SiS-specific packaging
- Switching PyPI Trusted Publisher back to DevoteamSP
