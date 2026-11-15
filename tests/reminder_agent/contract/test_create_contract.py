from reminder_agent.context import RuntimeContext
from reminder_agent.interpreter import interpret_request


def test_complete_create_request_returns_structured_output(
    stub_client_factory,
) -> None:
    expected = {
        "intent": "create_reminder",
        "task": "submit my assignment",
        "date": "2026-11-16",
        "time": "20:00",
        "needs_clarification": False,
        "clarification_question": None,
        "target_reminder": None,
        "snooze_duration_minutes": None,
    }

    result = interpret_request(
        "Remind me to submit my assignment tomorrow at 8 PM.",
        RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US"),
        client=stub_client_factory(expected),
    )

    assert result.to_dict() == expected
