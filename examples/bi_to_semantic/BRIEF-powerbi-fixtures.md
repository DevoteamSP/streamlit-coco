# Brief — replace the synthetic Power BI fixtures with real MIT Microsoft samples

**For:** `examples/bi_to_semantic` (was `tableau_to_semantic`)
**Goal:** the Power BI side of the app should stand on **real, redistributable, found-in-the-wild
reports** — the way the Tableau side stands on the MIT `tableau/community-tableau-server-insights`
workbooks — instead of the hand-authored `ops_content` / `ops_users` TMDL pack.

Every fact, formula, column list and file size below was verified by parsing the actual files.

---

## 1. What already exists (do not rebuild)

The multi-source scaffolding is in place and is the right shape. Keep it:

| file | role |
|---|---|
| `engine/bi_sources.py` | discovers `.twb/.twbx` vs `.pbix/.pbit/.tmdl`/PBIP folders; `partition_sources()` |
| `engine/powerbi_parse.py` | `parse_tmdl`, `parse_report_json`, `_from_model_json`, `estate_part`, `kpi_rows`, `dashboard_rows`, `access_rule` |
| `engine/access_parse.py` | `divergences_from_rules`, `merge_access_payloads` |
| `engine/paths.py` | `POWERBI_FIXTURES_DIR`, `POWERBI_PACK`, `warehouse_ids()` |

Two things change: **the fixtures**, and **one gap in `_extract_pbix`**.

---

## 2. The gap: real `.pbix` files have no `DataModelSchema`

`_extract_pbix()` currently reads the model from `DataModelSchema`. That entry exists **only in
`.pbit` templates**. A real `.pbix` instead carries `DataModel` — an XPress9-compressed VertiPaq
stream. So today, pointing the app at a real `.pbix` yields pages and visuals but **zero tables,
zero measures, zero roles**, and `access_rule()` returns `None`.

### Fix: `pbixray`

MIT, pure Python, cross-platform, no Windows and no Analysis Services. Verified working on all
10 Microsoft samples tested (`pbixray==0.15.4`, Python 3.12).

```bash
uv add pbixray
```

Exact API surface (verified — these are the real DataFrame column names):

| accessor | type | columns |
|---|---|---|
| `.schema` | DataFrame | `TableName`, `ColumnName`, `PandasDataType` |
| `.dax_measures` | DataFrame | `TableName`, `Name`, `Expression`, `DisplayFolder`, `Description` |
| `.dax_columns` | DataFrame | `TableName`, `ColumnName`, `Expression` |
| `.relationships` | DataFrame | `FromTableName`, `FromColumnName`, `ToTableName`, `ToColumnName`, `IsActive`, `Cardinality`, `CrossFilteringBehavior`, … |
| `.power_query` | DataFrame | `TableName`, `Expression` (the M query — this is how you recover the data source) |
| `.rls` | DataFrame | empty on every public Microsoft sample — see §5 |
| `.tables` | list | table names |

**Where it plugs in:** inside `_extract_pbix()`, when `DataModelSchema` is absent, build the same
`{"tables": {...}, "relationships": [...], "roles": [...]}` dict that `_from_model_json()` returns,
from `PBIXRay(path)`. Nothing downstream changes — `estate_part`, `kpi_rows` and `access_rule`
already consume that shape.

Keep the existing `Report/Layout` path untouched: it is UTF-16LE JSON, `sections[]` →
`visualContainers[]`, and `_read_json_bytes()` already handles the BOM correctly.

Filter out Power BI's auto-generated date tables (`LocalDateTable_*`, `DateTableTemplate_*`) when
building the estate map, or every model gains 3–5 phantom tables.

---

## 3. The fixture set — Microsoft's "Obvience `IP`" warehouse

These samples are the Power BI analogue of the Tableau `workgroup` repository: several
departmental reports built independently **on one company's warehouse**. They still carry the
literal connection string `Sql.Database(".", "IP")`.

### Default pack (commit these two — 2.7 MB, comparable to the Tableau pack's 2.4 MB)

