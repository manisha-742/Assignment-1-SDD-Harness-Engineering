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

- [ ] T005 Implement the typed reminder result and canonical-schema loading in `src/reminder_agent/model.py` using `specs/002-natural-language-reminder-agent/contracts/reminder-output.schema.json`; require exactly `intent`, `task`, `date`, `time`, `needs_clarification`, `clarification_question`, `target_reminder`, and `snooze_duration_minutes`, with the exact allowed intents and JSON types/nullability specified by FR-011–FR-014.
- [ ] T006 Implement local schema and business-rule validation in `src/reminder_agent/validation.py` and update `specs/002-natural-language-reminder-agent/contracts/reminder-output.schema.json` only as needed to align it with the approved contract; enforce real Gregorian `YYYY-MM-DD`, `HH:MM` from `00:00` through `23:59`, all intent-specific nullability and required-field rules, clarification/question consistency, and rejection of additional keys (FR-011–FR-014).
- [ ] T007 Implement `RuntimeContext` in `src/reminder_agent/context.py` with an aware reference instant, resolvable IANA time-zone name, locale, and `runtime`/`evaluation` source; support configured local context and immutable fixed per-case overrides, and never read host clock/locale for evaluation cases (FR-005).
- [ ] T008 Implement secure provider configuration and the narrow Responses API boundary in `src/reminder_agent/interpreter.py`; read `OPENAI_API_KEY` only from the process environment, use `OPENAI_MODEL` or `gpt-4o-mini`, send strict schema-constrained output with `store=false`, and never log or persist credentials (FR-001, FR-011–FR-012; Constitution V).
- [ ] T009 Implement the `python -m reminder_agent` entry point and `src/reminder_agent/cli.py` request path; emit exactly one validated JSON object to stdout on success, emit actionable configuration/provider/response errors to stderr with nonzero exit status, and never return success-shaped reminder output after an API or incomplete-response failure (FR-001, FR-011; `contracts/cli.md`).

**Checkpoint**: The Part 1B boundary, schema validator, fixed-context interface, provider error behavior, and CLI contract are ready; Part 1A remains unchanged.

## Phase 3: User Story 1 - Interpret a complete reminder request (Priority: P1)

**Goal**: Interpret fully specified create requests faithfully with deterministic local date/time semantics.

**Independent Test**: With a stubbed provider and fixed context, a complete create request returns a schema-valid interpretation preserving the task and exact resolved local date/time without clarification; deterministic tests need no network or API key.

