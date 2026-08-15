"""Build semantic-view YAML / deploy SQL and row-access-policy SQL from decisions."""

from __future__ import annotations

from typing import Any

from engine.paths import warehouse_ids


def _yaml_escape(text: str) -> str:
    return text.replace('"', '\\"')


def _decision_ids(decisions: list[dict[str, Any]]) -> str:
    ids = [str(d.get("id")) for d in decisions if d.get("id")]
    return ", ".join(ids) if ids else "(none)"


def build_semantic_yaml(
    estate: dict[str, Any] | None,
    metric_decisions: list[dict[str, Any]],
    *,
    all_decisions: list[dict[str, Any]] | None = None,
) -> str:
    """Emit a Cortex Analyst–style details.yaml (atomic-studio shape)."""
    provenance = _decision_ids(all_decisions or metric_decisions)
    database, schema = warehouse_ids()
    tables = (estate or {}).get("tables") or []
    joins = (estate or {}).get("joins") or []
    usage = (estate or {}).get("workbook_usage") or []

    # Prefer tables touched by multiple sources
    touch_counts: dict[str, int] = {}
    for row in usage:
        for t in row.get("tables") or []:
            touch_counts[str(t)] = touch_counts.get(str(t), 0) + 1
    ranked = sorted(
        [str(t.get("name")) for t in tables if t.get("name")],
        key=lambda n: (-touch_counts.get(n, 0), n),
    )
    selected = ranked[:8] if ranked else ["historical_events"]
    table_meta = {str(t.get("name")): t for t in tables if t.get("name")}

    lines: list[str] = [
        f"# Provenance decision ids: {provenance}",
        'semantic_model_name: "BI Estate Ops Metrics"',
        "description: >",
        "  Semantic model drafted from Tableau and/or Power BI sources.",
        "  Metrics and relationships reconciled via streamlit-coco arbitration.",
        f"  Source: {database}.{schema}.",
        "",
        "tables:",
    ]

    for tname in selected:
        meta = table_meta.get(tname) or {"columns": []}
        cols = meta.get("columns") or []
        lines.append(f"  - name: {tname}")
        lines.append("    description: >")
        lines.append(f"      Table `{tname}` inferred from BI source relations.")
        lines.append("    base_table:")
        lines.append(f"      database: {database}")
        lines.append(f"      schema: {schema}")
        lines.append(f"      table: {tname}")
        pk = _guess_pk(cols)
        if pk:
            lines.append("    primary_key:")
            lines.append("      columns:")
            lines.append(f"        - {pk}")

        dim_cols = [
            c
            for c in cols
            if str(c.get("type", "")).lower() in {"string", "boolean", "date", "datetime", "text"}
            or "id" in str(c.get("name", "")).lower()
        ][:6]
        if dim_cols:
            lines.append("    dimensions:")
            for c in dim_cols:
                cname = c.get("name")
                ctype = _map_type(str(c.get("type") or "TEXT"))
                lines.append(f"      - name: {cname}")
                lines.append(f'        description: "Column {cname} from {tname}."')
                lines.append(f"        expr: {cname}")
                lines.append(f"        data_type: {ctype}")

        num_cols = [
            c
            for c in cols
            if str(c.get("type", "")).lower() in {"integer", "real", "number", "float"}
        ][:4]
        if num_cols:
            lines.append("    measures:")
            for c in num_cols:
                cname = c.get("name")
                lines.append(f"      - name: {cname}")
                lines.append(f'        description: "Numeric column {cname}."')
                lines.append(f"        expr: {cname}")
                lines.append("        data_type: NUMBER")
                lines.append("        default_aggregation: sum")

        # Attach arbitrated metrics onto the first/highest-touch table
        if tname == selected[0] and metric_decisions:
            if not num_cols:
                lines.append("    measures:")
            for dec in metric_decisions:
                if dec.get("action") == "drop":
                    continue
                mname = dec.get("metric_name") or dec.get("subject") or "metric"
                formula = dec.get("canonical_formula") or "1"
                plain = dec.get("plain_english") or ""
                lines.append(f"      - name: {mname}")
                lines.append("        description: >")
                lines.append(f"          {plain}")
                lines.append(f"          Decision: {dec.get('id')}.")
                lines.append(f"          Source formula (reference): {formula}")
                lines.append("        expr: 1")
                lines.append("        data_type: NUMBER")
                lines.append("        default_aggregation: sum")
                lines.append("        synonyms:")
                lines.append(f'          - "{_yaml_escape(str(dec.get("subject") or mname))}"')

    # Relationships from joins among selected tables
    selected_set = set(selected)
    rels = [
        j
        for j in joins
        if j.get("left_table") in selected_set and j.get("right_table") in selected_set
    ][:12]
    if rels:
        lines.append("")
        lines.append("relationships:")
        for j in rels:
            lines.append(f"  - left_table: {j.get('left_table')}")
            lines.append(f"    right_table: {j.get('right_table')}")
            lines.append("    relationship_type: many_to_one")
            lines.append("    join_columns:")
            lines.append(f"      - left_column: {j.get('left_column')}")
            lines.append(f"        right_column: {j.get('right_column')}")

    return "\n".join(lines).rstrip() + "\n"


