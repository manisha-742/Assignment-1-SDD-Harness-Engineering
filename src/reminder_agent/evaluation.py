"""Deterministic evaluation layers and fixed aggregate acceptance policy."""

import hashlib
import json
import os
import re
import subprocess  # nosec B404
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from reminder_agent.context import RuntimeContext
from reminder_agent.evidence import (
    DEFAULT_EVIDENCE_ROOT,
    assert_credential_free,
    create_run_directory,
    write_json_evidence,
)
from reminder_agent.interpreter import (
    DEFAULT_MODEL,
    ProviderConfigurationError,
    ProviderError,
    create_provider_client,
    interpret_request,
)
from reminder_agent.semantic_scoring import (
    RUBRIC_CRITERIA,
    InvalidSemanticScore,
    validate_score_records,
)
from reminder_agent.validation import (
    SCHEMA_PATH,
    InvalidReminderOutput,
    validate_output,
)

SEMANTIC_THRESHOLD = 0.85
SEMANTIC_CASE_PASS_SCORE = 8
DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "data"
    / "reminder-evaluation-cases.json"
)
DATASET_SHA256 = "3193669b52b0605edb21678119f6a52bb06c8c500e53f73920701f439f64e3b0"
EXPECTED_CASE_IDS = tuple(f"E{index:02d}" for index in range(1, 26))
EXECUTION_CLAIM = re.compile(
    r"\b(?:stored|saved|created|updated|changed|rescheduled successfully|"
    r"already exists|is unique)\b",
    re.IGNORECASE,
)
TOPIC_TERMS = {
    "task": (("task",), ("action",), ("remind",), ("do",)),
    "target": (("target",), ("which", "reminder"), ("what", "reminder")),
    "date": (("date",), ("day",), ("calendar",), ("when",)),
    "time": (("time",), ("clock",), ("am",), ("pm",)),
    "snooze_duration": (("duration",), ("minutes",), ("long",)),
    "confirmation": (("confirm",), ("correct",), ("passed",), ("new", "time")),
}


class EvaluationIntegrityError(ValueError):
    """Raised when the approved evaluation corpus has been altered."""


class EvaluationMetadataError(RuntimeError):
    """Raised when source revision metadata cannot be captured."""


def load_verified_dataset(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    """Load only the approved, hash-pinned synthetic evaluation corpus."""
    if path.resolve() != DATASET_PATH.resolve():
        raise EvaluationIntegrityError(
            "live evaluation is restricted to the approved version-controlled dataset"
        )
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != DATASET_SHA256:
        raise EvaluationIntegrityError(
            "approved evaluation dataset digest does not match"
        )
    cases = json.loads(contents)
    if (
        not isinstance(cases, list)
        or tuple(case.get("case_id") for case in cases if isinstance(case, dict))
        != EXPECTED_CASE_IDS
    ):
        raise EvaluationIntegrityError("approved dataset must contain E01 through E25")
    case_map = {case["case_id"]: case for case in cases}
    if case_map["E22"]["input"] != "???" or case_map["E25"]["input"] != "":
        raise EvaluationIntegrityError("canonical malformed-input cases were changed")
    return cases


def _decode_output(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


def evaluate_layer1(cases: list[dict[str, Any]], outputs: list[Any]) -> dict[str, Any]:
    """Apply the shared schema validator to each captured case output."""
    results = []
    for case, raw_output in zip(cases, outputs, strict=True):
        try:
            validate_output(_decode_output(raw_output))
        except (json.JSONDecodeError, InvalidReminderOutput, JsonSchemaValidationError):
            errors = ["output failed structured schema or invariant validation"]
            passed = False
        else:
            errors = []
            passed = True
        results.append({"case_id": case["case_id"], "passed": passed, "errors": errors})
    passed_count = sum(result["passed"] for result in results)
    return {
        "layer": 1,
        "total": len(results),
        "passed_count": passed_count,
        "passed": passed_count == len(results),
        "results": results,
    }


def _normalized_tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold()))


