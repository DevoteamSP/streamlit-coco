"""``cwd_uploader``: the page's own uploader into the agent's working folder."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st

from streamlit_coco.errors import CwdUploadError
from streamlit_coco.options import CocoOptions
from streamlit_coco.session import CocoSession
from streamlit_coco.upload import (
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_MAX_BYTES,
    DEFAULT_UPLOAD_SUBDIR,
    OverwriteMode,
    UploadedPath,
    list_cwd_uploads,
    upload_to_cwd,
)


def _extensions_from_file_type(file_type: str | Sequence[str] | None) -> list[str] | frozenset[str]:
    if file_type is None:
        return DEFAULT_ALLOWED_EXTENSIONS
    types = [file_type] if isinstance(file_type, str) else list(file_type)
    return [ext if str(ext).startswith(".") else f".{ext}" for ext in types]


def cwd_uploader(
    target: CocoSession | CocoOptions | str,
    *,
    label: str = "Upload into agent workspace",
    subdir: str = DEFAULT_UPLOAD_SUBDIR,
    overwrite: OverwriteMode = "error",
    accept_multiple_files: bool = True,
    file_type: str | Sequence[str] | None = None,
    max_bytes: int | None = DEFAULT_MAX_BYTES,
    key: str = "coco_cwd_uploader",
    show_inventory: bool = True,
) -> list[UploadedPath]:
    """``st.file_uploader`` + :func:`upload_to_cwd` for app chrome / sidebar.

    Returns the list of :class:`~streamlit_coco.upload.UploadedPath` written on
    this run (empty when idle or on validation error).
    """
    type_arg: Any
    if file_type is not None:
        type_arg = file_type
    else:
        type_arg = sorted(ext.lstrip(".") for ext in DEFAULT_ALLOWED_EXTENSIONS)

    uploaded = st.file_uploader(
        label,
        type=type_arg,
        accept_multiple_files=accept_multiple_files,
        key=key,
        help=f"Files are saved under `{subdir}/` in the CoCo working directory.",
    )
    saved: list[UploadedPath] = []
    if uploaded:
        files = uploaded if isinstance(uploaded, list) else [uploaded]
        try:
            saved = upload_to_cwd(
                target,
                files,
                subdir=subdir,
                overwrite=overwrite,
                max_bytes=max_bytes,
                allowed_extensions=_extensions_from_file_type(file_type),
            )
            written = [item for item in saved if not item.skipped]
            if written:
                st.success("Saved · " + ", ".join(f"`{item.relative}`" for item in written))
        except CwdUploadError as exc:
            st.error(str(exc))
            saved = []

    if show_inventory:
        existing = list_cwd_uploads(target, subdir=subdir)
        if existing:
            st.caption(f"In `{subdir}/` · " + ", ".join(f"`{path.name}`" for path in existing))

    return saved
