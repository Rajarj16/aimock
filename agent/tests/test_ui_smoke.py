"""OPTIONAL. Proves search box -> results -> page number wiring. NOT an AI-quality test.
Adjust the data-testid / locators to the real Smartrecord UI."""
import pytest
pytest.importorskip("pytest_playwright")

@pytest.mark.ui
def test_search_shows_results_with_page_numbers(page, base_url):
    page.goto(base_url)
    page.get_by_test_id("search-box").fill("Dolo")
    page.get_by_test_id("search-btn").click()
    first = page.get_by_test_id("result").first
    first.wait_for()
    assert "page" in first.inner_text().lower()
