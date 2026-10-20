"""Ask CoCo, the conversation: events to thread, steps, requests, queue (feature file 1.1 to 1.4).

Pure Python, no Streamlit, no SDK. One `Conversation` per browser session; the agent (cortex.py,
or testing/scripted.py) reports plain events, the window reads one `view` and sends one action.

    conv = Conversation(cwd, policy=None, features=None, prompts=None, labels=None,
                        agent=None, on_files_changed=None)
    conv.set_labels(labels)   # another table of texts (the host changed language): see there
    conv.set_cwd(cwd)      # the working folder is the agent's folder: when it changes, the
                           # conversation ends as "new" does, with a line saying why
    conv.drain()           # True: files of the working folder changed (on_files_changed was called
                           # once with their paths): clear the caches and rerun once
    view = conv.view()     # a dict of plain data; call it once per run (it hands `restore` over
        once)
    conv.act({"type": "send", "text": "..."}, context)   # context: what the host's context()
        returned
    conv.busy              # True while something can still arrive: poll while it is
    conv.add_drafts([(title, text)])   # one bubble each, with Copy, no agent call
    conv.request_from_page(label, text, context, key=None) / conv.result_for(key)
    conv.notice(text, label=None, then=None)      # one line in the thread in the host's words

Built from: the working folder `cwd`; a `policy` (an object with judge / describe / rights, or a
function of the context returning one; None: `FolderPolicy(cwd)`; called once per message and frozen
with it); `Features` (features.py); `prompts` (first-screen prompts: text, or {title, text, fill});
`labels` (a dict of texts over `LABELS` below, with `{name}`-style placeholders); `agent` (a
    function
(emit) -> agent; None: `agent_factory()`, which gives the scripted agent when
STREAMLIT_COCO_AGENT=mock); and `on_files_changed` (a function ([path]) called once after the agent
changed files).

The conversation freezes a copy of the context when a message is sent and keeps it with a queued
message; navigation afterwards moves nothing. Keys of the context with a meaning here (all
    optional):
`scope` {name, folder}, `instructions`, `user` {name, language}; the conversation adds `screen` (the
action's own `screen` {text, dialog, selection}, cut, only with Features.page_text) and `rights`
    (the
policy's). Everything else is passed to the agent as facts.

Actions: send{text, files, screen} | prompt{text} | stop | allow{id} | decline{id} | unqueue{id} |
    new
         | connect{profile, file} | disconnect | reconnect | retry | seen      (ids are the `id` of
             a
         request or a queued message) and: answer, skip, approve_plan, decline_plan, carry_out,
         revoke, set, show_earlier, system_action

View:
    status    not_installed | not_connected | connecting | ready | working | waiting | lost
    setup     {missing: "package" | "program", command: text}          only when not_installed
    profiles  [name], profile: name | None, error: text | None          for not_connected,
        connecting
    prompts   [text | {title, text, fill}]   only on the first screen (ready, nothing asked), at
        most 3
    thread    [ {kind: "user", id, text}
              | {kind: "scope", text}                                    "About <scope name>"
              | {kind: "steps", id, folded, summary, items: [step]}       a section: summary is the
                                          sentence CoCo said before its steps (inline Markdown),
                                              None
                                          when no sentence introduced them; items may be empty: then
                                          the sentence stands alone
              | step                      a failed, declined or refused step kept outside the fold
              | {kind: "answer", id, text, streaming}
              | {kind: "draft", id, title, text}
              | {kind: "system", id?, text, detail, action: "retry" | {label} | None} ]
    step      {kind: "step", id, state: run | ok | bad | no, label, note, reason, tool, input,
        result,
               allowed, started, elapsed}
              note is the status in words (the "note_" labels); a failed step has none, its mark
                  says
              it; reason says why in plain words; started is epoch seconds, elapsed is whole seconds
              while state is run; input is the tool's exact input; result is cut at 20 000
                  characters
              and, in a finished turn, at 2 000 in the view ("... [truncated]"); a call that ran and
              exited non-zero for what it found, which the policy's `exit_note(tool, input,
                  content)`
              recognises, is "ok", its result opens with that text
    request   None | {id, kind: "read" | "change", question, where, reads, changes, evidence_label,
              evidence, standing}: the facts the policy wrote; the first pending request (the thread
              hides its step until it is answered)
    queue     [{id, text, note, full}]       restore  text | None, handed over once      rev  number
    pill      None | {kind: "request" | "answer" | "failed" | "question" | "plan", label, name}
              "seen" clears an answer or failed pill

Optional keys, each present only when the host's Features (or its data) call for it:
    wait      None | {id, kind: "request" | "question" | "plan", more, ...}   status "waiting"
        while set
              THE ONE WAITING BLOCK: the first thing waiting for the user, of any kind, in the order
              they came; the window draws only this one. more: None | {count, next}
              kind "question": source: "coco" | "app"; questions: [Q], in order
                               Q = {id, text, kind: "choice", multi, options: [{label,
                                   description}],
                                    other: None | {label}}
                                 | {id, text, kind: "form", fields: [F]}
                               F = {id, label, type: "text" | "longtext" | "number" | "choice",
                                    choices: [text], required, value}
              kind "plan":     text   CoCo's plan, Markdown
    mode      None | {planning: True, can_carry_out: bool}                 Features.planning
    options   [{id: "plan" | "latest" | "shorten" | "raw", label, sub, on}]   Features.planning /
        display
              latest and raw are applied here (hidden, step.raw); shorten is the window's own
    hidden    number   earlier messages left out of the thread by "latest"
    granted   [{id, text}]   what runs without asking, in words (a policy with standing=True)
    session   [{label, value}]                                             Features.session_details
    attach    {multi, accept: [".csv", ...] (empty: any), max_mb, existing: [file name]}
                                                                            Features.attachments
    type_ahead  bool   the field is shown while status is "connecting"     Features.queue
    send_held   True when Features.queue is off and CoCo works, waits or connects: the field keeps
                what is typed, Send is unavailable (a refused message comes back in `restore`)
    page_text   True with Features.page_text: only then does the window read the page for `screen`
    problem   text | None   not_connected with an error: what happened and what to do in plain words
    profile_files   None | [{file, profiles: [name]}]   the connection files with their profiles

Thread items, besides the above:
    {kind: "asked", id, text, note: None | "Skipped" | "Expired"}   a question CoCo asked, kept as
                                          CoCo's message; the answer follows as an ordinary `user`
                                              item
    user      gains  files: [name], sending: number, full: text | None
    answer    gains  blocks: [Block]      drawn after text
    steps.items[i]  may also be {kind: "reasoning", id, text}                  Features.reasoning
    step      gains  blocks: [Block], raw: None | {request, result}, standing: bool
    Block: {type: "data", id, title, fields: [{label, value}], tables: [T], json} | {type: "text",
        text}
           T = {id, label, columns: [{name, kind: "text" | "number"}], rows: [[text]], total}
           rows are the rows received (at most 200)

Python API for the page: `request_from_page(label, text, context, key=None)` makes the user message
(label as text, text as `full`), queued with the note "Sent when you connect" when not yet
    connected;
`result_for(key)` hands the structured result of such a job back, once.

Events from an agent, as plain dicts with a "t" key:
    connected | connect_failed{message} | lost{message}
    text{text}                a streamed fragment (never thinking, never tool arguments)
    snapshot{text}            a complete assistant text block
    result{text, error, message}   the turn's end; text is the final result, which may repeat what
                              was streamed
    error{message, retry}     the turn failed; retry is true only when trying again can end
        differently
    stopped{}                 the run really ended after a stop
    tool_use{id, name, input, started?, raw?}   tool_result{id, content, error, data?, raw?}
    refused{tool_id, reason}  the pre-tool hook refused the call (policy, or revalidation after
        Allow)
    request{id, tool_id, facts}   an agreement request   expired{id, tool_id} (also question, plan)
    question{id, tool_id, source, questions}   plan{id, tool_id, text}
    granted{id, text, family}   revoked{id}   standing{tool_id}
    structured{tool_id, data}   the turn's result as data   reasoning{text}

What the conversation asks of an agent (each optional; it never fails when one is missing):
    setup() / profiles() / connect(profile, cwd[, file=]) / send(text, ctx, policy) / stop() /
        close()
    decide(request_id, allow, standing=False)    revoke(permission_id)
    answer(id, answers) / skip(id)               approve_plan(id) / decline_plan(id, reason)
    set_planning(on) / set_raw(on) / set_reasoning(on)
    session_facts() -> [{label, value}]          connection_files() -> [{file, profiles}]
"""

