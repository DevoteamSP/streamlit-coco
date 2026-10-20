"""Load doc/training/training.yml (parent of this app)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

_MD_HREF = re.compile(r"(\[[^\]]*\]\()([^)\s]+?)\.md(#[^)]*)?(\))")
_HTML_HREF = re.compile(r'href="([^"]+)"')
_ANCHOR = re.compile(r"[^A-Za-z0-9_-]")

APP_DIR = Path(__file__).resolve().parent
_DEFAULT_PACK_DIR = APP_DIR.parent
_pack_dir_override: Path | None = None
MANIFEST_NAME = "training.yml"


def pack_dir() -> Path:
    """Folder that holds ``training.yml`` (parent of ``app/`` unless overridden)."""
    return _pack_dir_override if _pack_dir_override is not None else _DEFAULT_PACK_DIR


def set_pack_dir(directory: Path | None) -> None:
    """Point the viewer at another asset's ``doc/training/``. ``None`` resets."""
    global _pack_dir_override
    _pack_dir_override = Path(directory).resolve() if directory is not None else None


#: Default location (``app/`` parent). Prefer ``pack_dir()`` so an embed can override.
PACK_DIR = _DEFAULT_PACK_DIR

TRACKS = (
    "enablement",
    "training",
    "certifications",
    "user-guide",
    "technical-guide",
)
GUIDE_TRACKS = ("user-guide", "technical-guide")

_KIND_ORDER = {
    "enablement": ("intro", "setup", "guided-tour", "hands-on", "demo"),
    "training": ("case",),
    "certifications": ("quiz",),
    "user-guide": ("index", "section"),
    "technical-guide": ("index", "help", "section"),
}

#: Reading order of the levels, per track — `advanced` does not rank the same
#: for a practice case as for a certification.
_LEVEL_ORDER = {
    "training": ("simple", "intermediate", "advanced"),
    "certifications": ("enablement", "user", "advanced", "expert"),
}

#: Guide chapters in reading order, grouped as the app lists them (STANDARD §18
#: Guides). A name ending in "-" is a family of files. Same table as
#: `navigator/utils/training_manifest.py` in dsp-assets — copied, because this
#: app must run without dsp-assets.
GUIDE_CHAPTERS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "user-guide": (
        ("start", ("index", "concepts", "getting-started")),
        ("tasks", ("task-",)),
        ("reference", ("reference-", "outputs", "modes")),
        ("answers", ("faq",)),
    ),
    "technical-guide": (
        ("understand", ("index", "architecture")),
        ("run", ("install", "configuration", "security", "operations", "upgrade-and-release")),
        ("build", ("data-and-contracts", "testing-and-ci", "extending")),
        ("answers", ("limits", "help")),
    ),
}