def _fact_matches(
    actual: Any, expected: Any, allowed_phrases: list[str] | None = None
) -> bool:
    if expected is None:
        return actual is None
    if not isinstance(actual, str):
        return False
    if isinstance(expected, dict):
        required_terms = expected.get("required_terms", [])
        actual_tokens = _normalized_tokens(actual)
        if all(
            set(_normalized_tokens(term)) <= actual_tokens for term in required_terms
        ):
            return True
    if allowed_phrases:
        normalized_actual = " ".join(re.findall(r"\w+", actual.casefold()))
        return any(
            normalized_actual == " ".join(re.findall(r"\w+", phrase.casefold()))
            for phrase in allowed_phrases
        )
    return False


def _asks_for(question: Any, topics: list[str]) -> bool:
    if not isinstance(question, str) or not question.strip():
        return False
    tokens = _normalized_tokens(question)
    return all(
        any(set(term) <= tokens for term in TOPIC_TERMS.get(topic, ()))
        for topic in topics
    )


def evaluate_layer2(cases: list[dict[str, Any]], outputs: list[Any]) -> dict[str, Any]:
    """Compare every output with its pre-recorded facts and safety properties."""
    results = []
    for case, raw_output in zip(cases, outputs, strict=True):
        safety_failures: list[str] = []
        checks: dict[str, bool] = {}
        try:
            output = _decode_output(raw_output)
        except json.JSONDecodeError:
            output = None

        expected = case["expected"]
        if not isinstance(output, dict):
            checks = {
                "intent_matches": False,
                "task_matches": False,
                "target_matches": False,
                "schedule_matches": False,
                "clarification_matches": False,
                "clarification_question_focused": False,
                "no_execution_claims": False,
            }
            safety_failures.append("captured output is not a JSON object")
        else:
            checks["intent_matches"] = output.get("intent") == expected["intent"]
            if not checks["intent_matches"]:
                safety_failures.append("intent contradicts the case")

            normalizations = case.get("allowed_normalizations", {})
            checks["task_matches"] = _fact_matches(
                output.get("task"), expected["task"], normalizations.get("task")
            )
            if not checks["task_matches"]:
                safety_failures.append("task is missing, changed, or fabricated")

            checks["target_matches"] = _fact_matches(
                output.get("target_reminder"),
                expected["target"],
                normalizations.get("target"),
            )
            if not checks["target_matches"]:
                safety_failures.append("target is missing, changed, or fabricated")

            schedule = expected["schedule"]
            schedule_fields = {
                "date": schedule["date"],
                "time": schedule["time"],
            }
            if "snooze_duration_minutes" in schedule:
                schedule_fields["snooze_duration_minutes"] = schedule[
                    "snooze_duration_minutes"
                ]
            else:
                schedule_fields["snooze_duration_minutes"] = None
            checks["schedule_matches"] = all(
                output.get(field) == value for field, value in schedule_fields.items()
            )
            if not checks["schedule_matches"]:
                safety_failures.append(
                    "schedule contains an incorrect or fabricated value"
                )

            checks["clarification_matches"] = (
                output.get("needs_clarification") is expected["needs_clarification"]
            )
            if not checks["clarification_matches"]:
                safety_failures.append("clarification decision contradicts case facts")

            checks["clarification_question_focused"] = (
                _asks_for(
                    output.get("clarification_question"),
                    expected["clarification_topics"],
                )
                if expected["needs_clarification"]
                else output.get("clarification_question") is None
            )

            claims = " ".join(
                value
                for value in (
                    output.get("task"),
                    output.get("target_reminder"),
                    output.get("clarification_question"),
                )
                if isinstance(value, str)
            )
            checks["no_execution_claims"] = EXECUTION_CLAIM.search(claims) is None
            if not checks["no_execution_claims"]:
                safety_failures.append("output claims reminder storage or modification")

        passed = all(checks.values()) and not safety_failures
        results.append(
            {
                "case_id": case["case_id"],
                "passed": passed,
                "checks": checks,
                "safety_critical_failures": safety_failures,
            }
        )

    passed_count = sum(result["passed"] for result in results)
    safety_failure_count = sum(
        len(result["safety_critical_failures"]) for result in results
    )
    return {
        "layer": 2,
        "total": len(results),
        "passed_count": passed_count,
        "passed": passed_count == len(results),
        "safety_critical_failure_count": safety_failure_count,
        "results": results,
    }


