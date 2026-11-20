"""Configuration wrapper for Cortex Code Agent SDK options."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from streamlit_coco.errors import SDKNotInstalledError

try:
    from cortex_agent_sdk.cortexcode import CortexCodeAgentOptions
except ImportError:  # pragma: no cover
    CortexCodeAgentOptions = None  # type: ignore[misc, assignment]

# Meta keys that are fine in contract files / IDEs but break CoCo structured-output
# validation (referencing tries to resolve `$schema` as an external URI and fails with
# `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`).
_SDK_SCHEMA_META_KEYS = frozenset({"$schema", "$id"})


def _schema_for_sdk(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``schema`` safe to pass as SDK ``output_format.schema``."""
    return {k: v for k, v in schema.items() if k not in _SDK_SCHEMA_META_KEYS}


@dataclass
class CocoOptions:
    """User-facing CoCo configuration."""

    connection: str | None = None
    cwd: str = "."
    model: str | None = None
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    permission_mode: str = "default"
    profile: str | None = None
    cli_path: str | None = None
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    hooks: dict[str, Any] = field(default_factory=dict)
    require_approval_for: list[str] | Callable[..., bool] = field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    max_turns: int | None = None
    approval_timeout_seconds: float = 600.0
    extra_sdk_options: dict[str, Any] = field(default_factory=dict)
    # A settings.json for the program (`cortex --config`); None: the user's own settings.
    settings_file: str | None = None

    def options_hash(self) -> str:
        import hashlib
        import json

        payload = {
            "connection": self.connection,
            "cwd": self.cwd,
            "model": self.model,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "permission_mode": self.permission_mode,
            "profile": self.profile,
            "cli_path": self.cli_path,
            "require_approval_for": (
                list(self.require_approval_for)
                if isinstance(self.require_approval_for, list)
                else "callable"
            ),
            "add_dirs": [
                str(path) for path in (self.extra_sdk_options or {}).get("add_dirs") or []
            ],
        }
        if self.settings_file:  # another file is another session; absent keeps the old hash
            payload["settings_file"] = str(self.settings_file)
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    def to_sdk_options(
        self,
        *,
        can_use_tool: Callable[..., Any] | None = None,
    ) -> Any:
        if CortexCodeAgentOptions is None:
            raise SDKNotInstalledError()

        # When can_use_tool is set, CoCo uses SDK-managed permissions. Passing a
        # partial --allowed-tools list blocks every other tool outright instead
        # of invoking the callback — so auto-allow is handled in Python instead.
        cli_allowed_tools = None if can_use_tool is not None else (self.allowed_tools or None)

        kwargs: dict[str, Any] = {
            "connection": self.connection,
            "cwd": self.cwd,
            "model": self.model,
            "allowed_tools": cli_allowed_tools,
            "disallowed_tools": self.disallowed_tools or None,
            "permission_mode": self.permission_mode,  # type: ignore[arg-type]
            "profile": self.profile,
            "cli_path": self.cli_path,
            "mcp_servers": self.mcp_servers or None,
            "hooks": self.hooks or None,
            "can_use_tool": can_use_tool,
            "max_turns": self.max_turns,
            "include_partial_messages": True,
        }
        if self.output_schema is not None:
            kwargs["output_format"] = {
                "type": "json_schema",
                "schema": _schema_for_sdk(self.output_schema),
            }
        kwargs.update(self.extra_sdk_options)
        if self.settings_file:
            # merged with the caller's own flags; the settings file wins for `config`
            kwargs["extra_args"] = {
                **(self.extra_sdk_options.get("extra_args") or {}),
                "config": os.path.expanduser(str(self.settings_file)),
            }
        return CortexCodeAgentOptions(**{k: v for k, v in kwargs.items() if v is not None})

    def tools_requiring_approval(self) -> Iterable[str]:
        value = self.require_approval_for
        if callable(value):
            return []
        return value

    def auto_allow_tools(self) -> list[str]:
        """Tools that may run without a user approval prompt."""
        approval = (
            {tool.lower() for tool in self.tools_requiring_approval()}
            if isinstance(self.require_approval_for, list)
            else set()
        )
        return [tool for tool in self.allowed_tools if tool.lower() not in approval]
