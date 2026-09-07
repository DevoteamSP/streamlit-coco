# Release notes bank — 0.1.8.1

Freeform. Feed LinkedIn / Medium / GitHub Release.

## Headline (one line)

> Starter questions can fill the chat box — they no longer have to fire CoCo on click.

## Top 3 user-visible wins

1. **`deferred=True` on `copilot_rail()`** — click copies the question into `chat_input_bar`
2. **Per-item override** — `{"title", "question", "deferred": True}` (or a 3-tuple)
3. **BI → Semantic** (`make bi-semantic`) opts in so you can try it after Connect

## Use cases to feature

1. Room demo: show the prompt, let the owner edit, then send
2. Long example questions that need a table name or filter before they are safe to run

## Learnings (candid)

- Streamlit `st.chat_input` has no `value=` parameter. Prefill is a session-state write on the widget key; it is a field insert, not a submit.
- Example buttons live in the rail fragment; chat input lives outside it. Stash the draft on a non-widget key, full-`st.rerun()`, then copy onto the input key before `chat_input_bar` instantiates.
- Default stays send-on-click so App Builder demos still one-click CoCo.

## Quotes / soundbites

- “Click fills the box. You still hit send.”
- “Starters are not a hidden `session.send`.”

## Explicit non-goals this cut

- Changing App Builder starters (still send on click)
- API mode / no-CLI (`0.2.0`)
- Screenshots are optional for this patch; hero can wait if the LinkedIn post is a code card
