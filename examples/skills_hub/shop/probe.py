"""Inside the service: one chat turn with a skill, as the application, printed to the logs.

`python -m shop.probe` (the entrypoint runs it when SKILLS_HUB_PROBE=1). It answers the questions
that cannot be seen from outside: does the service token open a session, does the Agent API accept
its session token at the service's host, can the agent read the application's stage, does a skill
load. Every request that asks is declined: the probe changes nothing. No token is printed.
"""

from __future__ import annotations

import sys
import threading
import time

from shop import native
from shop.service import Shop

PROMPT = "Use the {skill} skill on this query: select * from t where a not in (select a from u)"


def run(options, store, skill_id: str = "sql-style-review", timeout: float = 240.0) -> bool:
    """True when the agent answered. `options`: the service's options; `store`: its stage."""
    from streamlit_coco.managed import ManagedAgent
    from streamlit_coco.policy import FolderPolicy

    shop = Shop(store)
    skills = shop.skills()
    print(f"probe: {len(skills)} skills on the stage: {[s.id for s in skills]}", flush=True)
    skill = shop.get(skill_id)
    verdict = shop.verify(skill)
    print(f"probe: verify {skill.id} {skill.version}: {verdict.ok} {verdict.problems}", flush=True)
    chat = shop.chat_options(options, skill)
    events: list[dict] = []
    agent = ManagedAgent(events.append, chat)
    agent.connect("probe", ".")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not {"connected", "connect_failed"} & {
        e["t"] for e in events
    }:
        time.sleep(0.3)
    kinds = [e["t"] for e in events]
    if "connect_failed" in kinds:
        print(
            "probe: connect failed:",
            next(e for e in events if e["t"] == "connect_failed")["message"][:500],
            flush=True,
        )
        return False
    print("probe: connected", flush=True)
    agent.send(PROMPT.format(skill=skill.id), {}, FolderPolicy("."))
    seen = len(events)
    answered = set()
    done = False
    while time.monotonic() < deadline and not done:
        for event in events[seen:]:
            kind = event["t"]
            if kind == "request" and event["id"] not in answered:
                answered.add(event["id"])
                print("probe: a request asked; declined", flush=True)
                agent.decide(event["id"], False)
            elif kind == "tool_use":
                print(f"probe: step {event.get('name')}", flush=True)
            elif kind in ("result", "error", "lost"):
                print(
                    f"probe: {kind}: {str(event.get('text') or event.get('message'))[:300]}",
                    flush=True,
                )
                done = True
        seen = len(events)
        time.sleep(0.3)
    agent.close()
    return any(e["t"] == "result" and not e.get("error") for e in events)


def main() -> int:
    threading.excepthook = lambda args: print(f"probe: thread error: {args.exc_value}", flush=True)
    options, store = native.connect()
    try:
        ok = run(options, store)
    finally:
        options.connection.close()
    print(f"probe: {'OK' if ok else 'FAILED'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
