from playwright.sync_api import expect
from test_workflow import description, login, save_draft, step


def test_chat_refinement_review_save_and_restart(page, workflow, serve):
    origin, _, _, factory = workflow
    login(page, origin)
    save_draft(page)
    step(page, "03 Clarify")
    page.get_by_role(
        "button", name="Request clarification & suggestions", exact=True
    ).click()
    step(page, "04 Review & save")
    page.get_by_role("button", name="Apply reviewed suggestions & save").click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    before = page.request.get(origin + "/api/job-definition").json()
    page.get_by_role("button", name="Chat with assistant", exact=True).click()
    page.get_by_label("Your message", exact=True).fill(
        "Change hybrid to at most 1 day per week."
    )
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Chat reply saved")
    assert (
        page.request.get(origin + "/api/job-definition").json()["preferences"]
        == before["preferences"]
    )
    page.get_by_role("button", name="Review chat suggestions", exact=True).click()
    expect(
        page.get_by_role(
            "heading", name="Bring the role you’re looking for into focus."
        )
    ).to_be_visible()
    page.get_by_role("button", name="Apply reviewed suggestions & save").click()
    expect(page.get_by_role("status")).to_contain_text("Definition saved")
    saved = page.request.get(origin + "/api/job-definition").json()
    assert saved["id"] == before["id"]
    assert next(p for p in saved["preferences"] if p["key"] == "onsite_limit")[
        "value"
    ] == {"days": 1, "period": "week"}
    with serve(factory) as (restarted, _):
        page.goto(restarted)
        expect(description(page)).to_have_value(before["description"])
        page.get_by_role("button", name="Chat with assistant", exact=True).click()
        expect(page.get_by_label("Saved conversation")).to_contain_text(
            "Change hybrid to at most 1 day per week."
        )
        expect(
            page.get_by_text(
                "The saved context has changed. "
                "Send a new message for current suggestions."
            )
        ).to_be_visible()
        assert (
            page.request.get(restarted + "/api/job-definition").json()["preferences"]
            == saved["preferences"]
        )


def test_chat_failure_language_switch_unrelated_and_delete_source(page, workflow):
    origin, _, ai, _ = workflow
    login(page, origin)
    save_draft(page)
    step(page, "02 Background")
    page.get_by_label("Source type").select_option("text")
    page.get_by_label("Source name").fill("Synthetic source")
    page.get_by_label("Background text").fill("Historical software work")
    page.get_by_role("button", name="Add source", exact=True).click()
    page.get_by_role("button", name="Chat with assistant", exact=True).click()
    message = "What can I change about hybrid work?"
    page.get_by_label("Your message", exact=True).fill(message)
    ai.failure = True
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_role("main").get_by_role("alert")).to_contain_text("unavailable")
    expect(page.get_by_label("Your message", exact=True)).to_have_value(message)
    page.locator(".locale-switcher select").select_option("es")
    expect(page.get_by_label("Tu mensaje", exact=True)).to_have_value(message)
    page.locator(".locale-switcher select").select_option("en")
    ai.failure = False
    page.get_by_label("Your message", exact=True).fill("Prepare an interview")
    before = page.request.get(origin + "/api/job-definition").json()
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Chat reply saved")
    assert page.request.get(origin + "/api/job-definition").json() == before
    expect(
        page.get_by_role("button", name="Review chat suggestions", exact=True)
    ).to_have_count(0)
    page.get_by_role("button", name="Minimize assistant", exact=True).click()
    step(page, "02 Background")
    page.get_by_role("button", name="Remove Synthetic source", exact=True).click()
    expect(
        page.get_by_text("Removing this source deletes", exact=False)
    ).to_contain_text("conversation")
    page.get_by_role("button", name="Confirm remove source", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Source removed")
    page.get_by_role("button", name="Chat with assistant", exact=True).click()
    expect(page.get_by_label("Saved conversation")).not_to_contain_text(
        "Prepare an interview"
    )
    assert page.request.get(origin + "/api/job-definition/chat").json()["turns"] == []


def test_first_message_starts_a_draft_and_chat_follows_the_workflow(page, workflow):
    origin, _, _, _ = workflow
    login(page, origin)
    endpoint = origin + "/api/job-definition"
    assert page.request.get(endpoint).status == 404
    page.get_by_role("button", name="Chat with assistant", exact=True).click()
    message = "Staff architecture role, remote preferred in Spain."
    page.get_by_label("Your message", exact=True).fill(message)
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Chat reply saved")
    expect(description(page)).to_have_value(message)
    saved = page.request.get(endpoint).json()
    assert saved["description"] == message and saved["preferences"] == []
    assert len(page.request.get(endpoint + "/chat").json()["turns"]) == 1
    page.get_by_role("button", name="Minimize assistant", exact=True).click()
    for current_step in ("02 Background", "05 Summary"):
        step(page, current_step)
        page.get_by_role("button", name="Chat with assistant", exact=True).click()
        expect(page.get_by_label("Saved conversation")).to_contain_text(message)
        page.get_by_role("button", name="Minimize assistant", exact=True).click()
    page.reload()
    page.get_by_role("button", name="Chat with assistant", exact=True).click()
    expect(page.get_by_label("Saved conversation")).to_contain_text(message)