def aggregate_evaluation(
    layer1: dict[str, Any],
    layer2: dict[str, Any],
    semantic_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute the fixed 100%/100%/85%/zero-safety aggregate decision."""
    case_count = layer1["total"]
    required_semantic_count = ceil(SEMANTIC_THRESHOLD * case_count)
    semantic_scores_valid = all(
        isinstance(result.get("total_score"), int)
        and not isinstance(result.get("total_score"), bool)
        and 0 <= result["total_score"] <= 10
        for result in semantic_results
    )
    semantic_pass_count = sum(
        isinstance(result.get("total_score"), int)
        and not isinstance(result.get("total_score"), bool)
        and 0 <= result["total_score"] <= 10
        and result["total_score"] >= SEMANTIC_CASE_PASS_SCORE
        for result in semantic_results
    )
    safety_failure_count = layer2.get("safety_critical_failure_count", 0) + sum(
        result.get("safety_critical_failure") is True for result in semantic_results
    )
    complete_case_coverage = (
        layer2["total"] == case_count
        and len(semantic_results) == case_count
        and semantic_scores_valid
    )
    layer1_complete = (
        case_count > 0
        and layer1["passed_count"] == case_count
        and layer1["passed"] is True
    )
    layer2_complete = (
        layer2["total"] > 0
        and layer2["passed_count"] == layer2["total"]
        and layer2["passed"] is True
    )
    passed = (
        layer1_complete
        and layer2_complete
        and complete_case_coverage
        and semantic_pass_count >= required_semantic_count
        and safety_failure_count == 0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "case_count": case_count,
        "layer1_passed_count": layer1["passed_count"],
        "layer2_passed_count": layer2["passed_count"],
        "semantic_pass_count": semantic_pass_count,
        "semantic_required_count": required_semantic_count,
        "semantic_threshold": SEMANTIC_THRESHOLD,
        "safety_critical_failure_count": safety_failure_count,
    }


def _git_metadata() -> dict[str, Any]:
    repository_root = DATASET_PATH.parents[2]
    git_environment = os.environ.copy()
    git_environment.pop("GROQ_API_KEY", None)
    try:
        revision = subprocess.run(  # nosec B603, B607
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            env=git_environment,
        ).stdout.strip()
        status = subprocess.run(  # nosec B603, B607
            ["git", "status", "--porcelain"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            env=git_environment,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise EvaluationMetadataError(
            "Could not read the repository revision for evaluation evidence."
        ) from error
    return {"source_revision": revision, "working_tree_dirty": bool(status.strip())}


def _implementation_snapshot() -> tuple[dict[str, str], str]:
    repository_root = DATASET_PATH.parents[2]
    source_paths = sorted((repository_root / "src" / "reminder_agent").rglob("*.py"))
    source_paths.append(SCHEMA_PATH)
    snapshot = {
        path.relative_to(repository_root).as_posix(): path.read_text(encoding="utf-8")
        for path in source_paths
    }
    return snapshot, _implementation_digest(snapshot)


def _implementation_digest(snapshot: dict[str, str]) -> str:
    digest_input = json.dumps(
        snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def _json_digest(value: Any) -> str:
    digest_input = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def _load_verified_run(
    run_dir: Path,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("run_id") != run_dir.name:
        raise EvaluationIntegrityError("evidence run identity does not match")
    cases = json.loads((run_dir / "dataset.json").read_text(encoding="utf-8"))
    if (
        manifest.get("dataset_sha256") != DATASET_SHA256
        or cases != load_verified_dataset()
    ):
        raise EvaluationIntegrityError(
            "evidence dataset does not match the approved corpus"
        )
    implementation = json.loads(
        (run_dir / "implementation-source.json").read_text(encoding="utf-8")
    )
    if _implementation_digest(implementation) != manifest.get("implementation_sha256"):
        raise EvaluationIntegrityError("evidence implementation digest does not match")
    case_results = json.loads(
        (run_dir / "case-results.json").read_text(encoding="utf-8")
    )
    layer1 = json.loads((run_dir / "layer1.json").read_text(encoding="utf-8"))
    layer2 = json.loads((run_dir / "layer2.json").read_text(encoding="utf-8"))
    payloads = {
        "case_results_sha256": case_results,
        "layer1_sha256": layer1,
        "layer2_sha256": layer2,
    }
    if any(
        manifest.get(digest_field) != _json_digest(payload)
        for digest_field, payload in payloads.items()
    ):
        raise EvaluationIntegrityError(
            "evidence results do not match their run manifest"
        )
    if [result["case_id"] for result in case_results] != [
        case["case_id"] for case in cases
    ]:
        raise EvaluationIntegrityError("evidence results do not contain every case")
    for case, result in zip(cases, case_results, strict=True):
        context = case["context"]
        fixed = RuntimeContext.fixed(
            context["reference_instant"], context["time_zone"], context["locale"]
        )
        if (
            result["input"] != case["input"]
            or result["expected"] != case["expected"]
            or result["context"]
            != {
                "reference_instant": fixed.reference_instant.isoformat(),
                "time_zone": fixed.time_zone,
                "locale": fixed.locale,
            }
        ):
            raise EvaluationIntegrityError(
                "evidence case facts or fixed context changed"
            )
    outputs = [result["output"] for result in case_results]
    if (
        evaluate_layer1(cases, outputs) != layer1
        or evaluate_layer2(cases, outputs) != layer2
    ):
        raise EvaluationIntegrityError(
            "evidence evaluation results do not match outputs"
        )
    return manifest, cases, case_results, layer1, layer2


def run_evaluation(
    cases_path: Path = DATASET_PATH,
    evidence_root: Path | None = None,
    client: Any | None = None,
    repair_of: Path | None = None,
    repair_feedback_path: Path | None = None,
) -> Path:
    """Run the pinned synthetic corpus with fixed contexts and preserve evidence."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ProviderConfigurationError(
            "GROQ_API_KEY must be configured before live evaluation."
        )
    cases = load_verified_dataset(cases_path)
    if (repair_of is None) != (repair_feedback_path is None):
        raise EvaluationIntegrityError(
            "--repair-of and --repair-feedback must be supplied together"
        )
    repair_link = None
    if repair_of is not None and repair_feedback_path is not None:
        root = (evidence_root or DEFAULT_EVIDENCE_ROOT).resolve()
        prior_run = repair_of.resolve()
        if prior_run.parent != root or not prior_run.is_dir():
            raise EvaluationIntegrityError(
                "repair source must be a run directory under the evidence root"
            )
        prior_manifest, _, prior_results, _, _ = _load_verified_run(prior_run)
        source_failures = [
            {
                "case_id": result["case_id"],
                "layer1": result["layer1"],
                "layer2": result["layer2"],
                "provider_error": result["provider_error"],
            }
            for result in prior_results
            if not result["layer1"]["passed"]
            or not result["layer2"]["passed"]
            or result["provider_error"] is not None
        ]
        if not source_failures:
            raise EvaluationIntegrityError(
                "repair source must contain a genuine recorded failure"
            )
        feedback = repair_feedback_path.read_text(encoding="utf-8").strip()
        if not feedback:
            raise EvaluationIntegrityError("repair feedback must be non-empty")
        assert_credential_free(json.dumps({"repair_feedback": feedback}))
        repair_link = {
            "source_failure_run": prior_run.name,
            "source_failures": source_failures,
            "repair_feedback": feedback,
        }
    started_at = datetime.now(timezone.utc).isoformat()
    git = _git_metadata()
    implementation, implementation_digest = _implementation_snapshot()
    provider = client if client is not None else create_provider_client()
    run_dir = create_run_directory(evidence_root or DEFAULT_EVIDENCE_ROOT)
    outputs: list[Any] = []
    provider_errors: list[str | None] = []
    case_contexts = []
    for case in cases:
        context_data = case["context"]
        context = RuntimeContext.fixed(
            context_data["reference_instant"],
            context_data["time_zone"],
            context_data["locale"],
        )
        case_contexts.append(
            {
                "reference_instant": context.reference_instant.isoformat(),
                "time_zone": context.time_zone,
                "locale": context.locale,
            }
        )
        try:
            output = interpret_request(case["input"], context, client=provider)
        except (ProviderConfigurationError, ProviderError) as error:
            outputs.append(None)
            provider_errors.append(str(error))
        else:
            outputs.append(output.to_dict())
            provider_errors.append(None)

    layer1 = evaluate_layer1(cases, outputs)
    layer2 = evaluate_layer2(cases, outputs)
    case_results = []
    for index, case in enumerate(cases):
        case_results.append(
            {
                "case_id": case["case_id"],
                "input": case["input"],
                "context": case_contexts[index],
                "expected": case["expected"],
                "output": outputs[index],
                "provider_error": provider_errors[index],
                "layer1": layer1["results"][index],
                "layer2": layer2["results"][index],
            }
        )

    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    manifest = {
        "run_id": run_dir.name,
        "started_at": started_at,
        **git,
        "implementation_sha256": implementation_digest,
        "dataset_sha256": DATASET_SHA256,
        "schema_sha256": hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(),
        "case_results_sha256": _json_digest(case_results),
        "layer1_sha256": _json_digest(layer1),
        "layer2_sha256": _json_digest(layer2),
        "validator_id": "reminder-output-schema-v1",
        "rubric_id": "human-semantic-rubric-10-point-v1",
        "provider": "Groq Responses API",
        "model": model,
        "request_settings": {
            "strict_json_schema": True,
            "store": False,
        },
        "acceptance_threshold": {
            "layer1_percent": 100,
            "layer2_percent": 100,
            "layer3_percent": 85,
            "layer3_case_score_minimum": 8,
            "safety_critical_failures": 0,
        },
        "aggregate_status": "PENDING_HUMAN_SEMANTIC_REVIEW",
        "repair_of": repair_link["source_failure_run"] if repair_link else None,
        "layer1_passed": layer1["passed"],
        "layer2_passed": layer2["passed"],
        "safety_critical_failure_count": layer2["safety_critical_failure_count"],
    }
    score_template = [
        {
            "case_id": case["case_id"],
            "scorer": "",
            "scores": {criterion: None for criterion in RUBRIC_CRITERIA},
            "rationales": {criterion: "" for criterion in RUBRIC_CRITERIA},
            "disputed": False,
            "second_review": None,
        }
        for case in cases
    ]
    human_decision_template = {
        "decision": None,
        "evidence_run": run_dir.name,
        "known_limitations": [],
        "residual_risks": [],
        "reviewer": "",
    }
    write_json_evidence(run_dir, "manifest.json", manifest)
    write_json_evidence(run_dir, "implementation-source.json", implementation)
    write_json_evidence(run_dir, "dataset.json", cases)
    write_json_evidence(run_dir, "case-results.json", case_results)
    write_json_evidence(run_dir, "layer1.json", layer1)
    write_json_evidence(run_dir, "layer2.json", layer2)
    write_json_evidence(run_dir, "semantic-review-template.json", score_template)
    write_json_evidence(
        run_dir, "human-decision-template.json", human_decision_template
    )
    failures = [
        result
        for result in case_results
        if not result["layer1"]["passed"]
        or not result["layer2"]["passed"]
        or result["provider_error"] is not None
    ]
    if failures:
        write_json_evidence(run_dir, "genuine-failures.json", failures)
        write_json_evidence(
            run_dir,
            "repair-feedback-template.json",
            {
                "source_failure_run": run_dir.name,
                "case_ids": [result["case_id"] for result in failures],
                "feedback": "",
            },
        )
    if repair_link is not None:
        write_json_evidence(run_dir, "repair-link.json", repair_link)
    return run_dir


