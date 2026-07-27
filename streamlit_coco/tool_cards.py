"""Meaningful transcript cards for CoCo tools (no default JSON expanders)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_coco.ask_user import extract_questions
from streamlit_coco.debug import is_debug_mode
from streamlit_coco.sql_tool import extract_sql_text, parse_sql_result_table
from streamlit_coco.tool_extract import (
    as_dict,
    extract_command,
    extract_content,
    extract_old_new,
    extract_path,
    extract_pattern,
    extract_plan,
    language_for_path,
    result_as_path_list,
    result_as_text,
    summarize_input_fields,
    truncate_text,
    unified_diff,
)
from streamlit_coco.tool_names import ToolFamily, family_label, status_label, tool_family

_GREP_SUMMARY_PREFIXES = ("grepped:", "found ", "matches for", "searching ")


def _grep_match_lines(text: str) -> list[str]:
    """Match lines from Grep output, skipping tool summary headers."""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(lower.startswith(prefix) for prefix in _GREP_SUMMARY_PREFIXES):
            continue
        lines.append(stripped)
    return lines


def render_tool_card(
    item: dict[str, Any],
    *,
    show_tool_details: bool = True,
) -> None:
    """Dispatch a transcript tool item to a family-specific card."""
    name = str(item.get("name") or "unknown")
    status = str(item.get("status") or "running")
    family = tool_family(name)
    tool_input = as_dict(item.get("input"))

    with st.container(border=True):
        if family == ToolFamily.ASK_USER:
            _render_ask_user(item, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.SQL:
            _render_sql(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.READ:
            _render_read(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.WRITE:
            _render_write(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.EDIT:
            _render_edit(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.BASH:
            _render_bash(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.GLOB:
            _render_glob(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.GREP:
            _render_grep(item, tool_input, status=status, show_tool_details=show_tool_details)
        elif family == ToolFamily.EXIT_PLAN:
            _render_exit_plan(item, tool_input, status=status, show_tool_details=show_tool_details)
        else:
            _render_generic(
                item,
                tool_input,
                name=name,
                status=status,
                show_tool_details=show_tool_details,
            )

        _maybe_raw_payload(item)


def render_approval_preview(tool_name: str, tool_input: dict[str, Any] | None) -> None:
    """Meaningful preview inside an approval interaction (not raw JSON)."""
    family = tool_family(tool_name)
    data = as_dict(tool_input)

    if family == ToolFamily.SQL:
        sql = extract_sql_text(data)
        if sql:
            st.code(sql, language="sql")
        return
    if family == ToolFamily.READ:
        path = extract_path(data)
        if path:
            st.markdown(f"Read `{path}`")
        return
    if family == ToolFamily.WRITE:
        path = extract_path(data)
        content = extract_content(data)
        if path:
            st.markdown(f"Write `{path}`")
        if content:
            diff = unified_diff("", content, path=path)
            st.code(
                truncate_text(diff or content, 3500),
                language="diff" if diff else language_for_path(path),
            )
        return
    if family == ToolFamily.EDIT:
        path = extract_path(data)
        old, new = extract_old_new(data)
        if path:
            st.markdown(f"Edit `{path}`")
        diff = unified_diff(old, new, path=path) if (old or new) else ""
        if diff:
            st.code(truncate_text(diff, 3500), language="diff")
        else:
            lang = language_for_path(path)
            if old:
                st.caption("Before")
                st.code(truncate_text(old, 1500), language=lang)
            if new:
                st.caption("After")
                st.code(truncate_text(new, 1500), language=lang)
        return
    if family == ToolFamily.BASH:
        command = extract_command(data)
        if command:
            st.code(command, language="bash")
        return
    if family == ToolFamily.GLOB:
        pattern = extract_pattern(data)
        if pattern:
            st.markdown(f"Pattern `{pattern}`")
        return
    if family == ToolFamily.GREP:
        pattern = extract_pattern(data)
        path = extract_path(data)
        bits = [f"Pattern `{pattern}`"] if pattern else []
        if path:
            bits.append(f"in `{path}`")
        if bits:
            st.markdown(" · ".join(bits))
        return
    if family == ToolFamily.EXIT_PLAN:
        plan = extract_plan(data)
        if plan:
            st.markdown(plan)
        return

    fields = summarize_input_fields(data)
    for key, value in fields:
        st.caption(f"**{key}:** {value}")


def _header(family: ToolFamily, status: str, *meta: str, tool_name: str = "") -> None:
    bits = [f"**{family_label(family, tool_name)}** · {status_label(status)}"]
    bits.extend(m for m in meta if m)
    st.markdown(" · ".join(bits))


def _maybe_raw_payload(item: dict[str, Any]) -> None:
    if not is_debug_mode():
        return
    with st.expander("Raw tool payload", expanded=False):
        st.json(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "input": item.get("input") or {},
                "result": item.get("result"),
            }
        )


def _render_ask_user(item: dict[str, Any], *, status: str, show_tool_details: bool) -> None:
    questions = extract_questions(as_dict(item.get("input")))
    headers = [
        str(q.get("header") or q.get("question") or f"Question {idx + 1}")
        for idx, q in enumerate(questions)
    ]
    summary = ", ".join(headers) if headers else "clarifying question"
    _header(ToolFamily.ASK_USER, status, summary)
    if status == "running":
        st.info(f"Waiting for your answer — {summary}")
    elif status == "completed":
        st.caption(f"Answered — {summary}")
    elif status == "error":
        st.error(f"Question cancelled or failed — {summary}")


def _render_sql(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    sql = extract_sql_text(tool_input)
    rows, text_fallback, total_rows = parse_sql_result_table(item.get("result"))
    meta = []
    if status == "completed" and total_rows is not None:
        shown = len(rows or [])
        if total_rows > shown:
            meta.append(f"{shown} of {total_rows} rows")
        else:
            meta.append(f"{total_rows} row{'s' if total_rows != 1 else ''}")
    _header(ToolFamily.SQL, status, *meta)
    if sql:
        st.code(sql, language="sql")
    else:
        st.caption("No SQL statement in tool input.")
    if status == "running":
        st.caption("Executing query…")
        return
    if status == "error":
        st.error(text_fallback or str(item.get("result") or "SQL tool failed"))
        return
    if not show_tool_details:
        return
    if rows is not None:
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.caption("Query returned no rows.")
        return
    if text_fallback:
        st.text(truncate_text(text_fallback))


def _render_read(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    path = extract_path(tool_input)
    _header(ToolFamily.READ, status, f"`{path}`" if path else "")
    if status == "running":
        st.caption("Reading file…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Read failed")
        return
    if not show_tool_details:
        return
    text = result_as_text(item.get("result"))
    if text:
        st.code(truncate_text(text), language=language_for_path(path))
    else:
        st.caption("File read completed.")


def _render_write(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    path = extract_path(tool_input)
    content = extract_content(tool_input)
    _header(ToolFamily.WRITE, status, f"`{path}`" if path else "")
    if content and (show_tool_details or status == "running"):
        diff = unified_diff("", content, path=path)
        st.code(
            truncate_text(diff or content, 2500),
            language="diff" if diff else language_for_path(path),
        )
    if status == "running":
        st.caption("Writing file…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Write failed")


def _render_edit(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    path = extract_path(tool_input)
    old, new = extract_old_new(tool_input)
    _header(ToolFamily.EDIT, status, f"`{path}`" if path else "")
    if show_tool_details or status in {"running", "error"}:
        diff = unified_diff(old, new, path=path) if (old or new) else ""
        if diff:
            st.code(truncate_text(diff, 3500), language="diff")
        else:
            lang = language_for_path(path)
            if old:
                st.caption("Before")
                st.code(truncate_text(old, 1500), language=lang)
            if new:
                st.caption("After")
                st.code(truncate_text(new, 1500), language=lang)
    if status == "running":
        st.caption("Applying edit…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Edit failed")


def _render_bash(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    command = extract_command(tool_input)
    _header(ToolFamily.BASH, status)
    if command:
        st.code(command, language="bash")
    if status == "running":
        st.caption("Running command…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Command failed")
        return
    if show_tool_details:
        text = result_as_text(item.get("result"))
        if text:
            st.text(truncate_text(text))


def _render_glob(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    pattern = extract_pattern(tool_input)
    _header(ToolFamily.GLOB, status, f"`{pattern}`" if pattern else "")
    if status == "running":
        st.caption("Searching files…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Glob failed")
        return
    if not show_tool_details:
        return
    paths, total = result_as_path_list(item.get("result"))
    if total == 0:
        st.caption("No files found.")
        return
    st.caption(f"{total} file{'s' if total != 1 else ''}")
    if is_debug_mode():
        for path in paths[:20]:
            st.markdown(f"- `{path}`")
        if total > 20:
            st.caption(f"+{total - 20} more")


def _render_grep(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    pattern = extract_pattern(tool_input)
    path = extract_path(tool_input)
    meta = []
    if pattern:
        meta.append(f"`{pattern}`")
    if path:
        meta.append(f"in `{path}`")
    _header(ToolFamily.GREP, status, *meta)
    if status == "running":
        st.caption("Searching content…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or "Grep failed")
        return
    if not show_tool_details:
        return
    text = result_as_text(item.get("result"))
    if not text or not text.strip():
        st.caption("No matches.")
        return
    matches = _grep_match_lines(text)
    count = len(matches)
    if count == 0:
        st.caption("Done.")
        return
    st.caption(f"{count} match{'es' if count != 1 else ''}")
    # Full match dump is noisy in the small card — preview only in debug mode.
    if is_debug_mode():
        preview = matches[:20]
        st.text("\n".join(truncate_text(line, 160) for line in preview))
        if count > len(preview):
            st.caption(f"+{count - len(preview)} more")


def _render_exit_plan(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
    plan = extract_plan(tool_input)
    _header(ToolFamily.EXIT_PLAN, status)
    if plan and show_tool_details:
        st.markdown(truncate_text(plan, 6000))
    if status == "running":
        st.caption("Waiting for plan approval…")
    elif status == "error":
        st.error(result_as_text(item.get("result")) or "Plan rejected or failed")


def _render_generic(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    name: str,
    status: str,
    show_tool_details: bool,
) -> None:
    _header(ToolFamily.GENERIC, status, tool_name=name)
    fields = summarize_input_fields(tool_input)
    for key, value in fields:
        st.caption(f"**{key}:** {value}")
    if status == "running":
        st.caption("Running…")
        return
    if status == "error":
        st.error(result_as_text(item.get("result")) or f"{name} failed")
        return
    if not show_tool_details:
        return
    text = result_as_text(item.get("result"))
    if text:
        st.text(truncate_text(text))
    elif item.get("result") is not None:
        result = item.get("result")
        if isinstance(result, dict):
            st.caption(f"Result received ({len(result)} keys)")
        elif isinstance(result, list):
            st.caption(f"Result received ({len(result)} items)")
        else:
            st.caption("Result received.")
