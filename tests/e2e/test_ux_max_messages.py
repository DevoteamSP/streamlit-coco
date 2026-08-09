"""E2E: max_messages truncation + Load earlier."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


def test_load_earlier_reveals_messages(harness_page) -> None:
    page = harness_page
    page.get_by_text("earlier message", exact=False).first.wait_for(timeout=15_000)

    # Newest window should not show the oldest seeded user line until load.
    oldest = page.get_by_text("Earlier user message 0", exact=True)
    assert oldest.count() == 0

    page.get_by_role("button", name="Load earlier").click()
    # After one load step, older items enter the window (still may not reach 0).
    page.get_by_text("Earlier user message", exact=False).first.wait_for(timeout=10_000)

    # Load until the oldest appears (harness seeds 8 pairs + extras).
    for _ in range(6):
        if oldest.count() > 0:
            break
        btn = page.get_by_role("button", name="Load earlier")
        if btn.count() == 0:
            break
        btn.click()
        page.wait_for_timeout(300)

    assert oldest.count() >= 1
