# Power BI demo fixtures — Microsoft Obvience `IP` samples

Several departmental reports built independently **on one company's warehouse**.
They still carry the literal connection string `Sql.Database(".", "IP")` (or the
Excel path under `Obvience\IP\`). Used by
[`examples/bi_to_semantic`](../bi_to_semantic/).

This is the Power BI analogue of the Tableau `workgroup` pack in
[`examples/tableau_legacy/`](../tableau_legacy/).

## Layout

```
powerbi_legacy/
├── README.md
├── fetch.sh            optional 17 MB pair (not committed)
├── Customer Profitability Sample (auto).pbix   committed (~1.9 MB)
└── Corporate Spend.pbix                        committed (~0.7 MB)
```

## Attribution

Redistributed from:

- [microsoft/fabric-samples](https://github.com/microsoft/fabric-samples) —
  `docs-samples/data-science/datasets/Customer Profitability Sample (auto).pbix`
- [microsoft/powerbi-desktop-samples](https://github.com/microsoft/powerbi-desktop-samples) —
  `new-power-bi-service-samples/Corporate Spend.pbix`

**© Microsoft, MIT licence.** Keep this attribution if these files move.

## What is committed vs fetched

| File | In git? | Why |
|---|---|---|
| `Customer Profitability Sample (auto).pbix` | **Yes** (1.9 MB) | default pack — colliding `Fact` / `Scenario` / `Date` |
| `Corporate Spend.pbix` | **Yes** (0.7 MB) | default pack |
| `Human Resources Sample PBIX.pbix` | No (~8.7 MB) | optional — `BU` grain conflict |
| `Employee Hiring and History.pbix` | No (~8.8 MB) | optional — fork case (overlap, almost no drift) |

Refresh the committed pair:

```bash
MS=https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main
FB=https://raw.githubusercontent.com/microsoft/fabric-samples/main/docs-samples
curl -sLO "$FB/data-science/datasets/Customer%20Profitability%20Sample%20(auto).pbix"
curl -sLO "$MS/new-power-bi-service-samples/Corporate%20Spend.pbix"
```

Fetch the optional pair (gitignored):

```bash
./fetch.sh
```

## Drift the default pack carries

`Customer Profitability (auto)` ∩ `Corporate Spend` share three table names and
agree on none of them: **`Fact`**, **`Scenario`**, **`Date`**. Public Microsoft
`.pbix` samples have **no RLS roles** — screen 4 compares those table contracts
(columns + Power Query M source), not row-level security.
