"""Tool name normalization and family detection ."""

from __future__ import annotations

from enum import Enum


class ToolFamily(str, Enum):
    ASK_USER = "ask_user"
    SQL = "sql"
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    BASH = "bash"
    GLOB = "glob"
    GREP = "grep"
    EXIT_PLAN = "exit_plan"
    GENERIC = "generic"


_FAMILY_BY_NORMALIZED: dict[str, ToolFamily] = {
    "askuserquestion": ToolFamily.ASK_USER,
    "sql": ToolFamily.SQL,
    "sqlexecute": ToolFamily.SQL,
    "sqlquery": ToolFamily.SQL,
    "snowflakesql": ToolFamily.SQL,
    "runsql": ToolFamily.SQL,
    "read": ToolFamily.READ,
    "write": ToolFamily.WRITE,
    "edit": ToolFamily.EDIT,
    "bash": ToolFamily.BASH,
    "shell": ToolFamily.BASH,
    "glob": ToolFamily.GLOB,
    "grep": ToolFamily.GREP,
    "exitplanmode": ToolFamily.EXIT_PLAN,
}


def normalize_tool_name(tool_name: str) -> str:
    """Lowercase tool name with separators removed for comparisons."""
    return "".join(ch for ch in tool_name.lower() if ch.isalnum())


def tool_family(tool_name: str) -> ToolFamily:
    """Map a tool name to its UI family."""
    return _FAMILY_BY_NORMALIZED.get(normalize_tool_name(tool_name), ToolFamily.GENERIC)


def is_ask_user_question(tool_name: str) -> bool:
    return tool_family(tool_name) == ToolFamily.ASK_USER


def is_sql_tool(tool_name: str) -> bool:
    return tool_family(tool_name) == ToolFamily.SQL


def is_exit_plan_mode(tool_name: str) -> bool:
    return tool_family(tool_name) == ToolFamily.EXIT_PLAN
