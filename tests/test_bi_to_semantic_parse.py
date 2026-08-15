"""Deterministic Tableau + Power BI parsers for the BI → Semantic example."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PBI = REPO / "examples" / "powerbi_legacy"
CUST = PBI / "Customer Profitability Sample (auto).pbix"
SPEND = PBI / "Corporate Spend.pbix"
TWB_CONTENT = REPO / "examples" / "tableau_legacy" / "workbooks" / "ts_content.twb"
TWB_USERS = REPO / "examples" / "tableau_legacy" / "workbooks" / "ts_users.twb"
ENGINE = REPO / "examples" / "bi_to_semantic"


@pytest.fixture(autouse=True)
def _engine_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.syspath_prepend(str(ENGINE))
    for name in list(sys.modules):
        if name == "engine" or name.startswith("engine."):
            sys.modules.pop(name, None)


def test_powerbi_estate_and_kpi_and_access() -> None:
    from engine.access_parse import build_powerbi_access
    from engine.dashboard_parse import list_dashboards
    from engine.estate_parse import build_estate_map
    from engine.extract import load_schema, validate_payload
    from engine.kpi_parse import build_kpi_inventory

    if not CUST.is_file() or not SPEND.is_file():
        pytest.skip("MIT Power BI fixtures missing")
    paths = [CUST, SPEND]
    estate = build_estate_map(paths)
    names = {t["name"] for t in estate["tables"]}
    assert {"Fact", "Scenario", "Date"} <= names
    assert not any(n.startswith(("LocalDateTable_", "DateTableTemplate_")) for n in names)
    assert estate["joins"]
    usage = {u["workbook"] for u in estate["workbook_usage"]}
    assert usage == {CUST.name, SPEND.name}
    origins = {(r["table"], r["workbook"]) for r in estate.get("table_sources") or []}
    assert ("Fact", CUST.name) in origins
    assert ("Fact", SPEND.name) in origins
    errors = validate_payload(estate, load_schema("estate_map.schema.json"))
    assert errors == []

    kpis = build_kpi_inventory(paths)
    by_name = {m["name"]: m for m in kpis["metrics"]}
    assert "Total Revenue" in by_name
    assert by_name["Total Revenue"]["definitions"]
    assert "Actual" in by_name
    assert any(m.get("formula") for m in by_name["Actual"]["definitions"])
    errors = validate_payload(kpis, load_schema("kpi_inventory.schema.json"))
    assert errors == []

    access = build_powerbi_access(paths)
    errors = validate_payload(access, load_schema("access_rules.schema.json"))
    assert errors == []
    branches = {str(d.get("branch") or "").lower() for d in access["divergences"]}
    assert any(name in branches for name in ("fact", "scenario", "date"))
    assert access["divergences"]

    dashes = list_dashboards(paths)
    assert dashes
    assert {d["workbook"] for d in dashes} == {CUST.name, SPEND.name}
    pbi_pages = [d for d in dashes if d["workbook"] == CUST.name]
    assert pbi_pages
    page_names = {d["name"] for d in dashes}
    assert "Tooltip" not in page_names
    assert "Info" not in page_names
    for dash in pbi_pages:
        sheets = dash["worksheets"]
        assert 1 <= len(sheets) <= 9
        assert sum(1 for ws in sheets if isinstance(ws, dict) and ws.get("kind") == "table") <= 1
        names = [ws.get("name") if isinstance(ws, dict) else ws for ws in sheets]
        assert names.count("visual") <= 1
        for ws in sheets:
            assert isinstance(ws, dict)
            assert ws.get("name")
            assert ws.get("kind") in {"kpi", "bar", "line", "scatter", "table"}
            assert ws.get("key")
    scorecard = next(d for d in pbi_pages if d["name"] == "Team Scorecard")
    assert scorecard.get("source") == "powerbi"
    slicer_names = {f.get("name") for f in (scorecard.get("filters") or [])}
    assert "Name" in slicer_names


def test_tableau_estate_still_parses() -> None:
    from engine.estate_parse import build_estate_map
    from engine.extract import load_schema, validate_payload
    from engine.kpi_parse import build_kpi_inventory

    if not TWB_CONTENT.is_file() or not TWB_USERS.is_file():
        pytest.skip("MIT Tableau fixtures missing")
    paths = [TWB_CONTENT, TWB_USERS]
    estate = build_estate_map(paths)
    assert estate["tables"]
    assert estate["workbook_usage"]
    assert validate_payload(estate, load_schema("estate_map.schema.json")) == []
    kpis = build_kpi_inventory(paths)
    assert kpis["metrics"]
    assert validate_payload(kpis, load_schema("kpi_inventory.schema.json")) == []


def test_powerbi_visuals_compose_not_one_dataframe_each() -> None:
    import json

    from engine.powerbi_parse import visuals_from_report
    from engine.streamlit_app_gen import build_disconnected_data, build_spec

    layout = {
        "sections": [
            {
                "displayName": "Scorecard",
                "visualContainers": [
                    {"config": json.dumps({"singleVisual": {"visualType": "textbox"}})},
                    {
                        "config": json.dumps(
                            {
                                "singleVisual": {
                                    "visualType": "card",
                                    "projections": {
                                        "Values": [{"queryRef": "Fact.Revenue"}]
                                    },
                                }
                            }
                        )
                    },
                    {
                        "config": json.dumps(
                            {
                                "singleVisual": {
                                    "visualType": "lineChart",
                                    "projections": {
                                        "Values": [{"queryRef": "Fact.Revenue"}]
                                    },
                                }
                            }
                        )
                    },
                    {
                        "config": json.dumps(
                            {
                                "singleVisual": {
                                    "visualType": "clusteredBarChart",
                                    "projections": {
                                        "Category": [{"queryRef": "State.Region"}]
                                    },
                                }
                            }
                        )
                    },
                    {
                        "config": json.dumps(
                            {
                                "singleVisual": {
                                    "visualType": "table",
                                    "projections": {
                                        "Values": [{"queryRef": "Fact.Detail"}]
                                    },
                                }
                            }
                        )
                    },
                    {"config": json.dumps({"singleVisual": {"visualType": "slicer"}})},
                ],
            }
        ]
    }
    layout["sections"].extend(
        [
            {
                "displayName": "Info",
                "visualContainers": [
                    {"config": json.dumps({"singleVisual": {"visualType": "textbox"}})},
                ],
            },
            {
                "displayName": "Tooltip",
                "visualContainers": [
                    {
                        "config": json.dumps(
                            {"singleVisual": {"visualType": "card"}}
                        )
                    },
                ],
            },
        ]
    )
    pages = visuals_from_report(layout)
    assert pages.get("Info") == []
    assert "Tooltip" not in pages
    tiles = pages["Scorecard"]
    kinds = [t["kind"] for t in tiles]
    assert "kpi" in kinds
    assert "line" in kinds
    assert "bar" in kinds
    assert kinds.count("table") == 1
    assert all(t["name"] != "visual" for t in tiles)

    spec = build_spec(
        dashboards=[
            {
                "id": "demo::Scorecard",
                "workbook": "demo.pbix",
                "name": "Scorecard",
                "source": "powerbi",
                "filters": [{"name": "Industry", "field": "Industry", "kind": "slicer"}],
                "worksheets": [
                    {"name": t["name"], "kind": t["kind"], "key": f"demo::{t['name']}"}
                    for t in tiles
                ],
            }
        ],
        metric_decisions=[],
        all_decisions=[],
        estate=None,
    )
    data = build_disconnected_data(spec)
    keys = list((data.get("tables") or {}).keys())
    assert len(keys) == len(set(keys))
    assert len(keys) <= 9
    assert "Industry" in (data.get("filters") or {})
    assert data.get("facts")

    from engine.streamlit_app_gen import build_coco_prompt

    brief = build_coco_prompt(spec, dest_name="streamlit_dash_coco")
    assert "visual, visual" not in brief
    assert "### demo.pbix" in brief
    assert "**Scorecard**" in brief
    assert "Slicers:" in brief
    assert "Industry" in brief
    assert "Cross-highlight" in brief
    assert "Clone it and you fail" in brief
    assert "F2C811" in brief
    assert "apply_filters" in brief


def test_preview_ports_differ_by_variant() -> None:
    from engine.preview_server import COCO_PORT, DEFAULT_PORT, port_for_dir

    assert port_for_dir(Path("out/streamlit_dash")) == DEFAULT_PORT == 8511
    assert port_for_dir(Path("out/streamlit_dash_coco")) == COCO_PORT == 8512
    assert DEFAULT_PORT != COCO_PORT


def test_list_bi_files_finds_powerbi_dirs(tmp_path: Path) -> None:
    from engine.bi_sources import list_bi_files, source_kind

    dest = tmp_path / "ops_content"
    dest.mkdir()
    (dest / "model.tmdl").write_text("model Model\n", encoding="utf-8")
    (dest / "report.json").write_text('{"pages":[]}', encoding="utf-8")
    (tmp_path / "book.twb").write_text("<workbook/>", encoding="utf-8")
    (tmp_path / "report.pbix").write_bytes(b"PK")

    found = list_bi_files(tmp_path)
    kinds = {p.name: source_kind(p) for p in found}
    assert kinds["ops_content"] == "powerbi"
    assert kinds["book.twb"] == "tableau"
    assert kinds["report.pbix"] == "powerbi"
