"""CoCo session lifecycle and background agent execution."""

from __future__ import annotations

import asyncio
import threading
import time
import traceback
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from streamlit_coco.errors import (
    SDKNotInstalledError,
    SessionNotReadyError,
    SessionStartError,
    wrap_exception,
)
from streamlit_coco.messages import (
    CocoEvent,
    append_events_to_transcript,
    message_to_events,
)
from streamlit_coco.options import CocoOptions
from streamlit_coco.permissions import PermissionManager, build_can_use_tool
from streamlit_coco.tool_names import is_exit_plan_mode

try:
    from cortex_code_agent_sdk import CortexCodeSDKClient
except ImportError:  # pragma: no cover
    CortexCodeSDKClient = None  # type: ignore[misc, assignment]

_SESSIONS: dict[str, CocoSession] = {}


class CocoRunStatus(str, Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    READY = "ready"
    RUNNING = "running"
    AWAITING_USER = "awaiting_user"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class CocoChatResult:
    last_prompt: str | None = None
    last_result: CocoEvent | None = None
    pending_approval: dict[str, Any] | None = None
    structured_output: Any = None
    events: list[CocoEvent] = field(default_factory=list)
    status: CocoRunStatus = CocoRunStatus.IDLE


class CocoSession:
    """Multi-turn CoCo session backed by CortexCodeSDKClient."""

    def __init__(
        self,
        *,
        options: CocoOptions | None = None,
        key: str | None = None,
    ) -> None:
        self.key = key
        self.options = options or CocoOptions()
        self.permission_manager = PermissionManager(
            approval_timeout_seconds=self.options.approval_timeout_seconds
        )
        self.status = CocoRunStatus.IDLE
        self.transcript: list[dict[str, Any]] = []
        self.events: list[CocoEvent] = []
        self.last_prompt: str | None = None
        self.last_result: CocoEvent | None = None
        self.last_error: str | None = None
        self.structured_output: Any = None
        self.init_info: dict[str, Any] | None = None
        self._prompt_queue: asyncio.Queue[str | None] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._loop_ready = threading.Event()
        self._client_ready = threading.Event()
        self._start_error: str | None = None
        self._client: Any = None
        self._cancel_requested = False
        self._turn_in_progress = False
        self._worker_options_hash: str | None = None
        self._show_structured_inline = True
        self._on_events: list[Callable[[CocoEvent], None]] = []
        self._lock = threading.Lock()

        if key is not None:
            _SESSIONS[key] = self

        self.permission_manager.on_request = self._handle_permission_request

    @property
    def is_running(self) -> bool:
        return self.status in {CocoRunStatus.RUNNING, CocoRunStatus.AWAITING_USER}

    @property
    def is_ready(self) -> bool:
        """True when the SDK client is connected and available for prompts."""
        return (
            self._client is not None
            and self._thread is not None
            and self._thread.is_alive()
            and self.status != CocoRunStatus.CONNECTING
        )

    @property
    def is_connecting(self) -> bool:
        return self.status == CocoRunStatus.CONNECTING

    @property
    def needs_polling(self) -> bool:
        """True while connecting or a turn is active and the UI should refresh."""
        return (
            self._turn_in_progress
            or self.is_running
            or self.is_connecting
            or self.permission_manager.active_pending() is not None
        )

    @property
    def messages(self) -> list[dict[str, Any]]:
        return self.get_transcript_snapshot()

    def get_transcript_snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self.transcript]

    def get_revision(self) -> int:
        with self._lock:
            return len(self.events)

    def add_event_listener(self, callback: Callable[[CocoEvent], None]) -> None:
        self._on_events.append(callback)

    def sync_options(self, options: CocoOptions) -> None:
        """Apply option changes and restart the worker when tool permissions change."""
        new_hash = options.options_hash()
        if new_hash != self._worker_options_hash:
            self.options = options
            if self._thread is not None and self._thread.is_alive():
                self.reset()
            return
        self.options = options

    def _wait_for_worker_stop(self, timeout: float = 5.0) -> None:
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def set_show_structured_inline(self, value: bool) -> None:
        self._show_structured_inline = value

    def start(self) -> None:
        """Start the background worker (connects the SDK client eagerly)."""
        if self._thread and self._thread.is_alive():
            return
        self._loop_ready.clear()
        self._client_ready.clear()
        self._start_error = None
        self._loop = None
        self._prompt_queue = None
        self._client = None
        self.status = CocoRunStatus.CONNECTING
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="coco-session")
        self._thread.start()

    def ensure_ready(self, timeout: float = 120.0) -> None:
        """Block until the SDK client is connected, or raise on failure/timeout."""
        if self.is_ready:
            return
        self.start()
        self._ensure_loop()
        if self.is_ready:
            return

        remaining = timeout
        deadline = time.monotonic() + timeout
        while remaining > 0:
            if self._client_ready.wait(timeout=min(remaining, 0.25)):
                break
            if self._start_error or self.status == CocoRunStatus.ERROR:
                break
            if not self._thread or not self._thread.is_alive():
                break
            remaining = deadline - time.monotonic()

        if self.is_ready:
            return

        detail = self.last_error or self._start_error or "timed out waiting for CoCo to connect"
        raise SessionNotReadyError(detail)

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._prompt_queue = asyncio.Queue()
        self._loop_ready.set()
        try:
            loop.run_until_complete(self._worker())
        except Exception as exc:  # pragma: no cover - runtime failures
            wrapped = wrap_exception(exc, context="session_start")
            self._start_error = str(wrapped)
            self.status = CocoRunStatus.ERROR
            self.last_error = str(wrapped)
            self._client_ready.set()
            traceback.print_exc()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Wait until the background worker loop is ready."""
        self.start()
        if not self._loop_ready.wait(timeout=10.0):
            raise SessionStartError("timed out waiting for worker")

        if self._start_error:
            raise SessionStartError(self._start_error)

        if self._loop is None or self._prompt_queue is None:
            raise SessionStartError("worker loop is unavailable")

        if not self._thread or not self._thread.is_alive():
            detail = self.last_error or "worker thread exited"
            raise SessionStartError(detail)

        return self._loop

    async def _worker(self) -> None:
        if CortexCodeSDKClient is None:
            self.status = CocoRunStatus.ERROR
            self.last_error = str(SDKNotInstalledError())
            self._client_ready.set()
            return

        require = list(self.options.tools_requiring_approval())
        auto_allow = list(self.options.auto_allow_tools()) if self.options.allowed_tools else None
        # Always install can_use_tool so AskUserQuestion (and approvals) can complete.
        approval_policy = (
            self.options.require_approval_for
            if require or callable(self.options.require_approval_for)
            else []
        )
        can_use_tool = build_can_use_tool(
            self.permission_manager,
            approval_policy,
            auto_allow_tools=auto_allow,
        )

        sdk_options = self.options.to_sdk_options(can_use_tool=can_use_tool)
        self._worker_options_hash = self.options.options_hash()
        self.status = CocoRunStatus.CONNECTING

        try:
            async with CortexCodeSDKClient(sdk_options) as client:
                self._client = client
                self.status = CocoRunStatus.READY
                self._client_ready.set()
                while True:
                    prompt = await self._prompt_queue.get()
                    if prompt is None:
                        break
                    await self._run_turn(client, prompt)
        except Exception as exc:  # pragma: no cover - runtime failures
            wrapped = wrap_exception(exc, context="session")
            self.status = CocoRunStatus.ERROR
            self.last_error = str(wrapped)
            self._client = None
            self._client_ready.set()

    async def _run_turn(self, client: Any, prompt: str) -> None:
        self.last_prompt = prompt
        self.last_error = None
        self._cancel_requested = False
        self.status = CocoRunStatus.RUNNING
        self.transcript.append(
            {"id": f"user-{len(self.transcript)}", "role": "user", "content": prompt}
        )

        try:
            await client.query(prompt)
            async for message in client.receive_response():
                if self._cancel_requested:
                    await client.interrupt()
                    self.status = CocoRunStatus.CANCELLED
                    return

                for event in message_to_events(message):
                    self._ingest_event(event)

                pending = self.permission_manager.active_pending()
                if pending is not None:
                    self.status = CocoRunStatus.AWAITING_USER

            if self.status != CocoRunStatus.CANCELLED:
                self.status = CocoRunStatus.COMPLETED
        except Exception as exc:
            wrapped = wrap_exception(exc, context="session")
            self.status = CocoRunStatus.ERROR
            self.last_error = str(wrapped)
            error_event = CocoEvent(
                type="error",
                message=str(wrapped),
                code=type(wrapped).__name__,
            )
            self._ingest_event(error_event)
            traceback.print_exc()
        finally:
            self._turn_in_progress = False

    def _ingest_event(self, event: CocoEvent) -> None:
        with self._lock:
            self.events.append(event)
            append_events_to_transcript(
                self.transcript,
                [event],
                show_structured_inline=self._show_structured_inline,
            )
            if event.type == "system" and event.subtype == "init":
                self.init_info = dict(event.metadata or {})
            if event.type == "result":
                self.last_result = event
                self.structured_output = event.structured_output
            callbacks = list(self._on_events)
        for callback in callbacks:
            callback(event)

    def _handle_permission_request(self, event: CocoEvent) -> None:
        self._ingest_event(event)
        self.status = CocoRunStatus.AWAITING_USER

    def send(self, prompt: str) -> None:
        """Queue a prompt on the background worker."""
        self._turn_in_progress = True
        loop = self._ensure_loop()
        assert self._prompt_queue is not None
        asyncio.run_coroutine_threadsafe(self._prompt_queue.put(prompt), loop)

    def set_permission_mode(self, mode: str) -> None:
        """Update local options and the live SDK client permission mode when connected."""
        self.options.permission_mode = mode
        client = self._client
        loop = self._loop
        if client is None or loop is None:
            return
        setter = getattr(client, "set_permission_mode", None)
        if setter is None:
            return
        asyncio.run_coroutine_threadsafe(setter(mode), loop)

    def execute_plan(
        self,
        *,
        mode: str = "default",
        prompt: str | None = "Execute the approved plan.",
    ) -> None:
        """Leave plan mode and optionally queue an execute prompt.

        If ``ExitPlanMode`` is awaiting approval, approving it is preferred —
        call ``approve_pending`` instead. This helper is for the banner CTA when
        the user wants to exit plan mode and start implementation.
        """
        pending = self.permission_manager.active_pending()
        if pending is not None and is_exit_plan_mode(pending.tool_name):
            self.permission_manager.resolve(
                pending.request_id,
                approved=True,
                updated_input={"message": "Plan approved — execute."},
            )
            return

        self.set_permission_mode(mode)
        if prompt:
            self.send(prompt)

    async def stream(self) -> AsyncIterator[CocoEvent]:
        """Yield session events as they arrive (headless multi-turn API).

        Events are produced by the background worker after ``send()`` / ``run()``.
        The iterator runs until cancelled by the caller. Use ``run()`` to drain a
        single turn until ``result``.
        """
        queue: asyncio.Queue[CocoEvent] = asyncio.Queue()
        caller_loop = asyncio.get_running_loop()

        def _on_event(event: CocoEvent) -> None:
            caller_loop.call_soon_threadsafe(queue.put_nowait, event)

        self.add_event_listener(_on_event)
        try:
            while True:
                yield await queue.get()
        finally:
            try:
                self._on_events.remove(_on_event)
            except ValueError:
                pass

    async def run(
        self,
        prompt: str,
        *,
        timeout: float | None = None,
    ) -> CocoChatResult:
        """Send ``prompt`` and wait until the turn finishes; return ``chat_result()``.

        While awaiting approvals, resolve them from another task with
        ``approve_pending`` / ``deny_pending``, or rely on ``approval_timeout_seconds``.
        """
        text = prompt.strip()
        if not text:
            return self.chat_result()

        self.send(text)
        deadline = None if timeout is None else time.monotonic() + timeout
        started = False

        while True:
            if self._turn_in_progress or self.is_running:
                started = True
            elif started:
                return self.chat_result()

            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"run() timed out after {timeout}s")

            await asyncio.sleep(0.05)

    def cancel(self) -> None:
        self._cancel_requested = True
        if self._client is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._client.interrupt(), self._loop)
        pending = self.permission_manager.active_pending()
        if pending is not None:
            self.permission_manager.resolve(
                pending.request_id,
                approved=False,
                reason="Cancelled by user",
            )
        if self.status == CocoRunStatus.RUNNING:
            self.status = CocoRunStatus.CANCELLED

    def close(self) -> None:
        if self._loop is not None and self._prompt_queue is not None:
            asyncio.run_coroutine_threadsafe(self._prompt_queue.put(None), self._loop)

    def reset(self) -> None:
        self.cancel()
        self.close()
        self._wait_for_worker_stop()
        self.transcript.clear()
        self.events.clear()
        self.last_prompt = None
        self.last_result = None
        self.last_error = None
        self.structured_output = None
        self.init_info = None
        self.status = CocoRunStatus.IDLE
        self.permission_manager = PermissionManager(
            approval_timeout_seconds=self.options.approval_timeout_seconds
        )
        self.permission_manager.on_request = self._handle_permission_request
        self._loop_ready.clear()
        self._client_ready.clear()
        self._start_error = None
        self._thread = None
        self._loop = None
        self._prompt_queue = None
        self._client = None
        self._turn_in_progress = False
        self._worker_options_hash = None

    def chat_result(self) -> CocoChatResult:
        pending = self.permission_manager.active_pending()
        return CocoChatResult(
            last_prompt=self.last_prompt,
            last_result=self.last_result,
            pending_approval=pending.to_dict() if pending else None,
            structured_output=self.structured_output,
            events=list(self.events),
            status=self.status,
        )

    async def __aenter__(self) -> CocoSession:
        self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.close()


def get_session(key: str) -> CocoSession | None:
    return _SESSIONS.get(key)
