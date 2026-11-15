import json
from types import SimpleNamespace

from reminder_agent.context import RuntimeContext
from reminder_agent.intent_rules import (
    extract_create_task,
    extract_target_and_task,
    has_specific_reminder_target,
    parse_snooze_duration_minutes,
)
from reminder_agent.interpreter import interpret_request


def _client(intent: str, *, task: str | None = "call Mom") -> SimpleNamespace:
    output = {
        "intent": intent,
        "task": task,
        "date": "2026-11-19",
        "time": "14:30",
        "needs_clarification": False,
        "clarification_question": None,
        "target_reminder": "model supplied target",
        "snooze_duration_minutes": 10 if intent == "snooze_reminder" else None,
    }

    def create(**request: object) -> SimpleNamespace:
        return SimpleNamespace(output_text=json.dumps(output), status="completed")

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def test_target_extraction_keeps_task_and_target_separate() -> None:
    target, task = extract_target_and_task(
        "Reschedule my dentist appointment reminder to 2026-11-19 at 14:30."
    )

    assert target == "dentist appointment reminder"
    assert task == "dentist appointment"
    assert has_specific_reminder_target(
        "Reschedule my dentist appointment reminder to Friday."
    )


def test_create_task_extraction_preserves_action_across_schedule_word_orders() -> None:
    assert (
        extract_create_task("Remind me at 14:00 to leave for the airport.")
        == "leave for the airport"
    )
    assert (
        extract_create_task("Remind me tomorrow at 8 PM to submit my assignment.")
        == "submit my assignment"
    )


def test_pronominal_target_is_not_treated_as_identified() -> None:
    assert not has_specific_reminder_target("Reschedule it to Friday at 2 PM.")
    assert extract_target_and_task("Reschedule it to Friday at 2 PM.") == (None, None)


def test_snooze_duration_requires_positive_explicit_whole_minutes() -> None:
    assert parse_snooze_duration_minutes("Snooze it for 10 minutes.") == 10
    assert parse_snooze_duration_minutes("Snooze it for 2 hours and 5 minutes.") == 125
    assert parse_snooze_duration_minutes("Snooze it for 0 minutes.") is None
    assert parse_snooze_duration_minutes("Snooze it for -10 minutes.") is None
    assert parse_snooze_duration_minutes("Snooze it for a while.") is None


def test_reschedule_uses_user_target_and_complete_explicit_schedule(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    context = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")

    result = interpret_request(
        "Reschedule my dentist appointment reminder to 2026-11-19 at 14:30.",
        context,
        client=_client("reschedule_reminder", task="model invented task"),
    )

    assert result.task == "dentist appointment"
    assert result.target_reminder == "dentist appointment reminder"
    assert (result.date, result.time) == ("2026-11-19", "14:30")
    assert not result.needs_clarification


def test_unknown_reschedule_target_is_clarified_without_fabrication(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    context = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")

    result = interpret_request(
        "Reschedule it to Friday at 2 PM.",
        context,
        client=_client("reschedule_reminder"),
    )

    assert result.task is None
    assert result.target_reminder is None
    assert result.needs_clarification
    assert "which reminder" in result.clarification_question.casefold()


def test_snooze_schedule_is_derived_from_fixed_reference_instant(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    context = RuntimeContext.fixed("2026-11-30T23:55:00Z", "UTC", "en-US")

    result = interpret_request(
        "Snooze my call Mom reminder for 10 minutes.",
        context,
        client=_client("snooze_reminder"),
    )

    assert result.task == "call Mom"
    assert result.target_reminder == "call Mom reminder"
    assert result.snooze_duration_minutes == 10
    assert (result.date, result.time) == ("2026-12-01", "00:05")
    assert not result.needs_clarification


def test_missing_snooze_duration_is_null_and_clarified(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    context = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")

    result = interpret_request(
        "Snooze my call Mom reminder.",
        context,
        client=_client("snooze_reminder"),
    )

    assert result.snooze_duration_minutes is None
    assert result.date is None and result.time is None
    assert result.needs_clarification
    assert "how many minutes" in result.clarification_question.casefold()


def test_unrepresentable_snooze_schedule_requests_a_correctable_duration(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    context = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")

    result = interpret_request(
        "Snooze my call Mom reminder for 100000000000000000000 minutes.",
        context,
        client=_client("snooze_reminder"),
    )

    assert result.needs_clarification
    assert result.date is None and result.time is None
    assert "shorter duration" in result.clarification_question
