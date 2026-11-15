---

description: "Implementation and evaluation tasks for the Natural-Language Reminder Agent"
---

# Tasks: Natural-Language Reminder Agent

**Input**: Approved design documents in `specs/002-natural-language-reminder-agent/`

**Scope**: Part 1B only. Do not modify `src/smart_todo/`, its tests, or other Part 1A behavior. These tasks do not authorize weakening any approved requirement or evaluation control.

**Organization**: Tasks are grouped by the four user stories in `spec.md`. The evaluation story follows the three interpretation stories because its end-to-end run depends on all supported intents.

## Phase 1: Setup

**Purpose**: Establish the separate Python 3.13 Part 1B package, dependencies, and safe credential boundary.

- [ ] T001 Configure the Part 1B project metadata in `pyproject.toml` for Python 3.13 and the repository's existing `src/` layout without changing Part 1A entry points or runtime behavior.
- [ ] T002 [P] Create the `src/reminder_agent/` package, `tests/reminder_agent/unit/`, `tests/reminder_agent/contract/`, `tests/reminder_agent/integration/`, and `tests/reminder_agent/evaluation/` directories with package initializers where needed; keep the existing `src/smart_todo/` package untouched.
- [ ] T003 Add the runtime dependencies `openai`, `jsonschema`, and `tzdata`, and use the existing development dependency conventions in `pyproject.toml` for pytest, Ruff, and Bandit; document/test the Python 3.13 environment without adding an unnecessary dependency manager.
- [ ] T004 [P] Update `.gitignore` to exclude local secret files such as `.env` and any Part 1B credential files; do not add real credentials, an API key placeholder that resembles a usable key, or a committed secret file.

## Phase 2: Foundational

**Purpose**: Implement shared output, context, provider, and CLI boundaries that block all user stories.

- [ ] T005 Add contract tests first in `tests/reminder_agent/contract/test_output_schema.py` for the eight required fields, allowed intents, JSON types/nullability, real dates, `HH:MM` times, positive snooze durations accepted, zero/negative durations rejected, and null duration permitted only for non-applicable or unresolved clarification cases; use synthetic values only and verify tests fail against invalid fixtures (FR-011–FR-014).
- [ ] T006 Implement the typed reminder result in `src/reminder_agent/model.py` and reusable local structured-output validation rules in `src/reminder_agent/validation.py`; update `specs/002-natural-language-reminder-agent/contracts/reminder-output.schema.json` to express `snooze_duration_minutes` as integer-or-null with `minimum: 1`. Validate exact schema/fields, types, allowed values, real Gregorian `YYYY-MM-DD`, `HH:MM` from `00:00` through `23:59`, nullability, positive snooze duration, and cross-field consistency. Snooze duration may be null only for non-snooze intents or an unresolved snooze request requiring clarification (FR-011–FR-014).
- [ ] T007 Implement `RuntimeContext` in `src/reminder_agent/context.py` with an aware reference instant, resolvable IANA time-zone name, locale, and `runtime`/`evaluation` source; support configured local context and immutable fixed per-case overrides, and never read host clock/locale for evaluation cases (FR-005).
- [ ] T008 Add provider/configuration security tests first in `tests/reminder_agent/unit/test_provider_security.py`; verify a missing API key fails safely with a clear configuration error, credentials are read only from `OPENAI_API_KEY`, synthetic keys never appear in application output, logs, or evaluation artifacts, provider errors are sanitized, and fixtures plus `tests/data/reminder-evaluation-cases.json` contain no real credentials (Constitution V; FR-021).
- [ ] T009 Implement the secure Responses API boundary in `src/reminder_agent/interpreter.py` and the `python -m reminder_agent` entry point in `src/reminder_agent/cli.py`; read `OPENAI_API_KEY` only from the process environment, use `OPENAI_MODEL` or `gpt-4o-mini`, send strict schema-constrained output with `store=false`, sanitize provider errors, and never log or persist credentials. On success emit exactly one validated JSON object; on configuration/provider/response failure emit an actionable sanitized stderr error with nonzero exit status, never success-shaped fallback output (FR-001, FR-011–FR-012; Constitution V; `contracts/cli.md`).