| file | bytes | source in repo |
|---|--:|---|
| `Customer Profitability Sample (auto).pbix` | 1 971 104 | `microsoft/fabric-samples` → `docs-samples/data-science/datasets/` |
| `Corporate Spend.pbix` | 754 873 | `microsoft/powerbi-desktop-samples` → `new-power-bi-service-samples/` |

### Optional third + fourth (fetch on demand — 17 MB, do not commit)

| file | bytes | adds |
|---|--:|---|
| `Human Resources Sample PBIX.pbix` | 8 700 848 | the `BU` grain conflict (§4) |
| `Employee Hiring and History.pbix` | 8 773 926 | the fork case: 9 shared tables, 30 byte-identical measures, one extra |

```bash
MS=https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main
FB=https://raw.githubusercontent.com/microsoft/fabric-samples/main/docs-samples

curl -sLO "$FB/data-science/datasets/Customer%20Profitability%20Sample%20(auto).pbix"
curl -sLO "$MS/new-power-bi-service-samples/Corporate%20Spend.pbix"
# optional
curl -sLO "$MS/Sample%20Reports/Human%20Resources%20Sample%20PBIX.pbix"
curl -sLO "$MS/new-power-bi-service-samples/Employee%20Hiring%20and%20History.pbix"
```

Both repos are **MIT © Microsoft**. Mirror `examples/tableau_legacy/README.md`: keep the
attribution and the refresh block with the files.

---

## 4. The drift the app must surface (all verified)

`Customer Profitability (auto)` ∩ `Corporate Spend` share three table names — and agree on none
of them.

**`Fact` — same name, entirely different fact table.** This is the estate-map punchline.
```
CustProfAuto    [Customer Key, Product Key, BU Key, Scenario Key, Revenue,
                 Material Costs, Labor Costs Variable, Taxes]        ← Sql.Database(".","IP")
CorporateSpend  [Date, Value, Department, Cost Element ID, Country/Region ID,
                 Business Area ID, IT Sub Area ID, Scenario ID]      ← Excel  Obvience\IP\IT\
```

**`Scenario` — two definitions, two shapes.**
```
CustProfAuto    [Scenario Key, Scenario]                        ← hardcoded inline table
CorporateSpend  [Scenario, Scenario ID, ScenarioDescription]    ← Excel sheet
```

**`Date` — three calendars for one company** (the third appears once HR is loaded).
```
CustProfAuto    [YearPeriod, Year, Period, Date, Month, QtrID, Qtr]   ← derived concat([Year],[period])
CorporateSpend  [Date, Year, Period, Month]                            ← stale Excel copy
HumanResources  [Date, Month, MonthNumber, Period, PeriodNumber,
                 Qtr, QtrNumber, Year]                                 ← SELECT [HR].[Date].*
```

**`BU` — same dimension, same server, incompatible grain and no shared key** (needs HR loaded).
This is the strongest arbitration case in the set.
```
HumanResources  [BU, RegionSeq, VP, Region]
                ← select distinct market BU, REGIONTITLE Region, MARKETDIRECTOR VP
CustProfAuto    [BU Key, BU, Division, Executive_id]
                ← SELECT [Profit Center Key] [BU Key], BU, Division, Executive_id
```
One is market-oriented, the other profit-centre-oriented. Arbitrating that is the point of
screens 4–5.

Recover the "same warehouse, different plumbing" evidence from `.power_query` — the M expressions
still name `Sql.Database(".", "IP")`, the Excel paths, and the inline tables. Worth showing on the
estate-map screen: it is what proves these reports belong to one estate.

---

## 5. Decision required: there is no RLS in any public Microsoft `.pbix`

Verified across all 10 samples: `.rls` is empty in every one. The Tableau punchline
(project-leader filter present in `ts_content`, dropped in `ts_users`) has **no found-in-the-wild
Power BI equivalent** in MIT-licensed material.

Three options, in order of preference:

1. **Recast screen 4 for Power BI.** Drive the divergence off the `BU` grain conflict and the
   colliding `Fact` names instead of RLS roles. This is what Power BI estates actually break on,
   and it uses only real material. `access_parse.divergences_from_rules()` already compares
   `grants_to` keys across sources — feed it dimension-key divergences and the screen works
   unchanged.
