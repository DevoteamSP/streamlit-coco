"""Merge access-rule payloads and compute branch divergences."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.powerbi_parse import access_rule


def normalize_branch_key(branch: dict[str, Any]) -> str:
    return str(branch.get("grants_to") or branch.get("condition") or "").strip().lower()


def _branch_condition(rule: dict[str, Any], key: str) -> str:
    for branch in rule.get("branches") or []:
        if normalize_branch_key(branch) == key:
            return str(branch.get("condition") or "").strip()
    return ""


def divergences_from_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare ``grants_to`` keys and conditions across sources."""
    if len(rules) < 2:
        return []
    keys_by_wb: dict[str, set[str]] = {}
    for rule in rules:
        wb = str(rule.get("workbook") or "?")
        keys = {normalize_branch_key(b) for b in (rule.get("branches") or [])}
        keys.discard("")
        keys_by_wb[wb] = keys
    all_keys: set[str] = set()
    for keys in keys_by_wb.values():
        all_keys |= keys
    workbooks = sorted(keys_by_wb)
    out: list[dict[str, Any]] = []
    for key in sorted(all_keys):
        present = [wb for wb in workbooks if key in keys_by_wb[wb]]
        absent = [wb for wb in workbooks if key not in keys_by_wb[wb]]
        label = key.replace("_", " ")
        if absent:
            out.append(
                {
                    "branch": label,
                    "present_in": present,
                    "absent_from": absent,
                    "consequence": (
                        f"`{label}` is defined in {', '.join(present)} "
                        f"and missing from {', '.join(absent)}."
                    ),
                }
            )
            continue
        conditions = {
            str(rule.get("workbook") or "?"): _branch_condition(rule, key) for rule in rules
        }
        unique = {c for c in conditions.values() if c}
        if len(unique) > 1:
            detail = "; ".join(f"{wb}: {cond}" for wb, cond in sorted(conditions.items()) if cond)
            out.append(
                {
                    "branch": label,
                    "present_in": present,
                    "absent_from": [],
                    "consequence": (
                        f"`{label}` is the same name in {', '.join(present)} "
                        f"but the columns / M source disagree. {detail}"
                    ),
                }
            )
    return out


def merge_access_payloads(*payloads: dict[str, Any] | None) -> dict[str, Any]:
    by_wb: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        if not payload:
            continue
        for rule in payload.get("access_rules") or []:
            wb = str(rule.get("workbook") or "")
            if wb:
                by_wb[wb] = rule
    rules = list(by_wb.values())
    divergences = divergences_from_rules(rules)
    if not divergences and len(rules) >= 2:
        # Schema requires minItems 1; keep a placeholder only if compare ran.
        names = [str(r.get("workbook")) for r in rules]
        divergences = [
            {
                "branch": "(none detected)",
                "present_in": names,
                "absent_from": [],
                "consequence": "No RLS / User Filter branch differences were parsed.",
            }
        ]
    return {"access_rules": rules, "divergences": divergences}


def build_powerbi_access(paths: list[Path]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    for path in paths:
        rule = access_rule(path)
        if rule:
            rules.append(rule)
    return merge_access_payloads({"access_rules": rules, "divergences": []})