**Checkpoint**: The Part 1B boundary, schema validator, fixed-context interface, provider error behavior, and CLI contract are ready; Part 1A remains unchanged.

## Phase 3: User Story 1 - Interpret a complete reminder request (Priority: P1)

**Goal**: Interpret fully specified create requests faithfully with deterministic local date/time semantics.

**Independent Test**: With a stubbed provider and fixed context, a complete create request returns a schema-valid interpretation preserving the task and exact resolved local date/time without clarification; deterministic tests need no network or API key.

- [ ] T010 [P] [US1] Write deterministic date/time tests first in `tests/reminder_agent/unit/test_date_time.py` for month/year boundaries, leap day, explicit and relative dates, numeric-date locale handling, AM/PM conversion, ambiguous bare hours, today/tomorrow/tonight/noon/midnight, invalid dates/times, and an elapsed time against fixed reference context; do not use the wall clock (FR-004–FR-006).
- [ ] T011 [US1] Implement the behavior exercised by `tests/reminder_agent/unit/test_date_time.py` in `src/reminder_agent/date_time.py`; support explicit/relative dates, 12-hour/24-hour times, today, tomorrow, tonight without an implied time, noon as `12:00`, and midnight as `00:00` at the named date's start; reject impossible dates and `24:00` rather than normalizing them (FR-004–FR-005).
- [ ] T012 [P] [US1] Write create-intent contract and integration tests first in `tests/reminder_agent/contract/test_create_contract.py` and `tests/reminder_agent/integration/test_create_interpretation.py`; use stubbed provider responses and fixed contexts for E01–E04 and E10–E13, verify task fidelity and exact resolved schedules, and assert no reminder is stored or executed (FR-001–FR-006; SC-001–SC-002).
- [ ] T013 [US1] Implement create-intent extraction in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/interpreter.py` to pass the preceding contract/integration tests; preserve the user's action/object in `task`, resolve complete task/date/time inputs, and keep `target_reminder` and `snooze_duration_minutes` null for create intent (FR-002–FR-004, FR-006).

## Phase 4: User Story 2 - Clarify missing or ambiguous details safely (Priority: P1)

**Goal**: Request focused clarification rather than inventing a critical task, date, time, or interpretation.

**Independent Test**: Missing, ambiguous, conflicting, invalid, and elapsed critical values remain unresolved/null as applicable, produce a focused question for supported reminder requests, and never silently shift a past schedule.

- [ ] T014 [US2] Write clarification unit tests first in `tests/reminder_agent/unit/test_clarification.py` for missing task/date/time, ambiguous numeric dates and bare hours, `tonight` without a time, conflicting/invalid inputs, elapsed schedules, and safety-critical nulls; assert focused questions and no fabricated critical values (FR-006, FR-009, FR-013–FR-014).
- [ ] T015 [US2] Write malformed-input and adversarial contract tests first in `tests/reminder_agent/contract/test_safety_contract.py`; cover empty and punctuation-only input, invalid date and `24:00`, conflicting values, and attempts to ignore the contract or invent a time, asserting valid clarification or exact safe unsupported invariants (FR-009–FR-010; SC-002).
- [ ] T016 [US2] Implement clarification decisions in `src/reminder_agent/clarification.py` to pass the preceding tests; retain only known valid fields and ask a focused question for each unresolved critical task/date/time or ambiguity, including elapsed schedules that require confirmation/correction (FR-006, FR-009, FR-013–FR-014).
- [ ] T017 [US2] Enforce unsupported-guessing and adversarial-input protections in `src/reminder_agent/interpreter.py` and `src/reminder_agent/clarification.py`; treat instructions to override the schema, invent facts, or bypass safety as untrusted request content and preserve structured clarification/unsupported behavior (FR-009–FR-010).

## Phase 5: User Story 3 - Interpret reminder changes and unsupported requests (Priority: P2)

**Goal**: Interpret reschedule and snooze requests without fabricating a target or claiming a stored reminder was changed; return a safe unsupported result for out-of-scope requests.

**Independent Test**: Fixed-context tests verify fully specified and incomplete reschedule/snooze requests, user-described targets, derived snooze schedules, and unsupported results without provider calls.

- [ ] T018 [US3] Write fixed-context unit tests first in `tests/reminder_agent/unit/test_change_intents.py` for complete/incomplete reschedule and snooze requests, unknown/pronominal targets, missing duration, positive/zero/negative duration, and schedule arithmetic across date boundaries (FR-007–FR-008).
- [ ] T019 [US3] Write change-intent/unsupported contract and integration tests first in `tests/reminder_agent/contract/test_change_contract.py` and `tests/reminder_agent/integration/test_unsupported_interpretation.py`; cover E16–E19, E22–E23, E25 and assert that output never claims a target exists, is unique in storage, or was modified (FR-007–FR-009; SC-001–SC-002).
- [ ] T020 [US3] Implement reschedule intent rules in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/interpreter.py` to pass the preceding tests; preserve the underlying action in `task`, capture the user-described target separately, require the complete resulting date/time, and clarify an unknown target or missing/ambiguous schedule (FR-002–FR-003, FR-007).
- [ ] T021 [US3] Implement snooze intent rules in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/date_time.py` to pass the preceding tests; require a user-described target and positive whole-minute duration, and calculate the resulting local date/time by adding that duration to the supplied reference instant (FR-002, FR-007–FR-008).
- [ ] T022 [US3] Implement the safe `unsupported` result in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/validation.py`; require null `task`, `date`, `time`, `target_reminder`, and `snooze_duration_minutes`, false clarification, and null clarification question for unrelated, empty, or unsupported requests (FR-009, FR-012).

