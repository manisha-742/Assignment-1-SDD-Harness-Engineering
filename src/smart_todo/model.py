from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class TaskError(Exception):
    """Base class for expected task-manager failures."""


class InvalidInputError(TaskError):
    """Raised when a user-supplied value is invalid."""


class NotFoundError(TaskError):
    """Raised when an operation references an unknown task ID."""


class InvalidDataError(TaskError):
    """Raised when persisted task data is invalid or unreadable."""


class InvalidTransitionError(TaskError):
    """Raised when a requested status transition is not permitted."""


class StorageError(TaskError):
    """Raised when valid task data cannot be saved."""


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    priority: Priority
    tags: list[str]
    status: Status


@dataclass(frozen=True)
class TaskCollection:
    tasks: list[Task]
    next_id: int


TASK_FIELDS = {"id", "title", "priority", "tags", "status"}


def normalize_title(title: str) -> str:
    if not isinstance(title, str):
        raise InvalidInputError("Title must be a string")
    normalized = title.strip()
    if not normalized:
        raise InvalidInputError("Title must not be empty")
    return normalized


def parse_priority(value: str | Priority | None) -> Priority:
    if value is None:
        return Priority.MEDIUM
    if isinstance(value, Priority):
        return value
    try:
        return Priority(value)
    except (TypeError, ValueError) as error:
        raise InvalidInputError("Priority must be LOW, MEDIUM, or HIGH") from error


def parse_status(value: str | Status) -> Status:
    if isinstance(value, Status):
        return value
    try:
        return Status(value)
    except (TypeError, ValueError) as error:
        raise InvalidInputError("Status must be TODO, IN_PROGRESS, or DONE") from error


def normalize_tags(tags: Iterable[str] | None) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, (str, bytes)):
        raise InvalidInputError("Tags must be a sequence of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    try:
        for tag in tags:
            if not isinstance(tag, str):
                raise InvalidInputError("Each tag must be a string")
            value = tag.strip()
            if not value:
                raise InvalidInputError("Tags must not be empty")
            if value in seen:
                raise InvalidInputError("Tags must be unique")
            seen.add(value)
            normalized.append(value)
    except TypeError as error:
        raise InvalidInputError("Tags must be a sequence of strings") from error
    return normalized


def create_task(
    task_id: int,
    title: str,
    priority: str | Priority | None = None,
    tags: Iterable[str] | None = None,
) -> Task:
    if type(task_id) is not int or task_id <= 0:
        raise InvalidInputError("Task ID must be a positive integer")
    return Task(
        id=task_id,
        title=normalize_title(title),
        priority=parse_priority(priority),
        tags=normalize_tags(tags),
        status=Status.TODO,
    )


def task_to_record(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority.value,
        "tags": list(task.tags),
        "status": task.status.value,
    }


def task_from_record(record: object) -> Task:
    if not isinstance(record, dict) or set(record) != TASK_FIELDS:
        raise InvalidInputError("Task record has an invalid shape")

    task = create_task(
        record["id"],
        record["title"],
        record["priority"],
        record["tags"],
    )
    status = parse_status(record["status"])
    return Task(
        id=task.id,
        title=task.title,
        priority=task.priority,
        tags=task.tags,
        status=status,
    )
