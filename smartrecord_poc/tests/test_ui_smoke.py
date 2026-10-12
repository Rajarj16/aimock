"""OPTIONAL - one Playwright smoke test. AI quality is NOT tested here; this only proves
the search box -> results list -> page number wiring works end to end.
Run: pip install pytest-playwright && playwright install chromium && pytest tests/test_ui_smoke.py"""
import pytest
pw = pytest.importorskip("playwright.sync_api")

def test_search_box_shows_page_numbers(page, base_url):
    page.goto(base_url)
    page.get_by_test_id("search-box").fill("Dolo")
    page.get_by_test_id("search-btn").click()
    first = page.get_by_test_id("result").first
    first.wait_for()
    assert "page 3" in first.inner_text()
