"""A scripted stand-in for the Cortex Agent SDK's client, to drive `ManagedAgent` offline.

    client = FakeClient([turn_1_events, turn_2_events])
    agent = ManagedAgent(emit, options, client_factory=lambda: client)

Each list is the stream of one turn: dicts as the server sends them
(`{"event": "response.text.delta", "text": ...}`). The first turn answers `conversation.send`,
the next ones answer `send_permission_decisions`. What the agent sent is kept for the test to
read: `client.sent` (the prompts and decisions, in order) and `client.spec` (the coding agent of
the conversation).
"""

from __future__ import annotations


def tool_use(tool_use_id: str, name: str, tool_input: dict, options=None) -> dict:
    """A `response.tool_use`; with `options`, one that waits for the user (what the server sends:
    ["Allow this command", "Allow all bash for this session", "Deny"])."""
    event = {"event": "response.tool_use", "tool_use_id": tool_use_id, "name": name}
    event["input"] = tool_input
    if options is not None:
        event["permission"] = {"options": list(options)}
    return event


def text(words: str) -> list[dict]:
    """The events of a short answer: one delta, the block, the end of the run."""
    return [
        {"event": "response.text.delta", "text": words},
        {"event": "response.text", "text": words},
        {"event": "response", "status": "completed"},
    ]


class FakeTurn:
    def __init__(self, events: list[dict], cancelled: list) -> None:
        self._events, self._cancelled = events, cancelled

    def events(self):
        return iter(self._events)

    def cancel(self) -> None:
        self._cancelled.append(True)


class FakeConversation:
    def __init__(self, client: FakeClient) -> None:
        self.id, self._client = "thread-1", client

    def _next(self) -> FakeTurn:
        if not self._client.turns:
            raise AssertionError("The agent sent more turns than the test scripted.")
        return FakeTurn(self._client.turns.pop(0), self._client.cancelled)

    def send(self, prompt: str) -> FakeTurn:
        self._client.sent.append(("send", prompt))
        return self._next()

    def send_permission_decisions(self, decisions: list) -> FakeTurn:
        self._client.sent.append(("decisions", list(decisions)))
        return self._next()


class FakeConversations:
    def __init__(self, client: FakeClient) -> None:
        self._client = client

    def create(self, *, agent=None, **kwargs) -> FakeConversation:
        if self._client.fail:
            raise RuntimeError(self._client.fail)
        self._client.spec = (agent or {}).get("spec")
        return FakeConversation(self._client)


class FakeClient:
    def __init__(self, turns: list[list[dict]], fail: str | None = None) -> None:
        self.turns, self.fail = list(turns), fail
        self.sent: list[tuple] = []
        self.cancelled: list = []
        self.spec = None
        self.closed = False
        self.conversations = FakeConversations(self)

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    """A Snowflake connector connection that keeps the statements it was given (a `PUT` to the
    upload stage, a `REMOVE`); `fail` makes a `PUT` raise with that text."""

    def __init__(self, fail: str | None = None) -> None:
        self.statements: list[str] = []
        self.fail, self.closed = fail, False

    def cursor(self):
        conn = self

        class Cursor:
            def execute(self, sql):
                if conn.fail and sql.startswith("PUT"):
                    raise RuntimeError(conn.fail)
                conn.statements.append(sql)

            def close(self):
                pass

        return Cursor()

    def close(self) -> None:
        self.closed = True
