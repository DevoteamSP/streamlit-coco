"""Parse certification Markdown (questions + answer-key table)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

_PASS = re.compile(r"pass\s+threshold[:\s\*]*(\d+)\s*/\s*(\d+)", re.IGNORECASE)
_ANSWER_HEADING = re.compile(r"^#{1,4}\s+answer\s*(key)?s?\s*$", re.IGNORECASE)
_Q_HEAD = re.compile(r"^#{1,6}\s+Q?\s*(\d+)[.)]\s+(.*)$", re.IGNORECASE)
_OPTION = re.compile(r"^[ \t]*(?:[-*]\s+)?([a-z])[.)]\s+(.+)$", re.IGNORECASE)
_SELECT_ALL = re.compile(r"select\s+all(?:\s+that\s+apply)?", re.IGNORECASE)
_TABLE = re.compile(r"^\|\s*(?:Q\s*)?(\d+)\s*\|\s*(.+)$")
_LETTERS = re.compile(r"[A-Za-z]")


@dataclass(frozen=True)
class Question:
    number: int
    prompt: str
    options: tuple[tuple[str, str], ...]
    answers: tuple[str, ...]
    multi: bool
    explanation: str


@dataclass(frozen=True)
class Quiz:
    title: str
    intro: str
    pass_score: int
    questions: tuple[Question, ...]


def _split_key(text: str) -> tuple[str, str]:
    lines = text.replace("\r\n", "\n").split("\n")
    for index, line in enumerate(lines):
        if _ANSWER_HEADING.match(line.strip()):
            return "\n".join(lines[:index]), "\n".join(lines[index + 1 :])
    return text, ""


def _parse_key(key: str) -> dict[int, tuple[tuple[str, ...], str]]:
    parsed: dict[int, tuple[tuple[str, ...], str]] = {}
    for line in key.split("\n"):
        match = _TABLE.match(line.strip())
        if not match or set(match.group(2)) <= set("-:| "):
            continue
        number = int(match.group(1))
        rest = match.group(2)
        cells = [cell.strip() for cell in rest.split("|")]
        answer_cell = cells[0].replace("*", "").strip()
        explanation = cells[1].strip() if len(cells) > 1 else ""
        letters = tuple(letter.lower() for letter in _LETTERS.findall(answer_cell))
        parsed[number] = (letters, explanation)
    return parsed


def parse_quiz(markdown: str) -> Quiz:
    body, key = _split_key(markdown)
    answers = _parse_key(key)
    title = "Certification"
    intro_lines: list[str] = []
    questions: list[Question] = []
    current_n: int | None = None
    prompt = ""
    options: list[tuple[str, str]] = []
    multi = False

    def flush() -> None:
        nonlocal current_n, prompt, options, multi
        if current_n is None:
            return
        letters, explanation = answers.get(current_n, ((), ""))
        questions.append(
            Question(
                number=current_n,
                prompt=prompt.strip(),
                options=tuple(options),
                answers=letters,
                multi=multi or len(letters) > 1,
                explanation=explanation,
            )
        )
        current_n, prompt, options, multi = None, "", [], False

    for line in body.split("\n"):
        heading = _Q_HEAD.match(line.strip())
        if heading:
            flush()
            current_n = int(heading.group(1))
            prompt = heading.group(2)
            multi = bool(_SELECT_ALL.search(prompt))
            continue
        if current_n is None:
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.strip():
                intro_lines.append(line)
            continue
        opt = _OPTION.match(line)
        if opt:
            options.append((opt.group(1).lower(), opt.group(2).strip()))

    flush()
    pass_need, pass_out = None, None
    found = _PASS.search(markdown)
    if found:
        pass_need, pass_out = int(found.group(1)), int(found.group(2))
    total = len(questions)
    if total == 0:
        pass_score = 0
    elif pass_need is not None and pass_out == total:
        pass_score = pass_need
    else:
        pass_score = math.ceil(0.8 * total)
    intro = "\n".join(intro_lines).strip()
    return Quiz(title=title, intro=intro, pass_score=pass_score, questions=tuple(questions))


def load_quiz(path: Path) -> Quiz:
    return parse_quiz(path.read_text(encoding="utf-8"))


def score(quiz: Quiz, picked: dict[int, frozenset[str]]) -> tuple[int, bool]:
    correct = 0
    for question in quiz.questions:
        got = picked.get(question.number, frozenset())
        expected = frozenset(question.answers)
        if got == expected and expected:
            correct += 1
    return correct, correct >= quiz.pass_score
