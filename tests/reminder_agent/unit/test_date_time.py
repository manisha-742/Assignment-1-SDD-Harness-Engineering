from datetime import date, datetime, time

import pytest

from reminder_agent.context import RuntimeContext
from reminder_agent.date_time import (
    AmbiguousDateError,
    AmbiguousTimeError,
    InvalidScheduleError,
    is_elapsed,
    resolve_date,
    resolve_time,
    snooze_schedule,
)


@pytest.fixture
def context() -> RuntimeContext:
    return RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today", date(2026, 11, 15)),
        ("tomorrow", date(2026, 11, 16)),
        ("tonight", date(2026, 11, 15)),
        ("2026-12-01", date(2026, 12, 1)),
        ("December 1, 2026", date(2026, 12, 1)),
        ("04/05/2027", date(2027, 4, 5)),
        ("Friday", date(2026, 11, 20)),
    ],
)
def test_resolves_dates_against_fixed_context(
    text: str, expected: date, context: RuntimeContext
) -> None:
    assert resolve_date(text, context) == expected


def test_ambiguous_numeric_date_without_locale_requires_clarification(
    context: RuntimeContext,
) -> None:
    no_locale = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", None)

    with pytest.raises(AmbiguousDateError):
        resolve_date("04/05/2027", no_locale)


@pytest.mark.parametrize("text", ["February 30, 2027", "2026-02-30", "13/32/2027"])
def test_invalid_dates_are_not_normalized(text: str, context: RuntimeContext) -> None:
    with pytest.raises(InvalidScheduleError):
        resolve_date(text, context)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("8 PM", time(20, 0)),
        ("12 AM", time(0, 0)),
        ("12 PM", time(12, 0)),
        ("20:30", time(20, 30)),
        ("00:05", time(0, 5)),
        ("noon", time(12, 0)),
        ("midnight", time(0, 0)),
        ("23:59", time(23, 59)),
    ],
)
def test_resolves_supported_times(text: str, expected: time) -> None:
    assert resolve_time(text) == expected


def test_tonight_does_not_invent_a_time() -> None:
    assert resolve_time("tonight") is None


def test_bare_hour_requires_clarification() -> None:
    with pytest.raises(AmbiguousTimeError):
        resolve_time("at 8")


@pytest.mark.parametrize("text", ["24:00", "12:60", "13 PM"])
def test_invalid_times_are_not_normalized(text: str) -> None:
    with pytest.raises(InvalidScheduleError):
        resolve_time(text)


def test_elapsed_schedule_requires_confirmation(context: RuntimeContext) -> None:
    assert is_elapsed(date(2026, 11, 15), time(8, 0), context)
    assert not is_elapsed(date(2026, 11, 15), time(18, 0), context)


def test_snooze_schedule_adds_duration_to_reference_instant(
    context: RuntimeContext,
) -> None:
    assert snooze_schedule(10, context) == datetime(
        2026, 11, 15, 9, 10, tzinfo=context.reference_instant.tzinfo
    )


def test_snooze_schedule_adds_elapsed_time_across_daylight_saving_transition() -> None:
    context = RuntimeContext.fixed(
        "2026-03-08T09:55:00Z", "America/Los_Angeles", "en-US"
    )

    result = snooze_schedule(10, context)

    assert result.isoformat() == "2026-03-08T03:05:00-07:00"


@pytest.mark.parametrize("duration", [0, -1, True])
def test_invalid_snooze_duration_is_rejected(
    duration: int, context: RuntimeContext
) -> None:
    with pytest.raises(InvalidScheduleError):
        snooze_schedule(duration, context)


def test_unrepresentable_snooze_schedule_is_rejected(context: RuntimeContext) -> None:
    with pytest.raises(InvalidScheduleError, match="calendar range"):
        snooze_schedule(10**20, context)
