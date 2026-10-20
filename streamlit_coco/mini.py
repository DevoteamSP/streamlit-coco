"""The floating window, off unless a classic mount is asked for it.

``chat``, ``panel`` and ``copilot_rail`` stay the 0.1.9 interface. Pass ``mini=True``
and the same call mounts Ask CoCo (``ask_coco``) instead. Calling ``ask_coco`` directly
does the same thing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from streamlit_coco.options import CocoOptions


def prompts_from_questions(
    example_questions: Sequence[Any] | None,
    *,
    deferred: bool = False,
) -> list | None:
    """Rail starter questions, as the window's first-screen prompts."""
    if not example_questions:
        return None
    prompts: list = []
    for item in example_questions:
        if isinstance(item, str):
            prompts.append({"title": item, "text": item, "fill": deferred})
            continue
        if isinstance(item, Mapping):
            title = item.get("title") or item.get("question") or item.get("text") or ""
            text = item.get("question") or item.get("text") or title
            prompts.append(
                {
                    "title": str(title),
                    "text": str(text),
                    "fill": bool(item.get("deferred", deferred)),
                }
            )
            continue
        if isinstance(item, Sequence):
            title = item[0]
            text = item[1] if len(item) > 1 else item[0]
            fill = bool(item[2]) if len(item) > 2 else deferred
            prompts.append({"title": str(title), "text": str(text), "fill": fill})
    return prompts or None


def options_for_window(options: CocoOptions | None) -> CocoOptions | None:
    """A copy ``ask_coco`` accepts.

    The window refuses ``allowed_tools``, ``disallowed_tools`` and
    ``require_approval_for``: those lists belong to a ``CocoSession``. The
    window's rights are its policy (the default folder policy when none is passed).
    """
    if options is None:
        return None
    return CocoOptions(
        connection=options.connection,
        cwd=options.cwd,
        model=options.model,
        permission_mode=options.permission_mode,
        profile=options.profile,
        cli_path=options.cli_path,
        mcp_servers=dict(options.mcp_servers or {}),
        output_schema=options.output_schema,
        max_turns=options.max_turns,
        approval_timeout_seconds=options.approval_timeout_seconds,
        extra_sdk_options=dict(options.extra_sdk_options or {}),
    )


def window_connection(session: Any) -> str | None:
    """The rail's Snowflake profile when that session is already connected."""
    if session is None or not getattr(session, "is_ready", False):
        return None
    name = getattr(getattr(session, "options", None), "connection", None)
    return name or None


def mount_mini(
    session: Any = None,
    *,
    key: str = "coco",
    options: CocoOptions | None = None,
    prompts: list | None = None,
    features: Any = None,
    labels: dict[str, str] | None = None,
    on_rail: Any = None,
) -> Any:
    """Mount the floating window for a classic session or ``CocoOptions``.

    ``on_rail`` draws a header icon that calls it and reruns the page.
    """
    from streamlit_coco.window import ask_coco

    opts = options
    cwd = "."
    if session is not None:
        opts = getattr(session, "options", None) or options
    if opts is not None and getattr(opts, "cwd", None):
        cwd = opts.cwd
    return ask_coco(
        cwd,
        key=key,
        options=options_for_window(opts),
        prompts=prompts,
        features=features,
        labels=labels,
        connection=window_connection(session),
        on_rail=on_rail,
    )
