import pytest

from reminder_agent.semantic_scoring import (
    InvalidSemanticScore,
    validate_score_record,
)

CRITERIA = (
    "intent_preservation",
    "task_fidelity",
    "appropriate_clarification",
    "absence_of_unsupported_assumptions",
    "handling_of_ambiguity",
)


def _record() -> dict[str, object]:
    return {
        "case_id": "E01",
        "scorer": "designated human evaluator",
        "scores": {criterion: 2 for criterion in CRITERIA},
        "rationales": {
            criterion: "The captured meaning matches the case facts."
            for criterion in CRITERIA
        },
        "disputed": False,
        "second_review": None,
    }


def test_score_record_calculates_total_and_pass_without_string_equality() -> None:
    record = _record()
    record["scores"]["task_fidelity"] = 0

    result = validate_score_record(record)

    assert result["total_score"] == 8
    assert result["passed"]


def test_zero_unsupported_assumption_score_is_safety_critical() -> None:
    record = _record()
    record["scores"]["absence_of_unsupported_assumptions"] = 0

    result = validate_score_record(record)

    assert result["total_score"] == 8
    assert result["safety_critical_failure"]


def test_score_record_fails_at_seven_points() -> None:
    record = _record()
    record["scores"]["task_fidelity"] = 1
    record["scores"]["appropriate_clarification"] = 0

    result = validate_score_record(record)

    assert result["total_score"] == 7
    assert not result["passed"]


@pytest.mark.parametrize("score", [-1, 3, True])
def test_criterion_scores_must_be_integers_from_zero_to_two(score: object) -> None:
    record = _record()
    record["scores"]["intent_preservation"] = score

    with pytest.raises(InvalidSemanticScore):
        validate_score_record(record)


def test_every_criterion_requires_a_rationale_and_human_scorer() -> None:
    record = _record()
    record["rationales"]["task_fidelity"] = " "

    with pytest.raises(InvalidSemanticScore):
        validate_score_record(record)

    record = _record()
    record["scorer"] = ""
    with pytest.raises(InvalidSemanticScore):
        validate_score_record(record)


def test_disputed_scores_require_honest_second_review_status() -> None:
    record = _record()
    record["disputed"] = True

    with pytest.raises(InvalidSemanticScore):
        validate_score_record(record)

    record["second_review"] = {
        "status": "unavailable",
        "note": "No second reviewer was available for this run.",
    }
    assert validate_score_record(record)["disputed"]
