import json
from types import SimpleNamespace

from reminder_agent.cli import main


def test_cli_returns_one_create_object_without_persisting_reminders(
    monkeypatch, capsys
) -> None:
    expected = {
        "intent": "create_reminder",
        "task": "submit my assignment",
        "date": "2026-11-16",
        "time": "20:00",
        "needs_clarification": False,
        "clarification_question": None,
        "target_reminder": None,
        "snooze_duration_minutes": None,
    }

    class FakeResponses:
        def create(self, **request: object) -> SimpleNamespace:
            assert request["store"] is False
            return SimpleNamespace(output_text=json.dumps(expected), status="completed")

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("REMINDER_TIME_ZONE", "UTC")
    monkeypatch.setenv("REMINDER_LOCALE", "en-US")

    result = main(["interpret", "Remind me to submit my assignment tomorrow at 8 PM."])
    captured = capsys.readouterr()

    assert result == 0
    assert json.loads(captured.out) == expected
    assert captured.err == ""
