"""Ask CoCo, what an agent is: the surface the conversation calls.

Pure Python: no Streamlit, no SDK. `Conversation` builds one agent per conversation with a function
(emit) -> agent and calls only what is listed here. Three agents keep this surface: the Cortex Code
program (`cortex.Agent`, the default), Snowflake's managed coding agent (`managed.ManagedAgent`)
and the scripted agent (`testing.scripted.ScriptedAgent`, tests and demos).

An agent reports by calling `emit(event)` with plain dicts (the vocabulary is `conversation.py`'s
docstring) and decides what asks the user through a `Gate` (gate.py), so every backend keeps the
same rights: the policy judges the call, the user answers, never the agent's own description.

Two optional parts, read with `getattr` (an agent that has none works as before):

    labels   {key: text}   the window's own words for this agent, under the host's `labels=`
    carry    carry(paths) -> [path the agent reads]   takes the files the user attached (saved
             where the host runs) to where the agent works, or raises `CarryError`. An agent
             that runs on this computer needs none: it reads the saved files.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

BACKENDS = ("cli", "managed")


class CarryError(Exception):
    """A file cannot go to the agent. `key` is a label of the conversation (`attach_*`): the
    sentence that says why, with `values` filled in."""

    def __init__(self, key: str, **values: Any) -> None:
        super().__init__(key)
        self.key, self.values = key, values


@runtime_checkable
class AgentBackend(Protocol):
    gate: Any  # the Gate: `begin(policy)` per message, `decide` for a call that may ask

    def setup(self) -> dict | None: ...  # None, or {missing: "package" | "program", command}

    def profiles(self) -> list[str]: ...

    def connection_files(self) -> list[dict]: ...

    def session_facts(self) -> list[dict]: ...  # [{label, value}], never a secret

    def connect(self, profile: str, cwd: str, file: str | None = None) -> None: ...

    def send(self, text: str, ctx: dict, policy) -> None: ...

    def decide(self, request_id: str, allow: bool, standing: bool = False) -> None: ...

    def revoke(self, permission_id: str) -> None: ...

    def answer(self, id: str, answers) -> None: ...

    def skip(self, id: str) -> None: ...

    def approve_plan(self, id: str) -> None: ...

    def decline_plan(self, id: str, reason: str = "") -> None: ...

    def set_planning(self, on: bool) -> None: ...

    def set_raw(self, on: bool) -> None: ...

    def set_reasoning(self, on: bool) -> None: ...

    def stop(self) -> None: ...

    def close(self) -> None: ...
