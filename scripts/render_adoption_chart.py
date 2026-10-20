#!/usr/bin/env python3
"""Render doc-dev/metrics/chart.html from history.jsonl."""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "doc-dev" / "metrics"
HISTORY_PATH = METRICS_DIR / "history.jsonl"
LATEST_PATH = METRICS_DIR / "latest.json"
CHART_PATH = METRICS_DIR / "chart.html"

Series = tuple[str, str, str]  # key, label, color


def _history_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not HISTORY_PATH.exists():
        return rows
    for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.sort(key=lambda r: str(r.get("date") or ""))
    return rows


def _pypi_lifetime() -> tuple[int | None, str]:
    """All-time PyPI downloads from the latest overall (without mirrors) series."""
    if not LATEST_PATH.exists():
        return None, "pypistats overall missing"
    payload = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
    days = (payload.get("pypi") or {}).get("overall_without_mirrors") or []
    if not days:
        return None, "pypistats overall missing"
    total = 0
    first = last = ""
    for row in days:
        total += int(row.get("downloads") or 0)
        day = str(row.get("date") or "")
        if day and (not first or day < first):
            first = day
        if day and (not last or day > last):
            last = day
    hint = "without mirrors"
    if first:
        hint += f" · since {first}"
        if last:
            hint += f" · through {last}"
    return total, hint