def build_semantic_sql(yaml_body: str, *, decisions: list[dict[str, Any]] | None = None) -> str:
    """Wrap details YAML in SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML (atomic-studio)."""
    provenance = _decision_ids(decisions or [])
    database, schema = warehouse_ids()
    return (
        f"-- Provenance decision ids: {provenance}\n"
        f"-- Generated by examples/bi_to_semantic — review before deploying.\n"
        f"CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(\n"
        f'  \'"{database}"."{schema}"\',\n'
        f"  $$$\n"
        f"{yaml_body.rstrip()}\n"
        f"  $$,\n"
        f"  False\n"
        f");\n"
    )


def build_row_access_policy_sql(
    access_decisions: list[dict[str, Any]],
    *,
    all_decisions: list[dict[str, Any]] | None = None,
    target_table: str | None = None,
) -> str:
    """One RAP expressing kept/merged access branches + ALTER TABLE attach."""
    provenance = _decision_ids(all_decisions or access_decisions)
    database, schema = warehouse_ids()
    table = target_table or "historical_events"
    kept = [d for d in access_decisions if d.get("action") in {"keep", "merge"}]

    when_parts: list[str] = []
    for dec in kept:
        grants = str(dec.get("grants_to") or dec.get("subject") or "role").strip()
        rationale = str(dec.get("rationale") or "").replace("'", "''")
        # Opinionated mapping: "project leader" etc. → CURRENT_AVAILABLE_ROLES()
        # Demo policy: allow if role name appears in available roles.
        token = grants.lower().replace(" ", "_")
        when_parts.append(
            f"  -- decision {dec.get('id')}: {grants} ({rationale})\n"
            f"  WHEN EXISTS (\n"
            f"    SELECT 1 FROM TABLE(FLATTEN(INPUT => PARSE_JSON(CURRENT_AVAILABLE_ROLES()))) r\n"
            f"    WHERE LOWER(r.VALUE::STRING) LIKE '%{token}%'\n"
            f"  ) THEN TRUE"
        )

    if not when_parts:
        body = "  TRUE  -- no access branches kept; open policy placeholder\n"
    else:
        body = "\n".join(when_parts) + "\n  ELSE FALSE\n"

    return f"""-- Provenance decision ids: {provenance}
-- Generated by examples/bi_to_semantic — review before deploying.
-- Maps arbitrated BI access branches into one Snowflake RAP.

CREATE OR REPLACE ROW ACCESS POLICY {database}.{schema}.BI_USER_FILTER
AS (ID NUMBER) RETURNS BOOLEAN ->
CASE
{body}
END
COMMENT = 'Reconciled from Tableau User Filters / Power BI RLS (streamlit-coco demo)';

ALTER TABLE {database}.{schema}.{table}
  ADD ROW ACCESS POLICY {database}.{schema}.BI_USER_FILTER ON (id);
"""


def _guess_pk(cols: list[dict[str, Any]]) -> str | None:
    names = [str(c.get("name")) for c in cols]
    for candidate in ("id", "ID", "pk"):
        if candidate in names:
            return candidate
    for name in names:
        if name.lower().endswith("_id") or name.lower().endswith("_key"):
            return name
    return names[0] if names else None


def _map_type(tableau_type: str) -> str:
    t = tableau_type.lower()
    if t in {"integer", "real", "number", "float"}:
        return "NUMBER"
    if t in {"date"}:
        return "DATE"
    if t in {"datetime", "timestamp"}:
        return "TIMESTAMP_NTZ"
    if t in {"boolean", "bool"}:
        return "BOOLEAN"
    return "TEXT"
