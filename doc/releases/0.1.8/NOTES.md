# Release notes bank — 0.1.8

Freeform. Feed LinkedIn / Medium / GitHub Release.

## Headline (one line)

> You never start from a blank `app.py` — pick a type, confirm what we found, CoCo Writes the app.

## Top 3 user-visible wins

1. **App Builder** — Welcome · Library · Brief · Studio · Admin; six live types; four need no Snowflake
2. **Profile + `infer:`** — pandas findings on the Brief; audience / must-not stay blank
3. **Rail** — `example_questions=` starter buttons; Display config popover (`transcript_display_config()`)

## Use cases to feature

See [`doc/features/app-builder/UX.md`](../../features/app-builder/UX.md).

1. **UC1** KPI presentation — fixture or semantic view → findings → Preview
2. **UC6** Room demo, no warehouse — Local topic pills, Try a local demo
3. **UC8** Brief is source of truth — Resume / Save & regenerate

## Learnings (candid)

- If a parser can answer it, a model is not asked (`engine/profile.py`).
- Two questions are always human: who opens this, what must never happen.
- Self-check once against `CHECKLIST.md` / `.preview.log`, then stop.
- Save & regenerate must write `BRIEF.md` from the expander *before* the Brief page reruns.

## Quotes / soundbites

- “You never start from a blank `app.py`.”
- “The filled brief is the product. The generated app is a rendering of it.”
- “If a parser can answer it, a model is not asked.”
- “Local = no Snowflake. Those types exist so a room with no account can still see the product.”

## Explicit non-goals this cut

- Napkin / photo-to-app ([#9](https://github.com/DevoteamSP/streamlit-coco/issues/9))
- Document comparison / `urls` types (UC9 host-fetch)
- API mode / no-CLI (`0.2.0`)
- SiS / Native App spawn of a local `streamlit run`
- Switching PyPI Trusted Publisher back to DevoteamSP
