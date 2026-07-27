"""Async query wrapper around the Cortex Code Agent SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from streamlit_coco.errors import SDKNotInstalledError
from streamlit_coco.messages import CocoEvent, message_to_events
from streamlit_coco.options import CocoOptions

try:
    from cortex_code_agent_sdk import query as sdk_query
except ImportError:  # pragma: no cover
    sdk_query = None  # type: ignore[assignment]


async def query(
    prompt: str,
    *,
    options: CocoOptions | None = None,
    output_schema: dict[str, Any] | None = None,
) -> AsyncIterator[CocoEvent]:
    """Run a single-turn CoCo query and yield normalized events."""
    if sdk_query is None:
        raise SDKNotInstalledError()

    opts = options or CocoOptions()
    if output_schema is not None:
        opts.output_schema = output_schema

    try:
        async for message in sdk_query(prompt=prompt, options=opts.to_sdk_options()):
            for event in message_to_events(message):
                yield event
    except Exception as exc:
        from streamlit_coco.errors import wrap_exception

        raise wrap_exception(exc, context="query") from exc
