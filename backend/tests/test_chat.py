"""Chat-specific domain limit: merged proposals must remain saveable."""

import pytest

from career_assistant.ai import AIError, AIResult, Usage
from career_assistant.workflow import ChatProposal, discuss


def test_chat_cannot_return_more_criteria_than_the_shared_editor_can_save():
    accepted = [
        dict(
            key=f"criterion_{i}",
            category="role",
            value="Existing criterion",
            priority="preferred",
            note=None,
        )
        for i in range(100)
    ]

    class AI:
        def complete(self, **kwargs):
            return AIResult(
                ChatProposal(
                    reply="Consider adding this criterion.",
                    in_scope=True,
                    preferences=[
                        dict(
                            key="extra",
                            category="role",
                            value="New criterion",
                            priority="preferred",
                            note=None,
                        )
                    ],
                    questions=[],
                    conflicts=[],
                ),
                "fixture",
                Usage(0, 0, 0, 0),
                0,
            )

    with pytest.raises(AIError) as failure:
        discuss(
            AI(),
            {"description": "Existing role", "accepted_preferences": accepted},
            "Add a new criterion",
            "English",
        )
    assert failure.value.code == "ai_invalid_response"
    assert len(accepted) == 100
