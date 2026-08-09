"""High-level Streamlit helpers to keep app code small."""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any, Literal

import streamlit as st

from streamlit_coco.diagnostics import CocoEnvironment, check_environment
from streamlit_coco.errors import CocoError, CwdUploadError
from streamlit_coco.options import CocoOptions
from streamlit_coco.session import CocoRunStatus, CocoSession
from streamlit_coco.ui import send_prompt
from streamlit_coco.upload import (
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_MAX_BYTES,
    DEFAULT_UPLOAD_SUBDIR,
    OverwriteMode,
    UploadedPath,
    format_upload_prompt,
    list_cwd_uploads,
    upload_to_cwd,
)


def _extensions_from_file_type(file_type: str | Sequence[str] | None) -> list[str] | frozenset[str]:
    if file_type is None:
        return DEFAULT_ALLOWED_EXTENSIONS
    types = [file_type] if isinstance(file_type, str) else list(file_type)
    return [ext if str(ext).startswith(".") else f".{ext}" for ext in types]


def render_environment_status(
    env: CocoEnvironment | None = None,
    *,
    connection: str | None = None,
    stacked: bool = False,
    show_title: bool = True,
) -> CocoEnvironment:
    """Render SDK / CLI / Snowflake readiness. Probes the environment when ``env`` is omitted."""
    status = env or check_environment(connection=connection)
    if show_title:
        st.subheader("CoCo environment")

    def _sdk_block() -> None:
        if status.sdk_installed:
            st.success(f"SDK installed · `{status.sdk_version or 'unknown'}`")
        else:
            st.error("SDK missing — `pip install cortex-code-agent-sdk`")

    def _cli_block() -> None:
        if status.cli_ok:
            st.success(f"CLI · `{status.cli_version}`")
            if status.cli_path:
                st.caption(status.cli_path)
        elif status.cli_path:
            st.warning("CLI found but `--version` failed")
            st.caption(status.cli_path)
        else:
            st.error("CLI not on PATH (`cortex`)")

    def _snowflake_block() -> None:
        display = status.snowflake_config_display
        if display:
            # Single line with the path (filename appears once inside it).
            st.success(f"Snowflake config · `{display}`")
            st.caption(f"Connection: `{status.connection_hint}`")
        else:
            st.warning("No `~/.snowflake/connections.toml` (or config.toml)")

    if stacked:
        _sdk_block()
        _cli_block()
        _snowflake_block()
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            _sdk_block()
        with c2:
            _cli_block()
        with c3:
            _snowflake_block()

    return status


def get_or_create_session(
    options: CocoOptions,
    *,
    key: str = "coco",
    sync_options: bool = True,
) -> CocoSession:
    """Return a ``CocoSession`` stored in ``st.session_state[key]``."""
    session = st.session_state.get(key)
    if session is None or not isinstance(session, CocoSession):
        session = CocoSession(options=options, key=key)
        st.session_state[key] = session
    elif sync_options:
        session.sync_options(options)
    return session


def render_start_gate(
    options: CocoOptions,
    *,
    session_key: str = "coco",
    gate_key: str = "coco_started",
    title: str = "CoCo demo is ready to be instantiated",
    button_label: str = "Start CoCo Chat",
    body: str | None = None,
    warm_up: bool = True,
    env: CocoEnvironment | None = None,
) -> bool:
    """Landing screen with environment probe and a start button.

    Returns ``True`` when the user has started CoCo (caller continues).
    Returns ``False`` while still on the gate (caller should ``st.stop()``).
    """
    if gate_key not in st.session_state:
        st.session_state[gate_key] = False

    if st.session_state[gate_key]:
        return True

    status = render_environment_status(env, connection=options.connection)
    st.divider()
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"### {title}")
        st.write(
            body
            or (
                "Click below to create the Streamlit CoCo session, connect the Cortex Code "
                "CLI, and open the chat panel. Nothing starts until you confirm."
            )
        )
        if not status.ready:
            st.warning(
                "Fix the CoCo SDK / CLI issues above before starting — "
                "the chat may fail to connect."
            )
        if st.button(button_label, type="primary", use_container_width=True):
            st.session_state[gate_key] = True
            session = CocoSession(options=options, key=session_key)
            if warm_up:
                session.start()
            st.session_state[session_key] = session
            st.rerun()
    return False


