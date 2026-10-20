"""Ask CoCo, what a host switches on (feature file 1.3). Pure Python.

Everything is optional for the host: a feature appears in the conversation's view only when the host
switches it on or supplies its data, and a host that uses none sees no trace of it.
"""

from __future__ import annotations

from dataclasses import dataclass

DISPLAY = ("latest", "shorten", "raw")
ACCEPT = (".csv", ".tsv", ".txt", ".md", ".json", ".pdf", ".xlsx", ".docx")


@dataclass(frozen=True)
class Attachments:
    """Files the user attaches in the field, saved in the working folder and named to the agent."""

    multi: bool = True
    accept: tuple[str, ...] | list[str] = ACCEPT  # an empty list accepts any type
    max_mb: float = 10


@dataclass(frozen=True)
class Features:
    queue: bool = True  # type while CoCo works or connects: the message waits its turn
    steps: bool = True  # one card per tool call (off: only failed and refused ones stay)
    motion: bool = True  # the window's animation
    copy: bool = True  # Copy on answers, code, tables
    page_text: bool = False  # each message carries the text the page shows
    page_exclude: tuple[str, ...] = ()  # CSS selectors left out of that text
    attachments: Attachments | None = None
    planning: bool = False  # the menu offers "Plan first"
    display: tuple[str, ...] = ()  # menu switches: "latest", "shorten", "raw"
    session_details: bool = False  # the menu offers Session details
    reasoning: bool = False  # CoCo's reasoning as a fold among the steps
    download_csv: bool = False  # Download CSV in the wider table view

    def __post_init__(self) -> None:
        unknown = [name for name in self.display if name not in DISPLAY]
        if unknown:
            raise ValueError(
                f"Features.display knows {', '.join(DISPLAY)}; not {', '.join(unknown)}"
            )

    @classmethod
    def all(cls) -> Features:
        """Everything on: the playground."""
        return cls(
            page_text=True,
            attachments=Attachments(),
            planning=True,
            display=DISPLAY,
            session_details=True,
            reasoning=True,
            download_csv=True,
        )
