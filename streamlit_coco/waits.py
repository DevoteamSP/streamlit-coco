"""Ask CoCo, the conversation: what waits for the user, in order (feature file 1.4, docstring of
    conversation.py).

Questions (kind "question"), plans (kind "plan"), the planning-only mode, standing permissions as
    the
conversation sees them, and the one list in which they and the agreement requests wait: the view's
`wait`, `mode`, `granted`, `pill`, and the actions answer, skip, approve_plan, decline_plan,
carry_out, revoke, system_action. The requests themselves stay in `conv.requests`; this module
orders them with the others and reads them, it never stores them.

Pure Python: no Streamlit, no SDK. Called by `Conversation` (conversation.py). Every sentence it
writes is a label of the conversation (`conv.t(key)`).

    reset(conv)                          the conversation was created or ended: give it this
        module's state (`w_*`)
    act(conv, action, context) -> bool   a window action the core does not know; True when handled
    on(conv, event) -> bool              an event from the agent the core does not know; True when
        handled
    view(conv) -> dict                   keys added to the view: wait, mode, granted (each only
        while it has something to say)
    on_message / on_step / on_answer     a message was accepted (its context is kept for "Carry out
        the plan") / a result arrived
    waits(conv) -> [wait]      every thing waiting, first to wait first: requests, questions, plans
    request(conv), pill(conv)  the first wait's request (None when it is not one), and the pill of
        the first wait
    quiet(conv)                tool ids the thread never shows as a step (the question and plan
        tools: the wait is their face)
    decline_all(conv)          Stop: every wait is declined, skipped or cancelled
    end(conv, kind, run)       the run is over: what still waits is settled, and a lost session
        loses its modes and grants
    set_planning(conv, on)     planning only on or off

Rules where the contract is silent:
  - a wait that ends with the run, other than by Stop, reads "Cancelled"; Stop reads "Skipped" for
      a question and "Declined"
    for a plan, as it reads "Declined" for a request
  - a question the window cannot show (no text, nothing to choose or fill in) is refused: the agent
      skips it, its step reads as failed
  - the standing tick is honoured only when the request offered one (`facts["standing"]`)
  - a lost connection takes the planning mode and the grants with it: the session that held them is
      gone
  - the planning strip is not in the view while a plan waits (the block says it)
  - approving a plan leaves planning only; declining keeps it (CoCo plans again)
"""

from __future__ import annotations

import itertools
import time

_QUESTION_KEYS = ("source", "questions", "text")


def reset(conv) -> None:
    conv.w_forms = getattr(conv, "w_forms", {})  # the application's forms outlive a conversation
    conv.w_items, conv.w_seq, conv.w_count = (
        [],
        {},
        itertools.count(1),
    )  # questions and plans; request id -> arrival number
    conv.w_quiet, conv.w_stand, conv.w_granted, conv.w_sys = (
        set(),
        set(),
        [],
        {},
    )  # tool ids; standing tool ids; grants; system item id -> grant id
    conv.w_planning, conv.w_from, conv.w_ctx, conv.w_grant = (
        False,
        0,
        None,
        None,
    )  # mode; first item of the planning; last context; tool just allowed for good


def ask_form(conv, key: str, title: str, fields: list[dict]) -> None:
    """The application asks a form (feature file 1.1, `coco.form`): it waits in the same list as
    CoCo's questions, with source "app", and needs no agent and no connection. Idempotent per
    `key`: asked once; asked again only while it is still waiting and was lost with a conversation
    that ended. Answered or skipped, it stays done: a new question needs a new key."""
    state = conv.w_forms.setdefault(key, {"state": "waiting", "values": {}, "handed": False})
    if state["state"] != "waiting" or any(w.get("app_key") == key for w in conv.w_items):
        return
    form = [
        {
            "id": str(f["id"]),
            "label": str(f.get("label") or f["id"]),
            "type": f.get("type")
            if f.get("type") in ("text", "longtext", "number", "choice")
            else "text",
            "choices": [str(c) for c in f.get("choices") or []],
            "required": bool(f.get("required", True)),
            "value": str(f.get("value", "")),
        }
        for f in fields
    ]
    conv.w_items.append(
        {
            "kind": "question",
            "id": conv._id("n"),
            "tool_id": None,
            "source": "app",
            "app_key": key,
            "questions": [{"id": "q1", "kind": "form", "text": title, "fields": form}],
            "n": next(conv.w_count),
        }
    )
    conv.rev += 1


