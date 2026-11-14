from dataclasses import replace

from .model import (
    InvalidInputError,
    InvalidTransitionError,
    NotFoundError,
    Priority,
    Status,
    Task,
    TaskCollection,
    create_task,
    normalize_tags,
    normalize_title,
    parse_priority,
    parse_status,
)
from .repository import JsonTaskRepository


class TaskService:
    def __init__(self, repository: JsonTaskRepository) -> None:
        self.repository = repository

    def create(
        self,
        title: str,
        priority: str | Priority | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        collection = self.repository.load()
        task = create_task(collection.next_id, title, priority, tags)
        candidate = TaskCollection(
            tasks=[*collection.tasks, task],
            next_id=collection.next_id + 1,
        )
        self.repository.save(candidate)
        return task

    def list_tasks(
        self,
        tag: str | None = None,
        sort_priority: bool = False,
    ) -> list[Task]:
        tasks = self.repository.load().tasks
        if tag is not None:
            tasks = [task for task in tasks if tag in task.tags]
        if sort_priority:
            priority_order = {
                Priority.HIGH: 0,
                Priority.MEDIUM: 1,
                Priority.LOW: 2,
            }
            return sorted(
                tasks,
                key=lambda task: (priority_order[task.priority], task.id),
            )
        return sorted(tasks, key=lambda task: task.id)

    def update(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | Priority | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        collection = self.repository.load()
        original = self._find_task(collection, task_id)
        if title is None and priority is None and tags is None:
            raise InvalidInputError("At least one task field must be provided")

        updated = replace(
            original,
            title=original.title if title is None else normalize_title(title),
            priority=(
                original.priority if priority is None else parse_priority(priority)
            ),
            tags=original.tags if tags is None else normalize_tags(tags),
        )
        self._save_replacement(collection, original, updated)
        return updated

    def change_status(self, task_id: int, status: str | Status) -> Task:
        collection = self.repository.load()
        original = self._find_task(collection, task_id)
        new_status = parse_status(status)
        allowed = {
            (Status.TODO, Status.IN_PROGRESS),
            (Status.IN_PROGRESS, Status.DONE),
        }
        if (original.status, new_status) not in allowed:
            raise InvalidTransitionError("Status transition is not permitted")

        updated = replace(original, status=new_status)
        self._save_replacement(collection, original, updated)
        return updated

    def delete(self, task_id: int) -> None:
        collection = self.repository.load()
        original = self._find_task(collection, task_id)
        candidate = TaskCollection(
            tasks=[task for task in collection.tasks if task.id != original.id],
            next_id=collection.next_id,
        )
        self.repository.save(candidate)

    def _save_replacement(
        self,
        collection: TaskCollection,
        original: Task,
        updated: Task,
    ) -> None:
        candidate = TaskCollection(
            tasks=[
                updated if task.id == original.id else task for task in collection.tasks
            ],
            next_id=collection.next_id,
        )
        self.repository.save(candidate)

    @staticmethod
    def _find_task(collection: TaskCollection, task_id: int) -> Task:
        if type(task_id) is not int or task_id <= 0:
            raise InvalidInputError("Task ID must be a positive integer")
        for task in collection.tasks:
            if task.id == task_id:
                return task
        raise NotFoundError(f"Task {task_id} was not found")
