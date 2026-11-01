import pytest
from pydantic import ValidationError

from career_assistant.persistence import DefinitionData, PreferenceData


def test_drafts_allow_unknowns_and_separate_priorities():
    data = DefinitionData(
        description="  Quiero un puesto de arquitectura.  ",
        preferences=[
            PreferenceData(key="salary", category="compensation"),
            PreferenceData(
                key="onsite_limit",
                category="work_arrangement",
                priority="mandatory",
                value={"days": 2, "period": None},
            ),
        ],
    )
    assert data.description == "Quiero un puesto de arquitectura."
    assert data.state == "draft"
    assert data.preferences[0].value is None
    assert data.preferences[1].value == {"days": 2, "period": None}


@pytest.mark.parametrize("description", ["", " \n\t "])
def test_empty_description_is_not_a_saved_draft(description):
    with pytest.raises(ValidationError):
        DefinitionData(description=description)


def test_duplicate_criteria_and_invalid_priorities_are_rejected():
    preference = PreferenceData(key="role", category="role", value="Staff engineer")
    with pytest.raises(ValidationError, match="unique"):
        DefinitionData(description="Architecture", preferences=[preference, preference])
    with pytest.raises(ValidationError):
        PreferenceData(key="role", category="role", priority="required")
