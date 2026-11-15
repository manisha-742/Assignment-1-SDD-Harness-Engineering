import pytest

from reminder_agent.clarification import build_clarification_guidance
from reminder_agent.validation import InvalidReminderOutput, validate_output


def _create_output(**changes: object) -> dict[str, object]:
    output: dict[str, object] = {
        "intent": "create_reminder",
        "task": "call Mom",
        "date": None,
        "time": None,
        "needs_clarification": True,
        "clarification_question": "What date and time should I use?",
        "target_reminder": None,
        "snooze_duration_minutes": None,
    }
    output.update(changes)
    return output


def test_missing_schedule_is_represented_as_null_with_a_focused_question() -> None:
    result = validate_output(_create_output())

    assert result.task == "call Mom"
    assert result.date is None
    assert result.time is None
    assert result.needs_clarification
    assert result.clarification_question == "What date and time should I use?"


def test_missing_task_is_not_replaced_with_an_invented_action() -> None:
    result = validate_output(
        _create_output(
            task=None,
            date="2026-11-16",
            time="20:00",
            clarification_question="What should I remind you to do?",
        )
    )

    assert result.task is None
    assert result.date == "2026-11-16"
    assert result.time == "20:00"


def test_unresolved_ambiguous_time_remains_null() -> None:
    result = validate_output(
        _create_output(
            date="2026-11-16",
            clarification_question="Did you mean 8 AM or 8 PM?",
        )
    )

    assert result.time is None
    assert result.needs_clarification


def test_clarification_question_is_required_when_flag_is_true() -> None:
    with pytest.raises(InvalidReminderOutput):
        validate_output(_create_output(clarification_question=None))


def test_clarification_question_must_be_null_when_flag_is_false() -> None:
    output = _create_output(
        date="2026-11-16",
        time="20:00",
        needs_clarification=False,
    )

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


def test_guidance_forbids_guessing_and_requires_focused_questions() -> None:
    guidance = build_clarification_guidance().casefold()

    assert "do not invent" in guidance
    assert "missing or ambiguous" in guidance
    assert "focused question" in guidance
    assert "null" in guidance
