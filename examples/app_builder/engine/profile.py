"""Deterministic tabular profiler — pandas only, no CoCo / network / Streamlit.

Used by the Brief screen to pre-fill ``infer:`` questions. Empty or unparseable
input returns an empty ``DataProfile``; the caller decides what that means in the UI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Grain: span >180 days → month; >21 days → week; else day. No dates → None.
_SPAN_MONTH_DAYS = 180
_SPAN_WEEK_DAYS = 21

_DATE_NAME = re.compile(
    r"(date|time|month|week|year|day|_at$|_ts$|^dt$|_dt$)",
    re.IGNORECASE,
)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?")
_ID_NAME = re.compile(r"(^id$|_id$|^uuid$|^pk$|^key$|_key$)", re.IGNORECASE)
_ID_UNIQUE_MIN_ROWS = 20
_MEASURE_HINTS = (
    "revenue",
    "amount",
    "total",
    "sales",
    "spend",
    "cost",
    "profit",
    "margin",
    "orders",
    "quantity",
    "qty",
    "count",
    "price",
    "value",
)
_MAX_FILTERS = 8
_MAX_METRICS = 5
_FILTER_CARD_CAP = 50


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    role: str
    cardinality: int
    null_pct: float
    example: str


@dataclass(frozen=True)
class DataProfile:
    columns: tuple[ColumnProfile, ...]
    row_count: int
    date_range: tuple[str, str] | None
    filters: tuple[str, ...]
    metrics: tuple[str, ...]
    grain: str | None


EMPTY_PROFILE = DataProfile(
    columns=(),
    row_count=0,
    date_range=None,
    filters=(),
    metrics=(),
    grain=None,
)


def profile_csv(path: Path) -> DataProfile:
    """Column roles, row count, date range, filter/metric candidates. Pure pandas."""
    frame = _read_table(path)
    if frame is None or frame.shape[1] == 0:
        return EMPTY_PROFILE
    return _profile_frame(frame)


def _read_table(path: Path) -> pd.DataFrame | None:
    try:
        resolved = Path(path)
        if not resolved.is_file():
            return None
        suffix = resolved.suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(resolved)
        return pd.read_csv(resolved)
    except Exception:  # noqa: BLE001 — inconclusive → empty profile
        return None


def _profile_frame(frame: pd.DataFrame) -> DataProfile:
    df = frame.copy()
    n = int(len(df))
    columns: list[ColumnProfile] = []
    date_series: list[pd.Series] = []

    for raw_name in df.columns:
        name = str(raw_name)
        series = df[raw_name]
        role = _infer_role(name, series, n)
        parsed = _as_dates(series) if role == "date" else None
        if parsed is not None:
            date_series.append(parsed)
        columns.append(
            ColumnProfile(
                name=name,
                role=role,
                cardinality=int(series.nunique(dropna=True)),
                null_pct=_null_pct(series, n),
                example=_example(series),
            )
        )

    date_range = _date_range(date_series)
    return DataProfile(
        columns=tuple(columns),
        row_count=n,
        date_range=date_range,
        filters=_pick_filters(columns, n),
        metrics=_pick_metrics(columns),
        grain=_infer_grain(date_range),
    )


def _infer_role(name: str, series: pd.Series, n: int) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if _DATE_NAME.search(name) or _iso_date_strings(series):
        if _looks_like_dates(series):
            return "date"
    if _is_id(name, series, n):
        return "id"
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        return "measure"
    return "dimension"


def _is_id(name: str, series: pd.Series, n: int) -> bool:
    if _ID_NAME.search(name):
        return True
    if n < _ID_UNIQUE_MIN_ROWS:
        return False
    unique = int(series.nunique(dropna=True))
    if unique != n:
        return False
    if pd.api.types.is_numeric_dtype(series) and _measure_rank(name) < 100:
        return False
    return True


def _iso_date_strings(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return False
    sample = series.dropna().astype(str).head(30)
    if sample.empty:
        return False
    return float(sample.str.match(_ISO_DATE).mean()) >= 0.8


def _looks_like_dates(series: pd.Series) -> bool:
    if _iso_date_strings(series):
        return True
    if pd.api.types.is_numeric_dtype(series):
        return False
    sample = series.dropna().head(30)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce")
    return float(parsed.notna().mean()) >= 0.8


def _as_dates(series: pd.Series) -> pd.Series | None:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.notna().any():
        return parsed
    return None


def _date_range(date_series: list[pd.Series]) -> tuple[str, str] | None:
    mins: list[pd.Timestamp] = []
    maxs: list[pd.Timestamp] = []
    for series in date_series:
        valid = series.dropna()
        if valid.empty:
            continue
        mins.append(valid.min())
        maxs.append(valid.max())
    if not mins:
        return None
    lo = min(mins).strftime("%Y-%m-%d")
    hi = max(maxs).strftime("%Y-%m-%d")
    return (lo, hi)


def _infer_grain(date_range: tuple[str, str] | None) -> str | None:
    if date_range is None:
        return None
    start = pd.Timestamp(date_range[0])
    end = pd.Timestamp(date_range[1])
    span = int((end - start).days)
    if span > _SPAN_MONTH_DAYS:
        return "month"
    if span > _SPAN_WEEK_DAYS:
        return "week"
    return "day"


def _pick_filters(columns: list[ColumnProfile], n: int) -> tuple[str, ...]:
    cap = _FILTER_CARD_CAP if n <= 0 else min(_FILTER_CARD_CAP, max(2, n))
    candidates = [
        col
        for col in columns
        if col.role == "dimension" and 2 <= col.cardinality <= cap
    ]
    candidates.sort(key=lambda col: (col.cardinality, col.name.lower()))
    return tuple(col.name for col in candidates[:_MAX_FILTERS])


def _pick_metrics(columns: list[ColumnProfile]) -> tuple[str, ...]:
    measures = [col for col in columns if col.role == "measure"]
    measures.sort(key=lambda col: (_measure_rank(col.name), col.name.lower()))
    return tuple(col.name for col in measures[:_MAX_METRICS])


def _measure_rank(name: str) -> int:
    lowered = name.lower()
    for index, hint in enumerate(_MEASURE_HINTS):
        if hint in lowered:
            return index
    return 100


def _null_pct(series: pd.Series, n: int) -> float:
    if n <= 0:
        return 0.0
    return round(float(series.isna().mean()), 4)


def _example(series: pd.Series) -> str:
    valid = series.dropna()
    if valid.empty:
        return ""
    value = valid.iloc[0]
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    return text[:40]
