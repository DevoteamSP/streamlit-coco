"""E2E: rich markdown highlighting + copy button."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


def test_sql_fence_highlighted_and_copy(harness_page) -> None:
    page = harness_page
    page.get_by_text("SELECT customer_id", exact=False).first.wait_for(timeout=15_000)

    # Streamlit st.code renders a <code> / pre block with the SQL body.
    sql_code = page.locator("code").filter(has_text="SELECT customer_id")
    assert sql_code.count() >= 1

    # CCv2 copy control — icon-only; message aria-label is "Copy SQL".
    copy_btn = page.locator(".coco-copy-btn[aria-label='Copy SQL']").first
    copy_btn.scroll_into_view_if_needed()
    copy_btn.click()
    page.locator(".coco-copy-btn[aria-label='Copy SQL'] .coco-copy-icon").filter(
        has_text="check"
    ).first.wait_for(timeout=5_000)

    clipboard = page.evaluate("navigator.clipboard.readText()")
    assert "SELECT customer_id" in clipboard
    assert "```sql" in clipboard or "FROM orders" in clipboard