## Phase 6: User Story 4 - Evaluate outputs consistently (Priority: P1; depends on US1–US3)

**Goal**: Run all 25 fixed cases through three immutable evaluation layers, preserve attributable evidence, and require human acceptance.

**Independent Test**: Replay a complete synthetic dataset and captured outputs offline; verify all per-case layer results, rubric records, fixed aggregate thresholds, unique evidence paths, and an explicit human ACCEPT/REJECT record. A live provider run is opt-in and never required by deterministic tests.

- [ ] T023 [US4] Create `tests/data/reminder-evaluation-cases.json` as a version-controlled corpus of all 25 stable case IDs E01–E25 from `specs/002-natural-language-reminder-agent/spec.md`; include category, exact input, fixed reference instant, time zone and locale (use null where the case deliberately has no established locale), expected intent, expected task/target/schedule facts, clarification behavior, allowed normalizations fixed in advance, and safety assertions. Preserve every E01–E25 case and outcome (FR-015–FR-016).
- [ ] T024 [US4] Write dataset integrity and Layer 1 regression tests first in `tests/reminder_agent/evaluation/test_dataset.py` and `tests/reminder_agent/evaluation/test_layer1.py`; require all 25 unique IDs, fixed contexts, and required coverage, and verify schema failures for missing/extra fields, wrong types, invalid dates/times, cross-field violations, zero/negative snooze durations, accepted positive integer durations, and null snooze duration only for non-applicable/unresolved cases (FR-011–FR-016; SC-001).
- [ ] T025 [US4] Apply the reusable validators from `src/reminder_agent/validation.py` to every evaluation case through `src/reminder_agent/evaluation.py` as Layer 1; record per-case Layer 1 PASS/FAIL evidence and the run's 100% acceptance result. Do not reimplement or duplicate schema, field, date/time, snooze-duration, or cross-field validation here (FR-011–FR-016; SC-001).
- [ ] T026 [US4] Extend `tests/reminder_agent/evaluation/test_layer1.py` with invalid-output regression cases for each required field, intent enum, type, nullability, date/time format, additional property, positive snooze minimum, and cross-field rule; assert accepted evaluation runs require 25/25 Layer 1 passes (FR-016; SC-001).
- [ ] T027 [US4] Write per-case Layer 2 tests first in `tests/reminder_agent/evaluation/test_layer2.py`; cover task meaning, target, schedule, clarification decision, no fabricated critical values, safety assertions, and all 25 fixed cases, including permitted semantic normalizations only (FR-016, FR-019; SC-002).
- [ ] T028 [US4] Implement deterministic Layer 2 evaluation in `src/reminder_agent/validation.py` and `src/reminder_agent/evaluation.py` to pass the preceding tests; compare intent, task meaning, target, schedule, and clarification to pre-recorded facts, detect unsupported critical values, and fail any violated safety assertion (FR-016, FR-019).
- [ ] T029 [US4] Write Layer 3 score-record tests first in `tests/reminder_agent/evaluation/test_semantic_scoring.py`; verify five criterion scores in 0–2, per-criterion rationale, total 0–10, case pass at 8 or more, human scorer identity, semantic-equivalence handling, and disputed-score/second-review availability records (FR-017–FR-018; SC-004).
- [ ] T030 [US4] Implement Layer 3 scoring-record validation in `src/reminder_agent/semantic_scoring.py`; require a designated human's five criterion scores and rationales for every case, calculate total/pass at 8/10, accept equivalent wording rather than exact-string matching, and record a second review only for disputed scores, including honest unavailability (FR-017–FR-018; SC-004).
- [ ] T031 [US4] Write aggregate boundary tests first in `tests/reminder_agent/evaluation/test_aggregate.py`; verify 25/25 Layer 1 and Layer 2 passes, 22/25 Layer 3 passes, rejection at 21/25, and FAIL on any Layer 1/2 failure or safety-critical failure (FR-019; SC-003).
- [ ] T032 [US4] Implement aggregate PASS/FAIL calculation in `src/reminder_agent/evaluation.py`; PASS requires 100% Layer 1, 100% Layer 2, at least `ceil(0.85 * case_count)` Layer 3 scores of 8/10 or higher (22 of the initial 25 cases), and zero safety-critical failures. Keep the approved policy fixed with no threshold overrides (FR-019; SC-003).
- [ ] T033 [US4] Write evidence-integrity tests first in `tests/reminder_agent/evaluation/test_evidence.py`; verify unique non-overwriting run paths, required initial/failure/repair/rerun/final evidence, attributable source revision and dataset/schema/validator/rubric identifiers, and exclusion of API keys and real user reminder text (FR-018–FR-022; SC-006).
- [ ] T034 [US4] Implement unique, non-overwriting run evidence in `src/reminder_agent/evidence.py`; capture source revision, dataset/schema/validator/rubric identifiers, provider/model/request settings, fixed contexts, outputs or explicit provider errors, all three layer results, human score records, unchanged threshold, aggregate result, failure reasons, and links between initial run, genuine failures, repair feedback, repaired run, and reruns. Never write API keys or real user reminder text (FR-018–FR-022; Constitution IV–V, XV).
- [ ] T035 [US4] Write evaluation-runner CLI tests first in `tests/reminder_agent/evaluation/test_evaluation_cli.py`; verify fixed per-case context, offline replay, one output/error record per case, and Layers 1/2 for all 25 cases, then implement the `evaluate --cases tests/data/reminder-evaluation-cases.json` workflow in `src/reminder_agent/evaluation.py` without host clock/locale dependence (FR-005, FR-015–FR-016; `contracts/cli.md`).
- [ ] T036 [US4] Write finalization CLI tests first in `tests/reminder_agent/evaluation/test_finalize_cli.py`; reject incomplete human score records and verify immutable threshold/aggregate results, then implement semantic-review capture and `finalize --run-dir artifacts/reminder-agent/<run-id>` in `src/reminder_agent/cli.py` and `src/reminder_agent/evaluation.py` without overwriting earlier runs (FR-018–FR-019, FR-021–FR-022; `contracts/cli.md`).
- [ ] T037 [US4] In `tests/reminder_agent/evaluation/test_integrity.py`, first add tests that reject deletion of difficult cases, weakened schema/invariant checks, reduced semantic thresholds, changed expected outcomes to accommodate incorrect output, hidden safety failures, or manufactured failures; then enforce these controls in `src/reminder_agent/evaluation.py`, retaining prior results and requiring rationale/review for approved control changes (FR-020–FR-021; Constitution IV, XIV).
- [ ] T038 [US4] Create human review and final decision records under `artifacts/reminder-agent/`; require the designated human to score each case, record any unavailable second reviewer honestly, and document final ACCEPT or REJECT with cited evaluation evidence, known limitations, and residual risks (FR-018, FR-021–FR-022; SC-004–SC-006).

