"""Deterministic App Builder profiler (no Streamlit, no CoCo)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "app_builder"))

from engine.profile import EMPTY_PROFILE, profile_csv  # noqa: E402

FIXTURE = ROOT / "examples" / "app_builder" / "fixtures" / "sales_sv.csv"


def test_profile_sales_sv_fixture() -> None:
    profile = profile_csv(FIXTURE)
    names = {col.name: col for col in profile.columns}
    assert profile.row_count == 9
    assert names["month"].role == "date"
    assert names["region"].role == "dimension"
    assert names["revenue"].role == "measure"
    assert names["orders"].role == "measure"
    assert names["margin"].role == "measure"
    assert profile.date_range is not None
    assert profile.date_range[0].startswith("2026-01")
    assert profile.date_range[1].startswith("2026-03")
    assert "region" in profile.filters
    assert profile.metrics[0] == "revenue"
    assert "orders" in profile.metrics
    assert "margin" in profile.metrics
    assert profile.grain in {"day", "week", "month"}


def test_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    profile = profile_csv(path)
    assert profile == EMPTY_PROFILE
    assert profile.row_count == 0
    assert profile.columns == ()
    assert profile.metrics == ()
    assert profile.filters == ()
    assert profile.grain is None
    assert profile.date_range is None


def test_missing_or_unparseable(tmp_path: Path) -> None:
    missing = profile_csv(tmp_path / "nope.csv")
    assert missing == EMPTY_PROFILE
    junk = tmp_path / "junk.csv"
    junk.write_bytes(b"\x00\x01\xffnot,a,csv")
    assert profile_csv(junk).row_count == 0 or profile_csv(junk).metrics == ()


def test_no_numeric_columns(tmp_path: Path) -> None:
    path = tmp_path / "cats.csv"
    path.write_text("region,segment\nEMEA,SMB\nAMER,ENT\nAPAC,SMB\n", encoding="utf-8")
    profile = profile_csv(path)
    assert profile.row_count == 3
    assert profile.metrics == ()
    assert profile.grain is None
    assert profile.date_range is None
    roles = {col.name: col.role for col in profile.columns}
    assert roles["region"] == "dimension"
    assert roles["segment"] == "dimension"
    assert "region" in profile.filters
    assert "segment" in profile.filters


def test_unambiguous_date_column(tmp_path: Path) -> None:
    path = tmp_path / "dated.csv"
    path.write_text(
        "order_date,region,revenue\n"
        "2024-01-15,EMEA,10\n"
        "2024-08-01,AMER,20\n"
        "2024-12-31,APAC,30\n",
        encoding="utf-8",
    )
    profile = profile_csv(path)
    names = {col.name: col for col in profile.columns}
    assert names["order_date"].role == "date"
    assert profile.date_range == ("2024-01-15", "2024-12-31")
    assert profile.grain == "month"
    assert profile.metrics[0] == "revenue"


def test_no_date_column(tmp_path: Path) -> None:
    path = tmp_path / "nodate.csv"
    path.write_text("sku,amount\nA,1.5\nB,2.0\n", encoding="utf-8")
    profile = profile_csv(path)
    names = {col.name: col for col in profile.columns}
    assert names["sku"].role != "date"
    assert names["amount"].role == "measure"
    assert profile.date_range is None
    assert profile.grain is None
    assert profile.metrics == ("amount",)
