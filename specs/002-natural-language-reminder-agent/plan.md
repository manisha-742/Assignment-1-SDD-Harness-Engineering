# Implementation Plan: Natural-Language Reminder Agent

**Branch**: `002-natural-language-reminder-agent` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

**Input**: Approved feature specification and clarification decisions in `specs/002-natural-language-reminder-agent/spec.md`

## Summary

Build a small, local Python 3.13 command-line application that submits one natural-language
reminder request to the OpenAI Responses API and returns one schema-constrained JSON
interpretation. Use configured local date/time, time zone, and locale in normal operation;
evaluation cases inject fixed contexts. Keep interpretation, date/time context, clarification,
schema validation, deterministic invariants, human semantic scoring, aggregate decisions, and
evidence capture separate. Do not store or execute reminders. No model call is made by the
deterministic pytest suite.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: OpenAI Python SDK for Responses API structured output; `jsonschema`
for local validation of the published JSON Schema; Python standard library for CLI, JSON,
date/time, and locale handling; `tzdata` for IANA time-zone rules on Windows. Development
dependencies follow the existing project: pytest, Ruff, and Bandit.

**Storage**: No reminder persistence or database. The 24+ evaluation cases are version-controlled
JSON. Evaluation runs and human scoring records are separate, non-overwriting local evidence
files under `artifacts/reminder-agent/`.

**Testing**: pytest unit, contract, and integration tests using fixed reference contexts and a
stubbed provider. Deterministic Layer 1 and Layer 2 tests run offline. Live model evaluation is
an explicit, credential-gated run; Layer 3 is scored by a designated human.

**Target Platform**: Local Python 3.13 command-line use; Windows is the current development
environment. The application itself is not deployed as a service.

**Project Type**: A separate Python CLI package, `reminder_agent`, alongside the existing
`smart_todo` package.

**Performance Goals**: No latency or throughput target is specified. Provider latency and
failures are reported explicitly and are not converted into successful reminder results.

**Constraints**: Reminder text and reference context are sent to the user-approved hosted
provider for inference. `OPENAI_API_KEY` is read from the environment and never committed or
written to evidence. Disable provider-side response storage where supported, while documenting
that default abuse-monitoring retention may still apply. No web UI, authentication, cloud
deployment of the application, database, microservices, Docker, Kubernetes, or unrelated
productivity features.

**Scale/Scope**: One request per invocation; one local user; at least 24 distinct evaluation
cases; no reminder records, concurrent service workload, or persistence lifecycle.

## Constitution Check

*GATE: Pass before Phase 0 research and again after Phase 1 design.*

| Principle / gate | Plan alignment | Result |
|---|---|---|
| I. Deterministic CLI and Controlled Task State | Applies to the existing Part 1A Smart Todo CLI only. Part 1B is a separate package and does not change Part 1A state or outputs. | PASS |
| II. Requirements Traceability | Components, contracts, evaluation cases, and tests map to Part 1B requirements and acceptance scenarios. | PASS |
| III. Automated Deterministic Testing | pytest covers schema, date/context rules, clarification consistency, deterministic properties, aggregation, and regression cases without live model calls. | PASS |
| IV. Harness Integrity and Evidence Preservation | Keep all 24+ cases, validators, scoring rules, thresholds, genuine failures, repair feedback, reruns, and final evidence; never alter them solely to obtain PASS. | PASS |
| V. Reproducible, Secure, and Maintainable Delivery | Fixed evaluation context, captured provider/model/settings, environment-only credentials, local output, and a small package boundary. | PASS |
| VI. Specification-Driven AI Behaviour | The approved specification and clarified decisions define model behavior and output before implementation. | PASS |
| VII. Structured Output Contract | A version-controlled JSON Schema is used for provider-constrained output and local structural validation. | PASS |
| VIII. Clarification Instead of Unsupported Guessing | Deterministic rules enforce required fields and clarification consistency; unknown critical values remain null. | PASS |
| IX. Property and Invariant Validation | Per-case task, target, schedule, clarification, and safety facts are checked deterministically. | PASS |
| X. Semantic Quality Evaluation | A human applies the five-criterion 10-point rubric; wording is not compared by exact string alone. | PASS |
| XI. Diverse Evaluation Dataset | The version-controlled benchmark retains the 24 specified cases and may grow only with meaningful cases. | PASS |
| XII. Three-Layer Evaluation | Every run records structural, deterministic, and semantic evaluation. | PASS |
| XIII. Quantitative Acceptance Threshold | Aggregate calculation is fixed at 100% Layer 1, 100% Layer 2, at least 85% Layer 3 case scores of 8/10 or higher (round up), and zero safety-critical failures. | PASS |
| XIV. Evaluation Integrity | No case, validator, threshold, or safety property is bypassed or weakened to obtain PASS. | PASS |
| XV. Evidence Preservation and Repair | Unique run evidence preserves initial outputs, failures, feedback, repairs, reruns, and final results without overwriting prior runs. | PASS |
| XVI. Human Accountability | A human records final ACCEPT/REJECT and limitations; reviewer unavailability is recorded honestly. | PASS |
| Technology, Security and Data Integrity | Part 1A technology/security gates remain intact. Part 1B does not add persistence; the hosted data flow and credential boundary are documented. | PASS |
| Verification, Evidence and Human Review | Automated PASS is evidence only; final acceptance is a documented human decision. | PASS |

