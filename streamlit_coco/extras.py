"""Ask CoCo, the conversation: data, files, requests from the page, display options, session facts.

Blocks on answers and steps (tables, query results, structured data), attached files saved in the
working folder, requests made by the page (label, full text, held before connecting, result handed
back once), the display options, session details and the connection facts of the view: `options`,
`hidden`, `session`, `attach`, `type_ahead`, `problem`, `profile_files`, and the actions set,
show_earlier, system_action (and send with files, via `on_message`). Each optional key is driven by
the host's `Features` (`conv.features`); `granted` and `revoke` belong to waits.py.

Pure Python: no Streamlit, no SDK. Called by `Conversation` (conversation.py). Every sentence it
writes is a label of the conversation (`conv.t(key)`). State lives in `conv.ex` (a dict).

    reset(conv) / act / on / view / on_message / on_step / on_answer      the hooks of the
        conversation
    sent(conv, message)                  after a send was queued or started: says what was refused
        (called by `_send`)
    request_from_page(conv, label, text, context, key=None, hint=None) -> bool     result_for(conv,
        key) -> dict | None
    notice(conv, text, label=None, then=None)   a system line with one button; `then()` runs when
        it is pressed
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import re
import time
import unicodedata
import uuid
from pathlib import Path

from streamlit_coco import waits as coco_waits

OPTIONS = ("plan", "latest", "shorten", "raw")  # menu order; "plan" is the state of waits.py
ROWS, FULL_TABLES, CUT_ROWS = 200, 3, 5
_RESERVED = re.compile(r"^(con|prn|aux|nul|com\d|lpt\d)$", re.I)
_SECRET = re.compile(r"token|secret|password|passwd|key|credential", re.I)
_TTL = 10


def offered(conv) -> list[str]:
    """The menu switches this host offers, in menu order."""
    f = conv.features
    return [o for o in OPTIONS if (o == "plan" and f.planning) or o in f.display]


def reset(conv) -> None:
    conv.ex = {
        "id": uuid.uuid4().hex[:12],
        "opts": dict.fromkeys(OPTIONS, False),
        "tables": [],
        "saved": {},
        "jobs": {},
        "handed": set(),
        "actions": {},
        "n": 0,
        "facts": (0, None),
        "files": (0, None),
    }


def _next(conv, prefix: str) -> str:
    return conv._id(
        prefix
    )  # one counter for the whole conversation: a table, a fold, a line never share an id


# ---- data


def _cell(value) -> str:
    return "" if value is None else str(value)


def _table(conv, spec, label=None):
    """A table from {columns, rows[, total]} or a list of dicts; None when there is nothing to
    show."""
    if isinstance(spec, list) and spec and all(isinstance(r, dict) for r in spec):
        columns = list(dict.fromkeys(k for r in spec for k in r))
        rows, total = [[r.get(k) for k in columns] for r in spec], len(spec)
    elif isinstance(spec, dict) and isinstance(spec.get("rows"), list) and spec["rows"]:
        columns, rows = (
            [c["name"] if isinstance(c, dict) else c for c in spec.get("columns") or []],
            spec["rows"],
        )
        if isinstance(rows[0], dict):
            columns = columns or list(rows[0])
            rows = [[r.get(c) for c in columns] for r in rows]
        total = spec.get("total") if isinstance(spec.get("total"), int) else len(rows)
        label = label or spec.get("label")
    else:
        return None
    rows = rows[:ROWS]
    kinds = [
        "number"
        if any(r[i] is not None for r in rows)
        and all(
            isinstance(r[i], (int, float)) and not isinstance(r[i], bool)
            for r in rows
            if r[i] is not None
        )
        else "text"
        for i in range(len(columns))
    ]
    table = {
        "id": _next(conv, "t"),
        "label": label,
        "columns": [{"name": str(c), "kind": k} for c, k in zip(columns, kinds)],
        "rows": [[_cell(c) for c in r] for r in rows],
        "total": max(total, len(rows)),
    }
    return _keep(conv, table)


def _keep(conv, table):
    conv.ex["tables"].append(table)
    for old in conv.ex["tables"][
        :-FULL_TABLES
    ]:  # older tables keep their first rows and their total
        del old["rows"][CUT_ROWS:]
    return table


def _blocks(conv, data) -> list[dict]:
    """The `data` block of a table, a query result or a structured answer ([] when it holds
    nothing)."""
    tables, fields, title, as_json = [], [], None, None
    if (
        isinstance(data, dict) and data.get("type") == "data"
    ):  # the adapter's own block: ids of this conversation, nothing rebuilt
        block = copy.deepcopy(data)
        block["id"] = _next(conv, "d")
        block["tables"] = [
            _keep(conv, {**t, "id": _next(conv, "t")}) for t in block.get("tables") or []
        ]
        return [block] if block["tables"] or block.get("fields") else []
    if isinstance(data, dict) and "rows" not in data:
        title = data.get("title") if isinstance(data.get("title"), str) else None
        given = data.get("fields")
        items = (
            given.items()
            if isinstance(given, dict)
            else [(f.get("label"), f.get("value")) for f in given or [] if isinstance(f, dict)]
        )
        scalars = (
            []
            if given is not None
            else [
                (k, v)
                for k, v in data.items()
                if isinstance(v, (str, int, float, bool)) and k not in ("title", "json")
            ]
        )
        fields = [{"label": str(k), "value": _cell(v)} for k, v in [*items, *scalars] if k]
        tables = [_table(conv, spec) for spec in data.get("tables") or []]
        tables += [
            _table(conv, v, label=str(k))
            for k, v in data.items()
            if k != "tables" and isinstance(v, list)
        ]
        as_json = (
            data["json"]
            if isinstance(data.get("json"), str)
            else json.dumps(data, indent=2, ensure_ascii=False, default=str)
        )
    else:
        tables = [_table(conv, data)]
    tables = [t for t in tables if t]
    if not (fields or tables):
        return []
    return [
        {
            "type": "data",
            "id": _next(conv, "d"),
            "title": title,
            "fields": fields,
            "tables": tables,
            "json": as_json,
        }
    ]


def _count(conv, blocks: list[dict]) -> str:
    n = sum(t["total"] for b in blocks for t in b["tables"][:1])
    return conv.t(
        "rows_none" if not blocks else "rows_one" if n == 1 else "rows",
        n=f"{n:,}".replace(",", " "),
    )


def _attach(step: dict, blocks: list[dict]) -> None:
    step.setdefault("blocks", []).extend(blocks)
    step["result"] = ""


def on_step(conv, run: dict, step: dict, event: dict) -> None:
    if conv.ex["opts"]["raw"] and isinstance(event.get("raw"), dict):
        step["raw"] = {k: str(event["raw"].get(k) or "")[:20_000] for k in ("request", "result")}
    data = event.get("data")
    if data is None and "sql" in str(step.get("tool")).lower() and not event.get("error"):
        try:
            data = json.loads(str(event.get("content") or ""))
        except ValueError:
            if re.match(r"\s*0 row\(s\) returned", str(event.get("content") or "")):
                step["note"] = conv.t("rows_none")
            return
        if not (isinstance(data, list) or (isinstance(data, dict) and "rows" in data)):
            return
    if data is None:
        return
    blocks = _blocks(conv, data)
    step["note"] = _count(conv, blocks)
    if blocks:
        _attach(step, blocks)


def on(conv, event: dict) -> bool:
    if event["t"] == "reasoning":
        if (
            conv.features.reasoning
            and conv.run is not None
            and str(event.get("text") or "").strip()
        ):
            conv.run["turn"]["seq"].append(
                {"k": "reasoning", "id": _next(conv, "r"), "text": str(event["text"])}
            )
        return True
    if event["t"] != "structured":
        return False
    run = conv.run
    blocks = _blocks(conv, event.get("data"))
    step = run["steps"].get(event.get("tool_id")) if run else None
    if step is not None and blocks:
        _attach(step, blocks)
        step["note"] = _count(conv, blocks)
    elif run is not None:
        run["turn"].setdefault("ex_blocks", []).extend(blocks)
        run["turn"]["ex_data"] = event["raw"] if "raw" in event else event.get("data")
    return True


def on_answer(conv, item: dict, answer: dict) -> None:
    if item.get("ex_blocks"):
        answer["blocks"] = item["ex_blocks"]


# ---- files


def clean_name(raw) -> str:
    """A file name that cannot leave its folder: no path, no control or device name, bounded
    length."""
    name = unicodedata.normalize("NFC", str(raw or "")).replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r'[\x00-\x1f<>:"|?*]', "", name).strip(" .")
    suffix = Path(name).suffix
    stem = (name[: -len(suffix)] if suffix else name).strip(" .")[:100] or "file"
    return ("_" if _RESERVED.match(stem.split(".")[0]) else "") + stem + suffix[:16]


def _folder(conv) -> Path:
    return Path(conv.cwd) / "_coco_uploads" / conv.ex["id"]


def _save(conv, files) -> tuple[list[str], list[tuple[str, str]]]:
    saved, refused, rules = [], [], conv.features.attachments
    accept = {a.lower() for a in rules.accept} if rules else set()
    limit = int((rules.max_mb if rules else 0) * 1024 * 1024)
    for spec in (files if isinstance(files, list) else [])[: 20 if rules and rules.multi else 1]:
        spec = spec if isinstance(spec, dict) else {}
        name = clean_name(spec.get("name"))
        data = str(spec.get("data") or "")
        if rules is None or (accept and Path(name).suffix.lower() not in accept):
            refused.append((name, conv.t("attach_type")))
        elif conv.conn != "ready":
            refused.append((name, conv.t("attach_wait")))
        elif len(data) * 3 // 4 > limit + 3:
            refused.append(
                (name, conv.t("attach_size", mb=len(data) * 3 // 4 // 1_000_000, max=rules.max_mb))
            )
        else:
            try:
                raw = base64.b64decode(
                    data.split(",", 1)[-1] if data.startswith("data:") else data, validate=True
                )
            except (binascii.Error, ValueError):
                refused.append((name, conv.t("attach_unreadable")))
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if len(raw) > limit:
                refused.append(
                    (name, conv.t("attach_size", mb=len(raw) // 1_000_000, max=rules.max_mb))
                )
            elif conv.ex["saved"].get(name) == digest:
                refused.append((name, conv.t("attach_duplicate")))
            else:
                folder = _folder(conv)
                folder.mkdir(parents=True, exist_ok=True)
                path = _free(folder, name, raw)
                conv.ex["saved"][name] = digest
                saved.append(str(path))
    return saved, refused


def _free(folder: Path, name: str, raw: bytes) -> Path:
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    while True:
        path = folder / (name if n == 1 else f"{stem} ({n}){suffix}")
        if path.resolve().parent != folder.resolve():
            raise ValueError("a file name left its folder")
        try:
            with open(path, "xb") as out:  # never overwrites
                out.write(raw)
            return path
        except FileExistsError:
            n += 1


def on_message(conv, action: dict, message: dict) -> None:
    if not action.get("files"):
        return
    paths, message["ex_refused"] = _save(conv, action["files"])
    if paths:
        if hasattr(message["policy"], "uploads"):  # attaching a file is the consent to read it
            message["policy"].uploads = Path(conv.cwd) / "_coco_uploads"
        message.setdefault("show", {})["files"] = [Path(p).name for p in paths]
        message["prompt"] = (
            (message["text"] or conv.t("attach_prompt"))
            + "\n\n"
            + conv.t("attach_intro")
            + "\n"
            + "\n".join(f"- {p}" for p in paths)
        )
    elif not message["text"]:
        message["ex_drop"] = True


def sent(conv, message: dict) -> None:
    if message.get("ex_refused"):
        text = conv.t(
            "attach_refused", files="; ".join(f"{n} ({why})" for n, why in message["ex_refused"])
        )
        conv.items.append(
            {"kind": "system", "id": _next(conv, "y"), "text": text, "detail": "", "action": None}
        )


# ---- page


def request_from_page(
    conv, label: str, text: str, context: dict, key: str | None = None, hint: str | None = None
) -> bool:
    """A button of the page asks in the user's name. Shown as `label`, the agent receives `text`.
    Held when not connected."""
    label, text = str(label).strip(), str(text)
    if conv.setup or not label:
        return False
    ctx, policy = conv.freeze(context)
    message = {
        "id": conv._id("q"),
        "text": label,
        "ctx": ctx,
        "policy": policy,
        "prompt": text,
        "ex_key": key or label,
    }
    if text != label:
        message["show"], message["ex_full"] = {"full": text}, text
    conv.ex["jobs"][message["ex_key"]] = message
    conv.ex["handed"].discard(message["ex_key"])
    conv.rev += 1
    if conv.conn == "ready" and conv.run is None:
        conv._start(message)
    else:
        conv.queue.append(message)
    return True


def result_for(conv, key: str, take: bool = True):
    """{text, data} of the finished job, once; None until then (or when it was never started)."""
    message = conv.ex["jobs"].get(key)
    if message is None or key in conv.ex["handed"]:
        return None
    ids = [i.get("id") if i["kind"] == "user" else None for i in conv.items]
    if message["id"] not in ids:
        return None
    turn = next((i for i in conv.items[ids.index(message["id"]) :] if i["kind"] == "turn"), None)
    if turn is None or not turn["done"]:
        return None
    texts = [e["text"] for e in turn["seq"] if e["k"] == "text" and e["text"].strip()]
    if not texts and turn.get("ex_data") is None:
        return None
    if take:
        conv.ex["handed"].add(key)
    return {"text": texts[-1] if texts else "", "data": turn.get("ex_data")}


def notice(conv, text: str, label: str | None = None, then=None) -> str:
    """A system line, with one button when `label` is given; `then()` runs on the server when it is
    pressed."""
    item = {
        "kind": "system",
        "id": _next(conv, "y"),
        "text": text,
        "detail": None,
        "action": {"label": label} if label else None,
    }
    conv.items.append(item)
    if then:
        conv.ex["actions"][item["id"]] = then
    conv.rev += 1
    return item["id"]


# ---- actions


def act(conv, action: dict, context: dict | None) -> bool:
    kind = action.get("type")
    if kind == "set" and action.get("option") in offered(conv):
        option, value = action["option"], bool(action.get("value"))
        if option == "plan":  # the waits' state, not ours
            coco_waits.set_planning(conv, value)
        else:
            conv.ex["opts"][option] = value
        if option == "raw" and hasattr(conv.agent, "set_raw"):
            conv.agent.set_raw(value)
    elif kind == "show_earlier":
        conv.ex["opts"]["latest"] = False
    elif kind == "system_action" and action.get("id") in conv.ex["actions"]:
        conv.ex["actions"].pop(action["id"])()
    else:
        return False
    return True


# ---- view


def _cached(conv, slot: str, read):
    at, value = conv.ex[slot]
    if time.monotonic() - at > _TTL or value is None:
        try:
            value = read()
        except Exception:  # an agent that cannot say simply gives nothing
            value = []
        conv.ex[slot] = (time.monotonic(), value)
    return value


def _problem(conv, error: str) -> str:
    low = error.lower()
    if re.search(r"password|credential|incorrect user|250001|sign.?in|authenticat", low):
        return conv.t("problem_signin")
    if re.search(r"timed? ?out|network|resolve|unreachable|refused", low):
        return conv.t("problem_network")
    return conv.t("problem_other")


def release(conv) -> None:
    """What was held while not connected goes now. Called before the view is built: a view that
    starts a run must say so itself."""
    while conv.conn == "ready" and conv.run is None and conv.queue and not conv.setup:
        conv._start(conv.queue.pop(0))
        conv.rev += 1


def view(conv) -> dict:
    ex, out = conv.ex, {}
    if offered(conv):
        out["options"] = [
            {
                "id": o,
                "label": conv.t("opt_" + o),
                "sub": conv.t("opt_" + o + "_sub"),
                "on": coco_waits.planning(conv) if o == "plan" else ex["opts"][o],
            }
            for o in offered(conv)
        ]
    if ex["opts"]["latest"]:
        last = max((n for n, i in enumerate(conv.items) if i["kind"] == "user"), default=0)
        if last:
            out["hidden"] = sum(i["kind"] in ("user", "draft", "turn") for i in conv.items[:last])
            out["thread"] = [v for item in conv.items[last:] for v in conv._item(item)]
    if conv.conn == "ready":
        if conv.features.session_details:
            facts = _cached(conv, "facts", lambda: conv.agent.session_facts())
            facts = [
                f
                for f in facts
                if isinstance(f, dict)
                and f.get("label")
                and f.get("value")
                and not _SECRET.search(str(f["label"]))
            ]
            if facts:
                out["session"] = [
                    {"label": str(f["label"]), "value": str(f["value"])} for f in facts
                ]
        if conv.features.attachments is not None:
            rules = conv.features.attachments
            out["attach"] = {
                "multi": rules.multi,
                "accept": list(rules.accept),
                "max_mb": rules.max_mb,
                "existing": [],
            }
    if conv.conn == "connecting" and conv.features.queue:
        out["type_ahead"] = True
    if conv.conn == "none" and not conv.setup:
        if conv.error:
            out["problem"] = _problem(conv, conv.error)
        groups = _cached(conv, "files", lambda: conv.agent.connection_files())
        if isinstance(groups, list) and len(groups) > 1:
            out["profile_files"] = [
                {"file": str(g["file"]), "profiles": list(g["profiles"])} for g in groups
            ]
    if conv.queue and (conv.conn != "ready" or any(m.get("ex_full") for m in conv.queue)):
        out["queue"] = [
            {
                "id": m["id"],
                "text": m["text"],
                "note": conv.t("queue_note") if conv.conn != "ready" else None,
                "full": m.get("ex_full"),
            }
            for m in conv.queue
        ]
    return out
