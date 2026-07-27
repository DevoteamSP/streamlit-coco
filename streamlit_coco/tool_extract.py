"""Shared extractors for CoCo tool input / result payloads."""

from __future__ import annotations

import difflib
from typing import Any

_PATH_KEYS = ("path", "file_path", "filePath", "filename", "file", "target")
_COMMAND_KEYS = ("command", "cmd")
_PATTERN_KEYS = ("pattern", "glob_pattern", "glob", "regex")
_CONTENT_KEYS = ("content", "new_str", "newString", "text", "file_text")
_OLD_KEYS = ("old_string", "oldString", "old_str")
_NEW_KEYS = ("new_string", "newString", "new_str")


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def first_str(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_path(tool_input: dict[str, Any] | None) -> str:
    data = as_dict(tool_input)
    found = first_str(data, _PATH_KEYS)
    if found:
        return found
    for key in ("input", "arguments", "params"):
        nested = data.get(key)
        if isinstance(nested, dict):
            found = first_str(nested, _PATH_KEYS)
            if found:
                return found
    return ""


def extract_command(tool_input: dict[str, Any] | None) -> str:
    return first_str(as_dict(tool_input), _COMMAND_KEYS)


def extract_pattern(tool_input: dict[str, Any] | None) -> str:
    return first_str(as_dict(tool_input), _PATTERN_KEYS)


def extract_content(tool_input: dict[str, Any] | None) -> str:
    return first_str(as_dict(tool_input), _CONTENT_KEYS)


def extract_old_new(tool_input: dict[str, Any] | None) -> tuple[str, str]:
    data = as_dict(tool_input)
    return first_str(data, _OLD_KEYS), first_str(data, _NEW_KEYS)


def unified_diff(
    old: str,
    new: str,
    *,
    path: str = "",
    n: int = 3,
) -> str:
    """Build a unified diff for Edit/Write approval previews."""
    from_file = f"a/{path}" if path else "a/before"
    to_file = f"b/{path}" if path else "b/after"
    old_lines = [f"{line}\n" for line in old.splitlines()] if old else []
    new_lines = [f"{line}\n" for line in new.splitlines()] if new else []
    return "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=from_file,
            tofile=to_file,
            n=n,
        )
    ).rstrip("\n")


def extract_plan(tool_input: dict[str, Any] | None) -> str:
    data = as_dict(tool_input)
    return first_str(data, ("plan", "message", "text"))


def language_for_path(path: str) -> str:
    lower = path.lower()
    mapping = {
        ".py": "python",
        ".sql": "sql",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".json": "json",
        ".md": "markdown",
        ".toml": "toml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".sh": "bash",
        ".css": "css",
        ".html": "html",
    }
    for ext, lang in mapping.items():
        if lower.endswith(ext):
            return lang
    return "text"


def truncate_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n…"


def result_as_text(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, str):
        return result
    if isinstance(result, (int, float, bool)):
        return str(result)
    if isinstance(result, list):
        if all(isinstance(item, str) for item in result):
            return "\n".join(result)
        return None
    if isinstance(result, dict):
        for key in ("content", "output", "stdout", "message", "error", "text", "result"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value
        stderr = result.get("stderr")
        if isinstance(stderr, str) and stderr.strip():
            return stderr
    return None


def result_as_path_list(result: Any, *, max_items: int = 100) -> tuple[list[str], int]:
    if isinstance(result, list) and all(isinstance(item, str) for item in result):
        return result[:max_items], len(result)
    text = result_as_text(result)
    if not text:
        return [], 0
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:max_items], len(lines)


def summarize_input_fields(
    tool_input: dict[str, Any] | None,
    *,
    max_fields: int = 6,
    max_value_len: int = 120,
) -> list[tuple[str, str]]:
    data = as_dict(tool_input)
    rows: list[tuple[str, str]] = []
    for key, value in data.items():
        if key in {"input", "arguments", "params"} and isinstance(value, dict):
            continue
        if isinstance(value, (dict, list)):
            rendered = f"({type(value).__name__}, {len(value)} items)"
        else:
            rendered = truncate_text(str(value), max_value_len)
        rows.append((str(key), rendered))
        if len(rows) >= max_fields:
            break
    return rows