def chapter_stem(source: str) -> str:
    """`technical-guide/sections/install.fr.md` -> `install`."""
    stem = PurePosixPath(source).stem
    for suffix in (".fr", ".es"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _matches(stem: str, chapter: str) -> bool:
    return stem.startswith(chapter) if chapter.endswith("-") else stem == chapter


def chapter_group(track: str, source: str) -> str:
    """Chapter family of a guide page (`start`, `tasks`, …), or `more`."""
    stem = chapter_stem(source)
    for group, chapters in GUIDE_CHAPTERS.get(track, ()):
        if any(_matches(stem, chapter) for chapter in chapters):
            return group
    return "more"


def chapter_rank(track: str, source: str) -> tuple[int, int, str]:
    """Reading-order key for a guide page. Stems outside the chapter list sort last."""
    stem = chapter_stem(source)
    groups = GUIDE_CHAPTERS.get(track, ())
    for group_idx, (_, chapters) in enumerate(groups):
        for chapter_idx, chapter in enumerate(chapters):
            if _matches(stem, chapter):
                return (group_idx, chapter_idx, stem)
    return (len(groups), 0, stem)


@dataclass(frozen=True)
class Doc:
    kind: str
    track: str
    lang: str
    source: str
    rendered: tuple[str, ...] = ()
    level: str | None = None
    certifies: bool = False
    title: str = ""

    @property
    def source_path(self) -> Path:
        return pack_dir() / self.source

    def html_path(self) -> Path | None:
        for name in self.rendered:
            if name.endswith(".html"):
                path = pack_dir() / name
                if path.is_file():
                    return path
        sibling = self.source_path.with_suffix(".html")
        if sibling.is_file():
            return sibling
        return None


@dataclass(frozen=True)
class Route:
    """One entry on the pack homepage — a situation, not a job title (STANDARD §18 R1)."""

    id: str
    title: str
    time: str
    entry_cost: str
    steps: tuple[str, ...]
    outcome: str


def page_id(source: str) -> str:
    """`user-guide/sections/concepts.fr.md` -> `user-guide/sections/concepts`.

    The language- and extension-independent id a route `steps` entry refers to.
    Same rule as `navigator/utils/training_manifest.py::page_id` in dsp-assets —
    copied, because this app must run without dsp-assets.
    """
    canonical = canonical_source(source)
    return str(Path(canonical).with_suffix(""))


@dataclass(frozen=True)
class Pack:
    format: str
    asset: str
    documents: tuple[Doc, ...]
    routes: tuple[Route, ...] = ()
    not_covered: tuple[str, ...] = ()
    contact_note: str = ""

    def route_by_id(self, route_id: str | None) -> Route | None:
        if not route_id:
            return None
        return next((route for route in self.routes if route.id == route_id), None)

    def doc_for_step(self, step: str, lang: str) -> Doc | None:
        return next(
            (doc for doc in self.documents if doc.lang == lang and page_id(doc.source) == step),
            None,
        )

    def tracks_present(self, lang: str) -> tuple[str, ...]:
        seen = {doc.track for doc in self.documents if doc.lang == lang}
        return tuple(track for track in TRACKS if track in seen)

    def docs_for(self, track: str, lang: str) -> tuple[Doc, ...]:
        docs = [
            doc
            for doc in self.documents
            if doc.track == track and doc.lang == lang and doc.kind != "deck"
        ]
        if track in GUIDE_TRACKS:
            return tuple(sorted(docs, key=lambda doc: chapter_rank(track, doc.source)))
        kinds = _KIND_ORDER.get(track, ())
        levels = _LEVEL_ORDER.get(track, ())
        return tuple(sorted(docs, key=lambda doc: _doc_sort_key(doc, kinds, levels)))

    def guide_groups(self, track: str, lang: str) -> list[tuple[str, tuple[Doc, ...]]]:
        """Guide pages by chapter family, in reading order. Empty families are skipped."""
        groups: dict[str, list[Doc]] = {}
        for doc in self.docs_for(track, lang):
            groups.setdefault(chapter_group(track, doc.source), []).append(doc)
        order = [group for group, _ in GUIDE_CHAPTERS.get(track, ())] + ["more"]
        return [(group, tuple(groups[group])) for group in order if group in groups]

    def sibling(self, doc: Doc, lang: str) -> Doc | None:
        key = canonical_source(doc.source)
        for other in self.documents:
            if other.lang == lang and canonical_source(other.source) == key:
                return other
        return None

    def doc_by_source(self, source: str, lang: str) -> Doc | None:
        for doc in self.documents:
            if doc.source == source and doc.lang == lang:
                return doc
        return None

    def doc_for_href(self, current_html: Path, href: str) -> Doc | None:
        path_part = href.strip().split("#", 1)[0].split("?", 1)[0].strip()
        if not path_part or path_part.startswith(
            ("http://", "https://", "mailto:", "javascript:", "data:")
        ):
            return None
        resolved = (current_html.parent / path_part).resolve()
        root = pack_dir().resolve()
        if resolved != root and root not in resolved.parents:
            return None
        wanted = {resolved}
        if resolved.suffix == ".html":
            wanted.add(resolved.with_suffix(".md"))
        for doc in self.documents:
            paths = [doc.source_path.resolve()]
            html_path = doc.html_path()
            if html_path is not None:
                paths.append(html_path.resolve())
            if any(path in wanted for path in paths):
                return doc
        return None

    @property
    def display_name(self) -> str:
        raw = (self.asset or "Training").strip()
        parts = [part for part in raw.replace("_", "-").split("-") if part]
        if not parts:
            return "Training"
        return " ".join(part.upper() if len(part) <= 3 else part.title() for part in parts)


def _doc_sort_key(
    doc: Doc, kinds: tuple[str, ...], levels: tuple[str, ...]
) -> tuple[int, int, str]:
    kind_rank = kinds.index(doc.kind) if doc.kind in kinds else 99
    level_rank = levels.index(doc.level) if doc.level in levels else 99
    return (kind_rank, level_rank, doc.source)


def html_links(markdown: str) -> str:
    """Rewrite Markdown hrefs so the app never points at ``.md`` files."""

    def _href(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}.html{match.group(3) or ''}{match.group(4)}"

    return _MD_HREF.sub(_href, markdown)


def slugify(text: str) -> str:
    """Heading id, identical to the renderer's rule (navigator/utils/training_html.py)."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = re.sub(r"[`*_\[\]()]", "", cleaned).lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    return re.sub(r"^-+|-+$", "", cleaned)


def safe_anchor(anchor: str | None) -> str:
    """Keep an element id usable in a selector: letters, digits, `-` and `_` only."""
    return _ANCHOR.sub("", anchor or "")


def html_for_iframe(
    html_text: str,
    current_html: Path,
    pack: Pack,
    *,
    anchor: str | None = None,
) -> str:
    """Rewrite in-pack links so the iframe never loads the Streamlit app.

    A link such as ``help.html#empty-discover`` keeps its fragment: the app
    opens that page and scrolls to the heading. ``anchor`` is the heading to
    scroll to once this page has loaded.
    """

    def _href(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("#", "http://", "https://", "mailto:", "javascript:", "?")):
            return match.group(0)
        target = pack.doc_for_href(current_html, href)
        if target is None:
            return match.group(0)
        fragment = safe_anchor(href.split("#", 1)[1]) if "#" in href else ""
        extra = f' data-pack-anchor="{fragment}"' if fragment else ""
        return (
            f'href="#"'
            f' data-pack-doc="{escape(target.source, quote=True)}"'
            f' data-pack-track="{escape(target.track, quote=True)}"'
            f"{extra}"
        )

    rewritten = _HTML_HREF.sub(_href, html_text)
    embed = """
<style>
.topbar{display:none!important}
.layout{padding-top:12px;grid-template-columns:minmax(0,1fr)!important}
.prevnext{display:none!important}
.toc{display:none!important}
</style>
<script>
document.addEventListener("click", function (event) {
  var node = event.target;
  var el0 = node && node.nodeType === 1 ? node : node && node.parentElement;
  var self = el0 && el0.closest ? el0.closest('a[href^="#"]') : null;
  if (self) {
    var id = (self.getAttribute("href") || "").slice(1);
    var target = id && document.getElementById(id);
    if (target) {
      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
  }
  var el = node && node.nodeType === 1 ? node : node && node.parentElement;
  var a = el && el.closest ? el.closest("a[data-pack-doc]") : null;
  if (!a || !window.top) return;
  event.preventDefault();
  var doc = a.getAttribute("data-pack-doc") || "";
  var track = a.getAttribute("data-pack-track") || "";
  var anchor = a.getAttribute("data-pack-anchor") || "";
  if (!doc) return;
  var url = new URL(window.top.location.href);
  url.searchParams.set("pack_doc", doc);
  url.searchParams.set("pack_track", track);
  if (anchor) url.searchParams.set("pack_anchor", anchor);
  else url.searchParams.delete("pack_anchor");
  window.top.location.href = url.toString();
}, true);
</script>
"""
    target = safe_anchor(anchor)
    if target:
        embed += f"""<script>
window.addEventListener("load", function () {{
  var el = document.getElementById("{target}");
  if (el) el.scrollIntoView();
}});
</script>
"""
    if "</head>" in rewritten:
        return rewritten.replace("</head>", f"{embed}</head>", 1)
    return embed + rewritten


def canonical_source(source: str) -> str:
    path = Path(source)
    stem = path.stem
    if stem.endswith(".fr"):
        stem = stem[:-3]
    elif stem.endswith(".es"):
        stem = stem[:-3]
    return str(path.with_name(f"{stem}{path.suffix}"))


def _title_from_markdown(path: Path, fallback: str) -> str:
    if not path.is_file():
        return fallback
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return re.sub(r"\s*\{#[\w-]+\}\s*$", "", stripped[2:]).strip()
    return fallback


def _fallback_title(entry: dict[str, Any]) -> str:
    level = str(entry.get("level") or "").strip()
    kind = str(entry.get("kind") or "").strip()
    source = str(entry.get("source") or "").strip()
    if kind == "quiz" and level:
        return level.replace("-", " ").title()
    if kind == "case" and level:
        return level.replace("-", " ").title()
    stem = Path(source).stem
    for suffix in (".fr", ".es"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("-", " ").replace("_", " ").title() or kind


def load_pack(directory: Path | None = None) -> Pack | None:
    root = Path(directory).resolve() if directory is not None else pack_dir()
    path = root / MANIFEST_NAME
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return None
    docs: list[Doc] = []
    for entry in raw.get("documents") or []:
        if not isinstance(entry, dict):
            continue
        rendered = entry.get("rendered") or []
        if isinstance(rendered, str):
            rendered = [rendered]
        source = str(entry.get("source") or "").strip()
        fallback = _fallback_title(entry)
        docs.append(
            Doc(
                kind=str(entry.get("kind") or "").strip(),
                track=str(entry.get("track") or entry.get("audience") or "").strip(),
                lang=str(entry.get("lang") or "en").strip(),
                source=source,
                rendered=tuple(str(item) for item in rendered),
                level=str(entry.get("level") or "").strip() or None,
                certifies=bool(entry.get("certifies", False)),
                title=_title_from_markdown(root / source, fallback) if source else fallback,
            )
        )
    routes: list[Route] = []
    for entry in raw.get("routes") or []:
        if not isinstance(entry, dict):
            continue
        steps = entry.get("steps") or []
        if isinstance(steps, str):
            steps = [steps]
        routes.append(
            Route(
                id=str(entry.get("id") or "").strip(),
                title=str(entry.get("title") or "").strip(),
                time=str(entry.get("time") or "").strip(),
                entry_cost=str(entry.get("entry_cost") or "").strip(),
                steps=tuple(str(step).strip() for step in steps if str(step).strip()),
                outcome=str(entry.get("outcome") or "").strip(),
            )
        )

    not_covered = raw.get("not_covered") or []
    if isinstance(not_covered, str):
        not_covered = [not_covered]

    return Pack(
        format=str(raw.get("format") or ""),
        asset=str(raw.get("asset") or ""),
        documents=tuple(docs),
        routes=tuple(routes),
        not_covered=tuple(str(item).strip() for item in not_covered if str(item).strip()),
        contact_note=str(raw.get("contact") or "").strip(),
    )
