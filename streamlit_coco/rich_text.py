"""Rich markdown helpers — fenced code blocks with language highlighting."""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE_RE = re.compile(
    r"```([^\n`]*)\n(.*?)```",
    re.DOTALL,
)

_LANG_ALIASES: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "ts": "typescript",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "yml": "yaml",
    "md": "markdown",
    "plaintext": "text",
    "txt": "text",
    "": "text",
}


@dataclass(frozen=True)
class MarkdownSegment:
    """One slice of assistant/user content."""

    kind: str  # "markdown" | "code"
    text: str
    language: str | None = None


def normalize_fence_language(raw: str | None) -> str:
    """Map a fence info string to a Streamlit ``st.code`` language id."""
    token = (raw or "").strip().split()[0] if (raw or "").strip() else ""
    token = token.lower().lstrip(".")
    return _LANG_ALIASES.get(token, token or "text")


def split_markdown_fences(text: str) -> list[MarkdownSegment]:
    """Split markdown into prose and fenced code segments (order preserved)."""
    if not text:
        return []
    segments: list[MarkdownSegment] = []
    pos = 0
    for match in _FENCE_RE.finditer(text):
        if match.start() > pos:
            prose = text[pos : match.start()]
            if prose:
                segments.append(MarkdownSegment(kind="markdown", text=prose))
        lang = normalize_fence_language(match.group(1))
        code = match.group(2)
        # Drop a single trailing newline that fences usually include.
        if code.endswith("\n"):
            code = code[:-1]
        segments.append(MarkdownSegment(kind="code", text=code, language=lang))
        pos = match.end()
    if pos < len(text):
        tail = text[pos:]
        if tail:
            segments.append(MarkdownSegment(kind="markdown", text=tail))
    if not segments:
        segments.append(MarkdownSegment(kind="markdown", text=text))
    return segments


def preview_text(text: str, *, limit: int | None) -> tuple[str, bool]:
    """Return ``(visible, truncated)`` cutting ``text`` to ``limit`` characters."""
    body = text or ""
    if limit is None or limit <= 0 or len(body) <= limit:
        return body, False
    return body[:limit].rstrip() + "…", True


def window_transcript(
    transcript: list,
    *,
    max_messages: int | None,
    extra: int = 0,
) -> tuple[list, int]:
    """Return ``(visible_items, hidden_count)`` for optional truncation.

    ``max_messages`` counts transcript items (user / assistant / tool / …).
    ``extra`` is additional items revealed via “load earlier”.
    """
    if max_messages is None or max_messages <= 0:
        return list(transcript), 0
    limit = max_messages + max(0, extra)
    if len(transcript) <= limit:
        return list(transcript), 0
    hidden = len(transcript) - limit
    return list(transcript[-limit:]), hidden
