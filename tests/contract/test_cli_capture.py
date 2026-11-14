import json


def read_json(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_add_and_list_report_stable_fields_and_defaults(run_cli) -> None:
    created = read_json(run_cli("add", "--title", "Review report", "--tag", "work"))
    listed = read_json(run_cli("list"))

    assert created == {
        "id": 1,
        "title": "Review report",
        "priority": "MEDIUM",
        "tags": ["work"],
        "status": "TODO",
    }
    assert listed == [created]


def test_list_returns_tasks_once_in_ascending_id_order(run_cli) -> None:
    created = [
        read_json(run_cli("add", "--title", f"Task {index}")) for index in range(100)
    ]

    listed = read_json(run_cli("list"))

    assert len(listed) == 100
    assert [task["id"] for task in listed] == list(range(1, 101))
    assert len({task["id"] for task in listed}) == 100
    assert listed == created


def test_invalid_title_is_rejected_without_partial_changes(run_cli) -> None:
    original = read_json(run_cli("add", "--title", "Keep this task"))

    result = run_cli("add", "--title", " \t ")

    assert result.returncode != 0
    assert read_json(run_cli("list")) == [original]


def test_corrupt_json_is_reported_and_left_unchanged(run_cli, tmp_path) -> None:
    path = tmp_path / ".smart-todo.json"
    original = b'{"next_id":1,"tasks":['
    path.write_bytes(original)

    result = run_cli("list")

    assert result.returncode != 0
    assert json.loads(result.stderr)["error"] == "INVALID_DATA"
    assert result.stdout == ""
    assert path.read_bytes() == original