def run_offline_replay(source_run: Path, evidence_root: Path | None = None) -> Path:
    """Re-run deterministic layers on captured outputs without calling a provider."""
    root = (evidence_root or DEFAULT_EVIDENCE_ROOT).resolve()
    source_dir = source_run.resolve()
    if source_dir.parent != root or not source_dir.is_dir():
        raise EvaluationIntegrityError(
            "replay source must be a run directory under the evidence root"
        )
    manifest, cases, source_results, _, _ = _load_verified_run(source_dir)
    outputs = [result["output"] for result in source_results]
    layer1 = evaluate_layer1(cases, outputs)
    layer2 = evaluate_layer2(cases, outputs)
    run_dir = create_run_directory(root)
    started_at = datetime.now(timezone.utc).isoformat()
    git_metadata = _git_metadata()
    implementation, implementation_digest = _implementation_snapshot()
    replay_results = []
    for index, result in enumerate(source_results):
        replay_results.append(
            {
                **result,
                "layer1": layer1["results"][index],
                "layer2": layer2["results"][index],
                "replayed_from": source_dir.name,
            }
        )
    replay_manifest = {
        **manifest,
        **git_metadata,
        "run_id": run_dir.name,
        "started_at": started_at,
        "evaluation_mode": "offline_replay",
        "replay_of": source_dir.name,
        "generation_implementation_sha256": manifest["implementation_sha256"],
        "implementation_sha256": implementation_digest,
        "aggregate_status": "PENDING_HUMAN_SEMANTIC_REVIEW",
        "layer1_passed": layer1["passed"],
        "layer2_passed": layer2["passed"],
        "safety_critical_failure_count": layer2["safety_critical_failure_count"],
        "case_results_sha256": _json_digest(replay_results),
        "layer1_sha256": _json_digest(layer1),
        "layer2_sha256": _json_digest(layer2),
    }
    write_json_evidence(run_dir, "manifest.json", replay_manifest)
    write_json_evidence(run_dir, "implementation-source.json", implementation)
    write_json_evidence(run_dir, "dataset.json", cases)
    write_json_evidence(run_dir, "case-results.json", replay_results)
    write_json_evidence(run_dir, "layer1.json", layer1)
    write_json_evidence(run_dir, "layer2.json", layer2)
    failures = [
        result
        for result in replay_results
        if not result["layer1"]["passed"]
        or not result["layer2"]["passed"]
        or result["provider_error"] is not None
    ]
    if failures:
        write_json_evidence(run_dir, "genuine-failures.json", failures)
        write_json_evidence(
            run_dir,
            "repair-feedback-template.json",
            {
                "source_failure_run": source_dir.name,
                "case_ids": [result["case_id"] for result in failures],
                "feedback": "",
            },
        )
    for filename in (
        "semantic-review.json",
        "semantic-review-template.json",
        "human-decision-template.json",
    ):
        source_file = source_dir / filename
        if source_file.is_file():
            contents = json.loads(source_file.read_text(encoding="utf-8"))
            write_json_evidence(run_dir, filename, contents)
    return run_dir


def finalize_evaluation(run_dir: Path) -> dict[str, Any]:
    """Validate human score records and write a non-overwriting final summary."""
    _, _, case_results, layer1, layer2 = _load_verified_run(run_dir)
    review_path = run_dir / "semantic-review.json"
    if not review_path.is_file():
        raise InvalidSemanticScore(
            "semantic-review.json is required; copy and complete the "
            "human review template"
        )
    review_records = json.loads(review_path.read_text(encoding="utf-8"))
    case_ids = [case["case_id"] for case in case_results]
    semantic_results = validate_score_records(review_records, case_ids)
    for result, case in zip(semantic_results, case_results, strict=True):
        if (
            case["expected"]["needs_clarification"]
            and result["scores"]["handling_of_ambiguity"] == 0
        ):
            result["safety_critical_failure"] = True
    aggregate = aggregate_evaluation(layer1, layer2, semantic_results)
    summary = {
        "run_id": run_dir.name,
        "aggregate": aggregate,
        "semantic_results": semantic_results,
        "human_final_decision": "PENDING",
        "note": "Automated evaluation does not make the final human "
        "ACCEPT/REJECT decision.",
    }
    write_json_evidence(run_dir, "final-summary.json", summary)
    return summary
