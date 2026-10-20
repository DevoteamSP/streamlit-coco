"""Streamlit navigator for a product training pack (STANDARD §18)."""

from __future__ import annotations

import html
import re
from pathlib import Path

import streamlit as st
from coco_rail import render_window
from html_frame import render_html_frame
from i18n import LANG_FLAG, LANG_LABEL, LANGS, TRACK_BADGE, TRACK_ICON, t
from pack import (
    Doc,
    Pack,
    Route,
    html_for_iframe,
    html_links,
    load_pack,
    pack_dir,
    page_id,
    set_pack_dir,
)
from quiz import load_quiz, score

_PATH = ("enablement", "training", "certifications")
_REFERENCE = ("user-guide", "technical-guide")
_LANG_KEY = "training_lang"
_TRACK_KEY = "training_track"
_ROUTE_KEY = "training_route"
_DOC_KEY = "training_doc"
_ANCHOR_KEY = "training_anchor"
_PACK_ROOT_KEY = "training_pack_root"
_QP_DOC = "pack_doc"
_QP_TRACK = "pack_track"
_QP_ANCHOR = "pack_anchor"
_QUIZ_KEY = "training_quiz_picks"


@st.cache_data(ttl="30s")
def _cached_pack(mtime: float, root: str) -> Pack | None:
    del mtime
    return load_pack(Path(root))


def _pack() -> Pack | None:
    root = pack_dir()
    manifest = root / "training.yml"
    stamp = manifest.stat().st_mtime if manifest.is_file() else 0.0
    return _cached_pack(stamp, str(root.resolve()))


def _logo() -> Path:
    return pack_dir() / "enablement" / "dsp_logo.png"


def _browser_lang(available: list[str]) -> str:
    """The reader's own language when the pack has it, English otherwise."""
    candidates: list[str] = []
    try:
        candidates.append(str(getattr(st.context, "locale", "") or ""))
    except Exception:  # noqa: BLE001 - older Streamlit, or no browser context
        pass
    try:
        header = st.context.headers.get("Accept-Language", "")
    except Exception:  # noqa: BLE001
        header = ""
    candidates += [part.split(";")[0] for part in header.split(",")]
    for candidate in candidates:
        code = candidate.strip().lower().replace("_", "-").split("-")[0]
        if code in available:
            return code
    return "en" if "en" in available else (available[0] if available else "en")


def _init_state(pack: Pack) -> None:
    if _LANG_KEY not in st.session_state:
        st.session_state[_LANG_KEY] = _browser_lang(_available_langs(pack))
    st.session_state.setdefault(_TRACK_KEY, None)
    st.session_state.setdefault(_ROUTE_KEY, None)
    st.session_state.setdefault(_DOC_KEY, None)
    st.session_state.setdefault(_ANCHOR_KEY, None)
    qp_doc = st.query_params.get(_QP_DOC)
    qp_track = st.query_params.get(_QP_TRACK)
    qp_anchor = st.query_params.get(_QP_ANCHOR)
    if isinstance(qp_doc, str) and qp_doc:
        st.session_state[_DOC_KEY] = qp_doc
        st.session_state[_ANCHOR_KEY] = qp_anchor if isinstance(qp_anchor, str) else None
        if isinstance(qp_track, str) and qp_track:
            st.session_state[_TRACK_KEY] = qp_track
        return
    if isinstance(qp_track, str) and qp_track:
        st.session_state[_TRACK_KEY] = qp_track
        st.session_state[_DOC_KEY] = None


def _sync_query(track: str | None, source: str | None, anchor: str | None = None) -> None:
    st.session_state[_ANCHOR_KEY] = anchor
    if anchor:
        st.query_params[_QP_ANCHOR] = anchor
    elif _QP_ANCHOR in st.query_params:
        del st.query_params[_QP_ANCHOR]
    if track:
        st.query_params[_QP_TRACK] = track
    elif _QP_TRACK in st.query_params:
        del st.query_params[_QP_TRACK]
    if source:
        st.query_params[_QP_DOC] = source
    elif _QP_DOC in st.query_params:
        del st.query_params[_QP_DOC]


