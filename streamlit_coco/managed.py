"""Ask CoCo, the managed agent: Snowflake's coding agent, by the Cortex Agent SDK (experimental).

Pure Python: no Streamlit. The agent runs in Snowflake (a sandbox with workspace and stage mounts),
not on this computer: no `cortex` program, no working folder. It is the second agent behind
backend.py, and it takes the same window:

    import streamlit_coco as st_coco
    managed = st_coco.ManagedOptions(account="myorg-myaccount", token=lambda: read_the_pat(),
                                     workspace_mounts=[{"name": "USER$ME.PUBLIC.DEFAULT$"}])
    st_coco.ask_coco(".", agent=st_coco.managed_agent(managed), connection="myorg-myaccount")

What is the same: the thread, the steps, the result, the stop, and the rights. Every call that asks
reaches the policy and the `Gate` and waits for Allow or Decline. The spec of the run always says
`permission_policy="always_ask"`: Snowflake's own `always_allow` is not offered, because it would
let the agent skip the gate. (The server still asks only about what it rates risky: see below.)

How an approval works there: the run pauses when a tool needs one (a `response.tool_use` with a
`permission` block of options: "Allow this command", "Allow all bash for this session", "Deny").
The stream ends, the gate asks the user, and the answer starts the next turn of the same thread
with a `permission_decision`. Only "Allow this command" is ever sent as an allow; a request without
it is declined (fail closed). The server asks only for what it classifies as risky: a command it
rates no risk (`echo hello`) runs without a request, so the policy sees what the server shows it.

What it does not have: a local folder (a call on a path of the sandbox is judged by the policy as
any other path, so it asks), questions and plans of the agent (Cortex Code's own tools), planning
only, and the program's session facts. The folder passed to `Conversation` is only the policy's.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from streamlit_coco.backend import CarryError
from streamlit_coco.cortex import Translator
from streamlit_coco.gate import EXPIRY, Gate

_LOG = logging.getLogger(__name__)
_PACKAGE = "pip install snowflake-cortex-agent-sdk"
# The only options this agent ever sends as an allow: for this one call. The server also offers
# "Allow all bash for this session" (a standing grant of its own): never chosen, the gate's own
# standing permission is the user's to give.
ALLOW = ("allow this command", "allow once")
_DENIALS = ("deny", "reject", "decline")
_STAGE_NAME = re.compile(r'^[A-Za-z0-9_$."]+$')


# `FolderPolicy(folder, words=SANDBOX_WORDS)`: the commands of the managed agent run in Snowflake's
# sandbox, not on this computer, and the request must say so.
SANDBOX_WORDS = {
    "ask_command": "Allow CoCo to run a command in the Snowflake sandbox?{undo}",
    "changes_command": "A command in the Snowflake sandbox",
    "covers_commands": "Any command, in the Snowflake sandbox, whatever it does.",
}


# `FolderPolicy(..., where=SANDBOX_WHERE)`: the request's "Where" line, in place of the name of a
# local folder the managed agent does not have.
SANDBOX_WHERE = "The Snowflake sandbox"

# What the window says of this agent in place of its defaults (a host's `labels=` still wins). The
# first screen must not say it reads project files of this computer.
LABELS = {
    "window.first.sub": (
        "It works in a Snowflake sandbox, not on this computer. It asks before it runs a command."
    ),
}


@dataclass
class ManagedOptions:
    """The managed coding agent: where it runs and what it may reach.

    account            "orgname-accountname" (the SDK derives the API URL), or give `base_url`
    token              a programmatic access token: a string, or a function returning it each time
    auth               instead of `token`: any authenticator of the SDK (OAuth, key pair, session)
    workspace_mounts   [{"name": "DB.SCHEMA.WORKSPACE", "mount_path": "/workspace"}]
    stage_mounts / stage_skills / disabled_skills   as the SDK's coding agent takes them
    models, instructions   the run's `models` and `instructions.system`
    upload_stage       DB.SCHEMA.STAGE: the files the user attaches in the window go to a folder of
                       this stage, mounted at `upload_mount` in the sandbox. The stage is read when
                       the first message is sent, so files go in before it (`connection` puts them)
    label              what the window shows as the account (default: the account)
    connection         a Snowflake connector connection that `auth` draws its token from: the agent
                       closes it with itself (`options_from_connection` sets it)
    """

    account: str | None = None
    token: str | Callable[[], str] | None = None
    auth: Any = None
    base_url: str | None = None
    workspace_mounts: list[dict] = field(default_factory=list)
    stage_mounts: list[dict] = field(default_factory=list)
    stage_skills: list[dict] = field(default_factory=list)
    disabled_skills: list[str] = field(default_factory=list)
    models: dict | None = None
    instructions: str | None = None
    label: str | None = None
    connection: Any = None
    upload_stage: str | None = None
    upload_mount: str = "/uploads"

    def spec(self) -> dict:
        """The coding agent of the conversation. `permission_policy` is not a field: always ask."""
        spec: dict[str, Any] = {
            "models": self.models or {"orchestration": "auto"},
            "permission_policy": "always_ask",
        }
        for key in ("workspace_mounts", "stage_mounts", "stage_skills", "disabled_skills"):
            if getattr(self, key):
                spec[key] = list(getattr(self, key))
        if self.upload_stage:
            if not _STAGE_NAME.match(self.upload_stage):
                raise ValueError("ManagedOptions.upload_stage is DATABASE.SCHEMA.STAGE.")
            mount = {"stage_name": self.upload_stage, "is_vstage": False}
            spec["stage_mounts"] = [
                *spec.get("stage_mounts", []),
                {**mount, "mount_path": self.upload_mount},
            ]
        if self.instructions:
            spec["instructions"] = self.instructions
        return spec

    def client(self):
        """The SDK's client; ValueError when there is no way to authenticate."""
        from cortex_agent_sdk import CortexAgentClient
        from cortex_agent_sdk.auth import PatAuth

        if not (self.account or self.base_url):
            raise ValueError("ManagedOptions needs an account (or a base_url).")
        if self.auth is None and self.token is None:
            raise ValueError("ManagedOptions needs a token or an auth.")
        return CortexAgentClient(
            account=self.account,
            base_url=self.base_url,
            auth=self.auth if self.auth is not None else PatAuth(self.token),
        )


