import json
from types import SimpleNamespace

from harness import runner


def fake_run_factory(failing_command: str | None = None):
    executed: list[list[str]] = []

    def fake_run(command, cwd, capture_output, text, check):
        executed.append(command)
        if command[:2] == ["git", "rev-parse"]:
            return SimpleNamespace(returncode=0, stdout="abc123\n", stderr="")
        report_argument = next(
            (argument for argument in command if argument.startswith("--junitxml=")),
            None,
        )
        if report_argument:
            report_path = report_argument.split("=", 1)[1]
            with open(report_path, "w", encoding="utf-8") as report:
                report.write("<testsuites />")
        name = command[2] if command[0] == runner.sys.executable else command[0]
        return SimpleNamespace(
            returncode=1 if name == failing_command else 0,
            stdout=f"{name} stdout\n",
            stderr=f"{name} stderr\n",
        )

    return fake_run, executed


def read_evidence(run_directory):
    return json.loads((run_directory / "run.json").read_text(encoding="utf-8"))


def test_harness_records_fixed_commands_versions_and_pass_evidence(
    tmp_path, monkeypatch
) -> None:
    fake_run, executed = fake_run_factory()
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.metadata,
        "version",
        lambda name: f"{name}-version",
    )

    run_directory = runner.run_harness(tmp_path)
    evidence = read_evidence(run_directory)

    assert [entry["name"] for entry in evidence["commands"]] == [
        "pytest",
        "ruff check",
        "ruff format",
        "bandit",
    ]
    assert [command[0] for command in executed[1:5]] == [
        runner.sys.executable,
        "ruff",
        "ruff",
        "bandit",
    ]
    assert executed[0][:2] == ["git", "rev-parse"]
    assert evidence["aggregate_status"] == "PASS"
    assert evidence["commit_id"] == "abc123"
    assert evidence["tool_versions"]["pytest"] == "pytest-version"
    assert all(entry["returncode"] == 0 for entry in evidence["commands"])
    assert all(
        "stdout" in entry and "stderr" in entry for entry in evidence["commands"]
    )
    assert (run_directory / "pytest.xml").is_file()


def test_harness_runs_all_checks_and_reports_failures(tmp_path, monkeypatch) -> None:
    fake_run, _ = fake_run_factory("bandit")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.metadata, "version", lambda name: "test-version")

    evidence = read_evidence(runner.run_harness(tmp_path))

    assert evidence["aggregate_status"] == "FAIL"
    assert [entry["returncode"] for entry in evidence["commands"]] == [0, 0, 0, 1]


def test_harness_creates_unique_non_overwriting_run_directories(
    tmp_path, monkeypatch
) -> None:
    fake_run, _ = fake_run_factory()
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.metadata, "version", lambda name: "test-version")

    first = runner.run_harness(tmp_path)
    second = runner.run_harness(tmp_path)

    assert first != second
    assert first.is_dir()
    assert second.is_dir()
    assert len(list((tmp_path / "artifacts" / "harness").iterdir())) == 2