2. **Add `microsoft/Analysis-Services` `SamplePBIP` as a fifth source** —
   `pbidevmode/fabricps-pbip/SamplePBIP/`, MIT, plain-text TMDL, already parseable by the existing
   `parse_tmdl()`. It has two genuine RLS roles:
   ```
   role 'Stores Cluster 1'
       tablePermission Store = 'Store'[Store Code] IN {"1","2","4"}
   role 'Stores Cluster 2'
       tablePermission Store = 'Store'[Store Code] IN {"10","11","15","8"}
   ```
   Honest, but it is a different estate (public CSVs at `pbi-tools/sales-sample`), so the RLS
   drift spans unrelated warehouses and reads as a weaker story.
3. **Keep one small authored TMDL fixture** purely for the RLS screen, clearly labelled synthetic
   in the README — i.e. what `ops_content`/`ops_users` do now, but reduced to the RLS case only.

Do not silently present option 2 or 3 as if the roles came from the Obvience estate.

---

## 6. Work items

- [ ] `uv add pbixray`; add to `pyproject.toml` dependencies.
- [ ] `engine/powerbi_parse.py`: in `_extract_pbix()`, fall back to `PBIXRay` when
      `DataModelSchema` is absent; map to the existing model dict. Filter `LocalDateTable_*` /
      `DateTableTemplate_*`.
- [ ] Surface `.power_query` M source per table so the estate map can show the shared
      `Sql.Database(".", "IP")` origin.
- [ ] `examples/powerbi_legacy/`: replace `ops_content/` + `ops_users/` with the real pack —
      commit the two default `.pbix`, add `fetch.sh` for the optional two, `.gitignore` the large ones.
- [ ] `examples/powerbi_legacy/README.md`: MIT © Microsoft attribution + refresh block, mirroring
      `examples/tableau_legacy/README.md`. State plainly which files are committed vs fetched.
- [ ] `engine/paths.py`: `POWERBI_PACK = ("Customer Profitability Sample (auto).pbix", "Corporate Spend.pbix")`.
- [ ] Load screen: "Use MIT Power BI pack" alongside the existing Tableau pack button; `peek_text()`
      should show a DAX measure or an M query for `.pbix` (it cannot show raw text).
- [ ] Resolve §5 and implement the chosen option.

## 7. Acceptance

Running the app against the two committed `.pbix` files, with no Snowflake account and no CoCo:

1. **Estate map** renders both models with real tables and relationships, no phantom date tables,
   and shows `Fact`, `Scenario`, `Date` as contested names.
2. **KPI inventory** lists real DAX — `Fact.Total Revenue`, `Fact.Actual`, `Fact.Var Plan %` and
   the rest of the 15 + 44 measures — with expressions.
3. **Screen 4** shows at least one genuine divergence sourced from the files, not a placeholder.
4. `out/estate_map.json` and `out/kpi_inventory.json` validate against `contracts/*.schema.json`.
5. The Tableau path is untouched and still passes.

## 8. Rejected alternatives, so they are not re-litigated

- **Store Sales + Sales & Returns + SamplePBIP `Sales`** — looks like one retail domain and has
  the richest KPI drift (`TotalSales` vs `Net Sales` vs `Sales Amount`), but the three point at
  three unrelated sources: SQL Server `RetailBIDW`, a developer's local Excel files, and public
  GitHub CSVs. No shared estate, so the estate map is fiction.
- **`.pbit` templates** — `DataModelSchema` parses beautifully with no extra dependency, but
  Microsoft ships exactly one (`COVID-19 US Tracking Sample.pbit`), and it has 6 tables,
  10 measures, 0 roles. Not enough for a two-source comparison.
- **`RuiRomano/pbip-demo`** — three TMDL models with RLS roles, ideal shape, **no licence file**.
  Not redistributable.
- **Human Resources + Employee Hiring alone** — 15 shared tables and 30 byte-identical measures.
  Real overlap, but zero drift, so screens 4–5 would have nothing to arbitrate. Useful only as the
  fork case alongside the others.