## Final Phase: Polish and Cross-Cutting Concerns

**Purpose**: Validate the complete Part 1B workflow and document operational limits without changing acceptance criteria or Part 1A.

- [ ] T039 Update `specs/002-natural-language-reminder-agent/quickstart.md` and `specs/002-natural-language-reminder-agent/contracts/cli.md` to document Python 3.13 setup, environment-only `OPENAI_API_KEY`, configured runtime context, deterministic offline tests, opt-in live evaluation, all three layers, fixed aggregate thresholds, evidence locations, provider data handling, and human final review (FR-005, FR-016–FR-023).
- [ ] T040 Run `python -m pytest tests/reminder_agent`, repository `python -m pytest`, `ruff check .`, `ruff format --check .`, and `bandit -q -r src`; record actual results under `artifacts/reminder-agent/` and confirm no Part 1A source/test changes were made (SC-001–SC-006; Constitution III–V).

## Dependencies and Execution Order

### Phase dependencies

- **Setup**: T001–T004 establish Python, package layout, dependencies, and secret exclusion before implementation.
- **Foundational**: T005–T009 depend on setup; all user stories depend on the shared typed contract, validator, runtime context, provider boundary, and CLI.
- **US1, US2, and US3**: Each depends on the foundation. US1 and US2 can proceed in parallel where file ownership permits; US3 depends on the shared intent/date-time components and follows their completion.
- **US4**: T023–T038 build the dataset and evaluation path; full end-to-end verification depends on US1–US3. Dataset and evaluator work may be developed independently of model-call logic after the contract is stable.
- **Polish**: T039–T040 depend on the implemented stories and evaluation workflow.