def _go_home() -> None:
    st.session_state[_TRACK_KEY] = None
    st.session_state[_ROUTE_KEY] = None
    st.session_state[_DOC_KEY] = None
    _sync_query(None, None)


def _open_track(track: str) -> None:
    st.session_state[_TRACK_KEY] = track
    st.session_state[_ROUTE_KEY] = None
    st.session_state[_DOC_KEY] = None
    _sync_query(track, None)


def _open_doc(source: str, track: str) -> None:
    st.session_state[_TRACK_KEY] = track
    st.session_state[_DOC_KEY] = source
    _sync_query(track, source)


def _open_route(route: Route) -> None:
    """Enter a situation from the homepage (R1) and jump to its first page."""
    st.session_state[_ROUTE_KEY] = route.id
    pack = _pack()
    lang = st.session_state.get(_LANG_KEY, "en")
    doc = pack.doc_for_step(route.steps[0], lang) if pack and route.steps else None
    if doc is not None:
        _open_doc(doc.source, doc.track)


def _open_anchor(source: str, track: str, anchor: str) -> None:
    st.session_state[_TRACK_KEY] = track
    st.session_state[_DOC_KEY] = source
    _sync_query(track, source, anchor)


def _set_lang(pack: Pack, lang: str) -> None:
    previous = st.session_state.get(_LANG_KEY)
    current_source = st.session_state.get(_DOC_KEY)
    st.session_state[_LANG_KEY] = lang
    if previous and previous != lang and isinstance(current_source, str):
        current = pack.doc_by_source(current_source, previous)
        sibling = pack.sibling(current, lang) if current is not None else None
        st.session_state[_DOC_KEY] = sibling.source if sibling is not None else None


def _available_langs(pack: Pack) -> list[str]:
    return [code for code in LANGS if any(doc.lang == code for doc in pack.documents)]


def _count_label(lang: str, track: str, n: int) -> str:
    if track == "certifications":
        return t(lang, "quiz_n").format(n=n)
    if track in _REFERENCE:
        return t(lang, "pages_n").format(n=n)
    return t(lang, "docs_n").format(n=n)


def _metrics(pack: Pack, lang: str) -> tuple[int, int]:
    tracks = pack.tracks_present(lang)
    docs = [doc for doc in pack.documents if doc.lang == lang and doc.kind != "deck"]
    return len(tracks), len(docs)


def _blurb(lang: str, track: str, name: str) -> str:
    text = t(lang, f"blurb_{track}")
    if "{name}" in text:
        return text.format(name=name)
    return text


def _short_title(title: str, name: str) -> str:
    for sep in (" — ", " – ", " - "):
        prefix = f"{name}{sep}"
        if title.startswith(prefix):
            return title[len(prefix) :]
    return title


def _doc_excerpt(doc: Doc, limit: int | None = None) -> str:
    """First prose lines of a page, as plain text (no links, no code marks).

    Shown in full: `limit` cuts the text only when a caller asks for it.
    """
    if not doc.source_path.is_file():
        return ""
    lines: list[str] = []
    for line in doc.source_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("---"):
            if stripped == "---" and lines:
                break
            continue
        if stripped.startswith("|") or stripped.startswith("```"):
            break
        lines.append(stripped)
        if limit is not None and len(" ".join(lines)) >= limit:
            break
        if len(lines) >= 3:
            break
    text = " ".join(lines)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit is not None and len(text) > limit:
        return text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text


def _flag_control(pack: Pack, lang: str, *, key: str) -> None:
    codes = _available_langs(pack)
    if not codes:
        return
    cols = st.columns(len(codes), gap="small")
    for col, code in zip(cols, codes, strict=True):
        with col:
            pressed = st.button(
                f"{LANG_FLAG[code]}",
                key=f"{key}_{code}",
                type="primary" if code == lang else "secondary",
                help=f"{LANG_FLAG[code]} {LANG_LABEL[code]}",
                width="stretch",
            )
            if pressed and code != lang:
                _set_lang(pack, code)
                st.rerun()


