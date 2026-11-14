import json

import pytest

from smart_todo.model import (
    InvalidDataError,
    Priority,
    Status,
    Task,
    TaskCollection,
)
from smart_todo.repository import JsonTaskRepository


def test_missing_file_starts_with_empty_collection_and_sequence_one(tmp_path) -> None:
    repository = JsonTaskRepository(tmp_path / ".smart-todo.json")

    collection = repository.load()

    assert collection == TaskCollection(tasks=[], next_id=1)


def test_round_trip_preserves_every_task_field_and_next_id(tmp_path) -> None:
    path = tmp_path / ".smart-todo.json"
    repository = JsonTaskRepository(path)
    collection = TaskCollection(
        tasks=[
            Task(
                id=4,
                title="Review",
                priority=Priority.HIGH,
                tags=["work", "urgent"],
                status=Status.IN_PROGRESS,
            )
        ],
        next_id=8,
    )

    repository.save(collection)

    assert repository.load() == collection
    assert json.loads(path.read_text(encoding="utf-8"))["next_id"] == 8


@pytest.mark.parametrize(
    "document",
    [
        "{",
        '{"next_id": 2, "tasks": [{"id": 1}]}',
        (
            '{"next_id": 3, "tasks": ['
            '{"id": 1, "title": "a", "priority": "LOW", "tags": [], "status": "TODO"},'
            '{"id": 1, "title": "b", "priority": "LOW", "tags": [], "status": "TODO"}]}'
        ),
        '{"next_id": 0, "tasks": []}',
        '{"next_id": 1, "next_id": 2, "tasks": []}',
        (
            '{"next_id": 2, "tasks": ['
            '{"id": 1, "title": " ", "priority": "LOW", "tags": [], "status": "TODO"}]}'
        ),
    ],
)
def test_invalid_document_fails_closed_and_remains_byte_for_byte_unchanged(
    tmp_path, document: str
) -> None:
    path = tmp_path / ".smart-todo.json"
    original = document.encode("utf-8")
    path.write_bytes(original)
    repository = JsonTaskRepository(path)

    with pytest.raises(InvalidDataError):
        repository.load()

    assert path.read_bytes() == original


def test_deleted_highest_id_does_not_lower_next_id(tmp_path) -> None:
    path = tmp_path / ".smart-todo.json"
    repository = JsonTaskRepository(path)
    repository.save(TaskCollection(tasks=[], next_id=15))

    assert repository.load().next_id == 15


def test_unreadable_existing_file_fails_closed_without_modification(
    tmp_path, monkeypatch
) -> None:
    from pathlib import Path

    path = tmp_path / ".smart-todo.json"
    original = b'{"next_id":1,"tasks":[]}'
    path.write_bytes(original)
    repository = JsonTaskRepository(path)
    read_bytes = Path.read_bytes

    def deny_read(target: Path) -> bytes:
        if target == path:
            raise PermissionError("test read denial")
        return read_bytes(target)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", deny_read)
        with pytest.raises(InvalidDataError):
            repository.load()

    assert path.read_bytes() == original
