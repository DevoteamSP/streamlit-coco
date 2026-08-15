"""Start / stop a child Streamlit app and scrape its process log.

Disk is the source of truth (``.preview.pid``, ``.preview.port``, ``.preview.log``)
so a host rerun can recover a running preview. No Streamlit import — safe for
unit tests. Do not point ``app_dir`` at the host app itself.
"""

from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PORT_LO = 8511
DEFAULT_PORT_HI = 8520
_START_WAIT_S = 15.0
_LOG_TS = re.compile(r"^\d{4}-\d{2}-\d{2} ")


def pid_file(app_dir: Path) -> Path:
    return Path(app_dir) / ".preview.pid"


def port_file(app_dir: Path) -> Path:
    return Path(app_dir) / ".preview.port"


def log_file(app_dir: Path) -> Path:
    return Path(app_dir) / ".preview.log"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _port_free(port: int, *, address: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex((address, port)) != 0


def _listening_pids(port: int) -> set[int]:
    try:
        out = subprocess.check_output(  # noqa: S603
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    pids: set[int] = set()
    for line in out.split():
        try:
            pids.add(int(line))
        except ValueError:
            pass
    return pids


def pick_free_port(
    *,
    lo: int = DEFAULT_PORT_LO,
    hi: int = DEFAULT_PORT_HI,
    preferred: int | None = None,
    address: str = "127.0.0.1",
) -> int:
    candidates: list[int] = []
    if preferred is not None:
        candidates.append(preferred)
    candidates.extend(p for p in range(lo, hi + 1) if p != preferred)
    for port in candidates:
        if _port_free(port, address=address):
            return port
    raise RuntimeError(f"No free preview port in {lo}–{hi}.")


def _read_pid(app_dir: Path) -> int | None:
    pf = pid_file(app_dir)
    if not pf.is_file():
        return None
    try:
        pid = int(pf.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    return pid if pid else None


def _read_port(app_dir: Path) -> int | None:
    pf = port_file(app_dir)
    if not pf.is_file():
        return None
    try:
        port = int(pf.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    return port if port else None


def preview_running(app_dir: Path) -> bool:
    pid = _read_pid(app_dir)
    return bool(pid and _pid_alive(pid))


def preview_url(app_dir: Path, *, address: str = "127.0.0.1") -> str | None:
    if not preview_running(app_dir):
        return None
    port = _read_port(app_dir)
    if port is None:
        return None
    return f"http://{address}:{port}"


def stop_app_preview(app_dir: Path) -> None:
    dest = Path(app_dir)
    pid = _read_pid(dest)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
    pf = pid_file(dest)
    if pf.is_file():
        try:
            old = int(pf.read_text(encoding="utf-8").strip())
            os.kill(old, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        pf.unlink(missing_ok=True)
    port_file(dest).unlink(missing_ok=True)


def _reclaim_port(port: int, app_dir: Path) -> None:
    holders = _listening_pids(port)
    if not holders:
        return
    ours: set[int] = set()
    pid = _read_pid(app_dir)
    if pid:
        ours.add(pid)
    for held in holders & ours:
        try:
            os.kill(held, signal.SIGTERM)
        except (OSError, ValueError):
            pass


def start_app_preview(
    app_dir: Path,
    *,
    port: int | None = None,
    address: str = "127.0.0.1",
    env: dict[str, str] | None = None,
    script_name: str = "streamlit_app.py",
) -> str:
    """Launch ``streamlit run <script>`` in ``app_dir``; return the local URL."""
    dest = Path(app_dir)
    script = dest / script_name
    if not script.is_file():
        raise FileNotFoundError(f"Generated app missing: {script}")

    stop_app_preview(dest)
    time.sleep(0.25)
    chosen = pick_free_port(preferred=port, address=address) if port is None else port
    if not _port_free(chosen, address=address):
        _reclaim_port(chosen, dest)
        time.sleep(1.0)
    if not _port_free(chosen, address=address):
        raise RuntimeError(f"Port {chosen} is already in use.")

    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    child_env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script),
        "--server.port",
        str(chosen),
        "--server.headless",
        "true",
        "--server.address",
        address,
        "--browser.gatherUsageStats",
        "false",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]
    log_path = log_file(dest)
    dest.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(dest),
        env=child_env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_file(dest).write_text(str(proc.pid), encoding="utf-8")
    port_file(dest).write_text(str(chosen), encoding="utf-8")
    deadline = time.time() + _START_WAIT_S
    while time.time() < deadline and _port_free(chosen, address=address):
        if proc.poll() is not None:
            tail = preview_log_tail(dest, n=12)
            raise RuntimeError(
                "Preview process exited immediately." + (f"\n{tail}" if tail else "")
            )
        time.sleep(0.15)

    if _port_free(chosen, address=address):
        stop_app_preview(dest)
        tail = preview_log_tail(dest, n=12)
        raise RuntimeError(
            f"Preview did not bind port {chosen} in {_START_WAIT_S:.0f}s."
            + (f"\n{tail}" if tail else "")
        )
    return f"http://{address}:{chosen}"


def preview_log_tail(app_dir: Path, *, n: int = 40) -> str:
    path = log_file(app_dir)
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n:])


def last_preview_exception(app_dir: Path) -> str | None:
    """Return the current traceback from ``.preview.log``, if the app is failing.

    Streamlit writes ``Uncaught app exception`` + a traceback to the process
    log. A later timestamped line (successful rerun) means the error is stale.
    """
    path = log_file(app_dir)
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = None
    for i in range(len(lines) - 1, -1, -1):
        if (
            "Traceback (most recent call last):" in lines[i]
            or "Uncaught app exception" in lines[i]
        ):
            start = i
            break
    if start is None:
        return None
    end = start
    for i in range(start + 1, len(lines)):
        if _LOG_TS.match(lines[i]) and "Uncaught app exception" not in lines[i]:
            return None
        end = i
    return "\n".join(lines[start : end + 1]).strip()[:4000]


def default_fix_prompt(traceback: str, app_dir: Path) -> str:
    name = Path(app_dir).name
    body = (traceback or "").strip() or (
        "(no traceback in .preview.log — inspect the preview UI and fix "
        f"`{name}/streamlit_app.py`)"
    )
    return (
        f"The Streamlit app under `{name}/` is running and raised this exception.\n\n"
        f"```\n{body}\n```\n\n"
        f"Read `{name}/streamlit_app.py` and nearby files. Fix the exception. "
        "Use Write / Edit. After fixing, say what you changed.\n"
    )
