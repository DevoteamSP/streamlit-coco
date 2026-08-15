"""BI → Semantic ports and thin wrappers around ``st_coco`` preview helpers."""

from __future__ import annotations

from pathlib import Path

from streamlit_coco import app_preview as _preview

DEFAULT_PORT = 8511
COCO_PORT = 8512

last_preview_exception = _preview.last_preview_exception
preview_log_tail = _preview.preview_log_tail

__all__ = [
    "COCO_PORT",
    "DEFAULT_PORT",
    "last_preview_exception",
    "port_for_dir",
    "preview_log_tail",
    "preview_running",
    "preview_url",
    "start_preview",
    "stop_preview",
    "variant_for_dir",
]


def variant_for_dir(app_dir: Path | None) -> str:
    if app_dir is not None and app_dir.name == "streamlit_dash_coco":
        return "coco"
    return "deterministic"


def port_for_dir(app_dir: Path | None) -> int:
    return COCO_PORT if variant_for_dir(app_dir) == "coco" else DEFAULT_PORT


def preview_url(app_dir: Path | None = None) -> str | None:
    if app_dir is None:
        return None
    return _preview.preview_url(app_dir)


def preview_running(app_dir: Path | None = None) -> bool:
    if app_dir is None:
        return False
    return _preview.preview_running(app_dir)


def stop_preview(app_dir: Path | None = None) -> None:
    if app_dir is None:
        return
    _preview.stop_app_preview(app_dir)


def start_preview(
    app_dir: Path,
    *,
    port: int | None = None,
    mode: str = "disconnected",
) -> str:
    chosen = port_for_dir(app_dir) if port is None else port
    return _preview.start_app_preview(
        app_dir,
        port=chosen,
        env={"TTS_DATA_MODE": mode},
    )
