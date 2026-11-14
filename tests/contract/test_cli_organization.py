import json


def read_json(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def read_error(result):
    assert result.returncode != 0
    return json.loads(result.stderr)


def test_cli_updates_fields_and_preserves_unmentioned_fields(run_cli) -> None:
    created = read_json(
        run_cli("add", "--title", "Initial", "--priority", "LOW", "--tag", "work")
    )

    updated = read_json(
        run_cli("update", str(created["id"]), "--title", "Updated", "--tag", "home")
    )

    assert updated == {
        "id": created["id"],
        "title": "Updated",
        "priority": "LOW",
        "tags": ["home"],
        "status": "TODO",
    }


def test_unknown_update_returns_not_found_without_changing_tasks(run_cli) -> None:
    created = read_json(run_cli("add", "--title", "Keep"))

    error = read_error(run_cli("update", "999", "--title", "Changed"))

    assert error["error"] == "NOT_FOUND"
    assert read_json(run_cli("list")) == [created]


def test_invalid_update_returns_error_without_partial_changes(run_cli) -> None:
    created = read_json(run_cli("add", "--title", "Keep", "--priority", "LOW"))

    error = read_error(
        run_cli(
            "update",
            str(created["id"]),
            "--title",
            "Changed",
            "--priority",
            "URGENT",
        )
    )

    assert error["error"] == "INVALID_INPUT"
    assert read_json(run_cli("list")) == [created]


def test_cli_filters_before_optional_priority_sort(run_cli) -> None:
    low = read_json(
        run_cli("add", "--title", "Low work", "--priority", "LOW", "--tag", "work")
    )
    high = read_json(
        run_cli("add", "--title", "High work", "--priority", "HIGH", "--tag", "work")
    )
    read_json(
        run_cli("add", "--title", "High home", "--priority", "HIGH", "--tag", "home")
    )

    assert read_json(run_cli("list", "--tag", "work", "--sort", "priority")) == [
        high,
        low,
    ]