### User story order

1. **US1 (P1)**: Complete create interpretation and fixed-context date/time support.
2. **US2 (P1)**: Clarification and safe handling of missing, ambiguous, invalid, or adversarial inputs.
3. **US3 (P2)**: Reschedule, snooze, and unsupported behavior.
4. **US4 (P1)**: Full dataset, layered evaluation, evidence, and human decision; scheduled after US3 because its acceptance run covers all intents.

### Parallel opportunities

- T002 and T004 can proceed in parallel with T001 because they touch separate paths.
- T005 writes output-contract tests before T006 implements the model/validators; T008 writes provider-security tests before T009 implements the provider and CLI boundary.
- Within US1, write T010 temporal tests before T011 date/time code, then T012 create-intent tests before T013 implementation.
- US1 and US2 can proceed in parallel after the foundation if edits to shared modules are coordinated; US3 can start once shared intent/date-time interfaces are stable.
- Within US4, T023 authors the immutable dataset; T024, T027, T029, T031, and T033 define regression tests before their corresponding evaluator/scoring/aggregate/evidence implementation tasks. T025 applies the existing Layer 1 validators and records results rather than duplicating validator code.

## Parallel Example: US1 and US2

```text
After T005–T009:
Worker A: T010 temporal tests, then T011 date/time implementation
Worker B: T014 clarification tests and T015 safety tests, then T016–T017 implementation

Then run the fixed-context US1/US2 test suites with stubbed provider responses.
```

## Implementation Strategy

### MVP first

1. Complete T001–T009.
2. Complete US1 (T010–T013).
3. Validate a complete create request using a stubbed provider and fixed context; confirm the schema-valid JSON output and no Part 1A changes.
4. Do not claim overall assignment acceptance until US2–US4, the full 25-case dataset, all three evaluation layers, evidence, and human review are complete.

### Incremental delivery

1. Setup and foundation establish the stable Part 1B contract and provider boundary.
2. US1 adds complete create interpretation and date/time semantics.
3. US2 adds clarification and safety behavior.
4. US3 adds reschedule, snooze, and unsupported behavior.
5. US4 evaluates all 25+ fixed cases, preserves each run and repair, and obtains human ACCEPT/REJECT.
6. Polish validates the documented quickstart and repository quality gates without modifying Part 1A or weakening evaluation criteria.
