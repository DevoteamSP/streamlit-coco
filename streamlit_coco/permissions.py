"""Human-in-the-loop permission handling for CoCo tool calls."""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from streamlit_coco.ask_user import is_ask_user_question
from streamlit_coco.errors import ApprovalTimeoutError
from streamlit_coco.messages import permission_request_event
from streamlit_coco.tool_names import is_exit_plan_mode

try:
    from cortex_code_agent_sdk import PermissionResultAllow, PermissionResultDeny
except ImportError:  # pragma: no cover

    @dataclass
    class PermissionResultAllow:
        updated_input: dict[str, Any] | None = None
        tool_use_id: str | None = None

    @dataclass
    class PermissionResultDeny:
        message: str = "Denied by user"


@dataclass
class PendingApproval:
    request_id: str
    tool_name: str
    tool_input: dict[str, Any]
    event: threading.Event = field(default_factory=threading.Event)
    decision: str | None = None
    always: bool = False
    reason: str | None = None
    updated_input: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
        }


class PermissionManager:
    """Coordinates async can_use_tool callbacks with UI approvals."""

    def __init__(self, *, approval_timeout_seconds: float = 600.0) -> None:
        self.approval_timeout_seconds = approval_timeout_seconds
        self._pending: dict[str, PendingApproval] = {}
        self.always_allowed_tools: set[str] = set()
        self.on_request: CallableHook | None = None

    def create_request(self, tool_name: str, tool_input: dict[str, Any]) -> PendingApproval:
        request_id = str(uuid.uuid4())
        pending = PendingApproval(
            request_id=request_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )
        self._pending[request_id] = pending
        if self.on_request is not None:
            self.on_request(permission_request_event(request_id, tool_name, tool_input))
        return pending

    def get_pending(self, request_id: str) -> PendingApproval | None:
        return self._pending.get(request_id)

    def active_pending(self) -> PendingApproval | None:
        for pending in self._pending.values():
            if pending.decision is None:
                return pending
        return None

    async def wait_for_decision(self, request_id: str) -> PendingApproval:
        pending = self._pending[request_id]
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, pending.event.wait),
                timeout=self.approval_timeout_seconds,
            )
        except TimeoutError as exc:
            pending.decision = "deny"
            pending.reason = "Approval timed out"
            raise ApprovalTimeoutError(pending.tool_name) from exc
        return pending

    def resolve(
        self,
        request_id: str,
        *,
        approved: bool,
        always: bool = False,
        reason: str | None = None,
        updated_input: dict[str, Any] | None = None,
    ) -> bool:
        pending = self._pending.get(request_id)
        if pending is None or pending.decision is not None:
            return False
        pending.decision = "allow" if approved else "deny"
        pending.always = always
        pending.reason = reason
        pending.updated_input = updated_input
        # AskUserQuestion must collect fresh answers every time.
        # ExitPlanMode must be reviewed each time plan mode exits.
        if (
            approved
            and always
            and not is_ask_user_question(pending.tool_name)
            and not is_exit_plan_mode(pending.tool_name)
        ):
            self.always_allowed_tools.add(pending.tool_name.lower())
        pending.event.set()
        return True

    def clear_resolved(self) -> None:
        self._pending = {
            request_id: pending
            for request_id, pending in self._pending.items()
            if pending.decision is None
        }


CallableHook = Any


def approve_pending(
    session: Any,
    request_id: str,
    *,
    always: bool = False,
    updated_input: dict[str, Any] | None = None,
) -> None:
    if session.permission_manager.resolve(
        request_id,
        approved=True,
        always=always,
        updated_input=updated_input,
    ):
        _mark_transcript_approval(session, request_id, approved=True, always=always)


def deny_pending(
    session: Any,
    request_id: str,
    *,
    reason: str | None = None,
) -> None:
    if session.permission_manager.resolve(request_id, approved=False, reason=reason):
        _mark_transcript_approval(session, request_id, approved=False, reason=reason)


def _mark_transcript_approval(
    session: Any,
    request_id: str,
    *,
    approved: bool,
    always: bool = False,
    reason: str | None = None,
) -> None:
    for item in session.transcript:
        if item.get("kind") == "approval" and item.get("id") == request_id:
            item["status"] = "approved" if approved else "denied"
            if always:
                item["always"] = True
            if reason:
                item["reason"] = reason
            break


def build_can_use_tool(
    manager: PermissionManager,
    require_approval_for: list[str] | Any,
    *,
    auto_allow_tools: list[str] | None = None,
) -> Any:
    normalized_required = (
        {tool.lower() for tool in require_approval_for}
        if isinstance(require_approval_for, list)
        else None
    )
    normalized_auto = {tool.lower() for tool in auto_allow_tools or []}
    enforce_allowlist = auto_allow_tools is not None

    def _needs_approval(tool_name: str, tool_input: dict[str, Any], context: Any) -> bool:
        if callable(require_approval_for):
            return bool(require_approval_for(tool_name, tool_input, context))
        if normalized_required is None:
            return False
        return tool_name.lower() in normalized_required

    def _is_auto_allowed(tool_name: str) -> bool:
        return tool_name.lower() in normalized_auto

    async def can_use_tool(
        tool_name: str,
        tool_input: dict[str, Any],
        context: Any,
    ) -> PermissionResultAllow | PermissionResultDeny:
        # AskUserQuestion / ExitPlanMode are SDK-routed: always collect a decision.
        if is_ask_user_question(tool_name) or is_exit_plan_mode(tool_name):
            pending = manager.create_request(tool_name, tool_input)
            return await _wait_and_resolve(manager, pending, tool_input, context)

        if _is_always_allowed(manager, tool_name):
            return PermissionResultAllow()

        if _needs_approval(tool_name, tool_input, context):
            pending = manager.create_request(tool_name, tool_input)
        elif enforce_allowlist:
            if _is_auto_allowed(tool_name):
                return PermissionResultAllow()
            return PermissionResultDeny(message=f"Tool {tool_name} is not allowed in this session")
        else:
            return PermissionResultAllow()

        return await _wait_and_resolve(manager, pending, tool_input, context)

    return can_use_tool


async def _wait_and_resolve(
    manager: PermissionManager,
    pending: PendingApproval,
    tool_input: dict[str, Any],
    context: Any,
) -> PermissionResultAllow | PermissionResultDeny:
    try:
        resolved = await manager.wait_for_decision(pending.request_id)
    except TimeoutError:
        return PermissionResultDeny(message="Approval timed out")

    if resolved.decision == "allow":
        updated = resolved.updated_input
        if is_ask_user_question(pending.tool_name):
            # Prefer the answered payload; never fall back to unanswered input.
            updated = resolved.updated_input or {
                "questions": tool_input.get("questions", []),
                "answers": {},
            }
        elif is_exit_plan_mode(pending.tool_name):
            updated = resolved.updated_input
        else:
            updated = updated or tool_input
        return PermissionResultAllow(
            updated_input=updated,
            tool_use_id=getattr(context, "tool_use_id", None) or None,
        )
    return PermissionResultDeny(message=resolved.reason or "Denied by user")


def _is_always_allowed(manager: PermissionManager, tool_name: str) -> bool:
    return tool_name.lower() in manager.always_allowed_tools
