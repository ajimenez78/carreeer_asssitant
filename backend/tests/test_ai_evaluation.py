import json

import pytest

from career_assistant.ai import AIError, AIResult, Usage
from career_assistant.ai_cli import main
from career_assistant.ai_evaluation import (
    Arithmetic,
    Background,
    Fact,
    Salary,
    SuggestedPreference,
    Suggestions,
    cases,
    check_case,
    evaluate_case,
)


def unknown_salary():
    return Salary(minimum=None, maximum=None, currency=None, period=None, basis=None)


def proposal(case):
    if case.name == "reviewable_refinement":
        preferences = [
            SuggestedPreference(
                **{
                    **item,
                    "priority": "mandatory"
                    if item["key"] == "ai_engineering"
                    else item["priority"],
                }
            )
            for item in case.data["accepted"]["preferences"]
        ]
        questions = []
    elif case.name == "reference_preferences":
        preferences = [
            SuggestedPreference(key=key, priority=priority, value=value)
            for key, priority, value in [
                ("seniority", "mandatory", "Staff"),
                ("architecture", "mandatory", "Architecture"),
                ("cross_team", "mandatory", "Cross-team collaboration"),
                ("learning", "preferred", "Continuous learning"),
                ("international_scope", "preferred", "International scope"),
                ("ai_engineering", "preferred", "AI engineering"),
                ("remote", "preferred", "Remote"),
                ("hybrid_location", "mandatory", "Madrid"),
                ("onsite_days", "mandatory", "2"),
                ("frontend_only", "excluded", "Frontend-only roles"),
            ]
        ]
        questions = ["What salary range and currency?", "Which period for office days?"]
    else:
        preferences = []
        questions = ["What role?", "What salary and work arrangement?"]
    return Suggestions(
        preferences=preferences,
        salary=unknown_salary(),
        onsite_period=None,
        questions=questions,
    )


def successful_value(case):
    if case.response_type is Background:
        source = case.data["sources"][0]
        quote = source["text"].split(".")[0]
        return Background(
            facts=[Fact(source_id=source["id"], content=quote, evidence=quote)],
            unknowns=["Education"],
        )
    return proposal(case)


class FakeAIClient:
    def __init__(self, value):
        self.value = value
        self.closed = False
        self.requests = []

    def complete(self, **request):
        self.requests.append(request)
        return AIResult(self.value, "gpt-6-luna", Usage(100, 0, 20, 5), 0.01)

    def close(self):
        self.closed = True


@pytest.mark.parametrize("case", cases(), ids=lambda case: case.name)
def test_quality_checks_can_run_with_a_fake_client(case):
    client = FakeAIClient(successful_value(case))
    result, checks = evaluate_case(client, case)
    assert result.value == client.value
    assert all(checks.values()), checks
    assert client.requests[0]["data"] == case.data


def test_grounding_checks_catch_invented_background_and_invalid_provenance():
    case = cases()[0]
    value = Background(
        facts=[
            Fact(
                source_id="not-a-provided-source",
                content="PhD from Invented University",
                evidence="invented quote",
            )
        ],
        unknowns=[],
    )
    checks = check_case(case, value)
    assert not checks["valid_provenance"]
    assert not checks["no_invented_education"]
    assert not checks["education_unknown"]
    assert not checks["employment_preserved"]


def test_quality_checks_catch_invented_salary_and_unrequested_updates():
    case = cases()[-1]
    value = proposal(case)
    value.salary.minimum = 100000.0
    value.onsite_period = "week"
    value.preferences[0].value = "Junior"
    checks = check_case(case, value)
    assert not checks["unknown_salary_preserved"]
    assert not checks["unknown_office_period_preserved"]
    assert not checks["only_requested_change"]


def test_reference_checks_reject_softening_conditional_hybrid_constraints():
    case = cases()[3]
    value = proposal(case)
    for preference in value.preferences:
        if preference.key in {"hybrid_location", "onsite_days"}:
            preference.priority = "preferred"
    checks = check_case(case, value)
    assert not checks["madrid_hybrid_constraint"]
    assert not checks["two_day_limit"]


def test_live_cli_writes_only_sanitized_results_with_a_fake_client(
    monkeypatch, tmp_path, capsys
):
    client = FakeAIClient(Arithmetic(answer=4))
    monkeypatch.setattr("career_assistant.ai_cli.OpenAIClient", lambda settings: client)
    report_path = tmp_path / "sanitized.json"
    main(["smoke", "--report", str(report_path)])
    report = json.loads(report_path.read_text())
    assert report["results"][0]["checks"] == {"answer_is_4": True}
    assert report["results"][0]["usage"]["reasoning_tokens"] == 5
    assert "instructions" not in report["results"][0]
    assert "OPENAI_API_KEY" not in capsys.readouterr().out
    assert client.closed


def test_cli_reports_failed_quality_check_and_closes_client(monkeypatch, capsys):
    client = FakeAIClient(Arithmetic(answer=5))
    monkeypatch.setattr("career_assistant.ai_cli.OpenAIClient", lambda settings: client)
    with pytest.raises(SystemExit):
        main(["smoke"])
    assert not json.loads(capsys.readouterr().out)["results"][0]["passed"]
    assert client.closed


def test_evaluation_command_runs_the_whole_synthetic_corpus_without_network(
    monkeypatch, capsys
):
    class CorpusAI(FakeAIClient):
        def complete(self, **request):
            case = next(case for case in cases() if case.data == request["data"])
            return AIResult(
                successful_value(case), "gpt-6-luna", Usage(100, 0, 20, 5), 0.01
            )

    client = CorpusAI(None)
    monkeypatch.setattr("career_assistant.ai_cli.OpenAIClient", lambda settings: client)
    main(["evaluate"])
    report = json.loads(capsys.readouterr().out)
    assert [record["case"] for record in report["results"]] == [
        case.name for case in cases()
    ]
    assert all(record["passed"] for record in report["results"])
    assert client.closed


def test_cli_keeps_usage_when_a_paid_response_is_rejected(monkeypatch, capsys):
    class IncompleteAI(FakeAIClient):
        def complete(self, **request):
            raise AIError(
                "ai_incomplete",
                "AI response incomplete.",
                502,
                Usage(100, 0, 2000, 1900),
            )

    client = IncompleteAI(None)
    monkeypatch.setattr("career_assistant.ai_cli.OpenAIClient", lambda settings: client)
    with pytest.raises(SystemExit):
        main(["evaluate"])
    report = json.loads(capsys.readouterr().out)
    assert report["error"]["code"] == "ai_incomplete"
    assert report["error"]["usage"]["output_tokens"] == 2000
    assert client.closed
