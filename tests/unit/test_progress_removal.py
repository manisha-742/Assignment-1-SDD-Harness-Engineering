import pytest

from smart_todo.model import (
    InvalidInputError,
    InvalidTransitionError,
    NotFoundError,
    Status,
)
from smart_todo.repository import JsonTaskRepository
from smart_todo.service import TaskService


@pytest.fixture
def service(tmp_path) -> TaskService:
    return TaskService(JsonTaskRepository(tmp_path / ".smart-todo.json"))


def test_both_permitted_status_transitions_succeed(service: TaskService) -> None:
    task = service.create("Advance task")

    in_progress = service.change_status(task.id, "IN_PROGRESS")
    done = service.change_status(task.id, "DONE")

    assert in_progress.status is Status.IN_PROGRESS
    assert done.status is Status.DONE


@pytest.mark.parametrize(
    ("current_status", "requested_status"),
    [
        ("TODO", "TODO"),
        ("TODO", "DONE"),
        ("IN_PROGRESS", "TODO"),
        ("IN_PROGRESS", "IN_PROGRESS"),
        ("DONE", "TODO"),
        ("DONE", "IN_PROGRESS"),
        ("DONE", "DONE"),
    ],
)
def test_every_other_supported_transition_is_rejected(
    service: TaskService,
    current_status: str,
    requested_status: str,
) -> None:
    task = service.create("Keep current state")
    if current_status in {"IN_PROGRESS", "DONE"}:
        service.change_status(task.id, "IN_PROGRESS")
    if current_status == "DONE":
        service.change_status(task.id, "DONE")
    before = service.repository.load()

    with pytest.raises((InvalidInputError, InvalidTransitionError)):
        service.change_status(task.id, requested_status)

    assert service.repository.load() == before


def test_unsupported_status_is_rejected_without_state_change(
    service: TaskService,
) -> None:
    task = service.create("Keep current state")
    before = service.repository.load()

    with pytest.raises(InvalidInputError):
        service.change_status(task.id, "BLOCKED")

    assert service.repository.load() == before


def test_reverse_transition_is_rejected_without_state_change(
    service: TaskService,
) -> None:
    task = service.create("Move forward")
    service.change_status(task.id, "IN_PROGRESS")
    before = service.repository.load()

    with pytest.raises(InvalidTransitionError):
        service.change_status(task.id, "TODO")

    assert service.repository.load() == before


def test_unknown_status_id_returns_not_found_without_state_change(
    service: TaskService,
) -> None:
    service.create("Keep this task")
    before = service.repository.load()

    with pytest.raises(NotFoundError):
        service.change_status(999, "BLOCKED")

    assert service.repository.load() == before


def test_delete_and_unknown_delete_preserve_collection_and_sequence(
    service: TaskService,
) -> None:
    task = service.create("Remove this task")
    service.delete(task.id)

    assert service.list_tasks() == []
    assert service.repository.load().next_id == task.id + 1
    before = service.repository.load()

    with pytest.raises(NotFoundError):
        service.delete(task.id)

    assert service.repository.load() == before
