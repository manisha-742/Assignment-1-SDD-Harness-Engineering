import json


def read_json(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_status_and_all_task_fields_survive_restart(run_cli) -> None:
    task = read_json(
        run_cli(
            "add",
            "--title",
            "Persist me",
            "--priority",
            "HIGH",
            "--tag",
            "work",
        )
    )
    read_json(run_cli("status", str(task["id"]), "IN_PROGRESS"))
    done = read_json(run_cli("status", str(task["id"]), "DONE"))

    assert read_json(run_cli("list")) == [done]


def test_deleted_id_is_not_reused_after_restart(run_cli) -> None:
    first = read_json(run_cli("add", "--title", "Delete this"))
    read_json(run_cli("delete", str(first["id"])))

    second = read_json(run_cli("add", "--title", "New task"))

    assert second["id"] > first["id"]


def test_all_task_fields_survive_ten_application_restarts(run_cli) -> None:
    task = read_json(
        run_cli(
            "add",
            "--title",
            "Ten restarts",
            "--priority",
            "MEDIUM",
            "--tag",
            "persist",
        )
    )
    expected = [task]

    for _ in range(10):
        assert read_json(run_cli("list")) == expected


def test_one_hundred_identical_executions_are_deterministic(run_cli, tmp_path) -> None:
    run_cli("add", "--title", "Repeatable")
    path = tmp_path / ".smart-todo.json"
    original_state = path.read_bytes()

    results = [run_cli("list") for _ in range(100)]

    assert all(
        (result.returncode, result.stdout, result.stderr)
        == (results[0].returncode, results[0].stdout, results[0].stderr)
        for result in results
    )
    assert path.read_bytes() == original_state
