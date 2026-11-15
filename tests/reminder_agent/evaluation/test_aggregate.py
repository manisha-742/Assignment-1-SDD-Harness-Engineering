import pytest

from reminder_agent.evaluation import aggregate_evaluation


def _layer(passed: bool = True, safety_failures: int = 0) -> dict[str, object]:
    return {
        "total": 25,
        "passed_count": 25 if passed else 24,
        "passed": passed,
        "safety_critical_failure_count": safety_failures,
    }


def _scores(count: int) -> list[dict[str, object]]:
    return [
        {"case_id": f"E{index:02d}", "total_score": 8 if index <= count else 7}
        for index in range(1, 26)
    ]


def test_aggregate_passes_at_fixed_22_of_25_semantic_threshold() -> None:
    result = aggregate_evaluation(_layer(), _layer(), _scores(22))

    assert result["status"] == "PASS"
    assert result["semantic_pass_count"] == 22
    assert result["semantic_required_count"] == 22
    assert result["safety_critical_failure_count"] == 0


def test_aggregate_fails_at_21_semantic_passes() -> None:
    result = aggregate_evaluation(_layer(), _layer(), _scores(21))

    assert result["status"] == "FAIL"


def test_aggregate_fails_for_any_layer_failure_or_safety_failure() -> None:
    assert (
        aggregate_evaluation(_layer(False), _layer(), _scores(25))["status"] == "FAIL"
    )
    assert (
        aggregate_evaluation(_layer(), _layer(True, 1), _scores(25))["status"] == "FAIL"
    )
    semantic = _scores(25)
    semantic[0]["safety_critical_failure"] = True
    result = aggregate_evaluation(_layer(), _layer(), semantic)
    assert result["status"] == "FAIL"
    assert result["safety_critical_failure_count"] == 1


def test_aggregate_threshold_cannot_be_overridden() -> None:
    with pytest.raises(TypeError):
        aggregate_evaluation(_layer(), _layer(), _scores(25), semantic_threshold=0.5)
