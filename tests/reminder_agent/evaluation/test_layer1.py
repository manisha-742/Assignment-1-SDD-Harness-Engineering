import json
from pathlib import Path

import pytest

from reminder_agent.evaluation import evaluate_layer1

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads(
    (ROOT / "tests" / "data" / "reminder-evaluation-cases.json").read_text(
        encoding="utf-8"
    )
)


def _valid_output(case: dict[str, object]) -> dict[str, object]:
    expected = case["expected"]
    task = expected["task"]
    target = expected["target"]
    task_text = " ".join(task["required_terms"]) if task is not None else None
    target_text = " ".join(target["required_terms"]) if target is not None else None
    schedule = expected["schedule"]
    clarification = expected["needs_clarification"]
    return {
        "intent": expected["intent"],
        "task": task_text,
        "date": schedule["date"],
        "time": schedule["time"],
        "needs_clarification": clarification,
        "clarification_question": (
            "Please clarify the reminder details." if clarification else None
        ),
        "target_reminder": target_text,
        "snooze_duration_minutes": schedule.get("snooze_duration_minutes"),
    }


def test_layer1_applies_shared_validation_to_all_cases() -> None:
    report = evaluate_layer1(CASES, [_valid_output(case) for case in CASES])

    assert report["total"] == 25
    assert report["passed_count"] == 25
    assert report["passed"]
    assert all(result["passed"] for result in report["results"])
    assert {result["case_id"] for result in report["results"]} == {
        case["case_id"] for case in CASES
    }


def test_layer1_records_schema_failure_per_case() -> None:
    outputs = [_valid_output(case) for case in CASES]
    outputs[3]["snooze_duration_minutes"] = 0

    report = evaluate_layer1(CASES, outputs)

    assert report["passed_count"] == 24
    assert not report["passed"]
    assert report["results"][3]["case_id"] == "E04"
    assert not report["results"][3]["passed"]
    assert report["results"][3]["errors"]


def test_layer1_parses_raw_json_before_using_shared_validator() -> None:
    outputs = [_valid_output(case) for case in CASES]
    outputs[0] = json.dumps(outputs[0])

    report = evaluate_layer1(CASES, outputs)

    assert report["results"][0]["passed"]


def test_layer1_rejects_malformed_json_without_aborting_other_cases() -> None:
    outputs = [_valid_output(case) for case in CASES]
    outputs[0] = '{"intent":'

    report = evaluate_layer1(CASES, outputs)

    assert not report["results"][0]["passed"]
    assert all(result["passed"] for result in report["results"][1:])


@pytest.mark.parametrize(
    "change",
    [
        lambda output: output.pop("task"),
        lambda output: output.update(extra="not allowed"),
        lambda output: output.update(intent="unsupported"),
        lambda output: output.update(needs_clarification="false"),
        lambda output: output.update(time=None),
        lambda output: output.update(date="2026-02-30"),
        lambda output: output.update(time="24:00"),
        lambda output: output.update(snooze_duration_minutes=0),
        lambda output: output.update(snooze_duration_minutes=-1),
        lambda output: output.update(target_reminder="invalid for create intent"),
    ],
)
def test_layer1_rejects_structural_and_cross_field_regressions(change) -> None:
    outputs = [_valid_output(case) for case in CASES]
    change(outputs[0])

    report = evaluate_layer1(CASES, outputs)

    assert not report["results"][0]["passed"]
    assert report["results"][0]["errors"]
    assert all(result["passed"] for result in report["results"][1:])