No constitution violations or scope exceptions are required. The hosted inference API is an
external dependency, not an application deployment; its data-flow and retention limits are
explicitly disclosed in this plan.

## Phase 0: Research Decisions

See [research.md](./research.md) for sources, alternatives, and rationale. Decisions carried
into design:

- Use the official OpenAI Python SDK and Responses API with strict JSON Schema output. Use
  `gpt-4o-mini` as the initial configured model; record the exact model identifier and request
  settings for every live evaluation run.
- Send no reminder text to a provider during pytest. Live evaluation is opt-in and uses the
  synthetic, version-controlled benchmark.
- Use one canonical JSON Schema for API constraints and local Layer 1 checks; apply date/time
  and cross-field business rules in deterministic Python validation.
- Use Python `datetime`/`zoneinfo` with an explicitly configured local time zone and locale.
  Evaluation supplies fixed per-case context, independent of host settings.
- Score Layer 3 manually from captured outputs; do not call a second model as an evaluator.

## Design Decisions

### Application and inference boundary

- Add `src/reminder_agent/` as a separate package; do not alter or import the Part 1A
  `smart_todo` package.
- The CLI accepts one request and returns exactly one JSON object on stdout. It has no tools,
  reminder store, notification capability, or network access beyond its single inference call.
- Keep the OpenAI client behind a narrow interpreter boundary. Read `OPENAI_API_KEY` from the
  environment; allow the model identifier to be configured, defaulting to `gpt-4o-mini`.
- Use the Responses API strict JSON Schema response format. Treat provider refusal as a safe
  structured unsupported result only when all unsupported-result invariants pass. Treat network,
  authentication, rate-limit, malformed provider response, and incomplete-response failures as
  explicit stderr/nonzero-exit errors, not success-shaped fallback results.

### Output model, context, and interpretation

- Keep `contracts/reminder-output.schema.json` as the canonical external contract. Validate
  every response against it locally; use Python `datetime` checks for real ISO calendar dates,
  24-hour times, and conditional field rules that the provider schema cannot express.
- Represent a validated response as a small typed Python model. The JSON Schema, typed model,
  and cross-field validator must remain aligned through contract tests.
- Build a `RuntimeContext` containing an aware local reference instant, IANA time-zone name,
  and configured locale. Normal calls use configured local context. Each evaluation case
  supplies its own fixed context and locale; never use the wall clock in those tests.
- Apply the clarified calendar rules: today is the current local date, tomorrow is the next
  local date, tonight identifies the current local date but no clock time, noon is 12:00, and
  midnight is 00:00 at the start of the named date. A past or elapsed schedule is clarified, not
  silently shifted.
- Model output identifies the reminder intent and underlying task. Deterministic rules enforce
  the operation-specific required fields, target description, positive snooze duration, and
  `needs_clarification`/question consistency. A target description is not proof of a stored or
  unique reminder.

### Evaluation and evidence

- Store the full evaluation dataset in version-controlled JSON with stable case IDs, text,
  fixed context, expected intent/task/target/schedule/clarification facts, permitted normalized
  wording variants, and safety assertions. Keep at least 24 meaningfully distinct cases.
- Layer 1 validates JSON and the exact schema. Layer 2 compares each output to that case's
  pre-recorded deterministic facts. Layer 3 records the designated human's five criterion
  scores and reasons; a second reviewer adjudicates disputed scores when available. If no
  second reviewer is available, mark that fact and any unresolved dispute honestly.
- The aggregate evaluator reports PASS only if all three threshold conditions in FR-019 hold.
  For 24 cases, the 85% semantic requirement means at least 21 cases score 8/10 or higher.
- Each run receives a unique directory. Preserve the dataset version, code revision, model,
  request settings, fixed contexts, captured outputs, layer results, human score records,
  aggregate result, and failure/repair links. Never overwrite initial failures or store API keys.
- Live evidence uses synthetic dataset inputs only. Normal CLI requests are sent to the hosted
  provider but are not persisted by the application; provider abuse-monitoring retention remains
  subject to the provider's terms and is documented for users.

## Project Structure

### Documentation (this feature)

```text
specs/002-natural-language-reminder-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── cli.md
    └── reminder-output.schema.json
```

### Source Code (planned; not created by this planning command)