def options_from_connection(
    profile: str, *, role: str | None = None, toml_file=None, **options: Any
) -> ManagedOptions:
    """`ManagedOptions` from a profile of ~/.snowflake: log in with it and hand the SDK that
    connection's session token (renewed by the connector). The connector reads the profile's
    secrets, never this code; of the file it reads only the key path, to give the connector the
    name it knows (`private_key_file`, for the `private_key_path` of Snowflake CLI and Cortex Code).

    role      the role of the session; the profile's own when None. A managed agent works with the
              rights of that role: give it the least that works (`PUBLIC` was enough to try).
    options   the other fields of `ManagedOptions`.
    """
    import os

    import snowflake.connector
    from cortex_agent_sdk.auth import SnowflakeSessionTokenAuth

    from streamlit_coco.diagnostics import _toml_loads, resolve_snowflake_config_path

    kwargs: dict[str, Any] = {"connection_name": profile}
    if role:
        kwargs["role"] = role
    path = resolve_snowflake_config_path(toml_file)
    if path is not None:
        try:
            data = _toml_loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        table = (data.get("connections") or data).get(profile)
        table = table if isinstance(table, dict) else {}
        key = table.get("private_key_path")
        if key and not table.get("private_key_file"):
            kwargs["private_key_file"] = os.path.expanduser(str(key))
    conn = snowflake.connector.connect(**kwargs)
    return ManagedOptions(
        base_url=f"https://{conn.host}",
        auth=SnowflakeSessionTokenAuth(lambda: conn.rest.token),
        label=options.pop("label", None) or profile,
        connection=conn,
        **options,
    )


def choose_option(options, allow: bool) -> str | None:
    """The option to send for the user's answer: "Allow this command" (one call) to allow; "Deny"
    (or an option that starts like a refusal) to decline. None when the request offers none."""
    for option in options:
        if option.strip().lower() in (ALLOW if allow else ("deny",)):
            return option
    if not allow:
        return next((o for o in options if o.strip().lower().startswith(_DENIALS)), None)
    return None


