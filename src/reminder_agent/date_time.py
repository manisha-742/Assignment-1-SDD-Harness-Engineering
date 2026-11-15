"""Context-aware parsing helpers for reminder dates and times."""

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from reminder_agent.context import RuntimeContext

ISO_DATE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
MONTH_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)
WEEKDAY = re.compile(
    r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.IGNORECASE,
)
TIME_12_HOUR = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\b", re.IGNORECASE)
TIME_24_HOUR = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
BARE_HOUR = re.compile(r"\bat\s+(\d{1,2})\b", re.IGNORECASE)

MONTH_NUMBERS = {
    name.casefold(): number
    for number, name in enumerate(
        (
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        )
    )
    if name
}
WEEKDAY_NUMBERS = {
    name.casefold(): number
    for number, name in enumerate(
        ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    )
}


class InvalidScheduleError(ValueError):
    """Raised when an explicit date or time is invalid or conflicting."""


class AmbiguousDateError(InvalidScheduleError):
    """Raised when a numeric date has no established order convention."""


class AmbiguousTimeError(InvalidScheduleError):
    """Raised when an hour has no unambiguous AM/PM meaning."""


def _make_date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as error:
        raise InvalidScheduleError("date is not a real calendar date") from error


def _locale_date_order(locale: str | None) -> str | None:
    if not locale:
        return None
    region = locale.replace("_", "-").split("-")[-1].casefold()
    if region == "us":
        return "month-first"
    if region in {"gb", "au", "nz", "ie", "in"}:
        return "day-first"
    return None


def resolve_date(text: str, context: RuntimeContext) -> date | None:
    """Resolve a supported date expression or report ambiguity/invalidity."""
    lowered = text.casefold()
    reference_date = context.reference_instant.date()
    results: list[date] = []

    if re.search(r"\btoday\b", lowered) or re.search(r"\btonight\b", lowered):
        results.append(reference_date)
    if re.search(r"\btomorrow\b", lowered):
        results.append(reference_date + timedelta(days=1))

    for match in ISO_DATE.finditer(text):
        try:
            results.append(date.fromisoformat(match.group(1)))
        except ValueError as error:
            raise InvalidScheduleError("date is not a real calendar date") from error

    for match in MONTH_DATE.finditer(text):
        month = MONTH_NUMBERS[match.group(1).casefold()]
        results.append(_make_date(int(match.group(3)), month, int(match.group(2))))

    for match in NUMERIC_DATE.finditer(text):
        first, second, year = (int(part) for part in match.groups())
        order = _locale_date_order(context.locale)
        if order is None:
            raise AmbiguousDateError("numeric date requires an established locale")
        month, day = (first, second) if order == "month-first" else (second, first)
        results.append(_make_date(year, month, day))

    for match in WEEKDAY.finditer(text):
        target_weekday = WEEKDAY_NUMBERS[match.group(1).casefold()]
        days_ahead = (target_weekday - reference_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        results.append(reference_date + timedelta(days=days_ahead))

    if not results:
        return None
    if any(item != results[0] for item in results[1:]):
        raise InvalidScheduleError("request contains conflicting dates")
    return results[0]


def _to_24_hour(hour: int, minute: int, meridiem: str) -> time:
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise InvalidScheduleError("12-hour time is invalid")
    if meridiem.casefold() == "am":
        hour = hour % 12
    else:
        hour = hour % 12 + 12
    return time(hour, minute)


def resolve_time(text: str) -> time | None:
    """Resolve common 12/24-hour expressions without guessing a bare hour."""
    lowered = text.casefold()
    results: list[time] = []

    if re.search(r"\bnoon\b", lowered):
        results.append(time(12, 0))
    if re.search(r"\bmidnight\b", lowered):
        results.append(time(0, 0))

    for match in TIME_12_HOUR.finditer(text):
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        results.append(_to_24_hour(hour, minute, match.group(3)))

    for match in TIME_24_HOUR.finditer(text):
        hour, minute = (int(part) for part in match.groups())
        if hour > 23 or minute > 59:
            raise InvalidScheduleError("24-hour time is invalid")
        results.append(time(hour, minute))

    if not results:
        if BARE_HOUR.search(text):
            raise AmbiguousTimeError("hour requires an unambiguous AM/PM value")
        return None
    if any(item != results[0] for item in results[1:]):
        raise InvalidScheduleError("request contains conflicting times")
    return results[0]


def is_elapsed(
    schedule_date: date, schedule_time: time, context: RuntimeContext
) -> bool:
    """Return whether a local schedule has elapsed at the reference instant."""
    zone = ZoneInfo(context.time_zone)
    scheduled = datetime.combine(schedule_date, schedule_time, tzinfo=zone)
    return scheduled.astimezone(timezone.utc) <= context.reference_instant.astimezone(
        timezone.utc
    )


def snooze_schedule(duration_minutes: int, context: RuntimeContext) -> datetime:
    """Calculate a snooze result from the supplied aware reference instant."""
    if type(duration_minutes) is not int or duration_minutes <= 0:
        raise InvalidScheduleError("snooze duration must be a positive whole number")
    try:
        elapsed = context.reference_instant.astimezone(timezone.utc) + timedelta(
            minutes=duration_minutes
        )
    except OverflowError as error:
        raise InvalidScheduleError(
            "snooze duration exceeds the supported calendar range"
        ) from error
    return elapsed.astimezone(ZoneInfo(context.time_zone))
