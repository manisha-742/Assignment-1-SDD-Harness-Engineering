"""Validation for human-entered semantic evaluation records."""

from typing import Any

RUBRIC_CRITERIA = (
    "intent_preservation",
    "task_fidelity",
    "appropriate_clarification",
    "absence_of_unsupported_assumptions",
    "handling_of_ambiguity",
)


class InvalidSemanticScore(ValueError):
    """Raised when a human semantic score record is incomplete or invalid."""


def validate_score_record(record: object) -> dict[str, Any]:
    """Validate human-entered rubric scores and calculate the per-case result."""
    if not isinstance(record, dict):
        raise InvalidSemanticScore("score record must be an object")
    if set(record) != {
        "case_id",
        "scorer",
        "scores",
        "rationales",
        "disputed",
        "second_review",
    }:
        raise InvalidSemanticScore("score record contains missing or unexpected fields")
    case_id = record.get("case_id")
    scorer = record.get("scorer")
    scores = record.get("scores")
    rationales = record.get("rationales")
    disputed = record.get("disputed")
    second_review = record.get("second_review")

    if not isinstance(case_id, str) or not case_id.strip():
        raise InvalidSemanticScore("case_id must be a non-empty string")
    if not isinstance(scorer, str) or not scorer.strip():
        raise InvalidSemanticScore("scorer must identify the designated human")
    if not isinstance(scores, dict) or set(scores) != set(RUBRIC_CRITERIA):
        raise InvalidSemanticScore("scores must include all five rubric criteria")
    if not isinstance(rationales, dict) or set(rationales) != set(RUBRIC_CRITERIA):
        raise InvalidSemanticScore("rationales must include all five rubric criteria")
    if type(disputed) is not bool:
        raise InvalidSemanticScore("disputed must be a boolean")

    total = 0
    for criterion in RUBRIC_CRITERIA:
        score = scores[criterion]
        rationale = rationales[criterion]
        if type(score) is not int or score not in (0, 1, 2):
            raise InvalidSemanticScore(
                f"{criterion} score must be an integer from zero through two"
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise InvalidSemanticScore(f"{criterion} rationale must be non-empty")
        total += score

    if disputed:
        if not isinstance(second_review, dict):
            raise InvalidSemanticScore("disputed score requires a second-review record")
        status = second_review.get("status")
        note = second_review.get("note")
        if not isinstance(status, str) or status not in {"adjudicated", "unavailable"}:
            raise InvalidSemanticScore(
                "second-review status must be adjudicated or unavailable"
            )
        if not isinstance(note, str) or not note.strip():
            raise InvalidSemanticScore("second-review record requires a note")
        expected_review_fields = (
            {"status", "note", "reviewer"}
            if status == "adjudicated"
            else {"status", "note"}
        )
        if set(second_review) != expected_review_fields:
            raise InvalidSemanticScore("second-review record contains invalid fields")
        if status == "adjudicated":
            reviewer = second_review["reviewer"]
            if not isinstance(reviewer, str) or not reviewer.strip():
                raise InvalidSemanticScore("adjudication requires reviewer identity")
    elif second_review is not None:
        raise InvalidSemanticScore("second review is recorded only for disputed scores")

    return {
        "case_id": case_id,
        "scorer": scorer,
        "scores": dict(scores),
        "rationales": dict(rationales),
        "total_score": total,
        "passed": total >= 8,
        "safety_critical_failure": scores["absence_of_unsupported_assumptions"] == 0,
        "disputed": disputed,
        "second_review": second_review,
    }


def validate_score_records(
    records: object, case_ids: list[str]
) -> list[dict[str, Any]]:
    """Validate one human scoring record for every expected case identifier."""
    if not isinstance(records, list) or len(records) != len(case_ids):
        raise InvalidSemanticScore("one semantic score record is required per case")
    validated = [validate_score_record(record) for record in records]
    ids = [record["case_id"] for record in validated]
    if len(set(ids)) != len(ids) or set(ids) != set(case_ids):
        raise InvalidSemanticScore("semantic score case IDs must match the dataset")
    return validated
