"""The production static export and authenticated API share one origin."""

from playwright.sync_api import expect


def test_static_export_and_private_api(page, workflow):
    origin, _, _, _ = workflow
    response = page.goto(origin)
    assert response.status == 200
    expect(
        page.get_by_role("heading", name="Sign in to your workspace.")
    ).to_be_visible()
    response = page.request.get(origin + "/api/job-definition")
    assert response.status == 401
    assert response.headers["cache-control"] == "no-store"
    assert page.request.get(origin + "/api/missing").status == 404
    assert page.request.get(origin + "/.env").status == 404
