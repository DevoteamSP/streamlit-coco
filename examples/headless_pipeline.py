"""Headless async pipeline example (requires CoCo CLI).

Demonstrates:
1. Single-turn ``query()``
2. Multi-turn ``CocoSession.run()`` / ``stream()``
3. Approvals answered in code: a ``Conversation`` with a policy; each request is read as plain
   data and answered with ``allow`` or ``decline``

Imports only the headless surface — no Streamlit UI modules are loaded.
"""

from __future__ import annotations

import asyncio
import sys
import time

import streamlit_coco as coco
from streamlit_coco.conversation import Conversation


def _assert_no_streamlit() -> None:
    """Fail fast if a Streamlit UI import leaked into this script."""
    if "streamlit" in sys.modules:
        raise RuntimeError(
            "streamlit was imported — headless path should not load Streamlit. "
            "Import core symbols only (CocoSession / query / permissions)."
        )


async def single_turn() -> None:
    options = coco.CocoOptions(
        cwd=".",
        allowed_tools=["Read", "Glob", "Grep"],
    )
    print("=== query() ===")
    # Drain the full iterator — early ``break`` can leave SDK cancel scopes unclean.
    async for event in coco.query("List files in the current directory.", options=options):
        if event.type == "assistant_text":
            print(event.text or "", end="", flush=True)
        elif event.type == "tool_use":
            print(f"\n> Tool: {event.name}")
        elif event.type == "result":
            print(f"\nDone: {event.subtype} ({event.duration_ms}ms)")


async def _auto_approve_loop(session: coco.CocoSession) -> None:
    """Resolve HITL prompts in scripts (no Streamlit buttons)."""
    while True:
        pending = session.permission_manager.active_pending()
        if pending is not None:
            updated = None
            if coco.is_ask_user_question(pending.tool_name):
                questions = pending.tool_input.get("questions") or []
                answers = {
                    str(q.get("question") or q.get("header") or "q"): "auto"
                    for q in questions
                    if isinstance(q, dict)
                }
                updated = {"questions": questions, "answers": answers}
            elif coco.is_exit_plan_mode(pending.tool_name):
                updated = {"message": "Plan approved (headless)."}
            session.permission_manager.resolve(
                pending.request_id, approved=True, updated_input=updated
            )
        await asyncio.sleep(0.1)


async def multi_turn() -> None:
    options = coco.CocoOptions(
        cwd=".",
        allowed_tools=["Read", "Glob", "Grep"],
    )
    session = coco.CocoSession(options=options, key="headless-demo")
    session.start()
    session.ensure_ready(timeout=120.0)

    approver = asyncio.create_task(_auto_approve_loop(session))
    try:
        print("\n=== session.run() ===")
        result = await session.run("Summarize the top-level files.", timeout=180.0)
        print(f"run status={result.status.value} events={len(result.events)}")

        print("\n=== session.stream() ===")
        session.send("Name one Python package in this repo.")
        async for event in session.stream():
            if event.type == "assistant_text" and event.text:
                print(event.text, end="", flush=True)
            elif event.type == "result":
                print(f"\nstream done: {event.subtype}")
                break
    finally:
        approver.cancel()
        try:
            await approver
        except asyncio.CancelledError:
            pass
        session.close()
        session._wait_for_worker_stop(timeout=5.0)


def run_with_approvals(conv: Conversation, text: str, decide, timeout: float = 120.0) -> list:
    """Send `text` and answer every request through `decide(request) -> bool`; return the thread.

    `request` is the plain dict the policy wrote ({kind, question, where, evidence, ...}):
    allow what a script can vouch for, decline the rest.
    """
    conv.act({"type": "send", "text": text})
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        conv.drain()
        view = conv.view()
        request = view["request"]
        if request:
            verdict = "allow" if decide(request) else "decline"
            conv.act({"type": verdict, "id": request["id"]})
        elif view["status"] == "ready" and any(i["kind"] == "answer" for i in view["thread"]):
            return view["thread"]
        time.sleep(0.05)
    raise TimeoutError(f"no answer to {text!r} within {timeout}s")


def connect(conv: Conversation, timeout: float = 120.0) -> None:
    """Connect with the first profile the agent lists, and wait until it is ready."""
    conv.act({"type": "connect", "profile": (conv.view()["profiles"] or [""])[0]})
    deadline = time.monotonic() + timeout
    while conv.conn != "ready":
        conv.drain()
        if conv.conn == "none" or time.monotonic() > deadline:
            raise RuntimeError("CoCo did not connect: " + str(conv.view()["error"]))
        time.sleep(0.05)


def approvals() -> None:
    """Read inside the folder is free (the default policy); a change asks, and is answered here."""
    print("\n=== Conversation with a policy ===")
    conv = Conversation(".", policy=coco.policy.FolderPolicy("."))
    try:
        connect(conv)
        thread = run_with_approvals(
            conv,
            "Summarize the top-level files.",
            lambda request: request["kind"] == "read",  # never a change
        )
        print([i["text"] for i in thread if i["kind"] == "answer"][-1])
    finally:
        conv.close()


def main() -> None:
    _assert_no_streamlit()
    # Separate event loops so SDK query() cleanup cannot cancel the session worker.
    asyncio.run(single_turn())
    _assert_no_streamlit()
    asyncio.run(multi_turn())
    _assert_no_streamlit()
    approvals()
    _assert_no_streamlit()


if __name__ == "__main__":
    main()
