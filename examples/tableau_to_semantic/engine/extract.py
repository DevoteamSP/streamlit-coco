"""Prompts, schema loading, and structured-output helpers for screens 2–4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.paths import CONTRACTS_DIR, OUT_DIR

ESTATE_MAP_PROMPT = """\
You are analysing a folder of Tableau workbook XML files (.twb).

1. Glob for `*.twb` in the working directory (including `_uploads/`).
2. For each workbook, Grep/Read enough of the XML to find:
   - tables referenced in `<relation type="table">` (names like `[public].[users]`)
   - join equalities between tables
   - worksheet and dashboard counts (elements named worksheet / dashboard)
3. Return ONLY structured output matching the schema — no prose.

Focus on the relational model implied by the workbooks. Prefer short table names
without schema brackets (e.g. `users` not `[public].[users]`).
List columns you can see from metadata-record column entries (name + local-type).
If a workbook is huge, sample Grep rather than reading the whole file.
"""

KPI_INVENTORY_PROMPT = """\
You are inventorying Tableau calculated fields across all `*.twb` workbooks in cwd.

1. Glob `*.twb` (including `_uploads/`).
2. Grep for calculated fields — look for `<column` with a nested `<calculation`
   and/or captions that look like metrics (not formatting flags).
3. Group by display name / caption. When the same name appears in multiple
   workbooks with different formulas, set is_conflicting=true.
4. For each metric write a one-sentence plain_english definition.
5. Return ONLY structured output matching the schema.

Prioritise fields that appear in more than one workbook. Include up to ~40
metrics; prefer conflicts and shared names over unique ones.
aggregation may be "unknown" when not clear.
"""


def access_rules_prompt() -> str:
    out = OUT_DIR.resolve()
    return f"""\
You are comparing Tableau row-level security across workbooks.

Prior step JSON may already exist in `{out}` (also mounted via add_dirs):
`estate_map.json`, `kpi_inventory.json`. Use those for workbook inventory / table
names if present — User Filter formulas still come from the `.twb` files.

1. Glob `*.twb` in the working directory (including `_uploads/`).
2. Optionally Glob/Read `{out}/*.json` for prior estate/KPI context.
3. Grep for User Filter calculated fields — typically caption="User Filter"
   (case-insensitive) with a long IF/ELSEIF cascade.
4. For EACH workbook that has a User Filter, decode the formula and break it
   into branches: condition, who it grants_to (e.g. server admin, site admin,
   project owner, project leader, item owner), and source_columns referenced.
5. Compare branches across workbooks. Emit divergences — especially missing
   project-leader branches, merged admin checks, or a final branch that changes
   meaning. Each divergence needs a concrete consequence in plain English
   (e.g. "A Project Leader sees a row in ts_content but not in ts_users.").
6. You MUST return at least one divergence when comparing 2+ workbooks.
7. Return ONLY structured output matching the schema.
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


def list_twb_files(cwd: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in ("*.twb", "*.twbx", "_uploads/*.twb", "_uploads/*.twbx"):
        found.extend(sorted(cwd.glob(pattern)))
    # de-dupe by name
    by_name: dict[str, Path] = {}
    for path in found:
        by_name[path.name] = path
    return list(by_name.values())
