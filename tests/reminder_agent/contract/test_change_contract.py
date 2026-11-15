import pytest

from reminder_agent.validation import InvalidReminderOutput, validate_output

RESCHEDULE = {
    "intent": "reschedule_reminder",
    "task": "dentist appointment",
    "date": "2026-11-19",
    "time": "14:30",
    "needs_clarification": False,
    "clarification_question": None,
    "target_reminder": "dentist appointment reminder",
    "snooze_duration_minutes": None,
}

SNOOZE = {
    "intent": "snooze_reminder",
    "task": "call Mom",
    "date": "2026-11-15",
    "time": "09:10",
    "needs_clarification": False,
    "clarification_question": None,
    "target_reminder": "call Mom reminder",
    "snooze_duration_minutes": 10,
}


def test_reschedule_keeps_task_and_target_separate() -> None:
    result = validate_output(RESCHEDULE)

    assert result.task == "dentist appointment"
    assert result.target_reminder == "dentist appointment reminder"


def test_reschedule_without_target_requires_clarification() -> None:
    result = validate_output(
        dict(
            RESCHEDULE,
            date="2026-11-20",
            time="14:00",
            target_reminder=None,
            needs_clarification=True,
            clarification_question="Which reminder should I reschedule?",
        )
    )

    assert result.target_reminder is None
    assert result.needs_clarification


def test_snooze_requires_target_positive_duration_and_resulting_schedule() -> None:
    result = validate_output(SNOOZE)

    assert result.target_reminder == "call Mom reminder"
    assert result.snooze_duration_minutes == 10
    assert result.date == "2026-11-15"
    assert result.time == "09:10"


def test_snooze_without_duration_requires_clarification() -> None:
    result = validate_output(
        dict(
            SNOOZE,
            date=None,
            time=None,
            needs_clarification=True,
            clarification_question="How long should I snooze the reminder?",
            snooze_duration_minutes=None,
        )
    )

    assert result.snooze_duration_minutes is None
    assert result.needs_clarification


def test_snooze_duration_is_positive_integer_only() -> None:
    with pytest.raises(InvalidReminderOutput):
        validate_output(dict(SNOOZE, snooze_duration_minutes=0))
