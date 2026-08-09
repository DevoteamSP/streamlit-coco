"""Meaningful transcript cards for CoCo tools (compact expanders; no raw JSON by default)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_coco.ask_user import extract_questions
from streamlit_coco.clipboard import render_copy_button
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


def _card_label(
    item: dict[str, Any],
    *,
    family: ToolFamily,
    status: str,
    tool_input: dict[str, Any],
    tool_name: str,
) -> str:
    """One-line expander title: family · status · short meta."""
    bits = [f"**{family_label(family, tool_name)}** · {status_label(status)}"]

    if family == ToolFamily.ASK_USER:
        questions = extract_questions(tool_input)
        headers = [
            str(q.get("header") or q.get("question") or f"Question {idx + 1}")
            for idx, q in enumerate(questions)
        ]
        if headers:
            bits.append(", ".join(headers[:2]) + ("…" if len(headers) > 2 else ""))
    elif family == ToolFamily.SQL:
        rows, _text, total_rows = parse_sql_result_table(item.get("result"))
        if status == "completed" and total_rows is not None:
            shown = len(rows or [])
            if total_rows > shown:
                bits.append(f"{shown} of {total_rows} rows")
            else:
                bits.append(f"{total_rows} row{'s' if total_rows != 1 else ''}")
    elif family in {ToolFamily.READ, ToolFamily.WRITE, ToolFamily.EDIT}:
        path = extract_path(tool_input)
        if path:
            bits.append(f"`{path}`")
    elif family == ToolFamily.BASH:
        command = extract_command(tool_input)
        if command:
            bits.append(f"`{truncate_text(command, 48)}`")
    elif family == ToolFamily.GLOB:
        pattern = extract_pattern(tool_input)
        if pattern:
            bits.append(f"`{pattern}`")
        if status == "completed":
            _paths, total = result_as_path_list(item.get("result"))
            bits.append(f"{total} file{'s' if total != 1 else ''}")
    elif family == ToolFamily.GREP:
        pattern = extract_pattern(tool_input)
        path = extract_path(tool_input)
        if pattern:
            bits.append(f"`{pattern}`")
        if path:
            bits.append(f"in `{path}`")
        if status == "completed":
            text = result_as_text(item.get("result")) or ""
            count = len(_grep_match_lines(text)) if text.strip() else 0
            bits.append(f"{count} match{'es' if count != 1 else ''}")
    elif family == ToolFamily.GENERIC and tool_name:
        bits[0] = f"**{tool_name}** · {status_label(status)}"

    return " · ".join(bits)


def render_tool_card(
    item: dict[str, Any],
    *,
    show_tool_details: bool = True,
    show_copy: bool = True,
) -> None:
    """Dispatch a transcript tool item to a compact family-specific expander."""
    name = str(item.get("name") or "unknown")
    status = str(item.get("status") or "running")
    family = tool_family(name)
    tool_input = as_dict(item.get("input"))
    label = _card_label(
        item,
        family=family,
        status=status,
        tool_input=tool_input,
        tool_name=name,
    )
    # Keep the rail dense; only auto-open failures so they are not missed.
    expanded = status == "error"

    with st.expander(label, expanded=expanded):
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

        if show_copy:
            _maybe_copy_tool_payload(item, family=family, tool_input=tool_input)
        _maybe_raw_payload(item)


def _maybe_copy_tool_payload(
    item: dict[str, Any],
    *,
    family: ToolFamily,
    tool_input: dict[str, Any],
) -> None:
    """Offer clipboard copy for the most useful tool payload."""
    status = str(item.get("status") or "")
    if status not in {"completed", "error"}:
        return
    item_id = str(item.get("id") or item.get("tool_use_id") or id(item))
    text: str | None = None
    label = "Copy result"

    if family == ToolFamily.SQL:
        sql = extract_sql_text(tool_input)
        if sql:
            text, label = sql, "Copy SQL"
        else:
            text = result_as_text(item.get("result"))
    elif family == ToolFamily.BASH:
        command = extract_command(tool_input)
        result = result_as_text(item.get("result"))
        if result:
            text, label = result, "Copy output"
        elif command:
            text, label = command, "Copy command"
    elif family in {ToolFamily.READ, ToolFamily.GREP, ToolFamily.GENERIC}:
        text = result_as_text(item.get("result"))
    elif family == ToolFamily.WRITE:
        text = extract_content(tool_input)
        label = "Copy content"
    elif family == ToolFamily.EDIT:
        old, new = extract_old_new(tool_input)
        path = extract_path(tool_input)
        text = new or unified_diff(old, new, path=path) or old
        label = "Copy after"
    elif family == ToolFamily.GLOB:
        paths, _total = result_as_path_list(item.get("result"))
        if paths:
            text = "\n".join(paths)
            label = "Copy paths"

    if text:
        render_copy_button(text, key=f"coco_copy_tool_{item_id}", label=label)


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
            st.dataframe(rows, width="stretch", hide_index=True)
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
            st.code(truncate_text(text), language="text")


def _render_glob(
    item: dict[str, Any],
    tool_input: dict[str, Any],
    *,
    status: str,
    show_tool_details: bool,
) -> None:
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
    # Full match dump is noisy — preview only in debug mode.
    if is_debug_mode():
        preview = matches[:20]
        st.code(
            "\n".join(truncate_text(line, 160) for line in preview),
            language="text",
        )
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
