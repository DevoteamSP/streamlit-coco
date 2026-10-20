"""E2E: cwd file upload via sidebar uploader."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def test_sidebar_upload_csv(harness_page, tmp_path: Path) -> None:
    page = harness_page
    sample = tmp_path / "e2e_sample.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")

    # Streamlit file_uploader exposes a hidden file input.
    page.set_input_files('section[data-testid="stSidebar"] input[type="file"]', str(sample))

    page.get_by_text("_uploads/e2e_sample.csv", exact=False).wait_for(timeout=15_000)
    assert page.get_by_text("Saved", exact=False).count() >= 1 or page.get_by_text(
        "e2e_sample.csv", exact=False
    ).count() >= 1
