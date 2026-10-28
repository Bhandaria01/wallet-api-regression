import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def api():
    """Playwright's API client, pointed at our running Wallet API."""
    with sync_playwright() as p:
        context = p.request.new_context(base_url="http://127.0.0.1:8000")
        yield context
        context.dispose()