import json


def read_json(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_exact_tag_filter_and_priority_sort_match_expected_tasks(run_cli) -> None:
    low_work = read_json(
        run_cli("add", "--title", "Low work", "--priority", "LOW", "--tag", "work")
    )
    high_home = read_json(
        run_cli("add", "--title", "High home", "--priority", "HIGH", "--tag", "home")
    )
    high_work = read_json(
        run_cli("add", "--title", "High work", "--priority", "HIGH", "--tag", "work")
    )

    assert read_json(run_cli("list", "--tag", "work", "--sort", "priority")) == [
        high_work,
        low_work,
    ]
    assert read_json(run_cli("list", "--tag", "Work")) == []
    assert high_home not in read_json(
        run_cli("list", "--tag", "work", "--sort", "priority")
    )


def test_equivalent_starting_states_produce_identical_results(
    run_cli, tmp_path
) -> None:
    run_cli("add", "--title", "First", "--tag", "work")
    run_cli("add", "--title", "Second", "--tag", "work")
    state_path = tmp_path / ".smart-todo.json"
    initial_state = state_path.read_bytes()

    first = run_cli("list", "--tag", "work", "--sort", "priority")
    state_path.write_bytes(initial_state)
    second = run_cli("list", "--tag", "work", "--sort", "priority")

    assert (first.returncode, first.stdout, first.stderr) == (
        second.returncode,
        second.stdout,
        second.stderr,
    )
