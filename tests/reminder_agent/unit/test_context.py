from datetime import datetime, timezone

import pytest

from reminder_agent.context import ContextConfigurationError, RuntimeContext


def test_runtime_context_requires_configured_iana_time_zone() -> None:
    with pytest.raises(ContextConfigurationError, match="REMINDER_TIME_ZONE"):
        RuntimeContext.from_environment({})


def test_runtime_context_uses_configured_zone_and_locale() -> None:
    instant = datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)

    context = RuntimeContext.from_environment(
        {"REMINDER_TIME_ZONE": "America/Los_Angeles", "REMINDER_LOCALE": "en-US"},
        now=instant,
    )

    assert context.reference_instant.isoformat() == "2026-11-15T01:00:00-08:00"
    assert context.time_zone == "America/Los_Angeles"
    assert context.locale == "en-US"
    assert context.source == "runtime"


def test_runtime_context_uses_optional_configured_reference_instant() -> None:
    context = RuntimeContext.from_environment(
        {
            "REMINDER_TIME_ZONE": "America/Los_Angeles",
            "REMINDER_LOCALE": "en-US",
            "REMINDER_REFERENCE_INSTANT": "2026-11-15T09:00:00Z",
        }
    )

    assert context.reference_instant.isoformat() == "2026-11-15T01:00:00-08:00"


def test_runtime_context_rejects_malformed_configured_reference_instant() -> None:
    with pytest.raises(ContextConfigurationError, match="REMINDER_REFERENCE_INSTANT"):
        RuntimeContext.from_environment(
            {
                "REMINDER_TIME_ZONE": "UTC",
                "REMINDER_REFERENCE_INSTANT": "2026-11-15T09:00:00",
            }
        )


def test_evaluation_context_uses_fixed_case_values() -> None:
    context = RuntimeContext.fixed("2026-11-15T09:00:00Z", "UTC", None)

    assert context.reference_instant.isoformat() == "2026-11-15T09:00:00+00:00"
    assert context.locale is None
    assert context.source == "evaluation"


def test_naive_reference_instant_is_rejected() -> None:
    with pytest.raises(ContextConfigurationError, match="timezone-aware"):
        RuntimeContext.from_environment(
            {"REMINDER_TIME_ZONE": "UTC"},
            now=datetime(2026, 11, 15, 9, 0),
        )


def test_invalid_iana_zone_is_rejected() -> None:
    with pytest.raises(ContextConfigurationError, match="IANA"):
        RuntimeContext.fixed("2026-11-15T09:00:00Z", "Not/AZone", None)