def _title_bar(pack: Pack, lang: str, *, key: str) -> None:
    name = html.escape(pack.display_name)
    kicker = html.escape(t(lang, "hero_kicker"))
    sub = html.escape(t(lang, "hero_sub"))
    brand = html.escape(t(lang, "brand"))
    n_tracks, n_docs = _metrics(pack, lang)
    tracks_l = html.escape(t(lang, "metric_tracks"))
    docs_l = html.escape(t(lang, "metric_docs"))
    st.html(
        """
<style>
  .st-key-tb_shell {
    background: linear-gradient(135deg, #1E2028 0%, #2A2D38 55%, #3A1F2C 100%);
    border-radius: 16px;
    padding: 1.05rem 1.15rem 0.95rem;
  }
  .tb-kicker { color: #F5364B; font-weight: 700; letter-spacing: 0.14em; font-size: 0.7rem;
    text-transform: uppercase; }
  .tb-name { font-size: clamp(1.4rem, 3.2vw, 2.05rem); font-weight: 700; line-height: 1.15;
    margin: 0.28rem 0 0.35rem; color: #fff; overflow-wrap: anywhere; }
  .tb-sub { color: #C8CAD4; font-size: 0.95rem; max-width: 42rem; }
  .tb-brand { margin-top: 0.4rem; color: #9AA0B5; font-size: 0.78rem; }
  .tb-kpis { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.85rem; }
  .tb-kpi { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px; padding: 0.4rem 0.8rem 0.45rem; min-width: 5.8rem; }
  .tb-kpi .lbl { color: #9AA0B5; font-size: 0.66rem; text-transform: uppercase; letter-spacing:
    0.08em; }
  .tb-kpi .val { color: #fff; font-size: 1.12rem; font-weight: 700; margin-top: 0.08rem; }
  [class*="st-key-pack_menu"] {
    position: sticky;
    top: 0.5rem;
    padding-right: 0.75rem;
    border-right: 1px solid rgba(30, 32, 40, 0.08);
  }
  [class*="st-key-pack_menu"] [data-testid="stVerticalBlock"] { gap: 0.2rem; }
  /* Streamlit centres the label in a flex wrapper inside the button. */
  [class*="st-key-pack_menu"] button {
    justify-content: flex-start !important;
    padding: 0.32rem 0.6rem;
    border-radius: 8px;
  }
  [class*="st-key-pack_menu"] button > div,
  [class*="st-key-pack_menu"] button > div > span {
    justify-content: flex-start !important;
    width: 100%;
  }
  [class*="st-key-pack_menu"] button p {
    text-align: left !important;
    margin: 0;
    font-size: 0.92rem;
    font-weight: 600;
    line-height: 1.35;
  }
  /* Chapter families: the headings of the menu, above the document titles. */
  [class*="st-key-pack_group"] p {
    font-size: 1.02rem;
    font-weight: 700;
    color: #1E2028;
    letter-spacing: 0.01em;
    margin: 0.75rem 0 0.2rem;
  }
  [class*="st-key-pack_menu"] button:hover {
    background: rgba(245, 54, 75, 0.08);
  }
  [class*="st-key-pack_hint"] {
    margin: -0.2rem 0 0.45rem 0.65rem;
  }
  [class*="st-key-pack_hint"] p {
    font-size: 0.74rem;
    line-height: 1.25;
    color: #7B7F8E;
    margin: 0;
  }
  [class*="st-key-card_row"] [data-testid="stHorizontalBlock"] {
    align-items: stretch;
  }
  [class*="st-key-card_row"] [data-testid="stColumn"] {
    display: flex;
    flex-direction: column;
  }
  [class*="st-key-card_row"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
  [class*="st-key-card_row"] [data-testid="stColumn"] [data-testid="stLayoutWrapper"],
  [class*="st-key-card_row"] [data-testid="stColumn"] [data-testid="stLayoutWrapper"] >
    [data-testid="stVerticalBlock"] {
    height: 100%;
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
  }
  [class*="st-key-card_row"] [data-testid="stColumn"] [data-testid="stLayoutWrapper"] >
    [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child {
    margin-top: auto;
  }
</style>
"""
    )
    with st.container(key="tb_shell"):
        title, actions = st.columns([5.2, 1.55], vertical_alignment="top")
        with title:
            st.html(
                f"""
<div class="tb-kicker">{kicker}</div>
<div class="tb-name">{name}</div>
<div class="tb-sub">{sub}</div>
<div class="tb-brand">{brand}</div>
<div class="tb-kpis">
  <div class="tb-kpi"><div class="lbl">{tracks_l}</div><div class="val">{n_tracks}</div></div>
  <div class="tb-kpi"><div class="lbl">{docs_l}</div><div class="val">{n_docs}</div></div>
</div>
"""
            )
        with actions:
            _flag_control(pack, lang, key=key)


