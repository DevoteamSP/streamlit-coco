"""Lightweight CoCo environment checks (no session / agent start)."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from streamlit_coco.errors import (
    CLINotFoundError,
    CLIProbeError,
    SDKNotInstalledError,
    SnowflakeConfigNotFoundError,
)


@dataclass(frozen=True)
class CocoEnvironment:
    """Result of :func:`check_environment`."""

    sdk_installed: bool
    sdk_version: str | None
    cli_path: str | None
    cli_version: str | None
    snowflake_config_file: str | None
    connection_hint: str | None

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
        path = Path(self.snowflake_config_file)
        try:
            return f"~/{path.relative_to(Path.home())}"
        except ValueError:
            return path.name


def check_environment(
    *,
    connection: str | None = None,
    cli_path: str | None = None,
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

    snowflake_dir = Path.home() / ".snowflake"
    connections = snowflake_dir / "connections.toml"
    legacy = snowflake_dir / "config.toml"
    if connections.is_file():
        snowflake_config_file = str(connections)
    elif legacy.is_file():
        snowflake_config_file = str(legacy)
    else:
        snowflake_config_file = None

    return CocoEnvironment(
        sdk_installed=sdk_installed,
        sdk_version=sdk_version,
        cli_path=resolved_cli,
        cli_version=cli_version,
        snowflake_config_file=snowflake_config_file,
        connection_hint=connection or "default",
    )


def require_environment(
    *,
    connection: str | None = None,
    cli_path: str | None = None,
    require_snowflake_config: bool = False,
) -> CocoEnvironment:
    """Like :func:`check_environment`, but raise typed errors when prerequisites fail."""
    env = check_environment(connection=connection, cli_path=cli_path)
    if not env.sdk_installed:
        raise SDKNotInstalledError()
    if not env.cli_path:
        raise CLINotFoundError()
    if not env.cli_ok:
        raise CLIProbeError(env.cli_path)
    if require_snowflake_config and not env.snowflake_config_found:
        raise SnowflakeConfigNotFoundError()
    return env