def form_result(conv, key: str, take: bool = True) -> dict | None:
    """None while the form waits (or was never asked, or was already handed over); once answered,
    {"skipped": False, "values": {field id: text}}; once skipped, {"skipped": True, "values": {}}.
    Handed over once."""
    state = conv.w_forms.get(key)
    if not state or state["state"] == "waiting" or state["handed"]:
        return None
    state["handed"] = take or state["handed"]
    return {"skipped": state["state"] == "skipped", "values": dict(state["values"])}


def _app_done(conv, wait: dict, answers) -> None:
    """The application's form is answered (answers: the window's list) or skipped (None)."""
    conv.w_items.remove(wait)
    state = conv.w_forms[wait["app_key"]]
    first = (answers[0] if isinstance(answers, list) and answers else None) or {}
    fields = first.get("fields") if isinstance(first, dict) else None
    if fields is None:
        state["state"] = "skipped"
    else:
        state.update(state="answered", values={str(k): str(v) for k, v in fields.items()})
    conv.rev += 1


def _agent(conv, name: str, *args, **kw) -> None:
    method = getattr(conv.agent, name, None)  # an agent that does not know a call still works
    if method:
        method(*args, **kw)


def waits(conv) -> list[dict]:
    for (
        request
    ) in conv.requests:  # the core appends requests without a number: number them as first seen
        conv.w_seq.setdefault(request["id"], next(conv.w_count))
    return sorted(
        [
            {"kind": "request", "id": r["id"], "req": r, "n": conv.w_seq[r["id"]]}
            for r in conv.requests
        ]
        + conv.w_items,
        key=lambda w: w["n"],
    )


def request(conv) -> dict | None:
    first = waits(conv)[:1]
    return first[0]["req"] if first and first[0]["kind"] == "request" else None


def quiet(conv) -> set:
    return conv.w_quiet


def planning(conv) -> bool:
    return conv.w_planning


def _scope(conv) -> str:
    return ((((conv.run or {}).get("message") or {}).get("ctx") or {}).get("scope") or {}).get(
        "name"
    ) or ""


def pill(conv) -> dict | None:
    first = waits(conv)[:1]
    if not first:
        return None
    wait = first[0]
    if wait["kind"] == "request":
        facts = wait["req"]["facts"]
        return {
            "kind": "request",
            "name": facts["where"],
            "label": facts.get("pill")
            or conv.t("pill_read" if facts["kind"] == "read" else "pill_change"),
        }
    return {
        "kind": wait["kind"],
        "label": conv.t("pill_question" if wait["kind"] == "question" else "pill_plan"),
        "name": _scope(conv),
    }


def _put(conv, items: list, *, new: bool = True, move=()) -> None:
    """Write `items` into the thread after the turn in progress. With `new`, what CoCo does next
        goes into a new turn after them
    (the turn so far is closed, so its steps fold), and the steps of `move` go there too."""
    old = conv.run["turn"]
    at = next(i for i, item in enumerate(conv.items) if item is old) + 1
    conv.items[at:at] = items
    if new:
        keep, moved = [], []
        for entry in old["seq"]:
            (moved if entry["k"] == "step" and entry["step"]["id"] in move else keep).append(entry)
        if moved and keep and keep[-1]["k"] == "text":
            moved.insert(
                0, keep.pop()
            )  # the sentence that introduced the step goes with it: it is not an answer
        old["seq"], old["done"] = keep, True
        conv.run["turn"] = {"kind": "turn", "id": conv._id("t"), "seq": moved, "done": False}
        conv.items.insert(at + len(items), conv.run["turn"])


def _close(
    conv,
    wait: dict,
    note: str | None,
    *,
    user: str | None = None,
    reason: str = "",
    new: bool = True,
) -> None:
    """A question or a plan is over: it leaves the list and the thread keeps what became of it
    (`note` a key of the "note_" labels; None: answered / approved)."""
    conv.w_items.remove(wait)
    tail = [{"kind": "user", "id": conv._id("u"), "text": user}] if user else []
    if wait["kind"] == "question":
        _put(
            conv,
            [
                {
                    "kind": "asked",
                    "id": wait["id"],
                    "text": "\n".join(q.get("text", "") for q in wait["questions"]),
                    "note": conv.t("note_" + note) if note else None,
                },
                *tail,
            ],
            new=new,
        )
        return
    step = {
        "kind": "step",
        "id": wait["id"] + "-plan",
        "state": "ok" if note is None else "no",
        "label": conv.t("plan_approved" if note is None else "plan_proposed"),
        "note": conv.t("note_" + note) if note else "",
        "reason": conv.t("reason_expired") if note == "expired" else "",
        "tool": None,
        "input": {},
        "result": "",
        "allowed": False,
        "started": time.time(),
        "blocks": [{"type": "text", "text": wait["text"]}],
    }
    conv.run["turn"]["seq"].append({"k": "step", "step": step})
    _put(conv, tail, new=new)