def _track_card(
    pack: Pack,
    lang: str,
    track: str,
    *,
    primary: bool = False,
    hint_key: str | None = None,
) -> None:
    docs = pack.docs_for(track, lang)
    icon = TRACK_ICON.get(track, ":material/folder:")
    color = TRACK_BADGE.get(track, "gray")
    with st.container(border=True, height="stretch"):
        st.markdown(f"{icon} :{color}-badge[{t(lang, track)}]")
        st.markdown(f"**{_blurb(lang, track, pack.display_name)}**")
        st.markdown(t(lang, f"includes_{track}"))
        if docs:
            listed = "\n".join(f"- {_short_title(doc.title, pack.display_name)}" for doc in docs)
            st.markdown(listed)
        st.caption(
            f"{_count_label(lang, track, len(docs))} · {t(lang, f'time_{track}')}"
            + (f" · {t(lang, hint_key)}" if hint_key else "")
        )
        st.button(
            t(lang, "start") if primary else t(lang, "open"),
            key=f"open_track_{track}",
            type="primary" if primary else "secondary",
            icon=":material/arrow_forward:",
            width="stretch",
            on_click=_open_track,
            args=(track,),
            disabled=not docs,
        )


def _route_card(pack: Pack, lang: str, route: Route, *, primary: bool = False) -> None:
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{route.title}**")
        st.caption(f":gray-badge[{route.entry_cost}]  :blue-badge[{route.time}]")
        if route.outcome:
            st.markdown(route.outcome)
        st.button(
            t(lang, "start") if primary else t(lang, "open"),
            key=f"open_route_{route.id}",
            type="primary" if primary else "secondary",
            icon=":material/arrow_forward:",
            width="stretch",
            on_click=_open_route,
            args=(route,),
            disabled=not route.steps,
        )


def _render_routes(pack: Pack, lang: str) -> None:
    if not pack.routes:
        return
    with st.container(key="card_row_routes"):
        st.subheader(t(lang, "routes_title"))
        cols = st.columns(len(pack.routes), gap="medium")
        for idx, (col, route) in enumerate(zip(cols, pack.routes, strict=True)):
            with col:
                _route_card(pack, lang, route, primary=idx == 0)


def _render_scope_callouts(pack: Pack, lang: str) -> None:
    items: list[tuple[str, str]] = []
    if pack.not_covered:
        items.append((t(lang, "scope_title"), "\n".join(f"- {line}" for line in pack.not_covered)))
    if pack.contact_note:
        items.append((t(lang, "contact_title"), pack.contact_note))
    if not items:
        return
    with st.container(key="card_row_scope"):
        cols = st.columns(len(items), gap="medium")
        for col, (title, body) in zip(cols, items, strict=True):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.markdown(body)


def _render_home(pack: Pack, lang: str) -> None:
    _title_bar(pack, lang, key="training_lang_home")
    st.space("small")
    _render_routes(pack, lang)
    _render_scope_callouts(pack, lang)
    present = set(pack.tracks_present(lang))
    path = [track for track in _PATH if track in present]
    if path:
        with st.container(key="card_row_path"):
            st.subheader(t(lang, "explore_by_track") if pack.routes else t(lang, "path_title"))
            cols = st.columns(len(path), gap="medium")
            hints = ("path_1_hint", "path_2_hint", "path_3_hint")
            for idx, (col, track) in enumerate(zip(cols, path, strict=True)):
                with col:
                    _track_card(
                        pack,
                        lang,
                        track,
                        primary=idx == 0 and not pack.routes,
                        hint_key=hints[idx] if idx < len(hints) else None,
                    )
    refs = [track for track in _REFERENCE if track in present]
    if refs:
        with st.container(key="card_row_refs"):
            st.subheader(t(lang, "reference"))
            cols = st.columns(len(refs), gap="medium")
            for col, track in zip(cols, refs, strict=True):
                with col:
                    _track_card(pack, lang, track)


