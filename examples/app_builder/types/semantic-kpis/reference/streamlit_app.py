"""KPI presentation — reference app for the semantic-kpis type.

Imitate this file. Fixture shape: month, region, revenue, orders, margin.
Generated apps get `data.csv` copied next to this script (demo pack).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent / "data.csv"
NEEDED = ("month", "region", "revenue", "orders", "margin")


st.set_page_config(
    page_title="KPI presentation",
    page_icon=":material/speed:",
    layout="wide",
)


@st.cache_data(ttl="5m")
def load_sales(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "month" in frame.columns:
        frame["month"] = pd.to_datetime(frame["month"], errors="coerce")
    return frame


def _fmt_currency(value: float) -> str:
    return f"${value:,.0f}"


def _fmt_count(value: float) -> str:
    return f"{value:,.0f}"


def _fmt_pct(value: float) -> str:
    ratio = value * 100 if abs(value) <= 1 else value
    return f"{ratio:.1f}%"


def _delta(current: float, previous: float) -> str | None:
    if previous == 0:
        return None
    return f"{(current - previous) / previous:.1%}"


st.title("Sales pulse")
st.caption("Exec pack · monthly grain · disconnected demo — no warehouse")

if not DATA.is_file():
    st.error("No `data.csv` next to this app — disconnected demo cannot run.")
    st.stop()

df = load_sales(str(DATA))
missing = [col for col in NEEDED if col not in df.columns]
if missing:
    st.error("Fixture is missing column(s): " + ", ".join(f"`{c}`" for c in missing))
    st.stop()


@st.fragment
def _board(data: pd.DataFrame) -> None:
    regions = sorted(data["region"].dropna().astype(str).unique().tolist())
    picked = st.multiselect("Region", regions, default=regions)
    filtered = data[data["region"].isin(picked)] if picked else data.iloc[0:0]

    if filtered.empty:
        st.info("No rows for this selection. Add a region back, or check the fixture.")
        return

    latest = filtered["month"].max()
    period = latest.strftime("%Y-%m") if pd.notna(latest) else "—"
    st.caption(f"KPIs are **{period}** vs the previous month in this filter.")
    prior = filtered.loc[filtered["month"] < latest, "month"].max()
    now = filtered[filtered["month"] == latest]
    before = filtered[filtered["month"] == prior] if pd.notna(prior) else now.iloc[0:0]

    rev, orders, margin = now["revenue"].sum(), now["orders"].sum(), now["margin"].mean()
    prev_rev = before["revenue"].sum() if not before.empty else 0.0
    prev_orders = before["orders"].sum() if not before.empty else 0.0
    prev_margin = before["margin"].mean() if not before.empty else 0.0
    by_month = filtered.groupby("month", sort=True)

    k1, k2, k3 = st.columns(3)
    k1.metric(
        "Revenue",
        _fmt_currency(float(rev)),
        _delta(float(rev), float(prev_rev)),
        border=True,
        chart_data=by_month["revenue"].sum().tolist(),
        chart_type="line",
    )
    k2.metric(
        "Orders",
        _fmt_count(float(orders)),
        _delta(float(orders), float(prev_orders)),
        border=True,
        chart_data=by_month["orders"].sum().tolist(),
        chart_type="bar",
    )
    k3.metric(
        "Avg margin",
        _fmt_pct(float(margin)),
        _delta(float(margin), float(prev_margin)),
        border=True,
    )

    # Time trend → line (not bar, never pie). Three regions is fine as color.
    trend = (
        filtered.groupby(["month", "region"], as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    with st.container(border=True):
        st.subheader("Revenue trend")
        st.line_chart(trend, x="month", y="revenue", color="region")

    detail = filtered.sort_values(["month", "region"], ascending=[False, True])
    with st.container(border=True):
        st.subheader("Detail")
        st.dataframe(
            detail,
            width="stretch",
            hide_index=True,
            column_config={
                "month": st.column_config.DateColumn("Month", format="YYYY-MM"),
                "region": st.column_config.TextColumn("Region"),
                "revenue": st.column_config.NumberColumn("Revenue", format="$%.0f"),
                "orders": st.column_config.NumberColumn("Orders", format="%d"),
                "margin": st.column_config.NumberColumn("Margin", format="%.1%"),
            },
        )


_board(df)