def _find(conv, kind: str, id) -> dict | None:
    return next((w for w in conv.w_items if w["kind"] == kind and w["id"] == id), None)


def _said(wait: dict, answers) -> str:
    """The answer as the user's message: the picked labels and the free text, or "Label: value"
    lines for a form."""
    questions, lines = {q.get("id"): q for q in wait["questions"]}, []
    for a in answers if isinstance(answers, list) else []:
        if isinstance(a, dict):
            labels = {
                f.get("id"): f.get("label")
                for f in questions.get(a.get("id"), {}).get("fields", [])
            }
            choice = [*(str(p) for p in a.get("picked") or []), str(a.get("other") or "").strip()]
            lines += [
                ", ".join(c for c in choice if c),
                *(
                    f"{labels.get(k, k)}: {v}"
                    for k, v in (a.get("fields") or {}).items()
                    if str(v).strip()
                ),
            ]
    return "\n".join(line for line in lines if line)


def _low(text: str) -> str:
    """The sentence of a family inside another ("... asks before it {what}."): its first letter low
    and no full stop of its own."""
    return text[:1].lower() + text[1:].rstrip(". ")


def _revoke(conv, pid, *, tell: bool = True) -> None:
    grant = next((g for g in conv.w_granted if g["id"] == pid), None)
    if grant is None:
        return
    conv.w_granted.remove(grant)
    if tell:
        _agent(conv, "revoke", pid)
    for item in conv.items:
        if conv.w_sys.get(item.get("id")) == pid:
            item.update(text=conv.t("revoked_line", what=_low(grant["text"])), action=None)


def set_planning(conv, on: bool) -> None:
    on = bool(on)
    if on != conv.w_planning:
        conv.w_planning, conv.w_from = on, len(conv.items)
        _agent(conv, "set_planning", on)


def decline_all(conv) -> None:
    """Stop: what waits besides the requests (which the core declines) is skipped or declined, in
    order."""
    for wait in list(conv.w_items):
        if not wait.get("app_key"):  # the application's form is not the run's: Stop leaves it
            _settle(conv, wait, stopped=True, tell=True, new=True)


def _settle(conv, wait: dict, *, stopped: bool, tell: bool, new: bool) -> None:
    if wait["kind"] == "question":
        _close(conv, wait, "skipped" if stopped else "cancelled", new=new)
        if tell:
            _agent(conv, "skip", wait["id"])
    else:
        _close(conv, wait, "declined" if stopped else "cancelled", new=new)
        if tell:
            _agent(conv, "decline_plan", wait["id"], "")


def end(conv, kind: str, run: dict | None) -> None:
    if kind == "lost":
        for grant in list(conv.w_granted):
            _revoke(conv, grant["id"], tell=False)
        conv.w_planning = False
    for wait in list(conv.w_items) if run else []:
        if not wait.get("app_key"):
            _settle(conv, wait, stopped=kind == "stopped", tell=kind != "lost", new=False)


