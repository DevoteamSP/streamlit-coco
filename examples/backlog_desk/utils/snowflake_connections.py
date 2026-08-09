"""Discover Snowflake CLI connection names from ~/.snowflake (CoCo auth only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib

SNOWFLAKE_DIR = Path.home() / ".snowflake"
CONNECTIONS_TOML = SNOWFLAKE_DIR / "connections.toml"
CONFIG_TOML = SNOWFLAKE_DIR / "config.toml"


@dataclass(frozen=True)
class ConnectionSource:
    label: str
    path: Path


def list_connection_sources() -> list[ConnectionSource]:
    sources: list[ConnectionSource] = []
    if CONNECTIONS_TOML.is_file():
        sources.append(ConnectionSource("connections.toml", CONNECTIONS_TOML))
    if CONFIG_TOML.is_file():
        sources.append(ConnectionSource("config.toml", CONFIG_TOML))
    return sources


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def list_connections(source: ConnectionSource) -> list[str]:
    data = _load_toml(source.path)
    if source.label == "config.toml":
        conns = data.get("connections") or {}
        if isinstance(conns, dict):
            return sorted(str(k) for k in conns.keys())
        return []
    return sorted(str(k) for k, v in data.items() if isinstance(v, dict))


def default_connection_name(source: ConnectionSource) -> str | None:
    if source.label != "config.toml":
        return None
    data = _load_toml(source.path)
    name = data.get("default_connection_name")
    return str(name) if name else None