def permission_of(event: dict) -> tuple[str, tuple[str, ...]] | None:
    """(tool_use_id, options) of a tool use that waits for the user, else None. A verdict already
    given by the server, or an empty list of options, is not a question."""
    permission = event.get("permission")
    tool_use_id = event.get("tool_use_id")
    if event.get("event") != "response.tool_use" or not isinstance(permission, dict):
        return None
    raw = permission.get("options")
    options = tuple(o for o in raw if isinstance(o, str)) if isinstance(raw, list) else ()
    if not tool_use_id or not options or permission.get("verdict") in ("allow", "deny"):
        return None
    return str(tool_use_id), options


_INSTRUCTIONS = (
    "You are CoCo, an assistant inside an application. You run in Snowflake's sandbox: you cannot "
    "see the user's computer, and you do not know any folder on it. Work in the sandbox "
    "(its /workspace if one is mounted) and say so when a file the user names is not there.\n"
    "Answer in the language of the user's message.\n"
    "Before each group of tool calls, say one short sentence about what you are about to do. "
    "Do not narrate every small call. Never output private reasoning.\n"
    "The application asks the user for agreement before a command that acts. So call the tool; "
    'never ask "may I run this?" in your text and never paste a command for approval. Until it '
    "has run, speak of it as about to happen, never as done. If it is declined, say so plainly.\n"
    "You have no question tool and no plan tool: when you need a detail, ask in one short question "
    "in your answer.\n"
    "When your answer is data (a table, a query result, JSON), still end with one sentence of text "
    "that says what it shows.\n"
    "Name the files you talk about. In SQL, qualify every object name (DATABASE.SCHEMA.OBJECT).\n"
)
# Keys of the conversation's context that describe this computer: the agent is not told them.
_LOCAL_FACTS = ("instructions", "rights")


def build_prompt(text: str, ctx: dict) -> str:
    """The managed agent's instructions, the host's (`ctx["instructions"]`), the context as JSON,
    then the user's message. Nothing of this computer goes in: not the working folder (`scope` keeps
    its name only), not the rights of the folder policy."""
    extra = str(ctx.get("instructions") or "").strip()
    facts = {k: v for k, v in ctx.items() if k not in _LOCAL_FACTS}
    if isinstance(facts.get("scope"), dict):
        facts["scope"] = {"name": facts["scope"].get("name")}
    return (
        _INSTRUCTIONS
        + (extra + "\n" if extra else "")
        + "\nContext of this request: "
        + json.dumps(facts, ensure_ascii=False, default=str)
        + "\n\nUser message:\n"
        + text
    )


def _event(kind: str, **fields) -> SimpleNamespace:
    """What the Translator reads of an event, with what it does not need left empty."""
    base = dict(
        type=kind,
        text=None,
        metadata={},
        name=None,
        input=None,
        tool_use_id=None,
        content=None,
        is_error=False,
        message=None,
        subtype=None,
        structured_output=None,
    )
    return SimpleNamespace(**{**base, **fields})


def _text_of(content) -> str:
    if not isinstance(content, list):
        return "" if content is None else str(content)
    parts = []
    for item in content:
        if not isinstance(item, dict):
            parts.append(str(item))
        elif item.get("type") == "text":
            parts.append(str(item.get("text", "")))
        elif item.get("type") == "json":
            parts.append(json.dumps(item.get("json"), default=str))
    return "\n".join(parts)