def act(conv, action: dict, context: dict | None) -> bool:
    kind, id = action.get("type"), action.get("id")
    if kind == "answer":
        wait = _find(conv, "question", id)
        text = wait and _said(wait, action.get("answers"))
        if wait and wait.get("app_key"):
            if isinstance(action.get("answers"), list) and action["answers"]:
                _app_done(conv, wait, action["answers"])
        elif text:
            _close(conv, wait, None, user=text)
            _agent(conv, "answer", id, action["answers"])
    elif kind == "skip":
        wait = _find(conv, "question", id)
        if wait and wait.get("app_key"):
            _app_done(conv, wait, None)
        elif wait:
            _close(conv, wait, "skipped")
            _agent(conv, "skip", id)
    elif kind == "approve_plan":
        wait = _find(conv, "plan", id)
        if wait:
            _close(conv, wait, None)
            conv.w_planning = False
            _agent(conv, "approve_plan", id)
            _agent(conv, "set_planning", False)
    elif kind == "decline_plan":
        wait = _find(conv, "plan", id)
        if wait:
            reason = str(action.get("reason") or "").strip()
            _close(conv, wait, "declined", user=reason)
            _agent(conv, "decline_plan", id, reason)
    elif kind == "carry_out":
        ctx = context if context is not None else conv.w_ctx
        if conv.w_planning and ctx is not None and conv.conn == "ready":
            set_planning(conv, False)
            conv._send({"type": "send", "text": conv.t("carry_out_prompt")}, ctx)
    elif kind == "revoke":
        _revoke(conv, id)
    elif kind == "system_action" and id in conv.w_sys:
        _revoke(conv, conv.w_sys[id])
    else:
        return False
    return True


def on(conv, event: dict) -> bool:
    kind, run = event.get("t"), conv.run
    if kind == "granted":
        conv.w_granted = [g for g in conv.w_granted if g["id"] != event["id"]] + [
            {"id": event["id"], "text": event.get("text", "")}
        ]
        line = {
            "kind": "system",
            "id": conv._id("y"),
            "text": conv.t("granted_line", what=_low(event.get("text", ""))),
            "detail": None,
            "action": {"label": conv.t("granted_ask_again")},
        }
        conv.w_sys[line["id"]], tool, conv.w_grant = event["id"], conv.w_grant, None
        if run:
            _put(
                conv, [line], move={tool}
            )  # the allowed step runs after the line that says why it was not asked again
        else:
            conv.items.append(line)
    elif kind == "revoked":
        _revoke(conv, event.get("id"), tell=False)
    elif run is None:
        return False
    elif kind in ("question", "plan"):
        waits(conv)  # number the requests already waiting before this one
        if _find(conv, kind, event["id"]):
            return True
        wait = {
            "kind": kind,
            "id": event["id"],
            "tool_id": event.get("tool_id"),
            "n": next(conv.w_count),
        }
        if kind == "plan":
            wait["text"] = str(event.get("text") or "")
        else:
            wait.update(
                source=event.get("source") or "coco",
                questions=[q for q in event.get("questions") or [] if _shown(q)],
            )
        conv.w_quiet.add(wait["tool_id"])
        if kind == "question" and not wait["questions"]:
            step = run["steps"].get(wait["tool_id"])
            if step:
                step["state"] = "bad"
            _agent(conv, "skip", wait["id"])
        else:
            conv.w_items.append(wait)
    elif kind == "expired":
        wait = next((w for w in conv.w_items if w["id"] == event.get("id")), None)
        if wait:
            _close(conv, wait, "expired")
    elif kind == "standing":
        conv.w_stand.add(event.get("tool_id"))
        step = run["steps"].get(event.get("tool_id"))
        if step:
            step["standing"] = True
    else:
        return False
    return True


def _shown(q) -> bool:
    """A question with no text and nothing to choose or fill in is an agent's mistake: it is not
    shown."""
    return (
        isinstance(q, dict)
        and bool(q.get("text"))
        and bool(q.get("options") or q.get("other") or q.get("fields"))
    )


def view(conv) -> dict:
    out, ws = {}, waits(conv)
    if ws:
        first = ws[0]
        out["wait"] = {
            "id": first["id"],
            "kind": first["kind"],
            "more": {"count": len(ws), "next": ws[1]["kind"]} if len(ws) > 1 else None,
            **{k: first[k] for k in _QUESTION_KEYS if k in first},
        }
    if conv.w_planning and not any(
        w["kind"] == "plan" for w in ws
    ):  # the strip and a plan never speak at once
        answered = conv.run is None and any(
            i["kind"] == "turn" and any(e["k"] == "text" and e["text"].strip() for e in i["seq"])
            for i in conv.items[conv.w_from :]
        )
        out["mode"] = {"planning": True, "can_carry_out": answered}
    if conv.w_granted:
        out["granted"] = [dict(g) for g in conv.w_granted]
    return out


def on_message(conv, action: dict, message: dict) -> None:
    conv.w_ctx = message["ctx"]


def on_step(conv, run: dict, step: dict, event: dict) -> None:
    if step["id"] in conv.w_stand:
        step["standing"] = True


def on_answer(conv, item: dict, answer: dict) -> None: ...