def _fmt_kpi(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"
    return str(value)


def _num(row: dict[str, Any], key: str) -> float:
    val = row.get(key)
    return float(val) if isinstance(val, (int, float)) else 0.0


def _nice_max(value: float) -> int:
    if value <= 0:
        return 1
    import math

    exp = int(math.floor(math.log10(value)))
    frac = value / (10**exp)
    if frac <= 1:
        nice = 1
    elif frac <= 2:
        nice = 2
    elif frac <= 5:
        nice = 5
    else:
        nice = 10
    return int(nice * 10**exp)


def _short_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return d.strftime("%b %-d")


def _svg_chart(
    rows: list[dict[str, Any]],
    series: list[Series],
    *,
    title: str,
    ylabel: str,
    width: int = 920,
    height: int = 280,
) -> str:
    pad_l, pad_r, pad_t, pad_b = 52, 18, 36, 40
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    n = len(rows)
    ymax = _nice_max(max((_num(row, key) for row in rows for key, _, _ in series), default=0))
    ticks = 4

    def x_at(i: int) -> float:
        if n <= 1:
            return pad_l + inner_w / 2
        return pad_l + inner_w * i / (n - 1)

    def y_at(val: float) -> float:
        return pad_t + inner_h * (1 - val / ymax)

    grid: list[str] = []
    for t in range(ticks + 1):
        val = ymax * t / ticks
        y = y_at(val)
        grid.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" />')
        grid.append(
            f'<text class="tick" x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end">'
            f"{int(val)}</text>"
        )

    label_idx = {0, n - 1}
    if n > 2:
        label_idx.add(n // 2)
    if n > 6:
        label_idx.add(n // 4)
        label_idx.add((3 * n) // 4)
    xlabels: list[str] = []
    for i in sorted(label_idx):
        xlabels.append(
            f'<text class="tick" x="{x_at(i):.1f}" y="{height - 14}" text-anchor="middle">'
            f"{html.escape(_short_date(str(rows[i].get('date') or '')))}</text>"
        )

    lines: list[str] = []
    for key, _label, color in series:
        pts = " ".join(f"{x_at(i):.1f},{y_at(_num(row, key)):.1f}" for i, row in enumerate(rows))
        lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round" points="{pts}" />'
        )
        for i, row in enumerate(rows):
            if row.get("backfilled"):
                lines.append(
                    f'<circle cx="{x_at(i):.1f}" cy="{y_at(_num(row, key)):.1f}" '
                    f'r="2.2" fill="{color}" opacity="0.35" />'
                )

    legend = "".join(
        f'<span class="swatch"><i style="background:{color}"></i>{html.escape(label)}</span>'
        for _key, label, color in series
    )
    return f"""
<figure>
  <figcaption>
    <strong>{html.escape(title)}</strong>
    <span class="unit">{html.escape(ylabel)}</span>
    <span class="legend">{legend}</span>
  </figcaption>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
    <g class="grid">{"".join(grid)}</g>
    {"".join(lines)}
    {"".join(xlabels)}
  </svg>
</figure>
"""


def render_chart(rows: list[dict[str, Any]] | None = None) -> Path:
    rows = rows if rows is not None else _history_rows()
    if not rows:
        raise FileNotFoundError(f"{HISTORY_PATH} has no rows")
    first, last = rows[0], rows[-1]
    start = str(first.get("date") or "")
    end = str(last.get("date") or "")
    backfilled = sum(1 for row in rows if row.get("backfilled"))
    caption = f"Source: history.jsonl · {start} → {end} · {len(rows)} days" + (
        f" · {backfilled} backfilled (lighter dots)" if backfilled else ""
    )
    lifetime, lifetime_hint = _pypi_lifetime()
    kpis = [
        ("PyPI total", lifetime, lifetime_hint),
        ("PyPI last month", last.get("pypi_last_month"), "rolling 30 days"),
        ("PyPI last week", last.get("pypi_last_week"), "rolling 7 days"),
        ("PyPI last day", last.get("pypi_last_day"), "prior calendar day"),
        ("GitHub stars", last.get("devoteam_stars"), "DevoteamSP/streamlit-coco"),
    ]
    kpi_html = "".join(
        f"""<div class="kpi">
  <div class="label">{html.escape(label)}</div>
  <div class="value">{html.escape(_fmt_kpi(value))}</div>
  <div class="hint">{html.escape(hint)}</div>
</div>"""
        for label, value, hint in kpis
    )
    pypi = _svg_chart(
        rows,
        [
            ("pypi_last_month", "Last month", "#93c5fd"),
            ("pypi_last_week", "Last week", "#3b82f6"),
            ("pypi_last_day", "Last day", "#1d4ed8"),
        ],
        title="PyPI downloads",
        ylabel="downloads",
    )
    github = _svg_chart(
        rows,
        [
            ("devoteam_views_14d", "DevoteamSP views (14d)", "#0f766e"),
            ("devoteam_clones_14d", "DevoteamSP clones (14d)", "#2dd4bf"),
            ("lletourmy_views_14d", "lletourmy views (14d)", "#b45309"),
            ("lletourmy_clones_14d", "lletourmy clones (14d)", "#f59e0b"),
        ],
        title="GitHub traffic",
        ylabel="rolling ~14-day window",
    )
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>streamlit-coco adoption</title>
  <style>
    :root {{
      --bg: #f6f6f3;
      --fg: #1b1b18;
      --muted: #6f6f68;
      --card: #ffffff;
      --line: #e6e6df;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #161615;
        --fg: #eeeae3;
        --muted: #9a9a92;
        --card: #1f1f1c;
        --line: #2c2c28;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--fg);
      font: 14px/1.45 ui-sans-serif, system-ui, sans-serif;
    }}
    main {{ max-width: 960px; margin: 0 auto; padding: 28px 20px 48px; }}
    h1 {{ font-size: 22px; font-weight: 650; margin: 0 0 4px; }}
    .sub {{ color: var(--muted); margin: 0 0 22px; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }}
    @media (max-width: 900px) {{
      .kpis {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    }}
    @media (max-width: 720px) {{
      .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .kpi .label {{ color: var(--muted); font-size: 12px; }}
    .kpi .value {{ font-size: 28px; font-weight: 650; letter-spacing: -0.03em; }}
    .kpi .hint {{ color: var(--muted); font-size: 11px; margin-top: 2px; }}
    figure {{
      margin: 0 0 16px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 12px 4px;
    }}
    figcaption {{
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 8px 14px;
      padding: 2px 6px 8px;
    }}
    figcaption .unit {{ color: var(--muted); font-size: 12px; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 10px 14px; margin-left: auto; }}
    .swatch {{ display: inline-flex; align-items: center; gap: 6px; color: var(--muted);
      font-size: 12px; }}
    .swatch i {{ width: 12px; height: 2px; display: inline-block; }}
    svg {{ width: 100%; height: auto; display: block; }}
    .grid line {{ stroke: var(--line); stroke-width: 1; }}
    .tick {{ fill: var(--muted); font-size: 11px; font-family: inherit; }}
  </style>
</head>
<body>
  <main>
    <h1>streamlit-coco adoption</h1>
    <p class="sub">{html.escape(caption)}</p>
    <section class="kpis">{kpi_html}</section>
    {pypi}
    {github}
  </main>
</body>
</html>
"""
    CHART_PATH.write_text(page, encoding="utf-8")
    return CHART_PATH


def main() -> int:
    path = render_chart()
    print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
