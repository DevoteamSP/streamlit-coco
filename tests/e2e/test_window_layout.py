"""E2E: the window's place: floating, attached to the left or the right edge, or the whole page."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e

WAIT = 20_000
BOX = (
    "(cc) => { const r = cc.getBoundingClientRect(); "
    "return { x: r.x, y: r.y, w: r.width, h: r.height, vw: innerWidth, vh: innerHeight }; }"
)


def _box(page) -> dict:
    return page.locator("section.cc").evaluate(BOX)  # the window is in a shadow root


def test_attach_left_right_and_full_page(window, ask) -> None:
    page = window
    ask.connect()
    floating = _box(page)
    assert floating["h"] < floating["vh"]

    page.get_by_role("button", name="Attach to the right").click(timeout=WAIT)
    box = _box(page)
    assert box["y"] == 0 and box["h"] == box["vh"] and box["x"] + box["w"] == box["vw"]
    # the pressed icon is now called "Floating window"
    assert page.get_by_role("button", name="Attach to the right").count() == 0
    pressed = page.get_by_role("button", name="Floating window")
    assert pressed.get_attribute("aria-pressed") == "true"

    page.get_by_role("button", name="Attach to the left").click(timeout=WAIT)
    box = _box(page)
    assert box["x"] == 0 and box["y"] == 0 and box["h"] == box["vh"]

    page.get_by_role("button", name="Full page").click(timeout=WAIT)
    box = _box(page)
    assert box["w"] > box["vw"] * 0.9 and box["h"] > box["vh"] * 0.9

    page.get_by_role("button", name="Floating window").click(timeout=WAIT)  # back
    assert _box(page) == floating


def test_the_place_survives_a_conversation(window, ask) -> None:
    page = window
    ask.connect()
    page.get_by_role("button", name="Attach to the left").click(timeout=WAIT)
    ask.say("hello")
    page.get_by_text("You wrote: hello").wait_for(timeout=WAIT)
    assert _box(page)["x"] == 0


def test_the_places_can_be_switched_off(page, base_url: str) -> None:
    for mode, gone, kept in (
        ("fixed", ("Attach to the left", "Attach to the right", "Full page"), ()),
        ("dock_only", ("Full page",), ("Attach to the left", "Attach to the right")),
    ):
        page.goto(f"{base_url}/?mode={mode}", wait_until="domcontentloaded")
        page.get_by_role("button", name="Ask CoCo").first.click(timeout=30_000)
        page.get_by_role("button", name="Minimise CoCo").wait_for(timeout=WAIT)
        for name in gone:
            assert page.get_by_role("button", name=name).count() == 0, (mode, name)
        for name in kept:
            assert page.get_by_role("button", name=name).count() == 1, (mode, name)


def test_a_click_on_the_title_bar_minimises(window, ask) -> None:
    page = window
    ask.connect()
    page.get_by_role("button", name="Attach to the right").click(timeout=WAIT)  # a button is not it
    assert page.locator("section.cc").is_visible()
    page.locator("section.cc h2").click(timeout=WAIT)
    page.locator("section.cc").wait_for(state="hidden", timeout=WAIT)
    page.get_by_role("button", name="Ask CoCo").first.click(timeout=WAIT)
    assert page.locator("section.cc").is_visible()


def test_the_page_is_told_the_place_and_takes_the_rest_of_the_screen(page, base_url: str) -> None:
    page.goto(f"{base_url}/?mode=split", wait_until="domcontentloaded")
    page.get_by_text("Window place: closed").wait_for(timeout=30_000)
    page.get_by_role("button", name="Ask CoCo").first.click(timeout=WAIT)
    page.get_by_text("Window place: float").wait_for(timeout=WAIT)

    app = page.locator('[data-testid="stApp"]')
    page.get_by_role("button", name="Attach to the right").click(timeout=WAIT)
    page.get_by_text("Window place: right").wait_for(timeout=WAIT)
    dock = _box(page)["w"]
    assert app.evaluate("(a) => innerWidth - a.getBoundingClientRect().right") == dock

    page.get_by_role("button", name="Attach to the left").click(timeout=WAIT)
    page.get_by_text("Window place: left").wait_for(timeout=WAIT)
    assert app.evaluate("(a) => a.getBoundingClientRect().left") == dock

    page.get_by_role("button", name="Full page").click(timeout=WAIT)
    page.get_by_text("Window place: full").wait_for(timeout=WAIT)
    assert app.evaluate("(a) => a.getBoundingClientRect().left") == 0  # nothing to share

    page.get_by_role("button", name="Minimise CoCo").click(timeout=WAIT)
    page.get_by_text("Window place: closed").wait_for(timeout=WAIT)


def test_a_header_icon_hints_after_750_ms(window, ask) -> None:
    page = window
    ask.connect()
    icon = page.get_by_role("button", name="Full page")
    shown = "(b) => getComputedStyle(b, '::after').visibility"
    icon.hover()
    assert icon.evaluate(shown) == "hidden"  # not at once
    page.wait_for_function(
        "() => [...document.querySelectorAll('*')].some(e => e.shadowRoot && "
        "[...e.shadowRoot.querySelectorAll('[data-a=layout]')].some(b => "
        "getComputedStyle(b, '::after').visibility === 'visible'))",
        timeout=3_000,
    )
    assert icon.get_attribute("data-tip") == "Full page"


def test_the_title_bar_is_never_under_the_page_header(window, ask) -> None:
    page = window
    page.set_viewport_size({"width": 1024, "height": 320})  # short: the window reaches the header
    ask.connect()
    on_top = """() => {
        const host = [...document.querySelectorAll('*')].find(
            (e) => e.shadowRoot && e.shadowRoot.querySelector('.coco-root'));
        const hd = host.shadowRoot.querySelector('.hd').getBoundingClientRect();
        const hit = document.elementFromPoint(hd.x + 40, hd.y + hd.height / 2);
        return hit === host || host.contains(hit);
    }"""
    assert page.evaluate(on_top)
    for name in ("Attach to the right", "Attach to the left", "Full page"):
        page.get_by_role("button", name=name).click(timeout=WAIT)
        assert page.evaluate(on_top), name
        page.get_by_role("button", name="Floating window").click(timeout=WAIT)
