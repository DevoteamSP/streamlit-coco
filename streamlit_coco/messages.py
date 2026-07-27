"""Normalized CoCo event model and SDK/NDJSON parsing."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from cortex_code_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        StreamEvent,
        SystemMessage,
        TextBlock,
        ThinkingBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )
    from cortex_code_agent_sdk.types import Message
except ImportError:  # pragma: no cover - optional sdk extra
    AssistantMessage = ResultMessage = StreamEvent = SystemMessage = object  # type: ignore[misc, assignment]
    TextBlock = ThinkingBlock = ToolResultBlock = ToolUseBlock = UserMessage = object  # type: ignore[misc, assignment]
    Message = Any  # type: ignore[misc, assignment]


@dataclass
class CocoEvent:
    """JSON-serializable normalized event for UI and logging."""

    type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str | None = None
    delta: str | None = None
    name: str | None = None
    tool_use_id: str | None = None
    input: dict[str, Any] | None = None
    content: Any = None
    is_error: bool | None = None
    request_id: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    subtype: str | None = None
    duration_ms: int | None = None
    structured_output: Any = None
    cost_usd: float | None = None
    message: str | None = None
    code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CocoEvent:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        payload = {key: data[key] for key in known if key in data}
        return cls(**payload)


def _content_to_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(json.dumps(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _blocks_to_events(blocks: Any) -> list[CocoEvent]:
    """Map SDK content blocks (assistant or user) to normalized events."""
    events: list[CocoEvent] = []
    if not isinstance(blocks, list):
        return events
    for block in blocks:
        if isinstance(block, TextBlock):
            events.append(CocoEvent(type="assistant_text", text=block.text))
        elif isinstance(block, ThinkingBlock):
            events.append(CocoEvent(type="thinking", text=block.thinking))
        elif isinstance(block, ToolUseBlock):
            events.append(
                CocoEvent(
                    type="tool_use",
                    tool_use_id=block.id,
                    name=block.name,
                    input=block.input,
                )
            )
        elif isinstance(block, ToolResultBlock):
            events.append(
                CocoEvent(
                    type="tool_result",
                    tool_use_id=block.tool_use_id,
                    content=_content_to_str(block.content),
                    is_error=bool(block.is_error),
                )
            )
    return events


def message_to_events(message: Message) -> list[CocoEvent]:
    """Convert an SDK Message into zero or more CocoEvent objects."""
    events: list[CocoEvent] = []

    if isinstance(message, AssistantMessage):
        events.extend(_blocks_to_events(message.content))
        if message.error:
            events.append(
                CocoEvent(
                    type="error",
                    message=str(message.error),
                    code=str(message.error),
                )
            )
        return events

    # Tool results arrive as UserMessage blocks (not AssistantMessage).
    if isinstance(message, UserMessage):
        content = message.content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, ToolResultBlock):
                    events.append(
                        CocoEvent(
                            type="tool_result",
                            tool_use_id=block.tool_use_id,
                            content=_content_to_str(block.content),
                            is_error=bool(block.is_error),
                        )
                    )
        tool_use_result = getattr(message, "tool_use_result", None)
        if isinstance(tool_use_result, dict) and tool_use_result:
            # Fallback when results are only on tool_use_result and not as blocks.
            seen_ids = {event.tool_use_id for event in events if event.type == "tool_result"}
            for tool_id, payload in tool_use_result.items():
                if tool_id in seen_ids:
                    continue
                is_error = False
                content_payload: Any = payload
                if isinstance(payload, dict):
                    is_error = bool(payload.get("is_error") or payload.get("error"))
                    content_payload = (
                        payload.get("content")
                        or payload.get("result")
                        or payload.get("output")
                        or payload
                    )
                events.append(
                    CocoEvent(
                        type="tool_result",
                        tool_use_id=str(tool_id),
                        content=_content_to_str(content_payload),
                        is_error=is_error,
                    )
                )
        return events

    if isinstance(message, ResultMessage):
        events = [
            CocoEvent(
                type="result",
                subtype=message.subtype,
                duration_ms=message.duration_ms,
                structured_output=message.structured_output,
                cost_usd=message.total_cost_usd,
                is_error=message.is_error,
                metadata={
                    "num_turns": message.num_turns,
                    "session_id": message.session_id,
                    "result": message.result,
                },
            )
        ]
        if isinstance(message.result, str) and message.result.strip():
            events.insert(0, CocoEvent(type="assistant_text", text=message.result))
        return events

    if isinstance(message, SystemMessage):
        return [
            CocoEvent(
                type="system",
                subtype=message.subtype,
                metadata=dict(message.data),
            )
        ]

    if isinstance(message, StreamEvent):
        delta = _extract_stream_delta(message.event)
        return [
            CocoEvent(
                type="stream_event",
                delta=delta,
                metadata={"event": message.event, "session_id": message.session_id},
            )
        ]

    return events


def parse_ndjson_stream(text: str) -> list[CocoEvent]:
    """Parse a multi-line NDJSON stream from the cortex CLI."""
    events: list[CocoEvent] = []
    for line in text.splitlines():
        events.extend(parse_ndjson_line(line))
    return events


def parse_ndjson_line(line: str) -> list[CocoEvent]:
    """Parse a single NDJSON line from the cortex CLI stream."""
    line = line.strip()
    if not line:
        return []
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return []

    msg_type = payload.get("type")
    if msg_type == "assistant":
        return _ndjson_content_blocks(
            payload.get("message", {}).get("content", []),
            include_text=True,
        )

    if msg_type == "user":
        # Tool results are typically user-role messages with tool_result blocks.
        message = payload.get("message") or payload
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            return _ndjson_content_blocks(content, include_text=False)
        return []

    if msg_type == "result":
        return [
            CocoEvent(
                type="result",
                subtype=payload.get("subtype"),
                duration_ms=payload.get("duration_ms"),
                structured_output=payload.get("structured_output"),
                cost_usd=payload.get("total_cost_usd"),
                is_error=payload.get("is_error"),
                metadata={
                    "num_turns": payload.get("num_turns"),
                    "session_id": payload.get("session_id"),
                    "result": payload.get("result"),
                },
            )
        ]

    if msg_type == "stream_event":
        event_payload = payload.get("event") or {}
        return [
            CocoEvent(
                type="stream_event",
                delta=_extract_stream_delta(event_payload),
                metadata={"event": event_payload},
            )
        ]

    if msg_type == "system":
        return [
            CocoEvent(
                type="system",
                subtype=payload.get("subtype"),
                metadata=payload.get("data") or {},
            )
        ]

    return []


def _ndjson_content_blocks(blocks: Any, *, include_text: bool) -> list[CocoEvent]:
    events: list[CocoEvent] = []
    if not isinstance(blocks, list):
        return events
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            if include_text:
                events.append(CocoEvent(type="assistant_text", text=block.get("text", "")))
        elif block_type == "thinking":
            events.append(CocoEvent(type="thinking", text=block.get("thinking", "")))
        elif block_type == "tool_use":
            events.append(
                CocoEvent(
                    type="tool_use",
                    tool_use_id=block.get("id"),
                    name=block.get("name"),
                    input=block.get("input") or {},
                )
            )
        elif block_type == "tool_result":
            events.append(
                CocoEvent(
                    type="tool_result",
                    tool_use_id=block.get("tool_use_id"),
                    content=_content_to_str(block.get("content")),
                    is_error=block.get("is_error"),
                )
            )
    return events


def permission_request_event(
    request_id: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> CocoEvent:
    return CocoEvent(
        type="permission_request",
        request_id=request_id,
        tool_name=tool_name,
        tool_input=tool_input,
    )


def _extract_stream_delta(event: dict[str, Any]) -> str | None:
    if not event:
        return None

    delta = event.get("delta")
    if isinstance(delta, dict):
        text = delta.get("text")
        if isinstance(text, str) and text:
            return text
        partial = delta.get("partial_json") or delta.get("thinking")
        if isinstance(partial, str) and partial:
            return partial

    if isinstance(delta, str) and delta:
        return delta

    # Anthropic-style content_block_delta payloads.
    if event.get("type") == "content_block_delta" and isinstance(delta, dict):
        text = delta.get("text")
        if isinstance(text, str) and text:
            return text

    content_block = event.get("content_block")
    if isinstance(content_block, dict):
        text = content_block.get("text")
        if isinstance(text, str) and text:
            return text

    return None


def events_to_dataframe(events: list[CocoEvent]) -> Any:
    """Flatten events into a pandas DataFrame for audit views."""
    import pandas as pd

    return pd.DataFrame([event.to_dict() for event in events])


def _merge_assistant_text_into_transcript(
    transcript: list[dict[str, Any]],
    *,
    event_id: str,
    text: str,
) -> None:
    """Merge a full assistant text snapshot, skipping duplicates after streaming.

    Streaming turns typically emit the same reply three ways: ``stream_event``
    deltas, a final ``AssistantMessage`` snapshot, and ``ResultMessage.result``.
    Incremental chunks still concatenate; identical or already-applied snapshots
    are ignored, and a longer final snapshot replaces a partial stream.
    """
    if (
        transcript
        and transcript[-1].get("role") == "assistant"
        and transcript[-1].get("kind") == "text"
    ):
        existing = str(transcript[-1].get("content") or "")
        if not existing:
            transcript[-1]["content"] = text
            return
        if existing == text or existing.endswith(text):
            # Exact snapshot replay (or already concatenated duplicate).
            return
        if text.startswith(existing):
            # Final snapshot supersedes a partial stream.
            transcript[-1]["content"] = text
            return
        transcript[-1]["content"] = existing + text
        return

    transcript.append(
        {
            "id": event_id,
            "role": "assistant",
            "kind": "text",
            "content": text,
        }
    )


def append_events_to_transcript(
    transcript: list[dict[str, Any]],
    events: list[CocoEvent],
    *,
    show_thinking: bool = False,
    show_structured_inline: bool = True,
) -> list[CocoEvent]:
    """Merge streaming events into a UI transcript."""
    new_events: list[CocoEvent] = []
    for event in events:
        if event.type == "thinking" and not show_thinking:
            continue

        if event.type == "assistant_text":
            text = event.text or event.delta or ""
            if not text:
                continue
            _merge_assistant_text_into_transcript(transcript, event_id=event.id, text=text)
            new_events.append(event)
            continue

        if event.type == "stream_event" and event.delta:
            # Deltas always append; dedup applies only to full assistant_text snapshots.
            if (
                transcript
                and transcript[-1].get("role") == "assistant"
                and transcript[-1].get("kind") == "text"
            ):
                transcript[-1]["content"] = transcript[-1].get("content", "") + event.delta
            else:
                transcript.append(
                    {
                        "id": event.id,
                        "role": "assistant",
                        "kind": "text",
                        "content": event.delta,
                    }
                )
            new_events.append(event)
            continue

        if event.type == "tool_use":
            transcript.append(
                {
                    "id": event.tool_use_id or event.id,
                    "role": "assistant",
                    "kind": "tool",
                    "name": event.name,
                    "input": event.input or {},
                    "status": "running",
                }
            )
            new_events.append(event)
            continue

        if event.type == "tool_result":
            for item in reversed(transcript):
                if item.get("kind") == "tool" and item.get("id") == event.tool_use_id:
                    item["status"] = "error" if event.is_error else "completed"
                    item["result"] = event.content
                    break
            new_events.append(event)
            continue

        if event.type == "permission_request":
            transcript.append(
                {
                    "id": event.request_id or event.id,
                    "role": "system",
                    "kind": "approval",
                    "tool_name": event.tool_name,
                    "tool_input": event.tool_input or {},
                    "status": "pending",
                }
            )
            new_events.append(event)
            continue

        if (
            event.type == "result"
            and event.structured_output is not None
            and show_structured_inline
        ):
            # Turn finished — never leave tools stuck on "Running" / progress captions.
            _finalize_running_tools(transcript, is_error=bool(event.is_error))
            transcript.append(
                {
                    "id": event.id,
                    "role": "assistant",
                    "kind": "structured_output",
                    "content": event.structured_output,
                }
            )
            new_events.append(event)
            continue

        if event.type == "result":
            _finalize_running_tools(transcript, is_error=bool(event.is_error))
            new_events.append(event)
            continue

        if event.type in {"error", "system"}:
            new_events.append(event)

    return new_events


def _finalize_running_tools(transcript: list[dict[str, Any]], *, is_error: bool) -> None:
    """Mark leftover ``running`` tool cards completed/failed when the turn ends.

    Progress captions (e.g. \"Searching content…\") must not remain after the
    assistant answer is shown — even if a ``tool_result`` event was missed.
    """
    final_status = "error" if is_error else "completed"
    for item in transcript:
        if item.get("kind") == "tool" and item.get("status") == "running":
            item["status"] = final_status
