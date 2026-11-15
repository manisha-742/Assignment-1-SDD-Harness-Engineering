"""Safe clarification decisions for incomplete reminder requests."""

from reminder_agent.model import ReminderIntent, ReminderOutput


def build_clarification_guidance() -> str:
    return (
        "When critical information is missing or ambiguous, do not invent it. "
        "Keep unknown values null and ask one focused question for the missing or "
        "ambiguous task, target, date, time, or snooze duration."
    )


def clarification_question(output: ReminderOutput) -> str:
    """Create a concise prompt for the first unresolved critical field."""
    if output.intent in {ReminderIntent.RESCHEDULE, ReminderIntent.SNOOZE} and (
        output.target_reminder is None
    ):
        return "Which reminder should I change?"
    if output.task is None:
        return "What should I remind you to do?"
    if (
        output.intent is ReminderIntent.SNOOZE
        and output.snooze_duration_minutes is None
    ):
        return "How many minutes should I snooze the reminder?"
    if output.date is None and output.time is None:
        return "What date and time should I use?"
    if output.date is None:
        return "What date should I use?"
    if output.time is None:
        return "What time should I use?"
    return "Could you clarify the reminder details?"
