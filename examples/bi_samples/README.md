# BI sample packs

Tableau and Power BI fixtures used by [`examples/bi_to_semantic`](../bi_to_semantic/).
Chat exploratory prompts stay in [`examples/testdata/`](../testdata/) — they are not BI
sources.

```
bi_samples/
├── tableau/     MIT Tableau Server Insights workbooks + reconstructed Snowflake model
└── powerbi/     MIT Microsoft Obvience `.pbix` samples
```

| Pack | Licence | Default demo files |
|---|---|---|
| [`tableau/`](tableau/) | **MIT © Tableau** | `ts_content.twb` + `ts_users.twb` (full set of four in `tableau/workbooks/`) |
| [`powerbi/`](powerbi/) | **MIT © Microsoft** | `Customer Profitability Sample (auto).pbix` + `Corporate Spend.pbix` |

Keep the attribution README in each subfolder if these files move.
