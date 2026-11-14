import json


def read_json(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def read_error(result):
    assert result.returncode != 0
    return json.loads(result.stderr)


def test_status_commands_allow_only_the_two_defined_transitions(run_cli) -> None:
    task = read_json(run_cli("add", "--title", "Progress me"))

    in_progress = read_json(run_cli("status", str(task["id"]), "IN_PROGRESS"))
    done = read_json(run_cli("status", str(task["id"]), "DONE"))
    before = read_json(run_cli("list"))
    error = read_error(run_cli("status", str(task["id"]), "TODO"))
    unsupported = read_error(run_cli("status", str(task["id"]), "BLOCKED"))

    assert in_progress["status"] == "IN_PROGRESS"
    assert done["status"] == "DONE"
    assert error["error"] == "INVALID_TRANSITION"
    assert unsupported["error"] == "INVALID_INPUT"
    assert read_json(run_cli("list")) == before


def test_status_and_delete_unknown_ids_return_not_found(run_cli) -> None:
    task = read_json(run_cli("add", "--title", "Keep"))
    before = read_json(run_cli("list"))

    status_error = read_error(run_cli("status", "999", "IN_PROGRESS"))
    delete_error = read_error(run_cli("delete", "999"))

    assert status_error["error"] == "NOT_FOUND"
    assert delete_error["error"] == "NOT_FOUND"
    assert read_json(run_cli("list")) == before == [task]


def test_delete_confirms_success_and_removes_task(run_cli) -> None:
    task = read_json(run_cli("add", "--title", "Delete me"))

    deleted = read_json(run_cli("delete", str(task["id"])))

    assert deleted == {"deleted": task["id"]}
    assert read_json(run_cli("list")) == []
