"""Schema and deterministic invariants for reminder interpretations."""

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from reminder_agent.model import ReminderIntent, ReminderOutput

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "002-natural-language-reminder-agent"
    / "contracts"
    / "reminder-output.schema.json"
)

OUTPUT_FIELDS = {
    "intent",
    "task",
    "date",
    "time",
    "needs_clarification",
    "clarification_question",
    "target_reminder",
    "snooze_duration_minutes",
}
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")


class InvalidReminderOutput(ValueError):
    """Raised when an interpretation violates its schema or invariants."""


@lru_cache(maxsize=1)
def load_output_schema() -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _validate_date(value: object) -> None:
    if value is None:
        return
    if not isinstance(value, str) or DATE_PATTERN.fullmatch(value) is None:
        raise InvalidReminderOutput("date must use YYYY-MM-DD or null")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise InvalidReminderOutput("date must be a real calendar date") from error


def _validate_time(value: object) -> None:
    if value is None:
        return
    if not isinstance(value, str) or TIME_PATTERN.fullmatch(value) is None:
        raise InvalidReminderOutput("time must use 24-hour HH:MM or null")


def _require_nonempty(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidReminderOutput(f"{field} must be a non-empty string")


def _validate_invariants(value: dict[str, Any]) -> None:
    intent = ReminderIntent(value["intent"])
    task = value["task"]
    target = value["target_reminder"]
    date_value = value["date"]
    time_value = value["time"]
    needs_clarification = value["needs_clarification"]
    question = value["clarification_question"]
    duration = value["snooze_duration_minutes"]

    if task is not None:
        _require_nonempty(task, "task")
    if target is not None:
        _require_nonempty(target, "target_reminder")
    _validate_date(date_value)
    _validate_time(time_value)

    if needs_clarification:
        if intent is ReminderIntent.UNSUPPORTED:
            raise InvalidReminderOutput(
                "unsupported intent cannot request clarification"
            )
        _require_nonempty(question, "clarification_question")
    elif question is not None:
        raise InvalidReminderOutput(
            "clarification_question must be null when clarification is not needed"
        )

    if intent is ReminderIntent.UNSUPPORTED:
        if (
            any(
                item is not None
                for item in (task, date_value, time_value, target, duration, question)
            )
            or needs_clarification
        ):
            raise InvalidReminderOutput("unsupported output contains reminder details")
        return

    if intent is ReminderIntent.CREATE:
        if target is not None or duration is not None:
            raise InvalidReminderOutput(
                "create output cannot include target or snooze duration"
            )
        if not needs_clarification and any(
            item is None for item in (task, date_value, time_value)
        ):
            raise InvalidReminderOutput(
                "resolved create output requires task, date, and time"
            )
        return

    if intent is ReminderIntent.RESCHEDULE:
        if duration is not None:
            raise InvalidReminderOutput(
                "reschedule output cannot include snooze duration"
            )
        if not needs_clarification and any(
            item is None for item in (task, target, date_value, time_value)
        ):
            raise InvalidReminderOutput(
                "resolved reschedule output requires task, target, date, and time"
            )
        return

    if not needs_clarification and any(
        item is None for item in (task, target, date_value, time_value, duration)
    ):
        raise InvalidReminderOutput(
            "resolved snooze output requires task, target, schedule, and duration"
        )


def validate_output_shape(value: object) -> ReminderOutput:
    """Validate the JSON schema and construct a typed model without cross-field
    invariant checks.
    """
    if not isinstance(value, dict) or set(value) != OUTPUT_FIELDS:
        raise InvalidReminderOutput("output must contain exactly the required fields")

    validator = Draft202012Validator(load_output_schema())
    try:
        validator.validate(value)
    except ValidationError as error:
        raise InvalidReminderOutput(
            "output does not match the reminder schema"
        ) from error

    return ReminderOutput(
        intent=ReminderIntent(value["intent"]),
        task=value["task"],
        date=value["date"],
        time=value["time"],
        needs_clarification=value["needs_clarification"],
        clarification_question=value["clarification_question"],
        target_reminder=value["target_reminder"],
        snooze_duration_minutes=value["snooze_duration_minutes"],
    )


def validate_output(value: object) -> ReminderOutput:
    """Validate schema, formats, nullability, and intent-specific cross-field rules."""
    output = validate_output_shape(value)
    _validate_invariants(value)
    return output
