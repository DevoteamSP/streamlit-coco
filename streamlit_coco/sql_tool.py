"""Helpers for CoCo SQL / sql_execute tool display."""

from __future__ import annotations

import json
import re
from typing import Any

from streamlit_coco.tool_names import is_sql_tool, status_label

_QUERY_KEYS = ("query", "command", "sql", "statement", "text")


def extract_sql_text(tool_input: dict[str, Any] | None) -> str:
    """Pull the SQL statement from a tool input payload."""
    if not isinstance(tool_input, dict):
        return ""
    for key in _QUERY_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("input", "arguments", "params"):
        nested = tool_input.get(key)
        if isinstance(nested, dict):
            found = extract_sql_text(nested)
            if found:
                return found
    return ""


def _try_json_loads(raw: str) -> Any | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            return None
    return None


def _rows_from_mapping(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    for key in ("rows", "data", "records", "result", "results"):
        value = payload.get(key)
        if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
            return value
        if isinstance(value, list) and value and all(isinstance(row, list) for row in value):
            columns = payload.get("columns") or payload.get("column_names") or []
            if isinstance(columns, list) and columns:
                names = [str(col) for col in columns]
                return [
                    {names[i] if i < len(names) else f"col_{i}": cell for i, cell in enumerate(row)}
                    for row in value
                    if isinstance(row, list)
                ]
    columns = payload.get("columns") or payload.get("column_names")
    rows = payload.get("rows")
    if isinstance(columns, list) and isinstance(rows, list) and rows and isinstance(rows[0], list):
        names = [str(col) for col in columns]
        return [
            {names[i] if i < len(names) else f"col_{i}": cell for i, cell in enumerate(row)}
            for row in rows
            if isinstance(row, list)
        ]
    return None


def parse_sql_result_table(
    result: Any,
    *,
    max_rows: int = 200,
) -> tuple[list[dict[str, Any]] | None, str | None, int | None]:
    """Best-effort parse of a SQL tool result into row dicts.

    Returns ``(rows, text_fallback, total_row_count)``.
    """
    if result is None:
        return None, None, None

    payload: Any = result
    if isinstance(result, str):
        parsed = _try_json_loads(result)
        if parsed is not None:
            payload = parsed
        else:
            text = result.strip()
            return None, text or None, None

    if isinstance(payload, list):
        if not payload:
            return [], None, 0
        if all(isinstance(row, dict) for row in payload):
            total = len(payload)
            return payload[:max_rows], None, total
        return None, json.dumps(payload, indent=2, default=str), len(payload)

    if isinstance(payload, dict):
        rows = _rows_from_mapping(payload)
        if rows is not None:
            total = len(rows)
            for count_key in ("row_count", "rowCount", "num_rows", "total"):
                raw_count = payload.get(count_key)
                if isinstance(raw_count, int) and raw_count >= 0:
                    total = raw_count
                    break
            return rows[:max_rows], None, total
        if "error" in payload or "message" in payload:
            message = payload.get("error") or payload.get("message")
            return None, str(message), None
        return None, json.dumps(payload, indent=2, default=str), None

    return None, str(payload), None


def sql_status_label(status: str) -> str:
    return status_label(status)


__all__ = [
    "extract_sql_text",
    "is_sql_tool",
    "parse_sql_result_table",
    "sql_status_label",
]
