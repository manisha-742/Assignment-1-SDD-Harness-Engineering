import pytest

from smart_todo.model import (
    InvalidInputError,
    Priority,
)
from smart_todo.repository import JsonTaskRepository
from smart_todo.service import TaskService


@pytest.fixture
def service(tmp_path) -> TaskService:
    return TaskService(JsonTaskRepository(tmp_path / ".smart-todo.json"))


def test_update_changes_supplied_fields_and_preserves_everything_else(
    service: TaskService,
) -> None:
    original = service.create("Initial title", "LOW", ["work"])

    updated = service.update(original.id, title=" Updated ", tags=["home"])

    assert updated.id == original.id
    assert updated.title == "Updated"
    assert updated.priority is Priority.LOW
    assert updated.tags == ["home"]
    assert updated.status is original.status


@pytest.mark.parametrize(
    "fields",
    [
        {"title": " "},
        {"priority": "URGENT"},
        {"tags": ["work", "work"]},
    ],
)
def test_invalid_update_is_atomic(
    service: TaskService,
    fields: dict[str, object],
) -> None:
    original = service.create("Keep this task", "MEDIUM", ["work"])
    before = service.repository.load()

    with pytest.raises(InvalidInputError):
        service.update(original.id, **fields)

    assert service.repository.load() == before


def test_filter_is_exact_and_empty_matches_do_not_change_collection(
    service: TaskService,
) -> None:
    work = service.create("Work", tags=["work"])
    service.create("Work uppercase", tags=["Work"])
    before = service.repository.load()

    assert service.list_tasks(tag="work") == [work]
    assert service.list_tasks(tag="missing") == []
    assert service.repository.load() == before


def test_priority_sort_uses_high_medium_low_then_ascending_id(
    service: TaskService,
) -> None:
    low_first = service.create("Low 1", "LOW")
    high_first = service.create("High 1", "HIGH")
    medium = service.create("Medium", "MEDIUM")
    high_second = service.create("High 2", "HIGH")
    low_second = service.create("Low 2", "LOW")

    assert service.list_tasks(sort_priority=True) == [
        high_first,
        high_second,
        medium,
        low_first,
        low_second,
    ]
