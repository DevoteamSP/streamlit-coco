"""Prompts, schema loading, and structured-output helpers for screens 2–4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.paths import CONTRACTS_DIR, OUT_DIR

ESTATE_MAP_PROMPT = """\
You are analysing a folder of BI sources: Tableau workbook XML (*.twb / *.twbx)
and/or Power BI (folders with model.tmdl + report.json, or *.pbix / *.pbit).

1. Glob for `*.twb`, `*.twbx`, `*.pbix`, `*.pbit`, `**/model.tmdl` (including `_uploads/`).
2. For Tableau, Grep/Read enough XML to find:
   - tables referenced in `<relation type="table">` (names like `[public].[users]`)
   - join equalities between tables
   - worksheet and dashboard counts
3. For Power BI, prefer the unpacked model (pbixray / DataModel): tables, columns,
   relationships, DAX measures, Power Query M. Report/Layout or report.json for
   page (dashboard) and visual counts. TMDL / DataModelSchema only if no DataModel.
4. Return ONLY structured output matching the schema — no prose.

Focus on the relational model implied by the sources. Prefer short table names
without schema brackets (e.g. `users` not `[public].[users]`).
If a file is huge, sample Grep rather than reading the whole file.
Use `workbook` in the schema for the source file or folder name.
"""

KPI_INVENTORY_PROMPT = """\
You are inventorying metrics across Tableau and Power BI sources in cwd.

1. Glob `*.twb`, `*.twbx`, `*.pbix`, `**/model.tmdl` (including `_uploads/`).
2. Tableau: Grep for calculated fields — `<column` with a nested `<calculation`.
3. Power BI: Read DAX measures from the .pbix model (or `measure` in TMDL).
4. Group by display name / caption. When the same name appears in multiple
   sources with different formulas, set is_conflicting=true.
5. For each metric write a one-sentence plain_english definition.
6. Return ONLY structured output matching the schema.

Prioritise fields that appear in more than one source. Include up to ~40
metrics; prefer conflicts and shared names over unique ones.
aggregation may be "unknown" when not clear. Put the source file/folder name
in `workbook`.
"""


def access_rules_prompt() -> str:
    out = OUT_DIR.resolve()
    return f"""\
You are comparing row-level security across BI sources (Tableau User Filters
and/or Power BI RLS roles).

Prior step JSON may already exist in `{out}` (also mounted via add_dirs):
`estate_map.json`, `kpi_inventory.json`. Use those for source inventory / table
names if present.

1. Glob `*.twb`, `*.twbx`, `*.pbix`, `**/model.tmdl` (including `_uploads/`).
2. Optionally Glob/Read `{out}/*.json` for prior estate/KPI context.
3. Tableau: Grep for User Filter calculated fields — typically caption="User Filter"
   (case-insensitive) with a long IF/ELSEIF cascade.
4. Power BI: Read RLS roles from the .pbix model (or `role` / `tablePermission` in TMDL).
5. For EACH source that has an access rule, decode it into branches: condition,
   who it grants_to (e.g. server admin, site admin, project owner, project leader,
   item owner), and source_columns referenced. Put the file/folder name in `workbook`.
6. Compare branches across sources. Emit divergences — especially missing
   project-leader branches. Each divergence needs a concrete consequence
   (e.g. "A Project Leader sees a row in ts_content and not in ts_users."
   or "`Fact` is the same name in both reports but the columns disagree.").
7. You MUST return at least one divergence when comparing 2+ sources.
8. Return ONLY structured output matching the schema.
"""


# Kept for callers/tests that import a constant; prefer access_rules_prompt().
ACCESS_RULES_PROMPT = access_rules_prompt()


def load_schema(name: str) -> dict[str, Any]:
    path = CONTRACTS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: Any, schema: dict[str, Any]) -> list[str]:
    """Lightweight JSON-Schema subset validator (required + types + additionalProperties).

    Avoids a hard jsonschema dependency in the library package.
    """
    errors: list[str] = []
    _validate_node(payload, schema, "$", errors, schema)
    return errors


def _validate_node(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
    root: dict[str, Any],
) -> None:
    if "$ref" in schema:
        # local refs not used in our contracts
        return

    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")
        props = schema.get("properties") or {}
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unexpected property '{key}'")
        for key, child_schema in props.items():
            if key in value:
                _validate_node(value[key], child_schema, f"{path}.{key}", errors, root)
        min_items = schema.get("minItems")
        # minItems on object is unusual; ignore
        _ = min_items
    elif expected == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} items, got {len(value)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{i}]", errors, root)
    elif expected == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
    elif expected == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path}: expected integer")
    elif expected == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: expected boolean")
    elif expected == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: expected number")


def accept_structured(
    data: Any,
    *,
    schema: dict[str, Any],
    on_ok,
) -> tuple[bool, list[str]]:
    """Validate and forward; returns (ok, errors)."""
    errors = validate_payload(data, schema)
    if errors:
        return False, errors
    on_ok(data)
    return True, []


def list_bi_files(cwd: Path) -> list[Path]:
    from engine.bi_sources import list_bi_files as _list

    return _list(cwd)


def list_twb_files(cwd: Path) -> list[Path]:
    """Back-compat alias for ``list_bi_files``."""
    return list_bi_files(cwd)
