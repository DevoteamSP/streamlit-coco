"""Inside the Native App: the connection of the service, the app's stage and the managed options.

Pure Python: no Streamlit. In a Snowpark Container Services service Snowflake provides the host and
account in the environment and a token in a file (`/snowflake/session/token`); the connector turns
it into a session, and that session's token is what the Cortex Agent SDK takes (the same as on a
laptop, see `streamlit_coco.managed.options_from_connection`). The service runs as the application:
the agent has the application's rights, not those of the person who opened the page.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from shop.stores import StageStore

TOKEN_FILE = Path("/snowflake/session/token")


def in_native_app(env: Mapping[str, str] | None = None) -> bool:
    """True when the service's spec says so (SKILLS_HUB_NATIVE=1)."""
    return (os.environ if env is None else env).get("SKILLS_HUB_NATIVE") == "1"


def stage_name(env: Mapping[str, str] | None = None) -> str:
    """DATABASE.SCHEMA.STAGE of the skills: the application's own stage."""
    env = os.environ if env is None else env
    database = env.get("SNOWFLAKE_DATABASE")
    if not database:
        raise RuntimeError("SNOWFLAKE_DATABASE is not set: not running as an application.")
    return ".".join(
        [
            database,
            env.get("SKILLS_STAGE_SCHEMA", "DATA"),
            env.get("SKILLS_STAGE", "SKILLS_STAGE"),
        ]
    )


def open_connection(
    env: Mapping[str, str] | None = None,
    token_file: Path = TOKEN_FILE,
    connect: Any = None,
):
    """A connector connection authenticated with the service's token (read each time: it is
    renewed by Snowflake)."""
    env = os.environ if env is None else env
    if connect is None:
        import snowflake.connector

        connect = snowflake.connector.connect
    try:
        host, account = env["SNOWFLAKE_HOST"], env["SNOWFLAKE_ACCOUNT"]
    except KeyError as error:
        raise RuntimeError(f"{error.args[0]} is not set: not running in a service.") from None
    return connect(
        host=host,
        account=account,
        authenticator="oauth",
        token=token_file.read_text(encoding="utf-8").strip(),
        database=env.get("SNOWFLAKE_DATABASE"),
    )


def managed_options(connection: Any, label: str = "this application"):
    """`ManagedOptions` that reads the session token of `connection` each time it is needed."""
    from cortex_agent_sdk.auth import SnowflakeSessionTokenAuth

    from streamlit_coco.managed import ManagedOptions

    return ManagedOptions(
        base_url=f"https://{connection.host}",
        auth=SnowflakeSessionTokenAuth(lambda: connection.rest.token),
        label=label,
        connection=connection,
    )


def connect(env: Mapping[str, str] | None = None, **kwargs: Any):
    """(managed options, the application's stage store). The caller closes
    `options.connection` when done."""
    connection = open_connection(env, **kwargs)
    return managed_options(connection), StageStore(connection, stage_name(env))
