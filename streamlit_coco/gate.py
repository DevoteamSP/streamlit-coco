"""Ask CoCo, the pre-tool gate: the decision that waits for the window.

Pure Python: no Streamlit, no SDK. The Cortex adapter and the scripted agent both use it; a host
never needs it. It is public for whoever writes another adapter.
"""

from __future__ import annotations

import json
import threading
import uuid

# A granted family also covers these (Statements: any SQL statement, so the reading ones too).
_ALSO = {"queries": ("statements",)}
EXPIRY = 600  # seconds without an answer: the request expires, as a decline


class Gate:
    """The pre-tool decision. `decide` blocks (call it off the event loop) and returns None to
    allow, or the reason.

    A call is free, asks, or is refused (only when the app cannot read it): the policy says which
    (policy.py). A request that asks may offer a standing permission for its family; the user's
    Allow with `standing` grants it, until the conversation ends or `revoke`. One Gate lives as
    long as its conversation: `begin` keeps the grants across the requests of one conversation,
    and `begin(policy, new_conversation=True)` ends them.
    Events emitted: request{id, tool_id, facts}, expired{id, tool_id}, refused{tool_id, reason},
    granted{id, text, family}, revoked{id}, standing{tool_id}.
    """

    def __init__(self, emit, expiry: float = EXPIRY) -> None:
        self.emit, self.expiry, self.policy = emit, expiry, None
        # Cortex Code's folder of long outputs for this session (see FolderPolicy.spill)
        self.spill = None
        self._slots: dict[str, dict] = {}
        self._agreed: set[str] = set()
        self._granted: dict[str, str] = {}  # family id -> what it covers, in words
        self._lock = threading.Lock()
        self._stopped = False

    def begin(self, policy, *, new_conversation: bool = False) -> None:
        """A new request: its policy, and no agreement of an earlier one. Standing permissions
        stay unless the conversation is new."""
        self.policy = policy
        self._agreed.clear()
        self._stopped = False
        if new_conversation:
            with self._lock:
                self._granted.clear()

    def granted(self) -> list[str]:
        """What runs without asking now, in words (for Policy.rights)."""
        with self._lock:
            return list(self._granted.values())

    def revoke(self, permission_id: str) -> None:
        with self._lock:
            gone = self._granted.pop(permission_id, None)
        if gone is not None:
            self.emit({"t": "revoked", "id": permission_id})

    @staticmethod
    def _key(tool: str, tool_input) -> str:
        return str(tool).lower() + json.dumps(tool_input, sort_keys=True, default=str)

    def _covered(self, family: str) -> bool:
        with self._lock:
            return bool(self._granted.keys() & {family, *_ALSO.get(family, ())})

    def decide(self, tool: str, tool_input, tool_id: str) -> str | None:
        policy = self.policy
        if policy:
            policy.spill = self.spill
        reason, facts = (
            policy.judge(tool, tool_input) if policy else ("No request is running.", None)
        )
        offer = (facts or {}).get("standing")
        if not reason and facts and offer and self._covered(offer["id"]):
            self._agreed.add(self._key(tool, tool_input))
            self.emit({"t": "standing", "tool_id": tool_id})  # it ran, and the user was not asked
            return None
        if not reason and facts:
            request_id = uuid.uuid4().hex
            slot = {"event": threading.Event(), "allow": False, "standing": False}
            with self._lock:
                if self._stopped:  # the user stopped meanwhile: nobody is left to answer
                    return "Declined by the user."
                self._slots[request_id] = slot
            self.emit({"t": "request", "id": request_id, "tool_id": tool_id, "facts": facts})
            answered = slot["event"].wait(self.expiry)
            self._slots.pop(request_id, None)
            if not answered:
                self.emit({"t": "expired", "id": request_id, "tool_id": tool_id})
                return "No answer after 10 minutes."
            if not slot["allow"]:
                return "Declined by the user."
            # An Allow never widens the policy: what the user was shown must still be what would
            # be shown (a file may have changed)
            reason, again = policy.judge(tool, tool_input)
            if not reason and again != facts:
                reason = "The call is no longer what you were shown, so it did not run."
            if not reason:
                self._agreed.add(self._key(tool, tool_input))
                if slot["standing"] and offer:
                    self._grant(offer)
        if reason:
            self.emit({"t": "refused", "tool_id": tool_id, "reason": reason})
        return reason

    def _grant(self, offer: dict) -> None:
        with self._lock:
            new = offer["id"] not in self._granted
            self._granted[offer["id"]] = offer["covers"]
        if new:
            family = offer["id"].split(":")[0]
            self.emit(
                {"t": "granted", "id": offer["id"], "text": offer["covers"], "family": family}
            )

    def agreed(self, tool: str, tool_input) -> bool:
        """For the SDK's own permission callback: a call that asks runs only if the user gave it
        (or a standing permission did)."""
        policy = self.policy
        if not policy:
            return False
        reason, facts = policy.judge(tool, tool_input)
        return not reason and (facts is None or self._key(tool, tool_input) in self._agreed)

    def answer(self, request_id: str, allow: bool, standing: bool = False) -> None:
        with self._lock:
            slot = self._slots.get(request_id)
            if slot and not slot["event"].is_set():  # the first answer stands
                slot["allow"], slot["standing"] = allow, bool(allow and standing)
                slot["event"].set()

    def cancel_all(self) -> None:
        with self._lock:
            self._stopped = True
        for request_id in list(self._slots):
            self.answer(request_id, False)
