# KPI presentation — self-check

Verify `streamlit_app.py` against every item before presenting it to a human.
If `.preview.log` shows a traceback, make **one** corrective Edit, then stop.

- [ ] `st.set_page_config` runs before any other `st.*` call
- [ ] No `use_container_width` anywhere (`width="stretch"` if width is set)
- [ ] App renders with **zero rows** in the fixture (or all filters cleared) without a traceback
- [ ] Missing `data.csv` shows an error, not a stack trace
- [ ] A missing expected column shows an error naming it, not a `KeyError`
- [ ] Every filter is a visible widget (`st.multiselect` / `st.selectbox` / `st.pills`) — no hidden `WHERE`
- [ ] Load is wrapped in `@st.cache_data` with a TTL
- [ ] Filter block (or the dashboard it drives) uses `@st.fragment`
- [ ] KPI row uses `st.metric` with a delta; no pie chart
- [ ] Time trend uses a line chart; ≤7-category comparison uses a bar if there is one
- [ ] Currency / percent / counts are formatted (not raw floats like `128000.0`)
- [ ] One detail table, not a stack of dataframes
