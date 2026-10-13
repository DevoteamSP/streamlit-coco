"""Ask CoCo, the window: the launcher at the bottom right of the page and the floating chat window.

    coco = st_coco.ask_coco(".")            # once per page run; returns the window's handle
    coco = get_window("coco")               # the same handle, anywhere else on the page

One component (static/coco/*, joined by streamlit_coco.assets), mounted inside a fragment. The
browser side holds the window's own state (open, menu, folds, what is typed, scroll) and draws the
`view` of the conversation; it sends one action at a time. Because the component sits in a
fragment, an action or a poll re-runs that fragment only, never the page. While CoCo works the
component asks for the next view by itself; idle, nothing runs. A file change the agent made is
the one thing that reruns the page, once, after `on_files_changed` was called.

What the component receives as `data`: view, ack, open_token, sess, spark, labels (the table of
streamlit_coco.labels with the host's overrides), theme ({name: CSS value} over the CSS defaults,
plus `avoid`, the selectors the launcher must clear), exclude (Features.page_exclude),
and features ({motion, copy, steps}).
"""

from __future__ import annotations

import copy
import json
import uuid
from collections.abc import Callable
from functools import lru_cache, partial
from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_coco import assets
from streamlit_coco import labels as labels_table
from streamlit_coco.errors import CocoError

# The lowest Streamlit on which the window runs (st.components.v2 in a fragment, isolated styles):
# found by driving a five-line app from 1.53 upward (feature file, section 4).
STREAMLIT_FLOOR = (1, 53)
_REFUSED = ("allowed_tools", "disallowed_tools", "require_approval_for")


