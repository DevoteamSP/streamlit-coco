# Release notes bank — 0.1.7

## Headline (one line)

> Preview the Streamlit app CoCo just wrote — and send the red exception back as a job.

## Top 3 user-visible wins

1. **`app_viewer()`** — child `streamlit run`, iframe, **Fix with CoCo** via `on_fix` + `default_fix_prompt`; compose next to `copilot_rail()`
2. **BI → Semantic** — Load Tableau **or** Power BI (`pbixray` + MIT Obvience pack); Welcome + source cards; Python / CoCo consumers on `:8511` / `:8512`
3. **Fix from the log** — the iframe is another origin; Fix scrapes `.preview.log`, not the DOM

## Use cases to feature

1. Host app queues a generate job; Preview **Run**s the written `streamlit_app.py`; a traceback becomes a Copilot job
2. A Power BI `.pbix` becomes a KPI row + charts + one detail table (not one dataframe per visual), then a Snowflake semantic view
3. Copilot and Preview open together — the rail writes, the viewer shows the child app

## Learnings (candid)

- Do not name a lazy-export module the same as the function (`app_viewer.py` shadowed `st_coco.app_viewer` after `import_module`)
- Streamlit hot-reload of the *caller* does not reload the library; `import_module` returns the cached module
- The parent cannot read the red exception from a `127.0.0.1:851x` iframe — Fix is log scrape + tail
- Power BI visuals named `"visual"` need Layout types + composition, or the consumer is a wall of dataframes
- One preview per `app_dir`; never point the viewer at the host app

## Quotes / soundbites

- “The rail writes the app. The viewer runs it. Fix sends the traceback back.”
- “`app_viewer` is a column, not a studio — same extraction path as `copilot_rail`.”
- “Tableau or Power BI in; one semantic view out.”

## Explicit non-goals this cut

- App Builder for business users (moved to **`0.1.8`**)
- SiS / Native App spawn of a local `streamlit run`
- Pixel-perfect Power BI / Tableau clone
- Live CoCo agent turns in CI
- Switching PyPI Trusted Publisher back to DevoteamSP
