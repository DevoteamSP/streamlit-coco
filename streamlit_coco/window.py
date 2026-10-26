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
features ({motion, copy, steps, dock, full_page}), and rail (true when a header icon restores the
Copilot rail). `place` ("closed", "float", "left", "right" or "full") is the window's place as
the browser reports it; the browser also writes it on the page (`data-coco-place` on <html>, and
`--coco-dock-w` for the width of a docked window).
"""

from __future__ import annotations

import copy
import uuid
from collections.abc import Callable
from functools import lru_cache, partial
from pathlib import Path
from typing import Any

import streamlit as st

from streamlit_coco import assets
from streamlit_coco import labels as labels_table
from streamlit_coco.errors import CocoError

# The lowest Streamlit the package supports. The window runs on 1.53 (st.components.v2 in a
# fragment, isolated styles), but copilot_rail needs st.popover(key=), new in 1.55; pyproject.toml
# says the same (tests/test_streamlit_floor.py).
STREAMLIT_FLOOR = (1, 55)
_REFUSED = ("allowed_tools", "disallowed_tools", "require_approval_for")
PLACES = ("closed", "float", "left", "right", "full")  # where the window is, as the browser says


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


# split=True: while the window is attached to an edge, the page takes the rest of the screen. The
# browser writes the place and the width on <html> (static/coco/coco.js, reportPlace).
_SPLIT_CSS = """
        <style>
        html[data-coco-place="left"] [data-testid="stApp"] { left: var(--coco-dock-w, 0px); }
        html[data-coco-place="right"] [data-testid="stApp"] { right: var(--coco-dock-w, 0px); }
        </style>
        """


def _slot(key: str) -> str:
    return f"_streamlit_coco:{key}"


def request_open(key: str = "coco") -> None:
    """Ask the next ``ask_coco`` mount of this key to open the window once."""
    st.session_state[f"{_slot(key)}:reveal"] = True


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

    @property
    def place(self) -> str:
        """Where the window is now: "closed" (minimised), "float", "left", "right" (attached to
        that edge) or "full" (the whole page). Read it on each run; give `ask_coco(on_layout=)` to
        have the page rerun when it changes."""
        return self._s.get("place", "closed")

    # ---- the application asks CoCo
    def ask(self, label: str, text: str | None = None, *, key: str | None = None) -> bool:
        """A button of the page asks in the user's name: the thread shows `label`, CoCo receives
        `text`. Sent when connected, shown as waiting until then. A structured answer is the
        session's (`options=CocoOptions(output_schema=...)`) and comes back through `result(key)`.

        It reruns the page once (the window was drawn before the click and must be drawn again,
        open and working), so it belongs behind a button: called on every run it would loop."""
        s = self._s
        key = key or label
        ctx = s["context"]() if s["context"] else {}
        if not s["conv"].request_from_page(
            label, text if text is not None else label, ctx, key=key
        ):
            return False
        s["asked"].add(key)
        self.open()
        st.rerun()
        return True

    def result(self, key: str) -> dict | None:
        """{"text", "data"} of the request sent with `ask(..., key=key)`, handed over once; None
        until it is finished. `data` is the structured result when the session has an
        output_schema, else None."""
        s = self._s
        found = s["conv"].result_for(key)
        if found is not None:  # while it is pending, the window still reruns the page when it ends
            s["asked"].discard(key)
        return found

    def form(self, title: str, fields: list[dict], *, key: str) -> dict | None:
        """A form asked by the application, answered in the window (no agent, no connection).

        `fields` are dicts {id, label?, type?: text | longtext | number | choice, choices?,
        required?, value?}. Call it on every run: it asks once per `key`, and returns None until
        the user has answered or skipped; then, once, {"skipped": False, "values": {id: text}} or
        {"skipped": True, "values": {}}. Afterwards it returns None again and never re-asks: a new
        question needs a new key."""
        conv = self._s["conv"]
        asked = key in conv.w_forms
        conv.ask_form(key, title, fields)
        if not asked:
            self.open()
            st.rerun()  # the window was drawn before this call: draw it again, open
        return conv.form_result(key)

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
        for item in reversed(self._s["conv"].thread()):
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
    if action["type"] == "layout":
        place = action.get("place")
        f = s["conv"].features
        allowed = (place == "full" and f.full_page) or (place in ("left", "right") and f.dock)
        if place in ("closed", "float") or allowed:
            changed, s["place"] = s.get("place") != place, place
            fn = s.get("on_layout")
            if changed and callable(fn):
                fn(place)
                s["page_rerun"] = True  # the page lays itself out for the new place
        return
    if action["type"] == "rail":
        # This runs as a widget callback. st.rerun() here is a no-op and shows
        # a warning. The flag is read on the fragment run that follows.
        st.session_state.pop(f"{_slot(key)}:rail_seen", None)
        fn = s.get("on_rail")
        if callable(fn):
            fn()
        s["page_rerun"] = True
        return
    ctx = None
    if action["type"] in ("send", "prompt"):
        ctx = copy.deepcopy(s["context"]()) if s["context"] else {}
    s["conv"].act(action, ctx)


def _page_must_run(s: dict) -> bool:
    """The only reasons the window reruns the page, each told once: the agent changed files
    (`on_files_changed` was called), an application form was answered, a request the page sent is
    finished. Whatever one run of the window finds, the page reruns once."""
    conv = s["conv"]
    files = conv.drain()
    forms = [k for k in conv.w_forms if k not in s["told"] and conv.form_result(k, take=False)]
    asked = [k for k in s["asked"] if conv.result_for(k, take=False) is not None]
    s["told"].update(forms)  # the page reads the values on its next run
    s["asked"].difference_update(asked)  # the page shows the request's line
    return bool(files or forms or asked)


@st.fragment
def _window(key: str) -> None:
    s = _state(key)
    conv = s["conv"]
    # Outside the callback, so a full-app rerun actually runs (Restore, file changes).
    if s.pop("page_rerun", False) or _page_must_run(s):
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
            "features": {
                "motion": f.motion,
                "copy": f.copy,
                "steps": f.steps,
                "dock": f.dock,
                "full_page": f.full_page,
            },
            "rail": callable(s.get("on_rail")),
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
    connection: str | None = None,
    on_rail: Callable[[], Any] | None = None,
    on_layout: Callable[[str], Any] | None = None,
    split: bool = False,
    audit: Callable[[dict], Any] | None = None,
) -> Window:
    """Mount the launcher and the window; see the module docstring and feature file 1.1.

    `cwd` must be an existing folder (one `CocoError` otherwise). `labels` given under the same
    key may change from one run to the next (an application that switches language): the window's
    own texts and every sentence the conversation writes afterwards follow, the conversation is
    kept; what is already written in the thread stays as it was written
    (Conversation.set_labels).

    `split=True`: while the window is attached to the left or the right edge, the page takes the
    rest of the screen (it is not covered). `on_layout(place)` is called when the window changes
    place ("closed", "float", "left", "right", "full"), then the page reruns once, so the page can
    lay itself out (a column, a different width); read `get_window(key).place` on each run.

    `audit`: an `AuditLog` (or a function of one record): every call that asked the user, was
    covered by a standing permission or was refused is written there (audit.py)."""
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
    if not cwd.is_dir():  # else it connects and every read fails; an agent must not get the path
        raise CocoError(
            f'ask_coco(cwd): "{cwd}" '
            + ("is not a folder." if cwd.exists() else "does not exist.")
            + " Give the working folder CoCo reads and writes in, and create it first."
        )
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
            connect=connection or None,
            audit=audit,
        )
        s = st.session_state[slot] = {
            "conv": conv,
            "ack": 0,
            "token": 0,
            "sess": uuid.uuid4().hex[:8],
            "asked": set(),
            "told": set(),
            "place": "closed",
        }
    conv = s["conv"]
    # what a host may change from one run to the next: the folder, the rights, the texts
    conv.set_cwd(cwd)
    conv.policy, conv.prompts, conv._on_files_changed = (
        policy,
        list(prompts or []),
        on_files_changed,
    )
    conv.set_labels(labels)
    conv.audit = audit
    if features is not None:
        conv.features = features
    # A rail that is already connected: start this client with the same profile. The two
    # clients stay separate (the window's gate is installed on its own), so there is no
    # Connect click and the rail's client is still there when the rail comes back.
    if connection and conv.conn == "none" and not conv.setup:
        conv.act({"type": "connect", "profile": connection})
    s["context"] = context
    s["on_rail"] = on_rail
    s["on_layout"] = on_layout
    # the agent's own words (the managed agent works in a sandbox, not in a folder), the host's over
    own = getattr(conv.agent, "labels", None) or {}
    s["labels"] = labels_table.table({**own, **(labels or {})})
    s["theme"] = dict(theme or {})
    # Open only when a host asked, once. Restore closes the window in the browser.
    if st.session_state.pop(f"{slot}:reveal", False):
        s["token"] += 1
    # The window is position:fixed. The host must not take a row on the page.
    st.html(
        f"""
        <style>
        .st-key-{key}_host,
        .st-key-{key}_host [data-testid="stLayoutWrapper"],
        .st-key-{key}_host [data-testid="stVerticalBlock"],
        .st-key-{key}_host [data-testid="stElementContainer"],
        .st-key-{key}_host [data-testid="stBidiComponentIsolated"] {{
          height: 0 !important;
          min-height: 0 !important;
          margin: 0 !important;
          padding: 0 !important;
          overflow: visible !important;
          border: 0 !important;
        }}
        /* Every poll reruns the fragment. When a run is slow Streamlit fades the stale element
           (opacity < 1), which makes it a stacking context: the position:fixed window blinks and
           the page's own layers (dataframes, headers) show on top of it. */
        .st-key-{key}_host [data-testid="stElementContainer"] {{
          opacity: 1 !important;
          transition: none !important;
        }}
        </style>
        """
        + (_SPLIT_CSS if split else "")
    )
    with st.container(key=f"{key}_host"):
        _window(key)
    return Window(key)
