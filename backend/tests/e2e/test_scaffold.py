from playwright.sync_api import Page, expect


def test_example_page_calls_real_api(page: Page, live_server: str):
    page.goto(live_server)

    expect(page.get_by_role("heading", name="Hello, world!")).to_be_visible()
    expect(page.locator("#api-status")).to_have_text("API status: ok")
    expect(page.get_by_role("button", name="Check API")).to_be_enabled()


def test_failed_api_call_can_be_retried(page: Page, live_server: str):
    page.route("**/api/health", lambda route: route.fulfill(status=503))
    page.goto(live_server)
    expect(page.locator("#api-status")).to_have_text(
        "Could not reach the API. Try again."
    )

    page.unroute("**/api/health")
    page.get_by_role("button", name="Check API").click()

    expect(page.locator("#api-status")).to_have_text("API status: ok")