def reset_session(
    options: CocoOptions,
    *,
    session_key: str = "coco",
    warm_up: bool = False,
) -> CocoSession:
    """Replace the stored session with a fresh one."""
    existing = st.session_state.get(session_key)
    if isinstance(existing, CocoSession):
        existing.reset()
        existing.close()
    session = CocoSession(options=options, key=session_key)
    if warm_up:
        session.start()
    st.session_state[session_key] = session
    return session


def stop_session(
    *,
    session_key: str = "coco",
    gate_key: str = "coco_started",
) -> None:
    """Tear down the session and return to the start gate."""
    existing = st.session_state.get(session_key)
    if isinstance(existing, CocoSession):
        existing.reset()
        existing.close()
    st.session_state.pop(session_key, None)
    st.session_state[gate_key] = False


def chat_input_bar(
    session: CocoSession,
    *,
    placeholder: str = "Ask CoCo…",
    connecting_placeholder: str = "Starting CoCo…",
    key: str | None = None,
    accept_file: bool | Literal["multiple"] = False,
    file_type: str | Sequence[str] | None = None,
    max_upload_size: int | None = None,
    upload_subdir: str = DEFAULT_UPLOAD_SUBDIR,
    upload_overwrite: OverwriteMode = "replace",
    inject_upload_paths: bool = True,
) -> str | None:
    """``st.chat_input`` wired for connect/run state; sends on submit.

    Stays enabled while CoCo is connecting (prompts are queued). Only a failed
    boot disables input. ``panel()`` triggers a full rerun when connect finishes
    so placeholder/status stay in sync.

    When ``accept_file`` is enabled (Streamlit supports attachments on
    ``st.chat_input``), files are written under ``cwd/<upload_subdir>/`` via
    :func:`streamlit_coco.upload_to_cwd` and optionally injected into the prompt.
    """
    connecting = session.status == CocoRunStatus.CONNECTING
    failed_boot = session.status == CocoRunStatus.ERROR and not session.is_ready
    chat_params = inspect.signature(st.chat_input).parameters
    kwargs: dict[str, Any] = {}
    if key is not None:
        kwargs["key"] = key
    if "submit_mode" in chat_params:
        kwargs["disabled"] = failed_boot
        kwargs["submit_mode"] = "disable" if session.is_running else "submit"
    else:
        # Streamlit < 1.59: no submit_mode — disable input while a turn is running.
        kwargs["disabled"] = failed_boot or session.is_running

    wants_files = bool(accept_file)
    if wants_files and "accept_file" in chat_params:
        kwargs["accept_file"] = accept_file
        if file_type is not None:
            kwargs["file_type"] = file_type
        if max_upload_size is not None and "max_upload_size" in chat_params:
            kwargs["max_upload_size"] = max_upload_size
    elif wants_files:
        st.caption("This Streamlit build does not support chat attachments; use `cwd_uploader`.")

    value = st.chat_input(
        connecting_placeholder if connecting else placeholder,
        **kwargs,
    )
    if not value:
        return None

    text = value
    files: list[Any] = []
    if not isinstance(value, str):
        text = str(getattr(value, "text", "") or "")
        raw_files = getattr(value, "files", None)
        if raw_files:
            files = list(raw_files)

    prompt_text = text.strip()
    if files:
        try:
            saved = upload_to_cwd(
                session,
                files,
                subdir=upload_subdir,
                overwrite=upload_overwrite,
                max_bytes=max_upload_size or DEFAULT_MAX_BYTES,
                allowed_extensions=_extensions_from_file_type(file_type),
            )
        except CwdUploadError as exc:
            st.error(str(exc))
            return None
        except CocoError as exc:
            st.error(str(exc))
            return None

        written = [item for item in saved if not item.skipped]
        if written:
            labels = ", ".join(f"`{item.relative}`" for item in written)
            st.caption(f"Saved to workspace · {labels}")
        if inject_upload_paths:
            prompt_text = format_upload_prompt(saved, user_text=prompt_text)
        elif not prompt_text and written:
            prompt_text = format_upload_prompt(saved, user_text="")

    if prompt_text:
        send_prompt(session, prompt_text)
        return prompt_text
    return None


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
