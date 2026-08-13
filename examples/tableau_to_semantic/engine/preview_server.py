"""Start / stop a generated Streamlit app on a side port."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

PID_KEY = "tts_preview_pid"
PORT_KEY = "tts_preview_port"
URL_KEY = "tts_preview_url"
MODE_KEY = "tts_preview_mode"
DEFAULT_PORT = 8511
_START_WAIT_S = 15.0


def _pid_file(app_dir: Path) -> Path:
    return app_dir / ".preview.pid"


def _log_file(app_dir: Path) -> Path:
    return app_dir / ".preview.log"


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def preview_url() -> str | None:
    return st.session_state.get(URL_KEY)


def preview_running() -> bool:
    pid = st.session_state.get(PID_KEY)
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        st.session_state.pop(PID_KEY, None)
        return False


def stop_preview(app_dir: Path | None = None) -> None:
    pid = st.session_state.get(PID_KEY)
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except (OSError, ValueError):
            pass
    if app_dir:
        pf = _pid_file(app_dir)
        if pf.is_file():
            try:
                old = int(pf.read_text(encoding="utf-8").strip())
                os.kill(old, signal.SIGTERM)
            except (OSError, ValueError):
                pass
            pf.unlink(missing_ok=True)
    st.session_state.pop(PID_KEY, None)
    st.session_state.pop(URL_KEY, None)
    st.session_state.pop(PORT_KEY, None)


def start_preview(
    app_dir: Path,
    *,
    port: int = DEFAULT_PORT,
    mode: str = "disconnected",
) -> str:
    """Launch ``streamlit run streamlit_app.py``; returns the local URL."""
    stop_preview(app_dir)
    time.sleep(0.25)
    script = app_dir / "streamlit_app.py"
    if not script.is_file():
        raise FileNotFoundError(f"Generated app missing: {script}")
    if not _port_free(port):
        time.sleep(1.0)
    if not _port_free(port):
        raise RuntimeError(f"Port {port} is already in use.")

    env = os.environ.copy()
    env["TTS_DATA_MODE"] = mode
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script),
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.address",
        "127.0.0.1",
        "--browser.gatherUsageStats",
        "false",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]
    log_path = _log_file(app_dir)
    log_handle = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(app_dir),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _pid_file(app_dir).write_text(str(proc.pid), encoding="utf-8")
    deadline = time.time() + _START_WAIT_S
    while time.time() < deadline and _port_free(port):
        if proc.poll() is not None:
            tail = _log_tail(log_path)
            raise RuntimeError(
                "Preview process exited immediately." + (f"\n{tail}" if tail else "")
            )
        time.sleep(0.15)

    if _port_free(port):
        stop_preview(app_dir)
        tail = _log_tail(log_path)
        raise RuntimeError(
            f"Preview did not bind port {port} in {_START_WAIT_S:.0f}s."
            + (f"\n{tail}" if tail else "")
        )

    url = f"http://127.0.0.1:{port}"
    st.session_state[PID_KEY] = proc.pid
    st.session_state[PORT_KEY] = port
    st.session_state[URL_KEY] = url
    st.session_state[MODE_KEY] = mode
    return url


def _log_tail(path: Path, *, n: int = 12) -> str:
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n:])
