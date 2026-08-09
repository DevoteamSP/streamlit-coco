"""Persist browser uploads under the CoCo working directory."""

from __future__ import annotations

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from streamlit_coco.errors import CwdUploadError
from streamlit_coco.options import CocoOptions

OverwriteMode = Literal["error", "replace", "skip"]

DEFAULT_UPLOAD_SUBDIR = "_uploads"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB
DEFAULT_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".txt",
        ".md",
        ".csv",
        ".tsv",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".sql",
        ".py",
        ".toml",
        ".xml",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".xlsx",
        ".xls",
        ".parquet",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
    }
)

_UNSAFE_NAME = re.compile(r"[^\w.\-]+", re.UNICODE)


@dataclass(frozen=True)
class UploadedPath:
    """One file written (or skipped) under ``cwd``."""

    path: Path
    relative: str
    name: str
    bytes_written: int
    overwritten: bool = False
    skipped: bool = False


def resolve_upload_cwd(target: str | Path | CocoOptions | Any) -> Path:
    """Resolve a writable absolute cwd from a path, options, or session."""
    if isinstance(target, CocoOptions):
        raw = target.cwd
    elif hasattr(target, "options") and isinstance(getattr(target, "options"), CocoOptions):
        raw = target.options.cwd
    else:
        raw = target
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    return path


def sanitize_upload_name(filename: str) -> str:
    """Return a basename-only safe filename (no path traversal)."""
    raw = (filename or "").strip()
    if not raw:
        raise CwdUploadError("Uploaded file has an empty name")
    # Drop any directory components (including Windows paths).
    name = Path(raw.replace("\\", "/")).name
    if not name or name in {".", ".."}:
        raise CwdUploadError(f"Unsafe uploaded filename: {filename!r}")
    cleaned = _UNSAFE_NAME.sub("_", name).strip()
    if not cleaned or cleaned in {".", ".."}:
        raise CwdUploadError(f"Unsafe uploaded filename: {filename!r}")
    return cleaned


def _read_file_bytes(file_obj: Any) -> tuple[str, bytes]:
    if isinstance(file_obj, tuple) and len(file_obj) == 2:
        name, data = file_obj
        if not isinstance(name, str):
            raise CwdUploadError("Tuple uploads must be (name: str, data: bytes)")
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not isinstance(data, (bytes, bytearray)):
            raise CwdUploadError(f"Unsupported upload payload type: {type(data).__name__}")
        return name, bytes(data)

    name = getattr(file_obj, "name", None)
    if not isinstance(name, str) or not name:
        raise CwdUploadError("Upload object is missing a file name")

    if hasattr(file_obj, "getvalue"):
        data = file_obj.getvalue()
    elif hasattr(file_obj, "read"):
        data = file_obj.read()
        # Rewind Streamlit UploadedFile-like objects when possible.
        seek = getattr(file_obj, "seek", None)
        if callable(seek):
            try:
                seek(0)
            except Exception:  # pragma: no cover - best effort
                pass
    else:
        raise CwdUploadError(f"Unsupported upload object type: {type(file_obj).__name__}")

    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, (bytes, bytearray)):
        raise CwdUploadError(f"Unsupported upload payload type: {type(data).__name__}")
    return name, bytes(data)


def _normalize_extensions(allowed_extensions: Collection[str] | None) -> frozenset[str] | None:
    if allowed_extensions is None:
        return None
    return frozenset(
        ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed_extensions
    )