def _active_route(pack: Pack, doc: Doc | None) -> Route | None:
    """The route the reader is walking, or None once they stray off it (R3-R4)."""
    route = pack.route_by_id(st.session_state.get(_ROUTE_KEY))
    if route is None:
        return None
    if doc is None or page_id(doc.source) not in route.steps:
        st.session_state[_ROUTE_KEY] = None
        return None
    return route


def _render_route_header(lang: str, track: str, route: Route, doc: Doc) -> None:
    """R2-R3-R5: where this page sits, what it costs to be here, before the content."""
    index = route.steps.index(page_id(doc.source))
    st.caption(
        t(lang, "route_step").format(
            track=t(lang, track), n=index + 1, total=len(route.steps), title=route.title
        )
    )
    st.markdown(f":gray-badge[{route.entry_cost}]  :blue-badge[{route.time}]")


def _render_route_nav(pack: Pack, lang: str, route: Route, doc: Doc, *, key_prefix: str) -> None:
    """R4: name the exit, and the escape hatch back to the five routes.

    Rendered both above and below the page body (`key_prefix` keeps the two
    copies' widget keys apart) so a long page always has it in view.
    """
    index = route.steps.index(page_id(doc.source))
    with st.container(horizontal=True, vertical_alignment="center"):
        if index < len(route.steps) - 1:
            next_doc = pack.doc_for_step(route.steps[index + 1], doc.lang)
            if next_doc is not None:
                st.button(
                    f"{t(lang, 'route_next')} → {_short_title(next_doc.title, pack.display_name)}",
                    key=f"{key_prefix}_route_next_{doc.source}",
                    type="primary",
                    icon=":material/arrow_forward:",
                    on_click=_open_doc,
                    args=(next_doc.source, next_doc.track),
                )
        st.button(
            t(lang, "route_back"),
            key=f"{key_prefix}_route_back_{doc.source}",
            icon=":material/switch_left:",
            on_click=_go_home,
        )
    if index == len(route.steps) - 1 and route.outcome:
        st.success(f"{t(lang, 'route_done')} {route.outcome}", icon=":material/check_circle:")


