import json
import re
from pathlib import Path

import pytest

from reminder_agent.evaluation import (
    EvaluationIntegrityError,
    load_verified_dataset,
)

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "tests" / "data" / "reminder-evaluation-cases.json"


def _cases() -> list[dict[str, object]]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def test_dataset_preserves_all_25_cases_and_fixed_contexts() -> None:
    cases = _cases()

    assert len(cases) == 25
    assert [case["case_id"] for case in cases] == [
        f"E{index:02d}" for index in range(1, 26)
    ]
    assert all(
        set(case["context"]) == {"reference_instant", "time_zone", "locale"}
        for case in cases
    )
    assert all(case["context"]["reference_instant"] for case in cases)


def test_dataset_has_required_category_coverage() -> None:
    categories = {category for case in _cases() for category in case["categories"]}

    assert {
        "ordinary",
        "explicit-date",
        "relative-date",
        "explicit-time",
        "today",
        "tomorrow",
        "tonight",
        "noon",
        "midnight",
        "date-time-boundary",
        "invalid-date",
        "ambiguous-numeric-date",
        "past-time",
        "missing-time",
        "missing-task",
        "malformed",
        "unsupported",
        "reschedule",
        "snooze",
        "adversarial",
    } <= categories


def test_e22_and_e25_are_distinct_canonical_malformed_cases() -> None:
    cases = {case["case_id"]: case for case in _cases()}

    assert cases["E22"]["input"] == "???"
    assert cases["E25"]["input"] == ""


def test_every_case_has_expected_facts_and_safety_assertions() -> None:
    for case in _cases():
        assert set(case) == {
            "case_id",
            "categories",
            "input",
            "context",
            "expected",
            "allowed_normalizations",
            "safety_assertions",
        }
        assert set(case["expected"]) == {
            "intent",
            "task",
            "target",
            "schedule",
            "needs_clarification",
            "clarification_topics",
        }
        assert case["safety_assertions"]


def test_committed_dataset_has_no_real_looking_provider_key() -> None:
    assert (
        re.search(r"sk-[A-Za-z0-9]{20,}", DATASET.read_text(encoding="utf-8")) is None
    )


def test_live_dataset_loader_verifies_the_pinned_corpus() -> None:
    assert len(load_verified_dataset()) == 25


def test_live_dataset_loader_rejects_unapproved_or_modified_corpus(
    tmp_path, monkeypatch
) -> None:
    with pytest.raises(EvaluationIntegrityError):
        load_verified_dataset(tmp_path / "other.json")

    import reminder_agent.evaluation as evaluation

    monkeypatch.setattr(evaluation, "DATASET_SHA256", "0" * 64)
    with pytest.raises(EvaluationIntegrityError, match="digest"):
        load_verified_dataset()
