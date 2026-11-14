import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .model import (
    InvalidDataError,
    InvalidInputError,
    InvalidTransitionError,
    NotFoundError,
    StorageError,
    task_to_record,
)
from .repository import JsonTaskRepository
from .service import TaskService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smart-todo")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--priority")
    add.add_argument("--tag", nargs="*")

    list_command = commands.add_parser("list")
    list_command.add_argument("--tag")
    list_command.add_argument("--sort", choices=("priority",))

    update = commands.add_parser("update")
    update.add_argument("id", type=int)
    update.add_argument("--title")
    update.add_argument("--priority")
    update.add_argument("--tag", nargs="*")

    status = commands.add_parser("status")
    status.add_argument("id", type=int)
    status.add_argument("status")

    delete = commands.add_parser("delete")
    delete.add_argument("id", type=int)
    return parser


def _write_json(value: object, stream: object) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    stream.write("\n")


def _write_error(code: str, message: str) -> None:
    _write_json({"error": code, "message": message}, sys.stderr)


def _run(arguments: argparse.Namespace, service: TaskService) -> object:
    if arguments.command == "add":
        return task_to_record(
            service.create(arguments.title, arguments.priority, arguments.tag)
        )
    if arguments.command == "list":
        return [
            task_to_record(task)
            for task in service.list_tasks(
                tag=arguments.tag,
                sort_priority=arguments.sort == "priority",
            )
        ]
    if arguments.command == "update":
        return task_to_record(
            service.update(
                arguments.id,
                title=arguments.title,
                priority=arguments.priority,
                tags=arguments.tag,
            )
        )
    if arguments.command == "status":
        return task_to_record(service.change_status(arguments.id, arguments.status))
    if arguments.command == "delete":
        service.delete(arguments.id)
        return {"deleted": arguments.id}
    raise InvalidInputError("Unknown command")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    repository = JsonTaskRepository(Path.cwd() / ".smart-todo.json")
    service = TaskService(repository)
    try:
        result = _run(arguments, service)
    except InvalidInputError as error:
        _write_error("INVALID_INPUT", str(error))
        return 2
    except InvalidTransitionError as error:
        _write_error("INVALID_TRANSITION", str(error))
        return 2
    except NotFoundError as error:
        _write_error("NOT_FOUND", str(error))
        return 3
    except InvalidDataError as error:
        _write_error("INVALID_DATA", str(error))
        return 4
    except StorageError as error:
        _write_error("IO_ERROR", str(error))
        return 5

    _write_json(result, sys.stdout)
    return 0