class ManagedAgent:
    labels = LABELS

    def __init__(self, emit, options: ManagedOptions, client_factory=None) -> None:
        self.emit, self.options = emit, options
        self._folder, self._sent, self._uploaded = uuid.uuid4().hex[:10], False, False
        self._client_factory = client_factory or options.client
        self.gate = Gate(emit, EXPIRY)
        self.client = self.conversation = self._turn = None
        self.raw = self.reasoning = False
        self._translator = Translator()
        self._stopped = self._closed = self._running = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ the agent's surface

    def setup(self) -> dict | None:
        if not importlib.util.find_spec("cortex_agent_sdk"):
            return {"missing": "package", "command": _PACKAGE}
        return None

    def profiles(self) -> list[str]:
        return [self.options.label or self.options.account or self.options.base_url or "managed"]

    def connection_files(self) -> list[dict]:
        return []

    def session_facts(self) -> list[dict]:
        facts = [
            ("Account", self.options.account or self.options.base_url),
            ("Agent", "Snowflake managed coding agent"),
            ("Thread", getattr(self.conversation, "id", None)),
        ]
        return [{"label": label, "value": str(value)} for label, value in facts if value]

    @property
    def upload_root(self) -> str | None:
        """Where the attached files are in the sandbox, None when the host gave no upload stage."""
        if not self.options.upload_stage:
            return None
        return f"{self.options.upload_mount.rstrip('/')}/{self._folder}"

    def carry(self, paths: list[Path]) -> list[str]:
        """Put the attached files in this conversation's folder of the upload stage and return the
        paths the agent reads. Only before the first message: the sandbox reads the stage once."""
        options = self.options
        if not options.upload_stage or options.connection is None:
            raise CarryError("attach_sandbox_none")
        if self._sent:
            raise CarryError("attach_sandbox_started")
        try:
            options.spec()  # the stage's name is checked there
            cursor = options.connection.cursor()
            try:
                for path in paths:
                    local = str(Path(path).resolve()).replace("\\", "/").replace("'", "''")
                    cursor.execute(
                        f"PUT 'file://{local}' @{options.upload_stage}/{self._folder}/ "
                        "AUTO_COMPRESS=FALSE OVERWRITE=FALSE"
                    )
            finally:
                cursor.close()
        except Exception as error:  # noqa: BLE001 - the window says why, whatever it was
            why = str(error) or type(error).__name__
            raise CarryError("attach_sandbox_failed", why=why) from error
        self._uploaded = True
        return [f"{self.upload_root}/{Path(path).name}" for path in paths]

    def _remove_uploads(self) -> None:
        """The user's files do not stay on the stage after the conversation."""
        if not self._uploaded or self.options.connection is None:
            return
        try:
            cursor = self.options.connection.cursor()
            try:
                cursor.execute(f"REMOVE @{self.options.upload_stage}/{self._folder}/")
            finally:
                cursor.close()
        except Exception:  # noqa: BLE001
            _LOG.warning("Removing the uploaded files failed", exc_info=True)
        self._uploaded = False

    def connect(self, profile: str, cwd: str, file: str | None = None) -> None:
        self._remove_uploads()
        self._folder, self._sent = uuid.uuid4().hex[:10], False
        self._close_client()
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self) -> None:
        try:
            client = self._client_factory()
            conversation = client.conversations.create(
                agent={"type": "coding", "spec": self.options.spec()}
            )
        except Exception as error:  # noqa: BLE001 - the window shows why, whatever it was
            self.emit({"t": "connect_failed", "message": str(error) or type(error).__name__})
            return
        with self._lock:
            if self._closed:
                self._close(client)
                return
            self.client, self.conversation = client, conversation
        self.emit({"t": "connected"})

    def send(self, text: str, ctx: dict, policy) -> None:
        self.gate.begin(policy)
        self._stopped, self._sent = False, True
        self._translator = Translator(self.raw, self.reasoning)
        threading.Thread(
            target=self._run, args=(build_prompt(text, ctx), self._translator), daemon=True
        ).start()

    def decide(self, request_id: str, allow: bool, standing: bool = False) -> None:
        if standing:
            self.gate.answer(request_id, allow, True)
        else:
            self.gate.answer(request_id, allow)

    def revoke(self, permission_id: str) -> None:
        self.gate.revoke(permission_id)

    # The agent has no question or plan of its own (they are Cortex Code's tools): nothing waits.
    def answer(self, id: str, answers) -> None:
        pass

    def skip(self, id: str) -> None:
        pass

    def approve_plan(self, id: str) -> None:
        pass

    def decline_plan(self, id: str, reason: str = "") -> None:
        pass

    def set_planning(self, on: bool) -> None:
        pass

    def set_raw(self, on: bool) -> None:
        self.raw = self._translator.raw = bool(on)

    def set_reasoning(self, on: bool) -> None:
        self.reasoning = self._translator.reasoning = bool(on)

    def stop(self) -> None:
        self._stopped = True
        self.gate.cancel_all()
        turn = self._turn
        if turn is not None and self._running:  # a finished run has nothing to cancel
            try:
                turn.cancel()
            except Exception as error:  # noqa: BLE001 - the loop ends on the flag anyway
                if type(error).__name__ == "ConflictError":
                    # a run that waits for the user's answer is already over for the service
                    _LOG.debug("The managed run had nothing left to cancel")
                else:
                    _LOG.warning("Cancelling the managed run failed", exc_info=True)

    def close(self) -> None:
        self._closed = True
        self.stop()
        self._close_client()
        self._remove_uploads()
        self._close(self.options.connection)

    # ------------------------------------------------------------------ one message

    def _run(self, prompt: str, translator: Translator) -> None:
        self._running = True
        try:
            conversation = self.conversation
            if conversation is None:
                raise RuntimeError("The managed agent is not connected.")
            turn = conversation.send(prompt)
            while True:
                self._turn = turn
                pending, final = self._stream(turn, translator)
                if self._stopped:
                    self.emit({"t": "stopped"})
                    return
                if not pending:
                    break
                decisions = [self._decision(*p) for p in pending]
                if self._stopped:
                    self.emit({"t": "stopped"})
                    return
                turn = conversation.send_permission_decisions(decisions)
            for out in translator.feed(final):
                self.emit(out)
        except Exception as error:  # noqa: BLE001 - the conversation learns of it as of any turn
            if not self._stopped:
                self.emit(Translator.failure(str(error) or type(error).__name__))
        finally:
            self._running = False

    def _stream(self, turn, translator: Translator) -> tuple[list[tuple], SimpleNamespace]:
        """Feed the events of one turn to the window. Returns the tool uses that wait for the user,
        as (tool_use_id, tool name, input, options), and the result that ends the message."""
        pending, said, last = [], [], ""
        for event in turn.events():
            if self._stopped:
                break
            kind = event.get("event")
            fed = None
            if kind == "response.text.delta" and event.get("text"):
                said.append(event["text"])
                fed = _event(
                    "stream_event",
                    metadata={
                        "event": {
                            "type": "content_block_delta",
                            "delta": {"type": "text_delta", "text": event["text"]},
                        }
                    },
                )
            elif kind == "response.text" and event.get("text"):
                last = event["text"]
                fed = _event("assistant_text", text=last)
            elif kind == "response.thinking" and event.get("text"):
                fed = _event("thinking", text=event["text"])
            elif kind == "response.tool_use":
                name, tool_input = str(event.get("name") or "tool"), event.get("input") or {}
                fed = _event(
                    "tool_use", tool_use_id=event.get("tool_use_id"), name=name, input=tool_input
                )
                asked = permission_of(event)
                if asked:
                    pending.append((asked[0], name, tool_input, asked[1]))
            elif kind == "response.tool_result":
                fed = _event(
                    "tool_result",
                    tool_use_id=event.get("tool_use_id"),
                    content=_text_of(event.get("content")),
                    is_error=event.get("status") not in (None, "success"),
                )
            elif kind == "error":
                raise RuntimeError(str(event.get("message") or "The managed agent failed."))
            elif kind == "response" and event.get("status") in ("cancelled", "timed_out"):
                raise RuntimeError(f"The run ended: {event['status']}.")
            for out in translator.feed(fed) if fed is not None else ():
                self.emit(out)
        return pending, _event("result", metadata={"result": last or "".join(said)})

    def _decision(self, tool_use_id: str, name: str, tool_input: dict, options: tuple):
        """Ask the gate (it waits for the window), then the option that says the answer."""
        try:
            reason = self.gate.decide(name, tool_input, tool_use_id)
        except Exception as error:  # noqa: BLE001 - whatever goes wrong, the call does not run
            _LOG.exception("The CoCo gate failed for %s", name)
            reason = f"CoCo's safeguard failed: {error}"
        allow = reason is None
        option = choose_option(options, allow)
        if option is None and allow:  # no one-call allow among the options: do not guess
            option, reason = choose_option(options, False), "The request offered no way to allow."
            self.emit({"t": "refused", "tool_id": tool_use_id, "reason": reason})
        if option is None:  # nothing to answer with: end the run rather than leave it open
            raise RuntimeError("The request offered no option to decline.")
        return (tool_use_id, option) if allow else (tool_use_id, option, reason or "Declined.")

    def _close_client(self) -> None:
        with self._lock:
            client, self.client, self.conversation = self.client, None, None
        self._close(client)

    @staticmethod
    def _close(client) -> None:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                _LOG.warning("Closing the managed client failed", exc_info=True)


def managed_agent(options: ManagedOptions) -> Callable:
    """A function (emit) -> agent, for `ask_coco(agent=...)` and `Conversation(agent=...)`."""
    return lambda emit: ManagedAgent(emit, options)
