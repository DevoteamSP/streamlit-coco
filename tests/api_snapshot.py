"""Describe the public API of ``streamlit_coco`` as plain data, and compare two descriptions.

``tests/fixtures/api_0.1.9.json`` is this description of the 0.1.9 release (the last one
on PyPI), taken from that release's source. ``test_compat_019.py`` checks the current
package against it, so a change that would break code written for 0.1.9 fails a test.

Regenerate a snapshot of another release from its source tree::

    python tests/api_snapshot.py <folder holding streamlit_coco/> > tests/fixtures/api_X.Y.Z.json
"""

from __future__ import annotations

import dataclasses
import enum
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any

_PRIMITIVES = (type(None), bool, int, float, str)


def _default(value: Any) -> str:
    if value is inspect.Parameter.empty:
        return "<required>"
    if isinstance(value, _PRIMITIVES):
        return repr(value)
    return "<object>"


def _params(obj: Any) -> list[list[str]] | None:
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return None
    return [[p.name, p.kind.name, _default(p.default)] for p in signature.parameters.values()]


def _describe(obj: Any, module: str | None = None) -> dict[str, Any]:
    owner = getattr(obj, "__module__", None)
    if module is not None and (inspect.isclass(obj) or inspect.isfunction(obj)) and owner != module:
        return {"kind": "reexport"}
    if inspect.isclass(obj):
        if issubclass(obj, enum.Enum):
            return {"kind": "enum", "members": sorted(obj.__members__)}
        entry: dict[str, Any] = {
            "kind": "class",
            "init": _params(obj),
            "members": sorted(name for name in vars(obj) if not name.startswith("_")),
        }
        if dataclasses.is_dataclass(obj):
            entry["fields"] = [f.name for f in dataclasses.fields(obj)]
        return entry
    if callable(obj):
        return {"kind": "function", "params": _params(obj)}
    return {"kind": "value"}


def snapshot() -> dict[str, Any]:
    """The public API of the importable ``streamlit_coco``."""
    package = importlib.import_module("streamlit_coco")
    top = {name: _describe(getattr(package, name)) for name in sorted(package.__all__)}
    modules: dict[str, dict[str, Any]] = {}
    for info in pkgutil.walk_packages(package.__path__, "streamlit_coco."):
        if ".static" in info.name:
            continue
        module = importlib.import_module(info.name)
        modules[info.name] = {
            name: _describe(value, info.name)
            for name, value in sorted(vars(module).items())
            if not name.startswith("_") and not inspect.ismodule(value)
        }
    return {"top": top, "modules": modules}


def _param_errors(where: str, old: list[list[str]], new: list[list[str]]) -> list[str]:
    errors: list[str] = []
    new_by_name = {name: (kind, default) for name, kind, default in new}
    positional = ("POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD")
    old_positional = [row for row in old if row[1] in positional]
    new_positional = [row for row in new if row[1] in positional]
    for index, (name, kind, default) in enumerate(old):
        if kind in ("VAR_POSITIONAL", "VAR_KEYWORD"):
            if not any(row[1] == kind for row in new):
                errors.append(f"{where}: lost {kind} {name}")
            continue
        if name not in new_by_name:
            errors.append(f"{where}: parameter `{name}` is gone")
            continue
        new_kind, new_default = new_by_name[name]
        if kind in positional:
            at = old_positional.index([name, kind, default])
            if at >= len(new_positional) or new_positional[at][0] != name:
                errors.append(f"{where}: parameter `{name}` moved from position {at}")
            if new_kind not in positional:
                errors.append(f"{where}: parameter `{name}` can no longer be passed by position")
        elif new_kind == "POSITIONAL_ONLY":
            errors.append(f"{where}: parameter `{name}` can no longer be passed by keyword")
        if default != "<required>":
            if new_default == "<required>":
                errors.append(f"{where}: parameter `{name}` became required")
            elif default != "<object>" and new_default not in (default, "<object>"):
                errors.append(f"{where}: `{name}` default {default} became {new_default}")
    old_names = {row[0] for row in old}
    for name, kind, default in new:
        if name in old_names or kind in ("VAR_POSITIONAL", "VAR_KEYWORD"):
            continue
        if default == "<required>":
            errors.append(f"{where}: new parameter `{name}` has no default")
    return errors


def _entry_errors(where: str, old: dict[str, Any], current: Any) -> list[str]:
    kind = old["kind"]
    if kind == "enum":
        missing = set(old["members"]) - set(getattr(current, "__members__", {}))
        return [f"{where}: enum members gone: {sorted(missing)}"] if missing else []
    if kind == "class":
        errors = [
            f"{where}: member `{name}` is gone"
            for name in old["members"]
            if not hasattr(current, name)
        ]
        if old.get("fields"):
            now = (
                {f.name for f in dataclasses.fields(current)}
                if dataclasses.is_dataclass(current)
                else set()
            )
            errors += [
                f"{where}: field `{name}` is gone" for name in old["fields"] if name not in now
            ]
        new_init = _params(current)
        if old["init"] is not None and new_init is not None:
            errors += _param_errors(f"{where}()", old["init"], new_init)
        return errors
    if kind == "function":
        new_params = _params(current)
        if old["params"] is not None and new_params is not None:
            return _param_errors(f"{where}()", old["params"], new_params)
    return []


def compat_errors(old: dict[str, Any]) -> list[str]:
    """What the current package no longer accepts of the described (older) API."""
    errors: list[str] = []
    package = importlib.import_module("streamlit_coco")
    for name, entry in old["top"].items():
        if name not in package.__all__:
            errors.append(f"streamlit_coco.{name}: left __all__")
            continue
        try:
            current = getattr(package, name)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"streamlit_coco.{name}: {type(exc).__name__}: {exc}")
            continue
        errors += _entry_errors(f"streamlit_coco.{name}", entry, current)
    for module_name, names in old["modules"].items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{module_name}: cannot import ({type(exc).__name__}: {exc})")
            continue
        for name, entry in names.items():
            if not hasattr(module, name):
                errors.append(f"{module_name}.{name}: is gone")
                continue
            if entry["kind"] != "reexport":
                errors += _entry_errors(f"{module_name}.{name}", entry, getattr(module, name))
    return errors


if __name__ == "__main__":
    root = sys.argv[1]
    sys.path.insert(0, root)
    result = snapshot()
    assert importlib.import_module("streamlit_coco").__file__.startswith(root)
    json.dump(result, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
