"""Snowflake connections TOML helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from streamlit_coco.diagnostics import (
    check_environment,
    default_snowflake_connection_name,
    list_snowflake_connections,
    list_snowflake_toml_files,
    resolve_snowflake_config_path,
    snowflake_config_missing_message,
)

CONNECTIONS_TOML = """
[analytics]
account = "xy12345"

[dev]
account = "xy12345"
"""

CONFIG_TOML = """
default_connection_name = "dev"

[connections.analytics]
account = "a"

[connections.dev]
account = "b"
"""


def test_list_snowflake_connections_from_connections_toml(tmp_path: Path) -> None:
    path = tmp_path / "connections.toml"
    path.write_text(CONNECTIONS_TOML, encoding="utf-8")
    assert list_snowflake_connections(path) == ["analytics", "dev"]
    assert default_snowflake_connection_name(path) is None


def test_list_snowflake_connections_from_config_toml(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG_TOML, encoding="utf-8")
    assert list_snowflake_connections(path) == ["analytics", "dev"]
    assert default_snowflake_connection_name(path) == "dev"


def test_list_snowflake_connections_missing_file(tmp_path: Path) -> None:
    assert list_snowflake_connections(tmp_path / "gone.toml") == []


def test_resolve_bare_filename_under_snowflake_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snowflake = tmp_path / ".snowflake"
    snowflake.mkdir()
    target = snowflake / "team.toml"
    target.write_text("[prod]\naccount = 'x'\n", encoding="utf-8")
    monkeypatch.setattr("streamlit_coco.diagnostics._snowflake_dir", lambda: snowflake)
    assert resolve_snowflake_config_path("team.toml") == target
    assert list_snowflake_connections("team.toml") == ["prod"]


def test_resolve_auto_detect_prefers_connections_toml(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snowflake = tmp_path / ".snowflake"
    snowflake.mkdir()
    connections = snowflake / "connections.toml"
    connections.write_text("[a]\naccount = 'x'\n", encoding="utf-8")
    (snowflake / "config.toml").write_text(CONFIG_TOML, encoding="utf-8")
    monkeypatch.setattr("streamlit_coco.diagnostics._snowflake_dir", lambda: snowflake)
    assert resolve_snowflake_config_path() == connections
    assert list_snowflake_connections() == ["a"]


def test_resolve_auto_detect_falls_back_to_config_toml(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snowflake = tmp_path / ".snowflake"
    snowflake.mkdir()
    config = snowflake / "config.toml"
    config.write_text(CONFIG_TOML, encoding="utf-8")
    monkeypatch.setattr("streamlit_coco.diagnostics._snowflake_dir", lambda: snowflake)
    assert resolve_snowflake_config_path() == config
    assert list_snowflake_connections() == ["analytics", "dev"]


def test_resolve_auto_detect_uses_single_custom_named_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snowflake = tmp_path / ".snowflake"
    snowflake.mkdir()
    team = snowflake / "team.toml"
    team.write_text("[prod]\naccount = 'x'\n", encoding="utf-8")
    monkeypatch.setattr("streamlit_coco.diagnostics._snowflake_dir", lambda: snowflake)
    assert list_snowflake_toml_files() == [team]
    assert resolve_snowflake_config_path() == team
    assert list_snowflake_connections() == ["prod"]


def test_list_snowflake_toml_files_orders_known_names_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snowflake = tmp_path / ".snowflake"
    snowflake.mkdir()
    team = snowflake / "team.toml"
    config = snowflake / "config.toml"
    connections = snowflake / "connections.toml"
    team.write_text("[prod]\naccount = 'x'\n", encoding="utf-8")
    config.write_text(CONFIG_TOML, encoding="utf-8")
    connections.write_text(CONNECTIONS_TOML, encoding="utf-8")
    monkeypatch.setattr("streamlit_coco.diagnostics._snowflake_dir", lambda: snowflake)
    assert list_snowflake_toml_files() == [connections, config, team]


def test_check_environment_uses_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "custom.toml"
    path.write_text("[analytics]\naccount = 'x'\n", encoding="utf-8")
    env = check_environment(toml_file=path, connection="analytics")
    assert env.snowflake_config_file == str(path)
    assert env.toml_file == str(path)
    assert env.connection_hint == "analytics"
    assert env.snowflake_config_display is not None
    assert "custom.toml" in env.snowflake_config_display


def test_missing_toml_message_names_requested_file(tmp_path: Path) -> None:
    missing = tmp_path / "gone.toml"
    message = snowflake_config_missing_message(missing)
    assert "gone.toml" in message
    generic = snowflake_config_missing_message()
    assert "*.toml" in generic
