"""Helpers for CoCo AskUserQuestion tool interactions."""

from __future__ import annotations

from typing import Any

from streamlit_coco.tool_names import is_ask_user_question, normalize_tool_name

OTHER_OPTION_LABEL = "Other..."

__all__ = [
    "OTHER_OPTION_LABEL",
    "build_answers_payload",
    "choice_labels_with_other",
    "extract_questions",
    "format_option_label",
    "is_ask_user_question",
    "is_other_choice",
    "normalize_tool_name",
    "option_is_free_form",
    "options_already_include_other",
    "resolve_selected_labels",
]


def extract_questions(tool_input: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return the questions list from an AskUserQuestion tool input."""
    if not isinstance(tool_input, dict):
        return []
    questions = tool_input.get("questions")
    if not isinstance(questions, list):
        return []
    return [q for q in questions if isinstance(q, dict)]


def build_answers_payload(
    questions: list[dict[str, Any]],
    answers: dict[str, str],
) -> dict[str, Any]:
    """Build the ``updated_input`` payload expected by the CoCo SDK."""
    return {"questions": questions, "answers": answers}


def format_option_label(option: dict[str, Any]) -> str:
    """Human-readable label for a question option."""
    label = str(option.get("label") or "").strip() or "Option"
    description = str(option.get("description") or "").strip()
    if description:
        return f"{label} — {description}"
    return label


def option_is_free_form(option: dict[str, Any]) -> bool:
    return bool(option.get("freeForm") or option.get("free_form"))


def options_already_include_other(options: list[dict[str, Any]]) -> bool:
    """True when the agent already provided an Other / free-form style choice."""
    return any(_is_other_style_option(opt) for opt in options)


def _is_other_style_option(option: dict[str, Any]) -> bool:
    """True for free-form / Other / Something else choices that belong at the end."""
    if option_is_free_form(option):
        return True
    label = str(option.get("label") or "").strip().lower().rstrip(".")
    return label in {
        "other",
        "other...",
        "something else",
        "none of the above",
        "type your own",
        "type your own feedback",
    }


def choice_labels_with_other(options: list[dict[str, Any]]) -> list[str]:
    """Display labels for widgets; free-form / Other choices always last."""
    primary: list[str] = []
    other_style: list[str] = []
    for opt in options:
        label = format_option_label(opt)
        if _is_other_style_option(opt):
            other_style.append(label)
        else:
            primary.append(label)
    labels = primary + other_style
    if options and not other_style:
        labels.append(OTHER_OPTION_LABEL)
    return labels


def is_other_choice(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip().lower().rstrip(".")
    return stripped == "other" or value == OTHER_OPTION_LABEL


def resolve_selected_labels(
    options: list[dict[str, Any]],
    selected: list[str] | str | None,
) -> list[str]:
    """Map widget selection(s) back to canonical option labels."""
    if selected is None:
        return []
    values = [selected] if isinstance(selected, str) else list(selected)
    labels_by_display = {format_option_label(opt): str(opt.get("label") or "") for opt in options}
    labels_by_label = {str(opt.get("label") or ""): str(opt.get("label") or "") for opt in options}
    resolved: list[str] = []
    for value in values:
        if is_other_choice(value):
            resolved.append(OTHER_OPTION_LABEL)
        elif value in labels_by_display:
            resolved.append(labels_by_display[value])
        elif value in labels_by_label:
            resolved.append(labels_by_label[value])
        elif value:
            resolved.append(str(value))
    return [label for label in resolved if label]
