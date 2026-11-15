import json
from pathlib import Path
from types import SimpleNamespace

from reminder_agent.cli import main
from reminder_agent.evaluation import DATASET_PATH

UNSUPPORTED = {
    "intent": "unsupported",
    "task": None,
    "date": None,
    "time": None,
    "needs_clarification": False,
    "clarification_question": None,
    "target_reminder": None,
    "snooze_duration_minutes": None,
}


def test_evaluate_fails_without_key_and_does_not_create_evidence(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        "reminder_agent.evaluation.DEFAULT_EVIDENCE_ROOT", tmp_path / "evidence"
    )

    result = main(["evaluate", "--cases", str(DATASET_PATH)])
    captured = capsys.readouterr()

    assert result != 0
    assert "GROQ_API_KEY" in captured.err
    assert not (tmp_path / "evidence").exists()


def test_evaluate_uses_fixed_cases_and_preserves_a_complete_run(
    monkeypatch, tmp_path, capsys
) -> None:
    secret = "synthetic-live-evaluation-key"
    monkeypatch.setenv("GROQ_API_KEY", secret)
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    monkeypatch.setattr(
        "reminder_agent.evaluation.DEFAULT_EVIDENCE_ROOT", tmp_path / "evidence"
    )
    calls = []

    class FakeResponses:
        def create(self, **request: object) -> SimpleNamespace:
            calls.append(request)
            assert request["store"] is False
            return SimpleNamespace(
                output_text=json.dumps(UNSUPPORTED),
                status="completed",
            )

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            assert api_key == secret
            self.responses = FakeResponses()

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)
    exit_code = main(["evaluate", "--cases", str(DATASET_PATH)])
    captured = capsys.readouterr()
    run_dir = Path(captured.out.strip())

    assert exit_code == 0
    assert len(calls) == 23
    assert run_dir.is_dir()
    cases = json.loads((run_dir / "dataset.json").read_text(encoding="utf-8"))
    results = json.loads((run_dir / "case-results.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert len(cases) == len(results) == 25
    assert manifest["model"] == "test-model"
    assert manifest["request_settings"]["strict_json_schema"]
    assert manifest["aggregate_status"] == "PENDING_HUMAN_SEMANTIC_REVIEW"
    assert results[11]["context"]["reference_instant"].startswith("2026-12-31")
    assert results[21]["input"] == "???"
    assert results[24]["input"] == ""
    failures = json.loads(
        (run_dir / "genuine-failures.json").read_text(encoding="utf-8")
    )
    assert failures
    assert (run_dir / "repair-feedback-template.json").is_file()
    for path in run_dir.iterdir():
        assert secret not in path.read_text(encoding="utf-8")

    provider_call_count = len(calls)
    monkeypatch.delenv("GROQ_API_KEY")
    replay_code = main(["replay", "--run-dir", str(run_dir)])
    replay_capture = capsys.readouterr()
    replay_dir = Path(replay_capture.out.strip())
    replay_manifest = json.loads(
        (replay_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert replay_code == 0
    assert replay_manifest["evaluation_mode"] == "offline_replay"
    assert replay_manifest["replay_of"] == run_dir.name
    assert len(calls) == provider_call_count

    monkeypatch.setenv("GROQ_API_KEY", secret)
    feedback_path = tmp_path / "repair-feedback.txt"
    feedback_path.write_text(
        "Preserve case facts and correct the recorded interpretation failures.",
        encoding="utf-8",
    )
    rerun_code = main(
        [
            "evaluate",
            "--cases",
            str(DATASET_PATH),
            "--repair-of",
            str(run_dir),
            "--repair-feedback",
            str(feedback_path),
        ]
    )
    rerun_capture = capsys.readouterr()
    rerun_dir = Path(rerun_capture.out.strip())
    repair_link = json.loads(
        (rerun_dir / "repair-link.json").read_text(encoding="utf-8")
    )
    assert rerun_code == 0
    assert rerun_dir != run_dir
    assert repair_link["source_failure_run"] == run_dir.name
    assert repair_link["source_failures"]
