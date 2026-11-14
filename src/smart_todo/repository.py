import json
import os
import tempfile
from pathlib import Path

from .model import (
    InvalidDataError,
    InvalidInputError,
    StorageError,
    Task,
    TaskCollection,
    task_from_record,
    task_to_record,
)


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class JsonTaskRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> TaskCollection:
        try:
            content = self.path.read_bytes()
        except FileNotFoundError:
            if self.path.parent.is_dir():
                return TaskCollection(tasks=[], next_id=1)
            raise InvalidDataError("Task file cannot be read") from None
        except OSError as error:
            raise InvalidDataError("Task file cannot be read") from error

        try:
            document = json.loads(
                content.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
            return self._collection_from_document(document)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as error:
            if isinstance(error, InvalidInputError):
                detail = str(error)
            else:
                detail = "Task file is not valid JSON data"
            raise InvalidDataError(detail) from error

    def save(self, collection: TaskCollection) -> None:
        document = self._document_from_collection(collection)
        content = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
        temporary_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        except OSError as error:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
                except OSError as cleanup_error:
                    raise StorageError(
                        "Task save and temporary file cleanup both failed"
                    ) from cleanup_error

            raise StorageError("Task file could not be saved") from error

    @staticmethod
    def _collection_from_document(document: object) -> TaskCollection:
        if (
            not isinstance(document, dict)
            or set(document) != {"next_id", "tasks"}
            or type(document["next_id"]) is not int
            or document["next_id"] <= 0
            or not isinstance(document["tasks"], list)
        ):
            raise InvalidDataError("Task document has an invalid shape")

        tasks: list[Task] = []
        seen_ids: set[int] = set()
        for record in document["tasks"]:
            try:
                task = task_from_record(record)
            except InvalidInputError as error:
                raise InvalidDataError("Task record is invalid") from error
            if task.id in seen_ids:
                raise InvalidDataError("Task IDs must be unique")
            seen_ids.add(task.id)
            tasks.append(task)

        next_id = document["next_id"]
        if seen_ids and next_id <= max(seen_ids):
            raise InvalidDataError("Next task ID must exceed every saved task ID")
        return TaskCollection(tasks=tasks, next_id=next_id)

    @staticmethod
    def _document_from_collection(
        collection: TaskCollection,
    ) -> dict[str, object]:
        if type(collection.next_id) is not int or collection.next_id <= 0:
            raise InvalidDataError("Next task ID must be a positive integer")
        ids: set[int] = set()
        tasks: list[dict[str, object]] = []
        for task in collection.tasks:
            try:
                record = task_to_record(task)
                validated = task_from_record(record)
            except (AttributeError, InvalidInputError) as error:
                raise InvalidDataError("Task record is invalid") from error
            if validated.id in ids:
                raise InvalidDataError("Task IDs must be unique")
            ids.add(validated.id)
            tasks.append(record)
        if ids and collection.next_id <= max(ids):
            raise InvalidDataError("Next task ID must exceed every task ID")
        tasks.sort(key=lambda task: task["id"])
        return {"next_id": collection.next_id, "tasks": tasks}
