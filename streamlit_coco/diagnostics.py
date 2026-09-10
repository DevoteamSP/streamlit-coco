"""Lightweight CoCo environment checks (no session / agent start)."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from streamlit_coco.errors import (
    CLINotFoundError,
    CLIProbeError,
    SDKNotInstalledError,
    SnowflakeConfigNotFoundError,
)

DEFAULT_CONNECTIONS_TOML = "connections.toml"
LEGACY_CONFIG_TOML = "config.toml"


def _snowflake_dir() -> Path:
    return Path.home() / ".snowflake"


def _toml_sort_key(path: Path) -> tuple[int, str]:
    name = path.name
    if name == DEFAULT_CONNECTIONS_TOML:
        return (0, name)
    if name == LEGACY_CONFIG_TOML:
        return (1, name)
    return (2, name.lower())


def list_snowflake_toml_files() -> list[Path]:
    """``*.toml`` files in ``~/.snowflake/``, connections.toml then config.toml first."""
    directory = _snowflake_dir()
    if not directory.is_dir():
        return []
    files = [path for path in directory.glob("*.toml") if path.is_file()]
    return sorted(files, key=_toml_sort_key)


def _toml_loads(text: str) -> dict[str, Any]:
    try:
        import tomllib
    except ImportError:  # Python 3.10
        import tomli as tomllib  # type: ignore
    data = tomllib.loads(text)
    return data if isinstance(data, dict) else {}


def _home_display(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def resolve_snowflake_config_path(
    toml_file: str | os.PathLike[str] | None = None,
    *,
    must_exist: bool = True,
) -> Path | None:
    """Resolve a Snowflake connections TOML path.

    A bare filename (``connections.toml``) is looked up under ``~/.snowflake/``.
    Absolute or relative paths are used as given (``~`` expanded). When
    ``toml_file`` is omitted, use the only ``*.toml`` in ``~/.snowflake/``
    whatever its name; if several exist, prefer ``connections.toml`` then
    ``config.toml``.
    """
    snowflake_dir = _snowflake_dir()
    if toml_file is None:
        files = list_snowflake_toml_files()
        return files[0] if files else None

    raw = Path(os.path.expanduser(str(toml_file)))
    if not raw.is_absolute() and len(raw.parts) == 1:
        raw = snowflake_dir / raw.name
    if must_exist and not raw.is_file():
        return None
    return raw


def _connection_names_from_data(data: dict[str, Any], *, filename: str) -> list[str]:
    if filename == LEGACY_CONFIG_TOML:
        conns = data.get("connections") or {}
        if isinstance(conns, dict):
            return sorted(str(key) for key in conns)
        return []
    return sorted(str(key) for key, value in data.items() if isinstance(value, dict))


def list_snowflake_connections(
    toml_file: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Return Snowflake CLI connection names from a connections TOML file."""
    path = resolve_snowflake_config_path(toml_file)
    if path is None:
        return []
    try:
        data = _toml_loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return _connection_names_from_data(data, filename=path.name)


def default_snowflake_connection_name(
    toml_file: str | os.PathLike[str] | None = None,
) -> str | None:
    """``default_connection_name`` from legacy ``config.toml``, else ``None``."""
    path = resolve_snowflake_config_path(toml_file)
    if path is None or path.name != LEGACY_CONFIG_TOML:
        return None
    try:
        data = _toml_loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    name = data.get("default_connection_name")
    return str(name) if name else None


def snowflake_config_missing_message(
    toml_file: str | os.PathLike[str] | None = None,
) -> str:
    """Warning text when the requested (or default) Snowflake TOML is missing."""
    if toml_file is not None:
        path = resolve_snowflake_config_path(toml_file, must_exist=False)
        if path is not None:
            return f"No `{_home_display(path)}`"
    return "No `~/.snowflake/*.toml` found"


@dataclass(frozen=True)
class CocoEnvironment:
    """Result of :func:`check_environment`."""

    sdk_installed: bool
    sdk_version: str | None
    cli_path: str | None
    cli_version: str | None
    snowflake_config_file: str | None
    connection_hint: str | None
    toml_file: str | None = None

    @property
    def snowflake_config_found(self) -> bool:
        return self.snowflake_config_file is not None

    @property
    def cli_ok(self) -> bool:
        return bool(self.cli_path and self.cli_version)

    @property
    def ready(self) -> bool:
        """True when the Python SDK and Cortex CLI look available."""
        return self.sdk_installed and self.cli_ok

    @property
    def snowflake_config_display(self) -> str | None:
        """Home-relative path such as ``~/.snowflake/connections.toml``."""
        if not self.snowflake_config_file:
            return None
        return _home_display(Path(self.snowflake_config_file))

    @property
    def snowflake_config_missing_label(self) -> str:
        return snowflake_config_missing_message(self.toml_file)


def check_environment(
    *,
    connection: str | None = None,
    cli_path: str | None = None,
    toml_file: str | os.PathLike[str] | None = None,
) -> CocoEnvironment:
    """Probe SDK, CLI, and Snowflake config without starting CoCo."""
    sdk_installed = False
    sdk_version: str | None = None
    try:
        import cortex_code_agent_sdk as sdk

        sdk_installed = True
        try:
            sdk_version = importlib.metadata.version("cortex-code-agent-sdk")
        except importlib.metadata.PackageNotFoundError:
            sdk_version = getattr(sdk, "__version__", None)
    except ImportError:
        pass

    resolved_cli = cli_path or os.environ.get("CORTEX_CODE_CLI_PATH") or shutil.which("cortex")
    cli_version: str | None = None
    if resolved_cli:
        try:
            completed = subprocess.run(
                [resolved_cli, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            output = (completed.stdout or completed.stderr or "").strip()
            cli_version = output.splitlines()[0] if output else None
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            cli_version = None

    requested = None if toml_file is None else str(toml_file)
    found = resolve_snowflake_config_path(toml_file)
    snowflake_config_file = str(found) if found is not None else None

    return CocoEnvironment(
        sdk_installed=sdk_installed,
        sdk_version=sdk_version,
        cli_path=resolved_cli,
        cli_version=cli_version,
        snowflake_config_file=snowflake_config_file,
        connection_hint=connection or "default",
        toml_file=requested,
    )


def require_environment(
    *,
    connection: str | None = None,
    cli_path: str | None = None,
    toml_file: str | os.PathLike[str] | None = None,
    require_snowflake_config: bool = False,
) -> CocoEnvironment:
    """Like :func:`check_environment`, but raise typed errors when prerequisites fail."""
    env = check_environment(connection=connection, cli_path=cli_path, toml_file=toml_file)
    if not env.sdk_installed:
        raise SDKNotInstalledError()
    if not env.cli_path:
        raise CLINotFoundError()
    if not env.cli_ok:
        raise CLIProbeError(env.cli_path)
    if require_snowflake_config and not env.snowflake_config_found:
        raise SnowflakeConfigNotFoundError()
    return env
