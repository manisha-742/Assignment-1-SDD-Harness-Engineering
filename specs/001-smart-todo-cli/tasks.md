# Tasks: Smart Todo & Task CLI

**Input**: Design documents in `specs/001-smart-todo-cli/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md) and `.specify/memory/constitution.md`

**Prerequisites**: Python 3.13; plan.md and spec.md

**Tests**: Pytest tasks are included because the specification and project constitution require automated requirement and acceptance-criteria coverage.

**Organization**: Tasks are grouped by user story and ordered by prerequisite. Each user-story test task must be implemented and observed failing before the corresponding production implementation.

## Phase 1: Setup

**Purpose**: Initialize the Python project and quality-tool configuration.

- [ ] T001 Configure Python 3.13 project metadata, `src/` package discovery, pytest, Ruff lint/format rules, and Bandit development tooling in `pyproject.toml`.
- [ ] T002 [P] Create the `smart_todo` package and command entry-point scaffold in `src/smart_todo/__init__.py` and `src/smart_todo/__main__.py`.

## Phase 2: Foundational

**Purpose**: Provide isolated, deterministic test execution before feature work.

- [ ] T003 Add pytest fixtures in `tests/conftest.py` that run the module CLI from an isolated temporary working directory, capture stdout/stderr and exit status, and never use a developer's real `.smart-todo.json`.

**Checkpoint**: Project scaffold and isolated CLI test support are ready.

## Phase 3: User Story 1 - Capture and review tasks (Priority: P1)

**Goal**: Create tasks with validated values, persist them locally, and list them with all required fields in ascending ID order.

**Independent Test**: In an isolated working directory, create tagged and untagged tasks with supplied and default priority, then list and verify unique increasing IDs, title, priority, tags, TODO status, and ascending ID order.

**Requirements / acceptance**: FR-001–FR-006, FR-013, FR-014, FR-015; AC-001–AC-003, AC-018.

### Tests for User Story 1

- [ ] T004 [P] [US1] Write failing model tests for title trimming/rejection, priority defaults and allowed values, tag validation, and initial TODO status mapped to FR-001, FR-003–FR-005 and AC-001, AC-002, AC-009 in `tests/unit/test_model.py`.
- [ ] T005 [P] [US1] Write failing repository tests for first-run initialization, full-document validation, round-trip persistence, monotonic `next_id`, and fail-closed corruption mapped to FR-002, FR-013 and AC-016, AC-018, AC-019 in `tests/repository/test_repository.py`. For corrupt or invalid JSON, assert rejection, that no partial task collection is loaded, that the original file remains byte-for-byte unchanged, and that the application does not silently replace or overwrite it.
- [ ] T006 [P] [US1] Write failing CLI contract tests for add/list arguments, stable result fields, default MEDIUM priority, TODO status, ascending-ID list order, invalid-title rejection, no partial changes, and exactly-once unique-ID listing of 100 tasks mapped to FR-001, FR-004–FR-006, FR-015, AC-001–AC-003, and SC-001 in `tests/contract/test_cli_capture.py`.

### Implementation for User Story 1

- [ ] T007 [US1] Implement task types, closed priority/status values, and validation in `src/smart_todo/model.py`; preserve these data-model constraints verbatim: ID is a “positive integer”, “Unique within the collection; allocated from the persisted increasing sequence; stable across updates and restarts; never reused after deletion”; title is “Required; reject empty or whitespace-only input; trim outer whitespace before storing”; priority is “Exactly `LOW`, `MEDIUM`, or `HIGH`; new tasks default to `MEDIUM`”; tags are “Zero or more; each trimmed, non-empty, case-sensitive; duplicate tags on one task rejected; no tags represented by an empty list”; status is “Exactly `TODO`, `IN_PROGRESS`, or `DONE`; new tasks start as `TODO`”.
- [ ] T008 [US1] Implement the JSON repository in `src/smart_todo/repository.py` for `.smart-todo.json`, persisting `tasks` and `next_id`, validating every record before exposing any tasks, and saving complete mutations through a same-directory temporary file and atomic replacement; a missing file initializes an empty collection, while unreadable, malformed, missing-field, duplicate-ID, invalid-value, or invalid-sequence data returns `INVALID_DATA`, loads no tasks, and leaves the source file byte-for-byte unchanged; write failures return `IO_ERROR` without claiming success or replacing valid prior data.
- [ ] T009 [US1] Implement create and default-list operations in `src/smart_todo/service.py`: allocate the next positive ID only for a valid create, default omitted priority to MEDIUM, set new status to TODO, and list each task once in ascending ID order.
- [ ] T010 [US1] Implement deterministic `add` and `list` command handling in `src/smart_todo/cli.py` and connect it through `src/smart_todo/__main__.py`; emit stable task fields and error identifiers, and ensure invalid input or persisted data is never reported as success.

**Checkpoint**: User Story 1 is independently usable and its pytest tests pass.

## Phase 4: User Story 2 - Find and maintain tasks (Priority: P2)

**Goal**: Update task details atomically, filter by exact tag, and optionally sort by priority with deterministic tie ordering.

**Independent Test**: Create tasks across all priorities and tags, update one task, and verify exact-match filtering, empty results, HIGH/MEDIUM/LOW ordering, ascending-ID ties, and unchanged state after invalid or unknown-ID updates.

**Requirements / acceptance**: FR-007, FR-009, FR-010, FR-012, FR-014, FR-015; AC-002, AC-004–AC-009, AC-017.

### Tests for User Story 2

- [ ] T011 [P] [US2] Write failing service tests for partial-field updates, preservation of unspecified fields, atomic rejection of invalid title/priority/tag values, exact case-sensitive tag filtering, empty filter results, and HIGH/MEDIUM/LOW sorting with ascending-ID ties mapped to FR-007, FR-009, FR-010 and AC-002, AC-004, AC-006–AC-009, SC-007 in `tests/unit/test_organization.py`.
- [ ] T012 [P] [US2] Write failing CLI contract tests for `update ID` and `list --tag TAG [--sort priority]`, including NOT_FOUND, invalid-input errors, stable output, and filter-before-sort behavior mapped to FR-007, FR-009, FR-010, FR-012, FR-015 and AC-005–AC-009 in `tests/contract/test_cli_organization.py`.
- [ ] T013 [P] [US2] Write failing integration tests that independently verify exact-tag membership, zero-match output, priority order and ID tie-breaks, and identical results from equivalent starting states mapped to AC-006–AC-008, AC-017 and SC-002, SC-003 in `tests/integration/test_organization_acceptance.py`.

### Implementation for User Story 2

- [ ] T014 [US2] Implement atomic update, exact case-sensitive tag filtering, and optional priority sorting in `src/smart_todo/service.py`; validate all supplied update fields before mutation, use HIGH then MEDIUM then LOW, and break equal-priority ties by ascending ID.
- [ ] T015 [US2] Implement `update` and `list --tag/--sort` argument handling in `src/smart_todo/cli.py`; report unknown IDs as `NOT_FOUND`, reject invalid values without saving partial changes, and filter before sorting.

**Checkpoint**: User Stories 1 and 2 work; tests verify update, filter, sort, and rejection behavior.

## Phase 5: User Story 3 - Progress and remove tasks (Priority: P2)

**Goal**: Permit only the specified status transitions, delete tasks by ID, and preserve task state and the non-reused ID sequence across restarts.

**Independent Test**: Create a task, perform TODO → IN_PROGRESS → DONE, verify every other transition and unknown ID is rejected without mutation, delete a task, restart, and confirm its ID is not reused and remaining task fields persist.

**Requirements / acceptance**: FR-002, FR-008, FR-011–FR-015; AC-010–AC-020.

### Tests for User Story 3

- [ ] T016 [P] [US3] Write failing service tests for both allowed transitions and rejected same-state, reverse, skipped, and unsupported-status transitions; assert unchanged state on rejection, and cover deletion and NOT_FOUND for status/delete mapped to FR-008, FR-011, FR-012 and AC-010–AC-015, AC-020, SC-007 in `tests/unit/test_progress_removal.py`.
- [ ] T017 [P] [US3] Write failing CLI contract tests for `status ID STATUS` and `delete ID`, including stable success/error results and unsupported transitions mapped to FR-008, FR-011, FR-012, FR-015 and AC-010–AC-015, AC-020 in `tests/contract/test_cli_progress_removal.py`.
- [ ] T018 [P] [US3] Write failing integration tests for persisted transition state, deletion across restart, non-reuse of deleted IDs, 10-restart field preservation, and 100-repeat deterministic outcomes mapped to FR-002, FR-013, FR-014 and AC-016, AC-017, AC-019, SC-004–SC-006 in `tests/integration/test_progress_persistence.py`.

### Implementation for User Story 3

- [ ] T019 [US3] Implement status transitions and deletion in `src/smart_todo/service.py`; accept only TODO → IN_PROGRESS and IN_PROGRESS → DONE, reject every other transition without mutation, return NOT_FOUND for unknown IDs, and never decrement or reuse `next_id`.
- [ ] T020 [US3] Implement `status` and `delete` command handling in `src/smart_todo/cli.py`; persist only successful operations and return deterministic success/error results.

**Checkpoint**: All three stories are independently verified through service, repository, and CLI behavior.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Provide reproducible quality gates, deterministic harness execution, and immutable run evidence.

- [ ] T021 [P] Write failing tests for fixed command ordering, captured tool versions/commands/stdout/stderr/exit codes, pytest report creation, aggregate PASS/FAIL, and unique non-overwriting evidence directories mapped to constitution principle IV in `tests/integration/test_harness.py`.
- [ ] T022 Implement `harness/runner.py` to run pytest with per-run JUnit XML, `ruff check .`, `ruff format --check .`, and `bandit -q -r src` in a fixed order; capture command, available commit ID, Python/tool versions, stdout, stderr, per-command exit status, and aggregate PASS/FAIL under a unique `artifacts/harness/` run directory without overwriting prior failures or including secrets/unnecessary user data.
- [ ] T023 Run the full harness and quickstart acceptance scenarios; preserve complete initial/final run evidence and genuine failures under separate `artifacts/harness/` paths, review Bandit findings without suppressing them to force a pass, and retain repair feedback and rerun evidence.
- [ ] T024 Before merge, have a second contributor review non-trivial changes. Record the reviewer, review outcome, issues found, resolution status, and evidence location in `artifacts/harness/`; keep this review separate from final human acceptance.
- [ ] T025 After T024, have a human review the specification, changes, all harness evidence, and unresolved findings, then record a separate ACCEPT or REJECT decision with rationale in the final run evidence.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on project setup; provides isolated CLI testing.
- **User Story 1 (Phase 3)**: Depends on Setup and Foundational; establishes the model, repository, and core create/list workflow.
- **User Story 2 (Phase 4)**: Depends on User Story 1's model, repository, service, and CLI.
- **User Story 3 (Phase 5)**: Depends on User Story 1's model and repository; its implementation follows User Story 2 because both extend the same service and CLI modules.
- **Polish (Phase 6)**: Depends on all desired stories. T023 runs the harness and captures evidence; T024 follows for the second-contributor review; T025 follows for final human acceptance.

### User Story Dependencies

- **US1 (P1)**: No story dependency; MVP.
- **US2 (P2)**: Requires the shared task model, JSON repository, and base CLI from US1.
- **US3 (P2)**: Requires the shared task model, JSON repository, and base CLI from US1. US2 and US3 behavior is otherwise independent, but implementation changes the same `service.py` and `cli.py` files and should be integrated serially.

### Parallel Opportunities

- T002 can proceed alongside T001 after the project layout is agreed; T003 follows the scaffold.
- Within US1, T004–T006 are parallelizable test files after T003.
- Within US2, T011–T013 are parallelizable test files after US1 is complete.
- Within US3, T016–T018 are parallelizable test files after US1 is complete.
- US2 and US3 test authoring can be parallelized after US1 because the tests target distinct files; their shared service/CLI implementation tasks should be integrated serially.
- T021 can be written independently of story implementation, but T022 depends on the specified testable harness behavior; T023 depends on all implementation and test tasks; T024 depends on T023; T025 depends on T024.

## Parallel Examples

### User Story 1

```text
After T003:
Task: T004 tests/unit/test_model.py
Task: T005 tests/repository/test_repository.py
Task: T006 tests/contract/test_cli_capture.py
```

### User Story 2

```text
After US1:
Task: T011 tests/unit/test_organization.py
Task: T012 tests/contract/test_cli_organization.py
Task: T013 tests/integration/test_organization_acceptance.py
```

### User Story 3

```text
After US1:
Task: T016 tests/unit/test_progress_removal.py
Task: T017 tests/contract/test_cli_progress_removal.py
Task: T018 tests/integration/test_progress_persistence.py
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundational phases.
2. Complete US1 tests before its model, repository, service, and CLI implementation.
3. Validate US1 independently: create/list tasks, verify deterministic IDs/defaults/order, and ensure corrupt existing JSON fails closed.
4. Stop at the US1 checkpoint for MVP acceptance.

### Incremental Delivery

1. Add US2 update/filter/sort behavior after the US1 checkpoint and validate its exact tag and priority ordering cases.
2. Add US3 transitions/deletion after the US1 foundation and validate restart persistence and non-reused IDs.
3. Complete the harness gates and retain separate, complete evidence for initial failures and final reruns.

### Acceptance and Traceability

- Tests identify their covered FR, AC, and (where measurable) SC directly in their task descriptions.
- The test suite must cover all FR-001–FR-015 and AC-001–AC-020, including invalid-input atomicity, unknown IDs, corruption handling, deterministic output/state, 100-task list/filter/sort checks, 10 restarts, and 100 equivalent executions.
- Automated PASS is necessary but not sufficient: complete final human review and record ACCEPT or REJECT with rationale.
