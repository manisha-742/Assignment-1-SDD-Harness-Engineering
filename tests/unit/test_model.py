import pytest

from smart_todo.model import (
    InvalidInputError,
    Priority,
    Status,
    create_task,
    normalize_tags,
    normalize_title,
    parse_priority,
)


def test_title_is_trimmed_before_storage() -> None:
    assert normalize_title("  finish report \t") == "finish report"


@pytest.mark.parametrize("title", ["", " ", "\t\n"])
def test_empty_or_whitespace_title_is_rejected(title: str) -> None:
    with pytest.raises(InvalidInputError):
        normalize_title(title)


def test_priority_defaults_to_medium_and_accepts_all_values() -> None:
    assert parse_priority(None) is Priority.MEDIUM
    assert [parse_priority(value).value for value in ("LOW", "MEDIUM", "HIGH")] == [
        "LOW",
        "MEDIUM",
        "HIGH",
    ]


@pytest.mark.parametrize("priority", ["", "URGENT", "high"])
def test_invalid_priority_is_rejected(priority: str) -> None:
    with pytest.raises(InvalidInputError):
        parse_priority(priority)


def test_tags_are_trimmed_and_empty_tags_are_allowed() -> None:
    assert normalize_tags([" work ", "home"]) == ["work", "home"]
    assert normalize_tags([]) == []


@pytest.mark.parametrize("tags", [[""], ["  "], ["work", "work"]])
def test_empty_or_duplicate_tags_are_rejected(tags: list[str]) -> None:
    with pytest.raises(InvalidInputError):
        normalize_tags(tags)


def test_new_task_has_only_required_fields_and_starts_todo() -> None:
    task = create_task(7, "Write tests", tags=["dev"])

    assert task.id == 7
    assert task.title == "Write tests"
    assert task.priority is Priority.MEDIUM
    assert task.tags == ["dev"]
    assert task.status is Status.TODO
