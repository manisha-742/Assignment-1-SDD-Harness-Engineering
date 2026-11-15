import json
from pathlib import Path

from reminder_agent.evaluation import evaluate_layer2

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads(
    (ROOT / "tests" / "data" / "reminder-evaluation-cases.json").read_text(
        encoding="utf-8"
    )
)


def _valid_outputs() -> list[dict[str, object]]:
    questions = {
        "task": "What task should I remind you about?",
        "target": "Which reminder should I change?",
        "time": "What time should I use?",
        "date": "What date should I use?",
        "confirmation": "Would you like to confirm or correct the elapsed time?",
        "snooze_duration": "How many minutes should I snooze the reminder?",
    }
    outputs = []
    for case in CASES:
        expected = case["expected"]
        task = expected["task"]
        target = expected["target"]
        schedule = expected["schedule"]
        clarification = expected["needs_clarification"]
        outputs.append(
            {
                "intent": expected["intent"],
                "task": (
                    " ".join(task["required_terms"]) if task is not None else None
                ),
                "date": schedule["date"],
                "time": schedule["time"],
                "needs_clarification": clarification,
                "clarification_question": (
                    (
                        "What date and time should I use?"
                        if set(expected["clarification_topics"]) == {"date", "time"}
                        else questions[expected["clarification_topics"][0]]
                    )
                    if clarification
                    else None
                ),
                "target_reminder": (
                    " ".join(target["required_terms"]) if target is not None else None
                ),
                "snooze_duration_minutes": schedule.get("snooze_duration_minutes"),
            }
        )
    return outputs


def test_layer2_accepts_case_facts_and_semantically_equivalent_task_wording() -> None:
    outputs = _valid_outputs()
    outputs[0]["task"] = "submit the assignment"

    report = evaluate_layer2(CASES, outputs)

    assert report["passed"]
    assert report["passed_count"] == 25


def test_layer2_detects_fabricated_date_and_safety_failure() -> None:
    outputs = _valid_outputs()
    outputs[23]["date"] = "2026-11-16"

    report = evaluate_layer2(CASES, outputs)

    assert not report["passed"]
    result = report["results"][23]
    assert not result["passed"]
    assert result["safety_critical_failures"]


def test_layer2_checks_target_schedule_and_clarification_per_case() -> None:
    outputs = _valid_outputs()
    outputs[16]["target_reminder"] = "a reminder"
    outputs[15]["time"] = "15:30"
    outputs[7]["needs_clarification"] = False

    report = evaluate_layer2(CASES, outputs)

    assert not report["passed"]
    assert not report["results"][16]["passed"]
    assert not report["results"][15]["passed"]
    assert not report["results"][7]["passed"]


def test_layer2_rejects_claims_that_a_reminder_was_changed() -> None:
    outputs = _valid_outputs()
    outputs[15]["task"] = "dentist appointment was updated"

    report = evaluate_layer2(CASES, outputs)

    assert not report["passed"]
    assert report["results"][15]["safety_critical_failures"]
