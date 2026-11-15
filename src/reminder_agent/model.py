"""Typed representation of a single reminder interpretation."""

from dataclasses import dataclass
from enum import Enum


class ReminderIntent(str, Enum):
    CREATE = "create_reminder"
    RESCHEDULE = "reschedule_reminder"
    SNOOZE = "snooze_reminder"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ReminderOutput:
    intent: ReminderIntent
    task: str | None
    date: str | None
    time: str | None
    needs_clarification: bool
    clarification_question: str | None
    target_reminder: str | None
    snooze_duration_minutes: int | None

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "intent": self.intent.value,
            "task": self.task,
            "date": self.date,
            "time": self.time,
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
            "target_reminder": self.target_reminder,
            "snooze_duration_minutes": self.snooze_duration_minutes,
        }