def _version(text: str) -> tuple[int, ...]:
    parts = []
    for piece in text.split(".")[:3]:
        digits = "".join(c for c in piece if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _check_streamlit() -> None:
    need = ".".join(map(str, STREAMLIT_FLOOR))
    if _version(st.__version__) < STREAMLIT_FLOOR or not hasattr(
        getattr(st, "components", None), "v2"
    ):
        raise CocoError(
            f"Ask CoCo needs Streamlit {need} or later (this is {st.__version__}): "
            f"upgrade with `pip install -U 'streamlit>={need}'`."
        )


@lru_cache(maxsize=1)
def _component():
    return st.components.v2.component(
        "streamlit_coco_ask_coco",
        html='<div class="coco-root"></div>',
        css=assets.css(),
        js=assets.js(),
        isolate_styles=True,
    )


def _slot(key: str) -> str:
    return f"_streamlit_coco:{key}"


def _state(key: str) -> dict:
    found = st.session_state.get(_slot(key))
    if found is None:
        raise CocoError(
            f"No Ask CoCo window with key {key!r}: call ask_coco(..., key={key!r}) first."
        )
    return found


class Window:
    """The handle of one window (feature file 1.1). Cheap: it holds only the key."""

    def __init__(self, key: str) -> None:
        self.key = key

    @property
    def _s(self) -> dict:
        return _state(self.key)

    @property
    def conversation(self):
        """The conversation object (view and actions as plain data)."""
        return self._s["conv"]

    # ---- the application asks CoCo
    def ask(
        self, label: str, text: str | None = None, *, key: str | None = None, schema=None
    ) -> bool:
        """A button of the page asks in the user's name: the thread shows `label`, CoCo receives
        `text`. Sent when connected, shown as waiting until then. `schema` (a JSON schema as a
        dict) asks for a structured result, which `result(key)` hands back in `data`."""
        s = self._s
        prompt = text if text is not None else label
        if schema is not None:
            prompt += (
                "\n\nAnswer with one JSON object matching this JSON schema, and nothing else:\n"
                + json.dumps(schema)
            )
        key = key or label
        ctx = s["context"]() if s["context"] else {}
        if not s["conv"].request_from_page(label, prompt, ctx, key=key):
            return False
        s["schemas"][key] = schema is not None
        self.open()
        st.rerun()  # the window was drawn before this click: draw it again, working
        return True

    def result(self, key: str) -> dict | None:
        """The structured result of that request, handed over once; None until it is finished."""
        got = self._s["conv"].result_for(key)
        if got is not None and self._s["schemas"].get(key) and got.get("data") is None:
            try:
                got = {**got, "data": json.loads(got["text"])}
            except (TypeError, ValueError):
                pass  # not JSON: the text stays, the host sees data is None
        return got

    def form(self, title: str, fields: list[dict], *, key: str) -> dict | None:
        """A form asked by the application, answered in the window; None until answered."""
        raise NotImplementedError("coco.form needs the conversation's application questions")

    # ---- what the page does to the window
    def open(self, drafts: list | None = None) -> None:
        """Open the window, optionally with prepared texts (one bubble each, with Copy)."""
        s = self._s
        if drafts:
            s["conv"].add_drafts([d if isinstance(d, tuple) else ("", str(d)) for d in drafts])
        s["token"] += 1

    def notice(self, text: str, *, action: dict | None = None) -> None:
        """One line in the thread in the application's words (`action`: {"label", "then"})."""
        action = action or {}
        self._s["conv"].notice(text, action.get("label"), action.get("then"))

    @property
    def latest_answer(self) -> str:
        """The latest answer's text, for a page that shows it elsewhere."""
        for item in reversed(self._s["conv"].view().get("thread", [])):
            for part in reversed(item.get("items", [item])):
                if part.get("kind") == "answer":
                    return part.get("text", "")
        return ""

    def new(self) -> None:
        """End the conversation."""
        self._s["conv"].act({"type": "new"})

    def disconnect(self) -> None:
        """End the session."""
        self._s["conv"].act({"type": "disconnect"})


def get_window(key: str = "coco") -> Window:
    """The handle of the window mounted with this key in this browser session."""
    _state(key)
    return Window(key)


def _on_act(key: str) -> None:
    """The window's one action since the last run. A repeat (the browser sends again when an
    answer is late) is ignored."""
    s = st.session_state.get(_slot(key))
    result = st.session_state.get(f"{_slot(key)}:component")  # absent after a page switch
    act = getattr(result, "act", None) if result else None
    if not s or not act or int(act.get("seq", 0)) <= s["ack"]:
        return
    s["ack"] = int(act["seq"])
    action = {k: v for k, v in act.items() if k not in ("a", "seq")} | {"type": act["a"]}
    if action["type"] == "poll":
        return
    ctx = None
    if action["type"] in ("send", "prompt"):
        ctx = copy.deepcopy(s["context"]()) if s["context"] else {}
    s["conv"].act(action, ctx)


@st.fragment
def _window(key: str) -> None:
    s = _state(key)
    conv = s["conv"]
    if conv.drain():  # the agent changed files (on_files_changed was called): read again, once
        st.rerun()
    f = conv.features
    _component()(
        key=f"{_slot(key)}:component",
        on_act_change=partial(_on_act, key),
        data={
            "view": conv.view(),
            "ack": s["ack"],
            "open_token": s["token"],
            "sess": s["sess"],
            "spark": assets.spark(),
            "labels": s["labels"],
            "theme": s["theme"],
            "exclude": list(f.page_exclude),
            "features": {"motion": f.motion, "copy": f.copy, "steps": f.steps},
        },
    )


def ask_coco(
    cwd: str | Path = ".",
    *,
    key: str = "coco",
    policy=None,
    context: Callable[[], dict] | None = None,
    features=None,
    prompts: list | None = None,
    labels: dict[str, str] | None = None,
    theme: dict[str, str] | None = None,
    options=None,
    on_files_changed: Callable[[list], Any] | None = None,
    agent: Callable | None = None,
) -> Window:
    """Mount the launcher and the window; see the module docstring and feature file 1.1."""
    _check_streamlit()
    if options is not None:
        bad = [name for name in _REFUSED if getattr(options, name, None)]
        if bad:
            raise ValueError(
                f"ask_coco(options=) refuses {', '.join(bad)}: the window sends the program no "
                "tool list, every call reaches the gate. Rights are the `policy`'s."
            )
    from streamlit_coco.conversation import Conversation, agent_factory

    slot = _slot(key)
    cwd = Path(cwd).expanduser().resolve()
    s = st.session_state.get(slot)
    if s is None:
        conv = Conversation(
            cwd,
            policy=policy,
            features=features,
            prompts=prompts,
            labels=labels,
            agent=agent or (agent_factory(options) if options is not None else None),
            on_files_changed=on_files_changed,
        )
        s = st.session_state[slot] = {
            "conv": conv,
            "ack": 0,
            "token": 0,
            "sess": uuid.uuid4().hex[:8],
            "schemas": {},
        }
    conv = s["conv"]
    # what a host may change from one run to the next: the folder, the rights, the texts
    conv.set_cwd(cwd)
    conv.policy, conv.prompts, conv._on_files_changed = (
        policy,
        list(prompts or []),
        on_files_changed,
    )
    if features is not None:
        conv.features = features
    s["context"] = context
    s["labels"] = labels_table.table(labels)
    s["theme"] = dict(theme or {})
    with st.container(key=f"{key}_host"):
        _window(key)
    return Window(key)