```text
src/
├── smart_todo/                         # Existing Part 1A; unchanged
└── reminder_agent/
    ├── __main__.py                     # Local CLI entry
    ├── cli.py                          # Interpret/evaluate command contract
    ├── context.py                      # Runtime and fixed evaluation context
    ├── interpreter.py                  # Provider request and structured response
    ├── model.py                        # Typed reminder interpretation
    ├── intent_rules.py                 # Create/reschedule/snooze field requirements
    ├── date_time.py                    # Context-aware calendar/date-time rules
    ├── clarification.py                # Missing/ambiguous field handling
    ├── validation.py                   # Layer 1 and Layer 2 validation
    ├── semantic_scoring.py             # Human rubric record validation
    ├── evaluation.py                   # Dataset runner and aggregate decision
    └── evidence.py                     # Non-overwriting run evidence

tests/
├── unit/                                # Existing Part 1A tests; unchanged
├── contract/                            # Existing Part 1A tests; unchanged
├── integration/                        # Existing Part 1A tests; unchanged
└── reminder_agent/
    ├── unit/
    ├── contract/
    ├── integration/
    └── evaluation/

tests/data/
└── reminder-evaluation-cases.json       # Version-controlled 24+ case corpus

artifacts/
└── reminder-agent/                      # Unique initial, repair, rerun, final evidence
```

**Structure Decision**: Follow the repository's existing `src/` package, `python -m`
entry-point, and pytest conventions, but isolate Part 1B in `reminder_agent` and its own test
subtree. Keep the case corpus in version control and generated run evidence outside source code.
No database, service layer for persistence, frontend, or deployment project is introduced.

## Test Strategy and Traceability

All automated tests use a fixed context and a stubbed provider. The 24-case live run is a
separate, explicit operation; rerunning captured outputs and validators does not require the
provider or repeat model generation.

| Requirement / criteria | Planned verification |
|---|---|
| FR-001–FR-003 | Unit/CLI: one request yields one JSON object; task intent is retained; no reminder is stored or executed. |
| FR-004–FR-006 | Fixed-context tests for today/tomorrow/tonight/noon/midnight, locale-specific numeric dates, valid date/time forms, missing task/date/time, and past times. |
| FR-007–FR-008 | Unit tests for target identification, reschedule full resulting schedule, snooze target/duration, and reference-time calculation. |
| FR-009–FR-010 | Contract tests for malformed/unrelated inputs, safe unsupported output, invalid-date clarification, and adversarial instructions. |
| FR-011–FR-014 | Schema/contract tests for exact required keys, enum, types, nullability, additional-key rejection, date/time validation, and clarification consistency. |
| FR-015 | Dataset integrity test asserts at least 24 unique stable case IDs and required category coverage. |
| FR-016, SC-001–SC-002 | Layer 1 and Layer 2 tests run deterministically over every case using recorded expected task, target, schedule, clarification, and safety facts. |
| FR-017–FR-018, SC-004 | Scoring-record tests validate five integer criterion scores in 0–2, reasons, designated scorer, dispute/adjudication status, and replayed score records. Human scoring itself is not represented as an automated pass. |
| FR-019, SC-003 | Aggregation tests cover 24/24 structural and invariant passes, 21/24 semantic passes as the minimum passing count, zero safety-critical failures, and fail cases immediately below every threshold. |
| FR-020–FR-022, SC-005–SC-006 | Evidence tests assert unique non-overwriting run paths, required evidence metadata, preserved failures/feedback/reruns, and recorded final human decision/limitations. |
| FR-023 | Scope review confirms all new code/tests/evidence use Part 1B paths and do not modify Part 1A behavior. |

Run the existing repository quality gates (`pytest`, Ruff, and Bandit) after implementation.
Network-dependent live API checks are opt-in and are never required for routine deterministic
test execution.

## Verification and Evidence Workflow

1. Capture the initial Part 1B implementation revision and run the complete fixed 24+ case
   dataset. Save the original outputs, context, model/settings, Layer 1/2 results, and a human
   Layer 3 score record in a unique evidence directory.
2. Record genuine failures and give repair feedback linked to case IDs, failed invariants,
   rubric criteria, and captured output. Never alter the original run.
3. Implement a repair without changing cases, validators, rubric, or threshold to secure PASS.
4. Rerun the same dataset and checks into a new directory. Preserve initial and repaired runs
   side-by-side, plus a manifest linking the repair to its failure and feedback.
5. A second human reviewer adjudicates disputed semantic scores when available. If unavailable,
   record that limitation and do not fabricate a review or adjudication.
6. A human reviews the specification, implementation, full evidence, unresolved scores, and
   residual risks, then records final ACCEPT or REJECT. Automated PASS alone is not acceptance.

## Complexity Tracking

| Added complexity | Reason | Bound |
|---|---|---|
| Hosted inference dependency | Required for non-deterministic natural-language interpretation without a bundled large local model. | One provider SDK call, no tools or persisted conversations, explicit key and data-flow disclosure. |
| Layered evaluation and evidence records | Required by the Part 1B constitution and evaluation threshold. | One JSON dataset, deterministic offline validators, human semantic rubric, and local unique run directories. |