def _render_track(pack: Pack, lang: str, track: str, source: str | None = None) -> None:
    """Left menu of the track's documents, the selected document on the right."""
    _title_bar(pack, lang, key="training_lang_track")
    docs = pack.docs_for(track, lang)
    doc = pack.doc_by_source(source, lang) if isinstance(source, str) else None
    route = _active_route(pack, doc)
    with st.container(key="page_band_track"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.button(
                t(lang, "home"),
                icon=":material/home:",
                on_click=_go_home,
                key="training_home_track",
            )
            here = f"{t(lang, 'you_are_here')} · {t(lang, track)}"
            st.caption(f"{here} · {doc.title}" if doc is not None else here)
    if not docs:
        st.caption(t(lang, "empty"))
        return
    menu, page = st.columns([1, 3.2], gap="medium")
    with menu:
        _render_menu(pack, lang, track, docs, doc.source if doc is not None else None)
    with page:
        if doc is None:
            _render_track_intro(pack, lang, track, docs)
        elif doc.kind == "quiz":
            if route is not None:
                _render_route_header(lang, track, route, doc)
                _render_route_nav(pack, lang, route, doc, key_prefix="top")
                st.divider()
            _render_quiz(doc, lang)
            if route is not None:
                st.divider()
                _render_route_nav(pack, lang, route, doc, key_prefix="bottom")
            else:
                _render_prev_next(pack, lang, track, docs, doc)
        else:
            if route is not None:
                _render_route_header(lang, track, route, doc)
                _render_route_nav(pack, lang, route, doc, key_prefix="top")
                st.divider()
            st.subheader(doc.title)
            _render_page_body(pack, doc, lang)
            if route is not None:
                st.divider()
                _render_route_nav(pack, lang, route, doc, key_prefix="bottom")
            else:
                _render_prev_next(pack, lang, track, docs, doc)


def _render_menu(
    pack: Pack, lang: str, track: str, docs: tuple[Doc, ...], current: str | None
) -> None:
    icon = TRACK_ICON.get(track, ":material/folder:")
    with st.container(key="pack_menu"):
        st.markdown(f"**{icon} {t(lang, track)}**")
        if track in _REFERENCE:
            for group, pages in pack.guide_groups(track, lang):
                with st.container(key=f"pack_group_{track}_{group}"):
                    st.caption(t(lang, f"group_{group}"))
                for doc in pages:
                    _menu_item(pack, doc, lang, track, current)
        else:
            for doc in docs:
                _menu_item(pack, doc, lang, track, current)


def _menu_item(pack: Pack, doc: Doc, lang: str, track: str, current: str | None) -> None:
    st.button(
        _short_title(doc.title, pack.display_name),
        key=f"menu_{doc.source}",
        type="primary" if doc.source == current else "tertiary",
        width="stretch",
        on_click=_open_doc,
        args=(doc.source, track),
    )
    hint = _doc_excerpt(doc)
    if hint:
        with st.container(key=f"pack_hint_{doc.source}"):
            st.caption(hint)


def _render_prev_next(pack: Pack, lang: str, track: str, docs: tuple[Doc, ...], doc: Doc) -> None:
    """Move to the previous or next document of the track, in its reading order."""
    order = [item.source for item in docs]
    if doc.source not in order:
        return
    index = order.index(doc.source)
    previous = docs[index - 1] if index > 0 else None
    following = docs[index + 1] if index < len(docs) - 1 else None
    if previous is None and following is None:
        return
    st.divider()
    left, right = st.columns(2, gap="small")
    with left:
        if previous is not None:
            st.button(
                f"{t(lang, 'previous')} · {_short_title(previous.title, pack.display_name)}",
                key=f"prev_{doc.source}",
                icon=":material/arrow_back:",
                width="stretch",
                on_click=_open_doc,
                args=(previous.source, track),
            )
    with right:
        if following is not None:
            st.button(
                f"{t(lang, 'next')} · {_short_title(following.title, pack.display_name)}",
                key=f"next_{doc.source}",
                icon=":material/arrow_forward:",
                type="primary",
                width="stretch",
                on_click=_open_doc,
                args=(following.source, track),
            )


def _render_track_intro(pack: Pack, lang: str, track: str, docs: tuple[Doc, ...]) -> None:
    st.header(f"{TRACK_ICON.get(track, ':material/folder:')} {t(lang, track)}")
    st.markdown(f"**{_blurb(lang, track, pack.display_name)}**")
    st.markdown(t(lang, f"includes_{track}"))
    st.caption(f"{_count_label(lang, track, len(docs))} · {t(lang, f'time_{track}')}")
    first = docs[0]
    st.button(
        t(lang, "start") if track in _PATH else t(lang, "open"),
        key=f"intro_open_{track}",
        type="primary",
        icon=":material/arrow_forward:",
        on_click=_open_doc,
        args=(first.source, track),
    )


def _render_quiz(doc: Doc, lang: str) -> None:
    quiz = load_quiz(doc.source_path)
    st.subheader(quiz.title)
    if quiz.intro:
        st.markdown(html_links(quiz.intro))
    st.caption(
        f"{t(lang, 'quiz_score')} · "
        f"{t(lang, 'pass_mark').format(score=f'{quiz.pass_score}/{len(quiz.questions)}')}"
    )
    picks_key = f"{_QUIZ_KEY}:{doc.source}"
    if picks_key not in st.session_state:
        st.session_state[picks_key] = {}
    stored: dict[int, list[str]] = st.session_state[picks_key]
    for question in quiz.questions:
        letters = [letter for letter, _ in question.options]
        texts = [f"{letter}) {text}" for letter, text in question.options]
        widget_key = f"q:{doc.source}:{question.number}"
        st.markdown(f"**Q{question.number}. {question.prompt}**")
        if question.multi:
            chosen = st.multiselect(
                f"Q{question.number}",
                texts,
                default=[
                    texts[letters.index(letter)]
                    for letter in stored.get(question.number, [])
                    if letter in letters
                ],
                label_visibility="collapsed",
                key=widget_key,
            )
            stored[question.number] = [
                letters[texts.index(item)] for item in chosen if item in texts
            ]
        else:
            options = ["—"] + texts
            previous = stored.get(question.number, [])
            default = "—"
            if previous and previous[0] in letters:
                default = texts[letters.index(previous[0])]
            chosen_one = st.radio(
                f"Q{question.number}",
                options,
                index=options.index(default) if default in options else 0,
                label_visibility="collapsed",
                key=widget_key,
            )
            stored[question.number] = (
                [letters[texts.index(chosen_one)]] if chosen_one in texts else []
            )
    with st.container(horizontal=True):
        submit = st.button(t(lang, "quiz_submit"), type="primary")
        reset = st.button(t(lang, "quiz_reset"))
    if reset:
        st.session_state[picks_key] = {}
        st.rerun()
    if submit:
        picked = {number: frozenset(letters) for number, letters in stored.items() if letters}
        correct, passed = score(quiz, picked)
        if passed:
            st.success(
                f"{t(lang, 'quiz_pass')} — {correct}/{len(quiz.questions)}",
                icon=":material/check_circle:",
            )
        else:
            st.error(
                f"{t(lang, 'quiz_fail')} ({correct}/{len(quiz.questions)}, "
                f"{t(lang, 'pass_mark').format(score=str(quiz.pass_score))})",
                icon=":material/error:",
            )


def _render_page_body(pack: Pack, doc: Doc, lang: str) -> None:
    html_path = doc.html_path()
    if html_path is not None and html_path.is_file():
        anchor = st.session_state.get(_ANCHOR_KEY)
        anchor = anchor if isinstance(anchor, str) and anchor else None
        render_html_frame(
            html_for_iframe(html_path.read_text(encoding="utf-8"), html_path, pack, anchor=anchor),
            source=f"{doc.source}#{anchor}" if anchor else doc.source,
        )
        return
    if not doc.source_path.is_file():
        st.caption(t(lang, "empty"))
        return
    st.markdown(doc.source_path.read_text(encoding="utf-8"))


def _render_page(pack: Pack, lang: str, track: str | None, source: str | None) -> None:
    if not track:
        _render_home(pack, lang)
        return
    _render_track(pack, lang, track, source)


def main(directory: Path | None = None) -> None:
    """Browse the pack. ``directory`` is the asset's ``doc/training/`` when embedded."""
    if directory is not None:
        set_pack_dir(directory)
    root = str(pack_dir().resolve())
    previous = st.session_state.get(_PACK_ROOT_KEY)
    if previous != root:
        st.session_state[_PACK_ROOT_KEY] = root
        st.session_state[_TRACK_KEY] = None
        st.session_state[_DOC_KEY] = None
        st.session_state[_ANCHOR_KEY] = None
        for key in (_QP_DOC, _QP_TRACK, _QP_ANCHOR):
            if key in st.query_params:
                del st.query_params[key]
    pack = _pack()
    if pack is None:
        st.error(t("en", "no_pack"), icon=":material/error:")
        return
    _init_state(pack)
    logo = _logo()
    if logo.is_file():
        st.logo(str(logo))
    lang = st.session_state[_LANG_KEY]
    track = st.session_state.get(_TRACK_KEY)
    source = st.session_state.get(_DOC_KEY)
    source = source if isinstance(source, str) else None
    _render_page(pack, lang, track, source)
    render_window(lang, source=source, track=track)


if __name__ == "__main__":
    early = load_pack()
    st.set_page_config(
        page_title=early.display_name if early else "Training",
        page_icon=":material/school:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    main()
