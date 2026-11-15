import json
from types import SimpleNamespace

from reminder_agent.cli import main

CREATE = {
    "intent": "create_reminder",
    "task": "check the weather",
    "date": "2026-11-16",
    "time": "09:00",
    "needs_clarification": False,
    "clarification_question": None,
    "target_reminder": None,
    "snooze_duration_minutes": None,
}

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


def test_unrelated_request_cannot_be_promoted_to_a_reminder(
    monkeypatch, capsys
) -> None:
    class FakeResponses:
        def create(self, **request: object) -> SimpleNamespace:
            return SimpleNamespace(output_text=json.dumps(CREATE), status="completed")

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("REMINDER_TIME_ZONE", "UTC")

    result = main(["interpret", "What is the weather tomorrow?"])
    captured = capsys.readouterr()

    assert result == 0
    assert json.loads(captured.out) == UNSUPPORTED


def test_unsupported_request_emits_safe_object_without_persistence(
    monkeypatch, capsys, tmp_path
) -> None:
    class FakeResponses:
        def create(self, **request: object) -> SimpleNamespace:
            return SimpleNamespace(
                output_text=json.dumps(UNSUPPORTED),
                status="completed",
            )

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("REMINDER_TIME_ZONE", "UTC")

    result = main(["interpret", "???"])
    captured = capsys.readouterr()

    assert result == 0
    assert json.loads(captured.out) == UNSUPPORTED
    assert list(tmp_path.iterdir()) == []
