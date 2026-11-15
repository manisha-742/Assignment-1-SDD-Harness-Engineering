import json
from types import SimpleNamespace

import pytest


@pytest.fixture
def stub_client_factory(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")

    def create(output: dict[str, object]) -> SimpleNamespace:
        def respond(**request: object) -> SimpleNamespace:
            return SimpleNamespace(output_text=json.dumps(output), status="completed")

        return SimpleNamespace(
            responses=SimpleNamespace(create=respond),
        )

    return create
