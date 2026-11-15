import json
from types import SimpleNamespace

import pytest

from reminder_agent.evaluation import (
    DATASET_PATH,
    finalize_evaluation,
    run_evaluation,
)
from reminder_agent.semantic_scoring import RUBRIC_CRITERIA, InvalidSemanticScore


def _case_output(case: dict[str, object]) -> dict[str, object]:
    expected = case["expected"]
    schedule = expected["schedule"]
    clarification = expected["needs_clarification"]
    topics = expected["clarification_topics"]
    questions = {
        "task": "What task should I remind you about?",
        "target": "Which reminder should I change?",
        "time": "What time should I use?",
        "date": "What date should I use?",
        "confirmation": "Would you like to confirm or correct the elapsed time?",
        "snooze_duration": "How many minutes should I snooze the reminder?",
    }
    if set(topics) == {"date", "time"}:
        question = "What date and time should I use?"
    else:
        question = questions[topics[0]] if topics else None
    task = expected["task"]
    target = expected["target"]
    return {
        "intent": expected["intent"],
        "task": " ".join(task["required_terms"]) if task is not None else None,
        "date": schedule["date"],
        "time": schedule["time"],
        "needs_clarification": clarification,
        "clarification_question": question,
        "target_reminder": (
            " ".join(target["required_terms"]) if target is not None else None
        ),
        "snooze_duration_minutes": schedule.get("snooze_duration_minutes"),
    }


def _create_run(tmp_path, monkeypatch, *, include_review: bool = True):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    outputs = {case["input"]: _case_output(case) for case in cases}

    class FakeResponses:
        def create(self, **request: object) -> SimpleNamespace:
            return SimpleNamespace(
                output_text=json.dumps(outputs[request["input"]]),
                status="completed",
            )

    class FakeClient:
        responses = FakeResponses()

    run_dir = run_evaluation(DATASET_PATH, tmp_path, client=FakeClient())
    case_ids = [case["case_id"] for case in cases]
    reviews = [
        {
            "case_id": case_id,
            "scorer": "synthetic test reviewer",
            "scores": {criterion: 2 for criterion in RUBRIC_CRITERIA},
            "rationales": {
                criterion: "Synthetic fixture rationale."
                for criterion in RUBRIC_CRITERIA
            },
            "disputed": False,
            "second_review": None,
        }
        for case_id in case_ids
    ]
    if include_review:
        (run_dir / "semantic-review.json").write_text(
            json.dumps(reviews), encoding="utf-8"
        )
    return run_dir


def test_finalize_computes_aggregate_without_making_human_decision(
    tmp_path, monkeypatch
) -> None:
    run_dir = _create_run(tmp_path, monkeypatch)

    summary = finalize_evaluation(run_dir)

    assert summary["aggregate"]["status"] == "PASS"
    assert summary["human_final_decision"] == "PENDING"
    assert (run_dir / "final-summary.json").is_file()

    with pytest.raises(FileExistsError):
        finalize_evaluation(run_dir)


def test_finalize_requires_a_complete_human_review_record(
    tmp_path, monkeypatch
) -> None:
    run_dir = _create_run(tmp_path, monkeypatch, include_review=False)

    with pytest.raises(InvalidSemanticScore, match="semantic-review.json"):
        finalize_evaluation(run_dir)


def test_finalize_does_not_overwrite_prior_run_files(tmp_path, monkeypatch) -> None:
    run_dir = _create_run(tmp_path, monkeypatch)
    previous = (run_dir / "layer1.json").read_text(encoding="utf-8")
    (run_dir / "semantic-review.json").write_text("[]", encoding="utf-8")

    with pytest.raises(InvalidSemanticScore):
        finalize_evaluation(run_dir)

    assert (run_dir / "layer1.json").read_text(encoding="utf-8") == previous


def test_finalize_fails_on_safety_critical_semantic_zero(tmp_path, monkeypatch) -> None:
    run_dir = _create_run(tmp_path, monkeypatch)
    review_path = run_dir / "semantic-review.json"
    reviews = json.loads(review_path.read_text(encoding="utf-8"))
    reviews[4]["scores"]["handling_of_ambiguity"] = 0
    review_path.write_text(json.dumps(reviews), encoding="utf-8")

    summary = finalize_evaluation(run_dir)

    assert summary["aggregate"]["status"] == "FAIL"
    assert summary["aggregate"]["safety_critical_failure_count"] == 1