from __future__ import annotations

import copy
import itertools
import logging
import os
import queue
import time
from collections.abc import Callable
from pathlib import Path

from streamlit_coco import extras, waits
from streamlit_coco.features import Features
from streamlit_coco.labels import DEFAULT

_LOG = logging.getLogger(__name__)
_RESULT_LIMIT = 20_000  # kept per step
_SENT_LIMIT = (
    2_000  # sent for a step of a finished turn: the window polls, and the thread only grows
)
_CUT = " ... [truncated]"
_PROFILES_TTL = 10  # seconds before the list of Snowflake connections is read again
_NONE = object()
_PARTS = (waits, extras)  # state, actions, events and view keys of the optional parts
_SCREEN = {
    "text": 12000,
    "dialog": 4000,
    "selection": 2000,
}  # characters kept of what the page showed
_PROMPTS_SHOWN = 3

# Every sentence the conversation writes, by key. A host overrides any of them with `labels=`.
# `{name}` marks a value the conversation fills in. Texts written by a policy, an agent or the
# host's own context (a request's question, a step's name, a session fact) are theirs, not here.
LABELS = {key[len("agent.") :]: text for key, text in DEFAULT.items() if key.startswith("agent.")}


def agent_factory(options=None) -> Callable:
    """A function (emit) -> agent: the scripted agent when STREAMLIT_COCO_AGENT=mock, else Cortex
        Code
    with the host's `CocoOptions` (cortex.py refuses the tool lists: see its docstring)."""

    def make(emit):
        if os.environ.get("STREAMLIT_COCO_AGENT") == "mock":
            from streamlit_coco.testing.scripted import ScriptedAgent

            return ScriptedAgent(emit)
        from streamlit_coco.cortex import Agent

        return Agent(emit, options)

    return make