- [ ] T010 [P] [US1] Implement context-aware date and time normalization in `src/reminder_agent/date_time.py` for explicit dates, relative dates, 12-hour and 24-hour times, `today`, `tomorrow`, `tonight`, `noon`, and `midnight`; apply the approved local-calendar meanings, including midnight as `00:00` on the named date, and reject impossible dates and invalid `24:00` rather than normalizing them (FR-004–FR-005).
- [ ] T011 [US1] Add deterministic date/time unit tests in `tests/reminder_agent/unit/test_date_time.py` for month/year boundaries, leap day, explicit and relative dates, numeric-date locale handling, AM/PM conversion, ambiguous bare hours, today/tomorrow/tonight/noon/midnight, invalid dates/times, and a time already elapsed against the supplied reference context (FR-004–FR-006).
- [ ] T012 [P] [US1] Implement create-intent extraction in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/interpreter.py`; preserve the user's action/object in `task`, resolve complete task/date/time inputs, and keep `target_reminder` and `snooze_duration_minutes` null for create intent (FR-002–FR-004, FR-006).
- [ ] T013 [US1] Add create interpretation contract and integration tests in `tests/reminder_agent/contract/test_create_contract.py` and `tests/reminder_agent/integration/test_create_interpretation.py`; use stubbed provider responses and fixed contexts, including the approved E01, E02, E03, E04, E10–E13 successful schedules, and verify no reminder is stored or executed (FR-001–FR-006; SC-001–SC-002).

## Phase 4: User Story 2 - Clarify missing or ambiguous details safely (Priority: P1)

**Goal**: Request focused clarification rather than inventing a critical task, date, time, or interpretation.

**Independent Test**: Missing, ambiguous, conflicting, invalid, and elapsed critical values remain unresolved/null as applicable, produce a focused question for supported reminder requests, and never silently shift a past schedule.

- [ ] T014 [US2] Implement clarification decisions in `src/reminder_agent/clarification.py` for missing task/date/time, ambiguous numeric dates without an established locale convention, bare ambiguous hours, `tonight` without an exact time, conflicting or invalid scheduling values, and elapsed schedules; retain only known valid fields and ask a focused question for each unresolved critical fact (FR-006, FR-009, FR-013–FR-014).
- [ ] T015 [US2] Enforce unsupported-guessing and adversarial-input protections in `src/reminder_agent/interpreter.py` and `src/reminder_agent/clarification.py`; treat user attempts to override the schema, invent facts, or bypass safety as untrusted request content and continue to enforce the structured reminder contract (FR-009–FR-010).
- [ ] T016 [US2] Add clarification/safety tests in `tests/reminder_agent/unit/test_clarification.py` for missing task/date/time, ambiguous numeric dates and bare hours, conflicting/invalid inputs, elapsed times, and safety-critical nulls; assert that no missing critical date/time is fabricated and no past schedule is silently moved (FR-006, FR-009–FR-010, FR-013–FR-014).
- [ ] T017 [US2] Add adversarial and malformed-input contract tests in `tests/reminder_agent/contract/test_safety_contract.py`; cover empty/uninterpretable input, invalid date and `24:00`, conflicting values, and instructions to ignore the contract or invent a time, asserting either valid clarification or the exact safe unsupported invariants (FR-009–FR-010; SC-002).

## Phase 5: User Story 3 - Interpret reminder changes and unsupported requests (Priority: P2)

**Goal**: Interpret reschedule and snooze requests without fabricating a target or claiming a stored reminder was changed; return a safe unsupported result for out-of-scope requests.

**Independent Test**: Fixed-context tests verify fully specified and incomplete reschedule/snooze requests, user-described targets, derived snooze schedules, and unsupported results without provider calls.

- [ ] T018 [US3] Implement reschedule intent rules in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/interpreter.py`; preserve the underlying reminder action in `task`, capture the user-described target separately, require the complete resulting date/time, and clarify an unknown target or missing/ambiguous schedule (FR-002–FR-003, FR-007).
- [ ] T019 [US3] Implement snooze intent rules in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/date_time.py`; require a user-described target and positive whole-minute duration, and calculate the resulting local date/time by adding that duration to the supplied reference instant (FR-002, FR-007–FR-008).
- [ ] T020 [US3] Implement the safe `unsupported` result in `src/reminder_agent/intent_rules.py` and `src/reminder_agent/validation.py`; require null `task`, `date`, `time`, `target_reminder`, and `snooze_duration_minutes`, false clarification, and null clarification question for unrelated, empty, or unsupported requests (FR-009, FR-012).
- [ ] T021 [US3] Add fixed-context unit tests in `tests/reminder_agent/unit/test_change_intents.py` for complete and incomplete reschedule and snooze requests, unknown/pronominal targets, missing snooze duration, positive whole-minute validation, and schedule arithmetic across a date boundary (FR-007–FR-008).
- [ ] T022 [US3] Add change-intent/unsupported contract and integration tests in `tests/reminder_agent/contract/test_change_contract.py` and `tests/reminder_agent/integration/test_unsupported_interpretation.py`; cover E16–E19, E22–E23 and assert that output never claims a target exists, is unique in storage, or was modified (FR-007–FR-009; SC-001–SC-002).

## Phase 6: User Story 4 - Evaluate outputs consistently (Priority: P1; depends on US1–US3)

**Goal**: Run all 24 fixed cases through three immutable evaluation layers, preserve attributable evidence, and require human acceptance.

**Independent Test**: Replay a complete synthetic dataset and captured outputs offline; verify all per-case layer results, rubric records, fixed aggregate thresholds, unique evidence paths, and an explicit human ACCEPT/REJECT record. A live provider run is opt-in and never required by deterministic tests.

- [ ] T023 [US4] Create `tests/data/reminder-evaluation-cases.json` as a version-controlled corpus of all 24 stable case IDs E01–E24 from `specs/002-natural-language-reminder-agent/spec.md`; include category, exact input, fixed reference instant, time zone and locale (use null where the case deliberately has no established locale), expected intent, expected task/target/schedule facts, clarification behavior, allowed normalizations fixed in advance, and safety assertions. Preserve every specified outcome; do not reduce the corpus below 24 cases (FR-015–FR-016).
- [ ] T024 [US4] Implement dataset loading and integrity checks in `src/reminder_agent/evaluation.py` with tests in `tests/reminder_agent/evaluation/test_dataset.py`; require at least 24 unique stable IDs, complete fixed contexts and expected properties, all required category coverage, valid JSON, and immutable expected facts/normalizations before a run (FR-015–FR-016; SC-002).
- [ ] T025 [US4] Implement deterministic Layer 1 structural validation in `src/reminder_agent/validation.py`; check JSON parseability, exactly eight required fields, allowed intent values, exact types and nullability, non-empty constraints, real ISO dates, valid 24-hour times, no extra keys, and every intent/clarification cross-field rule (FR-011–FR-014, FR-016).
- [ ] T026 [US4] Add Layer 1 evaluation tests in `tests/reminder_agent/evaluation/test_layer1.py`; run validation across every dataset case/output fixture and assert 100% pass for an accepted run, with explicit failing cases for each required-field, enum, type, nullability, date/time, extra-key, and cross-field violation (FR-016; SC-001).
- [ ] T027 [US4] Implement deterministic per-case Layer 2 checks in `src/reminder_agent/validation.py`; compare intent, task meaning, target, schedule, and clarification decision to pre-recorded case facts, permit only documented meaning-preserving normalizations, detect unsupported critical facts, and fail any violated safety assertion (FR-016, FR-019).
- [ ] T028 [US4] Add Layer 2 evaluation tests in `tests/reminder_agent/evaluation/test_layer2.py`; exercise every dataset case and prove a run passes only at 100%, including no fabricated task/date/time/target, no silently normalized invalid/ambiguous values, and no adversarial contract bypass (FR-016, FR-019; SC-002).
- [ ] T029 [US4] Implement the approved Layer 3 rubric record in `src/reminder_agent/semantic_scoring.py`; record five separate 0–2 criterion scores (intent preservation, task fidelity, appropriate clarification, absence of unsupported assumptions, handling of ambiguity), each criterion's human rationale, total 0–10, per-case pass at 8 or more, and scorer identity; accept semantic equivalence rather than exact-string matching (FR-017–FR-018).
- [ ] T030 [US4] Implement human scoring and dispute-record validation in `src/reminder_agent/semantic_scoring.py`; require a designated human's scores and rationales for every case, record a second review only for disputed scores, and explicitly record second-review unavailability without fabricating a reviewer or adjudication (FR-018; SC-004).
- [ ] T031 [US4] Implement aggregate PASS/FAIL calculation in `src/reminder_agent/evaluation.py`; PASS requires exactly 100% Layer 1 passes, exactly 100% Layer 2 passes, at least `ceil(0.85 * case_count)` Layer 3 scores of 8/10 or higher (at least 21 of 24), and zero safety-critical failures. Hard-code the approved policy rather than exposing threshold overrides (FR-019; SC-003).
- [ ] T032 [US4] Add aggregate boundary tests in `tests/reminder_agent/evaluation/test_aggregate.py`; verify the 24-case 21/24 semantic boundary passes, 20/24 fails, and any Layer 1 failure, Layer 2 failure, or single safety-critical failure forces FAIL regardless of semantic score (FR-019; SC-003).
- [ ] T033 [US4] Implement unique, non-overwriting run evidence in `src/reminder_agent/evidence.py`; capture source revision, dataset/schema/validator/rubric identifiers, provider/model/request settings, fixed contexts, outputs or explicit provider errors, all three layer results, human score records, threshold, aggregate result, failure reasons, and links between initial run, genuine failures, repair feedback, repaired run, and reruns. Never write API keys or real user reminder text (FR-018–FR-022; Constitution IV–V, XV).
- [ ] T034 [US4] Add evidence integrity tests in `tests/reminder_agent/evaluation/test_evidence.py`; verify unique run directories under `artifacts/reminder-agent/`, refusal to overwrite prior evidence, required run metadata, preservation of genuine failures and repair feedback, and exclusion of credential values (FR-018–FR-022; SC-006).
- [ ] T035 [US4] Implement the evaluation runner and offline replay in `src/reminder_agent/evaluation.py`; provide the `evaluate --cases tests/data/reminder-evaluation-cases.json` workflow using each case's fixed reference instant/time zone/locale, capture one output or explicit error per case, and execute/report Layers 1 and 2 for every case without relying on host date/time/locale (FR-005, FR-015–FR-016; `contracts/cli.md`).
- [ ] T036 [US4] Implement semantic-review capture and `finalize --run-dir artifacts/reminder-agent/<run-id>` in `src/reminder_agent/cli.py` and `src/reminder_agent/evaluation.py`; require complete valid human scores before finalization, calculate the fixed aggregate decision, and record final results without overwriting earlier runs (FR-018–FR-019, FR-021–FR-022; `contracts/cli.md`).
- [ ] T037 [US4] Enforce evaluation-integrity controls in `src/reminder_agent/evaluation.py` and `tests/reminder_agent/evaluation/test_integrity.py`; prohibit deleting difficult cases, weakening schema/invariant checks, reducing semantic thresholds, changing expected outcomes solely to accommodate incorrect model output, hiding safety failures, or manufacturing failures; require documented rationale and review for any approved control change while retaining prior results (FR-020–FR-021; Constitution IV, XIV).
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
- After T005 establishes the output contract, T007 can proceed in parallel with T006; T008 and T009 depend on the shared contract/provider setup.
- Within US1, T010 and T012 can be developed on separate modules after T005–T009; run T011 and T013 once their respective implementation is available.
- US1 and US2 can proceed in parallel after the foundation if edits to shared modules are coordinated; US3 can start once shared intent/date-time interfaces are stable.
- Within US4, T023 dataset authoring can proceed alongside independent evidence/rubric design after the contract is stable; Layer 1, Layer 2, scoring, evidence, and aggregate work may be split by their distinct modules/tests, while T031/T032 require the preceding score and layer result shapes.

## Parallel Example: US1 and US2

```text
After T005–T009:
Worker A: T010 date/time normalization in src/reminder_agent/date_time.py
Worker B: T014 clarification rules in src/reminder_agent/clarification.py

Then run T011/T013 for US1 and T016/T017 for US2 against fixed contexts and stubbed provider responses.
```

## Implementation Strategy

### MVP first

1. Complete T001–T009.
2. Complete US1 (T010–T013).
3. Validate a complete create request using a stubbed provider and fixed context; confirm the schema-valid JSON output and no Part 1A changes.
4. Do not claim overall assignment acceptance until US2–US4, the full 24-case dataset, all three evaluation layers, evidence, and human review are complete.

### Incremental delivery

1. Setup and foundation establish the stable Part 1B contract and provider boundary.
2. US1 adds complete create interpretation and date/time semantics.
3. US2 adds clarification and safety behavior.
4. US3 adds reschedule, snooze, and unsupported behavior.
5. US4 evaluates all 24+ fixed cases, preserves each run and repair, and obtains human ACCEPT/REJECT.
6. Polish validates the documented quickstart and repository quality gates without modifying Part 1A or weakening evaluation criteria.
