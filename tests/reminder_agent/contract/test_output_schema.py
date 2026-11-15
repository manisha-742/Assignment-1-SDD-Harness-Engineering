import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from reminder_agent.validation import InvalidReminderOutput, validate_output

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = (
    ROOT
    / "specs"
    / "002-natural-language-reminder-agent"
    / "contracts"
    / "reminder-output.schema.json"
)

CREATE = {
    "intent": "create_reminder",
    "task": "submit my assignment",
    "date": "2026-11-16",
    "time": "20:00",
    "needs_clarification": False,
    "clarification_question": None,
    "target_reminder": None,
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


def test_canonical_schema_has_all_required_output_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    assert set(schema["required"]) == set(CREATE)
    validator.validate(CREATE)


def test_valid_output_is_returned_as_typed_model() -> None:
    result = validate_output(CREATE)

    assert result.to_dict() == CREATE


@pytest.mark.parametrize(
    "field",
    [
        "intent",
        "task",
        "date",
        "time",
        "needs_clarification",
        "clarification_question",
        "target_reminder",
        "snooze_duration_minutes",
    ],
)
def test_every_output_field_is_required(field: str) -> None:
    output = dict(CREATE)
    del output[field]

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("intent", "delete_reminder"),
        ("task", 4),
        ("date", 20261116),
        ("time", "8 PM"),
        ("needs_clarification", "false"),
        ("clarification_question", 2),
        ("target_reminder", []),
        ("snooze_duration_minutes", True),
    ],
)
def test_invalid_intent_or_field_types_are_rejected(field: str, value: object) -> None:
    output = dict(CREATE)
    output[field] = value

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


@pytest.mark.parametrize("value", ["2026-02-30", "26-11-16", "2026-1-16"])
def test_invalid_calendar_dates_are_rejected(value: str) -> None:
    output = dict(CREATE, date=value)

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


@pytest.mark.parametrize("value", ["24:00", "9:00", "12:60", "noon"])
def test_invalid_24_hour_times_are_rejected(value: str) -> None:
    output = dict(CREATE, time=value)

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


def test_additional_properties_are_rejected() -> None:
    output = dict(CREATE, stored_reminder_id="not-supported")

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


def test_positive_snooze_duration_is_accepted() -> None:
    assert validate_output(SNOOZE).snooze_duration_minutes == 10


@pytest.mark.parametrize("duration", [0, -1])
def test_zero_and_negative_snooze_durations_are_rejected(duration: int) -> None:
    output = dict(SNOOZE, snooze_duration_minutes=duration)

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


def test_snooze_duration_null_is_valid_for_non_snooze_intent() -> None:
    assert validate_output(CREATE).snooze_duration_minutes is None


def test_snooze_duration_null_is_valid_only_when_unresolved_with_clarification() -> (
    None
):
    output = dict(
        SNOOZE,
        date=None,
        time=None,
        needs_clarification=True,
        clarification_question="How long should I snooze the reminder?",
        snooze_duration_minutes=None,
    )

    assert validate_output(output).snooze_duration_minutes is None


def test_fully_resolved_snooze_requires_target_and_duration() -> None:
    output = dict(SNOOZE, snooze_duration_minutes=None)

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)


def test_create_clarification_requires_a_focused_question() -> None:
    output = dict(
        CREATE,
        time=None,
        needs_clarification=True,
        clarification_question=None,
    )

    with pytest.raises(InvalidReminderOutput):
        validate_output(output)