class Conversation:
    def __init__(
        self,
        cwd,
        *,
        policy=None,
        features: Features | None = None,
        prompts=None,
        labels: dict | None = None,
        agent: Callable | None = None,
        on_files_changed: Callable | None = None,
        connect: str | None = None,
    ) -> None:
        self.cwd = Path(cwd)
        self.policy, self.features = policy, features or Features()
        self.prompts = list(prompts or [])
        self.set_labels(labels)
        self._factory = agent or agent_factory()
        self._on_files_changed = on_files_changed
        self._default_policy = None
        self._changed: list[str] = []
        self.profile: str | None = None
        self.file: str | None = None  # the connection file the profile was chosen from
        self.agent = None
        self.folder: Path | None = None  # the folder the session works in; None while there is none
        self._reset()
        self._fresh_agent(connect or None)

    def set_labels(self, labels: dict | None) -> None:
        """The host's texts, which it may change from one run to the next (another language): every
        sentence written from now on, and what the view works out each time (the menu's options,
        a queued message's note, the connection problem, a pill the policy did not word), is in
        the new ones. What is already written (a line of the thread, a step's note, the pill of
        an answer) stays as it was written; a policy's sentences are the policy's."""
        self.labels = {**LABELS, **{k.removeprefix("agent."): v for k, v in (labels or {}).items()}}

    def t(self, key: str, **values) -> str:
        """A label's text, with its values filled in."""
        text = self.labels.get(key) or LABELS.get(key, key)
        try:
            return text.format(**values) if values else text
        except (KeyError, IndexError, ValueError):
            return text  # a host's text with a placeholder we do not know: shown as it is

    def close(self) -> None:
        if self.agent is not None:
            self.agent.close()

    def __del__(self) -> None:  # the browser session ended: nothing else would stop the program
        try:
            self.close()
        except Exception:  # at interpreter exit there may be nothing left to close
            pass

    def set_cwd(self, cwd) -> None:
        """The working folder is the agent's folder and the base of relative paths: when it changes
        while a session works in the old one, the conversation ends as New conversation does, and
        says why."""
        self.cwd = Path(cwd)
        if self.folder is not None and self.cwd != self.folder:
            self._restart()
            self.items.append(
                {"kind": "system", "text": self.t("folder_changed"), "detail": "", "action": None}
            )
            self.rev = 1

    # ------------------------------------------------------------------ session

    def _reset(self) -> None:
        self.items: list[dict] = []
        self.queue: list[dict] = []
        self.requests: list[dict] = []
        self.run: dict | None = None
        self.last: dict | None = None  # the message of a failure that can be retried
        self.pill = None
        self.restore: str | None = None
        self.error: str | None = None
        self.scope = _NONE
        self.rev = 0
        self._ids = itertools.count(1)
        for part in _PARTS:
            part.reset(self)

    def _fresh_agent(self, connect: str | None = None, file: str | None = None) -> None:
        if self.agent is not None:
            self.agent.close()
        self.inbox: queue.SimpleQueue = (
            queue.SimpleQueue()
        )  # an old agent writes to a queue nobody reads
        self.agent = self._factory(self.inbox.put)
        if self.features.reasoning and hasattr(self.agent, "set_reasoning"):
            self.agent.set_reasoning(True)
        self.setup = self.agent.setup()
        self.conn, self.folder, self._names = "none", None, None
        if connect and not self.setup:
            self._connect(connect, file)

    def _connect(self, profile: str, file: str | None = None) -> None:
        self.conn, self.profile, self.file, self.folder = "connecting", profile, file, self.cwd
        self.agent.connect(profile, str(self.folder), **({"file": file} if file else {}))

    def _restart(self) -> None:
        """A new session of the same profile when there was one to keep, in a conversation with
        nothing in it."""
        profile = self.profile if self.conn in ("ready", "lost") else None
        self._reset()
        self._fresh_agent(profile, self.file)

    def _id(self, prefix: str) -> str:
        return f"{prefix}{next(self._ids)}"

    @property
    def busy(self) -> bool:
        return self.run is not None or self.conn == "connecting" or bool(self.requests)

    # ------------------------------------------------------------------ actions

    def act(self, action: dict, context: dict | None = None) -> None:
        kind, self.rev = action.get("type"), self.rev + 1
        if kind in ("send", "prompt"):
            self._send(action, context)
        elif kind == "stop" and self.run and not self.run["stopping"]:
            self.run["stopping"] = True
            for request in list(self.requests):
                self._answer(request, False, self.t("note_declined"))
            waits.decline_all(self)
            self.agent.stop()
        elif kind in ("allow", "decline"):
            request = next((r for r in self.requests if r["id"] == action.get("id")), None)
            if request:
                self._answer(
                    request, kind == "allow", self.t("note_declined"), bool(action.get("standing"))
                )
        elif kind == "unqueue":
            message = next((m for m in self.queue if m["id"] == action.get("id")), None)
            if message:
                self.queue.remove(message)
                self.restore = (
                    message["text"]
                    if self.restore is None
                    else self.restore + "\n\n" + message["text"]
                )
        elif kind == "new":
            self._restart()
        elif kind == "connect" and self.conn == "none" and not self.setup:
            self.error = None
            self._connect(str(action.get("profile") or ""), str(action.get("file") or "") or None)
        elif kind == "disconnect":
            self._reset()
            self.profile = self.file = None
            self._fresh_agent()
        elif kind == "reconnect" and self.conn == "lost":
            self._fresh_agent(self.profile, self.file)
        elif kind == "retry" and self.last and self.run is None and self.conn == "ready":
            message, self.last = self.last, None
            self.items = [i for i in self.items if i.get("action") != "retry"]
            self._start(message, show_user=False)
        elif kind == "seen":
            self.pill = None
        else:
            any(part.act(self, action, context) for part in _PARTS)

    def freeze(self, context: dict | None, screen=None) -> tuple[dict, object]:
        """The context of one message, copied and completed, and the policy it is judged by."""
        ctx = copy.deepcopy(dict(context or {}))
        if self.features.page_text and isinstance(screen, dict):
            ctx["screen"] = {
                key: str(value)[:limit]
                for key, limit in _SCREEN.items()
                if (value := screen.get(key)) and isinstance(value, str)
            }
        policy = self._policy(ctx)
        try:
            ctx["rights"] = policy.rights()
        except Exception:  # a policy that cannot say what is free tells the agent nothing
            _LOG.exception("The policy could not give its rights")
            ctx["rights"] = {}
        return ctx, policy

    def _policy(self, ctx: dict):
        policy = self.policy
        if policy is not None and not hasattr(policy, "judge") and callable(policy):
            try:
                policy = policy(ctx)
            except Exception:  # the safest policy stands in for one that failed
                _LOG.exception("The host's policy function failed; the default policy is used")
                policy = None
        if policy is None:
            if self._default_policy is None:
                from streamlit_coco.policy import FolderPolicy

                self._default_policy = FolderPolicy(self.cwd)
            policy = self._default_policy
        return policy

    def _send(self, action: dict, context: dict | None) -> None:
        """A message from the field or a prompt button: accepted, then started or queued behind the
        run."""
        text = str(action.get("text") or "").strip()
        if self.setup or not (text or action.get("files")):
            return
        free = self.conn == "ready" and self.run is None and not self.queue
        if self.conn not in ("ready", "connecting"):
            return
        if not free and not self.features.queue:  # the window does not let this happen (send_held)
            self.restore = f"{self.restore}\n\n{text}" if self.restore else text  # never lost
            return
        ctx, policy = self.freeze(context, action.get("screen"))
        message = {"id": self._id("q"), "text": text, "ctx": ctx, "policy": policy}
        for part in _PARTS:
            part.on_message(self, action, message)
        if not message.get(
            "ex_drop"
        ):  # nothing to send: every file was refused and there was no text
            if self.conn == "ready" and self.run is None and not self.queue:
                self._start(message)
            else:
                self.queue.append(message)  # behind the run, or behind the connection (typed ahead)
        extras.sent(self, message)

    def request_from_page(self, label, text, context=None, key=None, *, hint=None) -> bool:
        """A button of the page asks in the user's name; see extras."""
        return extras.request_from_page(self, label, text, context, key, hint)

    def result_for(self, key, take: bool = True):
        return extras.result_for(self, key, take)

    def ask_form(self, key: str, title: str, fields: list[dict]) -> None:
        """The application asks a form; see waits.ask_form."""
        waits.ask_form(self, key, title, fields)

    def form_result(self, key: str, take: bool = True) -> dict | None:
        return waits.form_result(self, key, take)

    def notice(self, text: str, label: str | None = None, then=None) -> str:
        return extras.notice(self, text, label, then)

    def add_drafts(self, drafts) -> None:
        for title, text in drafts:
            self.items.append({"kind": "draft", "id": self._id("d"), "title": title, "text": text})
        self.rev += 1

    def _start(self, message: dict, show_user: bool = True) -> None:
        if show_user:
            name = (message["ctx"].get("scope") or {}).get("name") or None
            self.items.append(
                {
                    "kind": "user",
                    "id": message["id"],
                    "text": message["text"],
                    **message.get("show", {}),
                }
            )
            if name != self.scope:
                if (
                    self.scope is not _NONE or name
                ):  # a host that gives no scope never sees the line
                    text = self.t("scope_about", name=name) if name else self.t("scope_none")
                    self.items.append({"kind": "scope", "text": text})
                self.scope = name
        turn = {"kind": "turn", "id": self._id("t"), "seq": [], "done": False}
        self.items.append(turn)
        self.run = {
            "message": message,
            "turn": turn,
            "steps": {},
            "verdicts": {},
            "allowed": set(),
            "stopping": False,
        }
        self.pill = None
        self.agent.send(message.get("prompt", message["text"]), message["ctx"], message["policy"])

    def _answer(self, request: dict, allow: bool, note: str, standing: bool = False) -> None:
        self.requests.remove(request)
        # only a request that offered it
        standing = allow and standing and bool(request["facts"].get("standing"))
        if standing:
            self.w_grant = request["tool_id"]
        if allow:
            self.run["allowed"].add(request["tool_id"])
            step = self.run["steps"].get(request["tool_id"])
            if step:
                step.update(allowed=True, note=self.t("note_allowed"))
        else:
            self._verdict(request["tool_id"], note)
        self.agent.decide(request["id"], allow, **({"standing": True} if standing else {}))

    def _verdict(self, tool_id: str, note: str, reason: str = "") -> None:
        """The hook's own decision for a call. It overrides whatever the CLI reports afterwards."""
        self.run["verdicts"][tool_id] = (note, reason)
        step = self.run["steps"].get(tool_id)
        if step:
            step.update(state="no", note=note, reason=reason)

    # ------------------------------------------------------------------ events

    def drain(self) -> bool:
        """Apply what the agent reported. True when files of the working folder changed (the host's
        `on_files_changed` was then called once): clear the caches, rerun once."""
        changed = False
        while True:
            try:
                event = self.inbox.get_nowait()
            except queue.Empty:
                break
            self.rev += 1
            try:
                changed = self._on(event) or changed
            except Exception:  # one event the app cannot apply must not take the page down
                _LOG.exception("A CoCo event could not be applied: %r", event)
        paths, self._changed = sorted(set(self._changed)), []
        if paths and self._on_files_changed:
            try:
                self._on_files_changed(paths)
            except Exception:  # the host's hook failing is not the conversation's failure
                _LOG.exception("on_files_changed failed")
        return changed

    def _on(self, event: dict) -> bool:
        kind, run = event["t"], self.run
        if kind == "connected":
            self.conn = "ready"
        elif kind == "connect_failed":
            self.conn, self.error = "none", event.get("message")
        elif kind == "lost":
            if self.conn != "lost":  # the failed turn and the session's own watch both report it
                self._end("lost", detail=event.get("message", ""))
        elif run is None:
            waits.on(self, event)  # only a grant or a revocation means something without a run
            return False  # a late event of a run that has ended
        elif kind in ("text", "snapshot"):
            self._text(run["turn"]["seq"], event["text"], snapshot=kind == "snapshot")
        elif kind == "tool_use":
            self._tool_use(run, event)
        elif kind == "refused":
            self._verdict(event["tool_id"], self.t("note_not_allowed"), event["reason"])
        elif kind == "request":
            self.requests.append(
                {"id": event["id"], "tool_id": event["tool_id"], "facts": event["facts"]}
            )
        elif kind == "expired":
            request = next((r for r in self.requests if r["id"] == event["id"]), None)
            if request:
                self.requests.remove(request)
                self._verdict(event["tool_id"], self.t("note_expired"), self.t("reason_expired"))
            else:
                waits.on(self, event)  # a question or a plan
        elif kind == "tool_result":
            return self._tool_result(run, event)
        elif kind == "result" and event.get("error"):
            self._end(
                "stopped" if run["stopping"] else "failed",
                event.get("message") or event.get("text") or "",
            )
        elif kind == "result":
            self._reconcile(run["turn"]["seq"], event.get("text"))
            self._end("stopped" if run["stopping"] else "done")
        elif kind == "error":
            self._end(
                "stopped" if run["stopping"] else "failed",
                event.get("message", ""),
                retry=bool(event.get("retry")),
            )
        elif kind == "stopped":
            self._end("stopped")
        else:
            any(part.on(self, event) for part in _PARTS)
        return False

    @staticmethod
    def _text(seq: list, text: str, *, snapshot: bool) -> None:
        last = seq[-1] if seq and seq[-1]["k"] == "text" else None
        if last is None:
            seq.append({"k": "text", "text": text})
        elif not snapshot:
            last["text"] += text  # a fragment always appends
        elif last["text"] and (last["text"] == text or last["text"].endswith(text)):
            pass  # the snapshot of what was streamed
        else:
            # complete, or next to it
            last["text"] = text if text.startswith(last["text"]) else last["text"] + text

    @staticmethod
    def _reconcile(seq: list, result) -> None:
        """The final result repeats the last block, or all the turn's text, or is all there is, or
        completes a partial stream. Only what is new is added."""

        def norm(value) -> str:
            return "".join(str(value or "").split())

        value = norm(result)
        texts = [e for e in seq if e["k"] == "text"]
        shown = [norm(e["text"]) for e in texts]
        if not value or value in shown or value == "".join(shown):
            return
        if texts and seq[-1] is texts[-1] and value.startswith(shown[-1]):
            texts[-1]["text"] = result
        else:
            seq.append({"k": "text", "text": result})

    def _tool_use(self, run: dict, event: dict) -> None:
        started = event.get("started") or time.time()
        try:
            label = run["message"]["policy"].describe(event["name"], event.get("input"))
        except Exception:  # a step is named by its tool when the policy cannot say
            label = str(event["name"])
        step = {
            "kind": "step",
            "id": event["id"],
            "state": "run",
            "label": label,
            "note": "",
            "reason": "",
            "tool": event["name"],
            "input": event.get("input") or {},
            "result": "",
            "allowed": event["id"] in run["allowed"],
            "started": started,
        }
        if step["allowed"]:
            step["note"] = self.t("note_allowed")
        run["steps"][event["id"]] = step
        run["turn"]["seq"].append({"k": "step", "step": step})
        if event["id"] in run["verdicts"]:
            self._verdict(event["id"], *run["verdicts"][event["id"]])

    def _tool_result(self, run: dict, event: dict) -> bool:
        step = run["steps"].get(event["id"])
        if step is None:
            return False
        content = str(event.get("content") or "")
        step["result"] = content[:_RESULT_LIMIT] + (_CUT if len(content) > _RESULT_LIMIT else "")
        for part in _PARTS:
            part.on_step(self, run, step, event)
        if event["id"] in run["verdicts"]:
            return False  # refused, declined or expired: never done, whatever the CLI says
        if content.startswith("Tool denied"):  # the CLI's own refusal, reported as a success
            step.update(state="bad", reason=self.t("reason_cli_refused"))
            return False
        exit_note = getattr(run["message"]["policy"], "exit_note", None)
        note = event.get("error") and exit_note and exit_note(step["tool"], step["input"], content)
        if note:  # a call that ran and exited non-zero for what it found
            step["state"], step["result"] = "ok", note + chr(10) * 2 + step["result"]
            return False
        step["state"] = "bad" if event.get("error") else "ok"
        if event.get("error"):
            return False  # a failed step shows its mark only
        return self._written(step)

    def _written(self, step: dict) -> bool:
        """A change that succeeded in the working folder: remember the file for
        `on_files_changed`."""
        if str(step["tool"]).lower() not in ("edit", "write"):
            return False
        raw = step["input"].get("file_path")
        try:
            path = (self.cwd / str(raw)).resolve()
            path.relative_to(self.cwd.resolve())
        except (OSError, ValueError, TypeError):
            return False
        if not raw or not path.is_file():
            return False
        self._changed.append(str(path))
        return True

    def _end(self, kind: str, detail: str = "", retry: bool = False) -> None:
        """The run is over: done, failed, lost or stopped. Settles its steps, its requests and the
        queue."""
        run, requests, self.requests = self.run, self.requests, []
        waits.end(self, kind, run)
        if run:
            for request in requests:
                note = self.t("note_declined" if kind == "stopped" else "note_cancelled")
                run["verdicts"][request["tool_id"]] = (note, "")
                if kind != "lost":
                    self.agent.decide(request["id"], False)
            for step in run["steps"].values():
                verdict = run["verdicts"].get(step["id"])
                if verdict:
                    step.update(state="no", note=verdict[0], reason=verdict[1])
                elif step["state"] == "run":
                    if kind == "done":
                        step.update(state="ok")
                    else:
                        note = self.t("note_stopped" if kind == "stopped" else "note_interrupted")
                        step.update(state="bad", note=note)
            run["turn"]["done"] = True
        self.run = None
        name = ((run or {}).get("message", {}).get("ctx", {}).get("scope") or {}).get("name", "")
        if kind == "done":
            self.pill = {"kind": "answer", "label": self.t("pill_answer"), "name": name}
            if self.queue:
                self._start(self.queue.pop(0))
            return
        if self.queue:  # the user stopped, or it failed: they decide what is sent next
            texts = [m["text"] for m in self.queue]
            self.restore = "\n\n".join([self.restore, *texts] if self.restore else texts)
            self.queue = []
        if kind == "stopped":
            self.pill = None
        elif kind == "lost":
            self.conn = "lost"
            self.pill = {"kind": "failed", "label": self.t("pill_lost"), "name": name}
            self.items.append(
                {"kind": "system", "text": self.t("lost_text"), "detail": detail, "action": None}
            )
        else:
            self.last = run["message"] if run and retry else None
            self.pill = {"kind": "failed", "label": self.t("pill_failed"), "name": name}
            self.items.append(
                {
                    "kind": "system",
                    "text": self.t("failed_text"),
                    "detail": detail,
                    "action": "retry" if self.last else None,
                }
            )

    # ------------------------------------------------------------------ view

    def view(self) -> dict:
        extras.release(self)
        if self.setup:
            status = "not_installed"
        elif self.conn == "ready":
            status = "waiting" if waits.waits(self) else "working" if self.run else "ready"
        else:
            status = {"none": "not_connected"}.get(self.conn, self.conn)
        first = status == "ready" and not any(i["kind"] == "user" for i in self.items)
        restore, self.restore = self.restore, None
        setup = self.setup
        if setup and setup.get("missing") == "package" and self.labels.get("setup_package"):
            setup = {**setup, "command": self.labels["setup_package"]}
        request = waits.request(self)
        pill = waits.pill(self) or self.pill
        base = {
            "status": status,
            "setup": setup,
            "profiles": self._profile_names() if status == "not_connected" else [],
            "profile": self.profile,
            "error": self.error,
            "prompts": list(self.prompts[:_PROMPTS_SHOWN]) if first else [],
            "thread": self.thread(),
            "request": {"id": request["id"], **request["facts"]} if request else None,
            "queue": [{"id": m["id"], "text": m["text"]} for m in self.queue],
            "restore": restore,
            "pill": pill,
            "rev": self.rev,
        }
        for part in _PARTS:
            base.update(part.view(self))
        if self.features.page_text:
            base["page_text"] = True
        if not self.features.queue and status in ("working", "waiting", "connecting"):
            base["send_held"] = True
        return base

    def thread(self) -> list[dict]:
        """The view's thread alone: no side effect (view() hands `restore` over once)."""
        return [view for item in self.items for view in self._item(item)]

    def _profile_names(self) -> list[str]:
        """The agent reads the connections file for its list: once every few seconds, not on every
        page run."""
        if self._names is None or time.monotonic() - self._names[0] > _PROFILES_TTL:
            self._names = (time.monotonic(), self.agent.profiles())
        return self._names[1]

    def _item(self, item: dict) -> list[dict]:
        if item["kind"] != "turn":
            return [dict(item)]
        seq, now = item["seq"], time.time()
        # a step waits behind its own request
        hidden = {r["tool_id"] for r in self.requests} | waits.quiet(self)
        sections, answer = (
            [],
            None,
        )  # a section starts at each sentence CoCo says before a group of calls
        for index, entry in enumerate(seq):
            if entry["k"] == "text" and entry["text"].strip():
                if index == len(seq) - 1:
                    answer = entry
                else:
                    sections.append({"summary": " ".join(entry["text"].split()), "items": []})
            elif entry["k"] == "reasoning":
                if not sections:
                    sections.append({"summary": None, "items": []})
                sections[-1]["items"].append(
                    {"kind": "reasoning", "id": entry["id"], "text": entry["text"]}
                )
            elif entry["k"] == "step" and entry["step"]["id"] not in hidden:
                step = entry["step"]
                if not sections:
                    sections.append({"summary": None, "items": []})
                result = step["result"]
                sent = (
                    result[:_SENT_LIMIT] + _CUT
                    if item["done"] and len(result) > _SENT_LIMIT
                    else result
                )
                elapsed = int(now - step["started"]) if step["state"] == "run" else 0
                sections[-1]["items"].append({**step, "result": sent, "elapsed": elapsed})
        folded = answer is not None or item["done"]

        def kept(p: dict) -> bool:  # what stays inside the fold
            failed = p.get("state") in ("bad", "no")
            if failed and folded:
                return False
            return self.features.steps or failed or p["kind"] == "reasoning"

        out = [
            {
                "kind": "steps",
                "id": f"{item['id']}-steps{n}",
                "folded": folded,
                "summary": sec["summary"],
                "items": [p for p in sec["items"] if kept(p)],
            }
            for n, sec in enumerate(sections)
        ]
        out = [sec for sec in out if sec["summary"] or sec["items"]]
        out += [
            p
            for sec in sections
            for p in sec["items"]
            if folded and p.get("state") in ("bad", "no")
        ]
        if answer:
            shown = {
                "kind": "answer",
                "id": item["id"] + "-answer",
                "text": answer["text"],
                "streaming": not item["done"],
            }
            for part in _PARTS:
                part.on_answer(self, item, shown)
            out.append(shown)
        return out
