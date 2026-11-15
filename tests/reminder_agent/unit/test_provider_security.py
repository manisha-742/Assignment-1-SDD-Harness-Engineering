import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from openai import OpenAIError

from reminder_agent.cli import main
from reminder_agent.context import RuntimeContext
from reminder_agent.interpreter import (
    GROQ_BASE_URL,
    ProviderConfigurationError,
    ProviderError,
    interpret_request,
)

ROOT = Path(__file__).resolve().parents[3]
SYNTHETIC_KEY = "test-secret-sentinel-not-a-real-key"
CREATE_OUTPUT = {
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
    def __init__(
        self, output: str | None = None, error: Exception | None = None
    ) -> None:
        self.output = output or json.dumps(CREATE_OUTPUT)
        self.error = error
        self.request: dict[str, object] | None = None

    def create(self, **request: object) -> SimpleNamespace:
        self.request = request
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output_text=self.output, status="completed")


def _context() -> RuntimeContext:
    return RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", "en-US")


def test_missing_api_key_fails_before_client_creation(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", SYNTHETIC_KEY)

    with pytest.raises(ProviderConfigurationError, match="GROQ_API_KEY"):
        interpret_request("remind me tomorrow", _context())


def test_groq_key_and_base_url_are_used(monkeypatch) -> None:
    captured: list[tuple[str, str]] = []
    responses = FakeResponses()

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            captured.append((api_key, base_url))
            self.responses = responses

    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", "not-the-approved-name")
    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    interpret_request("Remind me tomorrow at 8 PM to submit my assignment.", _context())

    assert captured == [(SYNTHETIC_KEY, GROQ_BASE_URL)]
    assert responses.request is not None
    assert responses.request["store"] is False


def test_provider_errors_are_sanitized_and_not_logged(monkeypatch, caplog) -> None:
    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    responses = FakeResponses(error=OpenAIError(f"provider rejected {SYNTHETIC_KEY}"))

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = responses

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    with pytest.raises(ProviderError) as error:
        interpret_request("request", _context())

    assert SYNTHETIC_KEY not in str(error.value)
    assert SYNTHETIC_KEY not in caplog.text


def test_escaped_api_key_in_provider_json_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    escaped_key = "".join(f"\\u{ord(character):04x}" for character in SYNTHETIC_KEY)
    raw_output = json.dumps(CREATE_OUTPUT).replace("submit my assignment", escaped_key)
    responses = FakeResponses(output=raw_output)

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = responses

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    with pytest.raises(ProviderError) as error:
        interpret_request(
            "Remind me to submit my assignment tomorrow at 8 PM.", _context()
        )

    assert SYNTHETIC_KEY not in str(error.value)


@pytest.mark.parametrize(
    ("user_request", "provider_output", "expected"),
    [
        (
            "Remind me to take my book tonight.",
            dict(
                CREATE_OUTPUT,
                task="take my book",
                date="2026-11-15",
                time=None,
                needs_clarification=False,
            ),
            {
                "intent": "create_reminder",
                "task": "take my book",
                "date": "2026-11-15",
                "time": None,
                "needs_clarification": True,
            },
        ),
        (
            "Remind me to call the dentist tomorrow.",
            dict(
                CREATE_OUTPUT,
                task="call the dentist",
                date="2026-11-16",
                time=None,
                needs_clarification=False,
            ),
            {
                "intent": "create_reminder",
                "task": "call the dentist",
                "date": "2026-11-16",
                "time": None,
                "needs_clarification": True,
            },
        ),
        (
            "Snooze my call Mom reminder for 10 minutes.",
            dict(
                CREATE_OUTPUT,
                intent="snooze_reminder",
                task=None,
                date=None,
                time=None,
                target_reminder=None,
                snooze_duration_minutes=None,
            ),
            {
                "intent": "snooze_reminder",
                "task": "call Mom",
                "date": "2026-11-15",
                "time": "09:10",
                "needs_clarification": False,
                "target_reminder": "call Mom reminder",
                "snooze_duration_minutes": 10,
            },
        ),
        (
            "What is the weather tomorrow?",
            dict(
                CREATE_OUTPUT,
                intent="unsupported",
                task="check the weather",
                date="2026-11-16",
            ),
            {
                "intent": "unsupported",
                "task": None,
                "date": None,
                "time": None,
                "needs_clarification": False,
            },
        ),
    ],
)
def test_request_constraints_repair_schema_valid_provider_output(
    monkeypatch, user_request, provider_output, expected
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    responses = FakeResponses(output=json.dumps(provider_output))

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = responses

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    output = interpret_request(user_request, _context()).to_dict()

    for field, value in expected.items():
        assert output[field] == value


def test_provider_output_still_requires_the_complete_schema(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    malformed_output = dict(CREATE_OUTPUT)
    del malformed_output["task"]
    responses = FakeResponses(output=json.dumps(malformed_output))

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = responses

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    with pytest.raises(ProviderError, match="invalid reminder response"):
        interpret_request(
            "Remind me to submit my assignment tomorrow at 8 PM.", _context()
        )


def test_api_key_is_never_in_application_output(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GROQ_API_KEY", SYNTHETIC_KEY)
    monkeypatch.setenv("REMINDER_TIME_ZONE", "UTC")
    monkeypatch.setenv("REMINDER_LOCALE", "en-US")
    responses = FakeResponses()

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.responses = responses

    monkeypatch.setattr("reminder_agent.interpreter.OpenAI", FakeClient)

    exit_code = main(
        ["interpret", "Remind me tomorrow at 8 PM to submit my assignment."]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == CREATE_OUTPUT
    assert SYNTHETIC_KEY not in captured.out
    assert SYNTHETIC_KEY not in captured.err


def test_missing_key_cli_error_is_clear_and_contains_no_secret(
    monkeypatch, capsys
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("REMINDER_TIME_ZONE", "UTC")
    monkeypatch.setenv("OPENAI_API_KEY", SYNTHETIC_KEY)

    exit_code = main(["interpret", "Remind me tomorrow at 8 PM to submit my work."])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "GROQ_API_KEY" in captured.err
    assert SYNTHETIC_KEY not in captured.out + captured.err


def test_test_fixtures_and_evaluation_data_contain_no_real_api_keys() -> None:
    credential_pattern = re.compile(r"sk-[A-Za-z0-9]{20,}")
    paths = [
        ROOT / "tests" / "data" / "reminder-evaluation-cases.json",
        *(ROOT / "tests" / "reminder_agent").rglob("*"),
    ]

    for path in paths:
        if path.is_file() and path.suffix not in {".pyc"}:
            assert credential_pattern.search(path.read_text(encoding="utf-8")) is None
