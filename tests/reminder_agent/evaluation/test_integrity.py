import json
import shutil
from pathlib import Path

import pytest

import reminder_agent.evaluation as evaluation
from reminder_agent.evaluation import (
    EvaluationIntegrityError,
    load_verified_dataset,
)
from reminder_agent.validation import load_output_schema

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "tests" / "data" / "reminder-evaluation-cases.json"


@pytest.mark.parametrize("mutation", ["delete-case", "change-expected-outcome"])
def test_dataset_integrity_rejects_case_deletion_or_expected_fact_changes(
    mutation: str, tmp_path, monkeypatch
) -> None:
    modified = tmp_path / "cases.json"
    shutil.copyfile(DATASET, modified)
    cases = json.loads(modified.read_text(encoding="utf-8"))
    if mutation == "delete-case":
        cases.pop()
    else:
        cases[0]["expected"]["schedule"]["date"] = "2026-11-17"
    modified.write_text(json.dumps(cases), encoding="utf-8")
    monkeypatch.setattr(evaluation, "DATASET_PATH", modified)

    with pytest.raises(EvaluationIntegrityError, match="digest"):
        load_verified_dataset(modified)


def test_snooze_minimum_and_semantic_threshold_remain_fixed() -> None:
    assert load_output_schema()["properties"]["snooze_duration_minutes"]["minimum"] == 1
    assert evaluation.SEMANTIC_THRESHOLD == 0.85
    assert evaluation.SEMANTIC_CASE_PASS_SCORE == 8
