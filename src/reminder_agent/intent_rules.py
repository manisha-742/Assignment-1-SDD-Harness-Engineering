"""Deterministic intent and explicit snooze-duration helpers."""

import re

from reminder_agent.model import ReminderIntent

SNOOZE_DURATION = re.compile(
    r"\bfor\s+(?:(\d+)\s+hours?(?:\s+and\s+)?(?:(\d+)\s+minutes?)?)"
    r"|(?:for\s+(\d+)\s+minutes?)\b",
    re.IGNORECASE,
)


def has_content(text: str) -> bool:
    """Return whether input contains a letter or digit that can carry meaning."""
    return any(character.isalnum() for character in text)


def detect_intent(text: str) -> ReminderIntent | None:
    """Classify explicit change verbs before treating a request as a create."""
    lowered = text.casefold()
    if re.search(r"\bsnooze\b", lowered) or (
        re.search(r"\b(?:put\s+off|delay)\b", lowered)
        and re.search(r"\b(?:reminder|appointment|meeting|it|this|that)\b", lowered)
    ):
        return ReminderIntent.SNOOZE
    if re.search(r"\b(?:reschedule|postpone)\b", lowered) or (
        re.search(r"\b(?:move|change)\b", lowered)
        and re.search(r"\b(?:reminder|appointment|meeting|it|this|that)\b", lowered)
    ):
        return ReminderIntent.RESCHEDULE
    if re.search(r"\b(?:remind|reminder)\b", lowered):
        return ReminderIntent.CREATE
    return None


def parse_snooze_duration_minutes(text: str) -> int | None:
    """Return only an explicit, whole-minute snooze duration."""
    if re.search(r"\bfor\s*-\s*\d", text, re.IGNORECASE):
        return None
    if len(list(re.finditer(r"\bfor\s+", text, re.IGNORECASE))) != 1:
        return None
    match = SNOOZE_DURATION.search(text)
    if match is None:
        return None
    try:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or match.group(3) or 0)
    except ValueError:
        return None
    duration = hours * 60 + minutes
    return duration if duration > 0 else None


def has_specific_reminder_target(text: str) -> bool:
    """Reject pronouns and generic reminder labels as uniquely identifying targets."""
    lowered = text.casefold()
    if re.search(r"\b(?:it|that|this)\b", lowered):
        return False
    if re.search(r"\b(?:my|the)\s+reminder\b", lowered):
        return bool(
            re.search(
                r"\b(?:reminder|appointment)\s+(?:for|to|about)\s+\w+",
                lowered,
            )
        )
    return bool(
        re.search(
            r"\b(?:my|the)\s+[\w'-]+(?:\s+[\w'-]+){0,4}\s+"
            r"(?:reminder|appointment|meeting|call|task)\b",
            lowered,
        )
    )


def extract_create_task(text: str) -> str | None:
    """Extract the task phrase explicitly introduced by a create request."""
    match = re.search(
        r"\bremind\s+me\b.*?\bto\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match is None:
        match = re.search(r"\bremind\s+me\s*:\s*(.+)", text, re.IGNORECASE)
    if match is None:
        return None
    task = re.split(
        r"\b(?:today|tomorrow|tonight|at\s+\d|on\s+(?:\d|"
        r"January|February|March|April|May|June|July|August|September|October|"
        r"November|December|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)|"
        r"by\s+(?:today|tomorrow|tonight))\b",
        match.group(1),
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return task.strip(" \t\r\n.,!?") or None


def extract_target_and_task(text: str) -> tuple[str | None, str | None]:
    """Return a user-described reminder target and its underlying task phrase."""
    match = re.search(
        r"\b(?:my|the)\s+(.+?\s+reminder)\b",
        text,
        re.IGNORECASE,
    )
    if match is None:
        match = re.search(
            r"\b(?:my|the)\s+(.+?\s+(?:appointment|meeting|call|task))\b",
            text,
            re.IGNORECASE,
        )
    if match is None:
        match = re.search(
            r"\breminder\s+(?:for|to|about)\s+([^.!?,]+)",
            text,
            re.IGNORECASE,
        )
    if match is None:
        return None, None
    target = match.group(1).strip(" \t\r\n.,!?")
    task = re.sub(r"\s+reminder$", "", target, flags=re.IGNORECASE).strip()
    return (target or None), (task or None)