def upload_to_cwd(
    target: str | Path | CocoOptions | Any,
    files: Sequence[Any] | Any | None,
    *,
    subdir: str = DEFAULT_UPLOAD_SUBDIR,
    overwrite: OverwriteMode = "error",
    max_bytes: int | None = DEFAULT_MAX_BYTES,
    allowed_extensions: Collection[str] | None = DEFAULT_ALLOWED_EXTENSIONS,
) -> list[UploadedPath]:
    """Write uploaded files under ``cwd/subdir`` and return saved paths.

    ``files`` may be a single upload, a sequence of Streamlit ``UploadedFile``
    objects, or ``(name, bytes)`` tuples. Paths are quarantined under ``subdir``
    (default ``_uploads``). Filenames are sanitized; path traversal is rejected.

    Overwrite policy:

    - ``\"error\"`` — raise :class:`CwdUploadError` if the destination exists
    - ``\"replace\"`` — overwrite existing files
    - ``\"skip\"`` — leave existing files untouched (``skipped=True``)
    """
    if overwrite not in {"error", "replace", "skip"}:
        raise CwdUploadError(f"Invalid overwrite mode: {overwrite!r}")

    if files is None:
        return []
    if isinstance(files, (str, bytes, bytearray)):
        raise CwdUploadError("Pass upload objects or (name, bytes) tuples, not raw strings")
    items: list[Any]
    is_upload_obj = hasattr(files, "getvalue") or hasattr(files, "read")
    if isinstance(files, Sequence) and not is_upload_obj:
        items = list(files)
    else:
        items = [files]
    if not items:
        return []

    cwd = resolve_upload_cwd(target)
    # Keep quarantine inside cwd (no absolute / parent subdir escape).
    sub = Path(subdir)
    if sub.is_absolute() or ".." in sub.parts:
        raise CwdUploadError(f"subdir must be a relative path under cwd, got {subdir!r}")
    dest_dir = (cwd / sub).resolve()
    try:
        dest_dir.relative_to(cwd)
    except ValueError as exc:
        raise CwdUploadError(f"subdir escapes cwd: {subdir!r}") from exc
    dest_dir.mkdir(parents=True, exist_ok=True)

    allowed = _normalize_extensions(allowed_extensions)
    results: list[UploadedPath] = []

    for file_obj in items:
        name, data = _read_file_bytes(file_obj)
        safe_name = sanitize_upload_name(name)
        suffix = Path(safe_name).suffix.lower()
        if allowed is not None and suffix not in allowed:
            raise CwdUploadError(
                f"Disallowed file extension for {safe_name!r} "
                f"(allowed: {', '.join(sorted(allowed))})"
            )
        if max_bytes is not None and len(data) > max_bytes:
            raise CwdUploadError(
                f"File {safe_name!r} is {len(data)} bytes; max allowed is {max_bytes}"
            )

        dest = (dest_dir / safe_name).resolve()
        try:
            dest.relative_to(dest_dir)
        except ValueError as exc:
            raise CwdUploadError(f"Refusing to write outside upload dir: {safe_name!r}") from exc

        exists = dest.exists()
        if exists and overwrite == "error":
            raise CwdUploadError(
                f"File already exists: {dest.relative_to(cwd).as_posix()} "
                "(pass overwrite='replace' or 'skip')"
            )
        if exists and overwrite == "skip":
            results.append(
                UploadedPath(
                    path=dest,
                    relative=dest.relative_to(cwd).as_posix(),
                    name=safe_name,
                    bytes_written=0,
                    overwritten=False,
                    skipped=True,
                )
            )
            continue

        dest.write_bytes(data)
        results.append(
            UploadedPath(
                path=dest,
                relative=dest.relative_to(cwd).as_posix(),
                name=safe_name,
                bytes_written=len(data),
                overwritten=exists,
                skipped=False,
            )
        )

    return results


def format_upload_prompt(
    paths: Sequence[UploadedPath],
    *,
    user_text: str = "",
    intro: str = "I uploaded the following file(s) into the agent workspace:",
) -> str:
    """Build a prompt that points the agent at saved upload paths."""
    saved = [item for item in paths if not item.skipped]
    if not saved and not user_text.strip():
        return ""
    lines: list[str] = []
    if saved:
        lines.append(intro)
        for item in saved:
            lines.append(f"- `{item.relative}`")
        lines.append("")
    text = user_text.strip()
    if text:
        lines.append(text)
    elif saved:
        lines.append("Please inspect these files and summarize what you find.")
    return "\n".join(lines).strip()


def list_cwd_uploads(
    target: str | Path | CocoOptions | Any,
    *,
    subdir: str = DEFAULT_UPLOAD_SUBDIR,
) -> list[Path]:
    """List files currently under the upload quarantine directory."""
    cwd = resolve_upload_cwd(target)
    dest_dir = (cwd / subdir).resolve()
    try:
        dest_dir.relative_to(cwd)
    except ValueError as exc:
        raise CwdUploadError(f"subdir escapes cwd: {subdir!r}") from exc
    if not dest_dir.is_dir():
        return []
    return sorted(path for path in dest_dir.iterdir() if path.is_file())
