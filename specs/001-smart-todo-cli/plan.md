# Implementation Plan: Smart Todo & Task CLI

**Branch**: `main` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Approved feature specification in `specs/001-smart-todo-cli/spec.md`

## Summary

Build a deterministic, single-user Python 3.13 command-line task manager with validated task operations and local JSON persistence. Keep command handling, task model/validation, business rules, persistence, tests, and harness/evidence capture in small, separate modules. Use pytest for deterministic requirement-mapped tests, Ruff for code-quality checks, and Bandit for security analysis. Preserve invalid persisted data and fail closed rather than resetting it.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Python standard library for CLI and JSON handling; pytest, Ruff, and Bandit as development tools

**Storage**: Local JSON file containing the task collection and next task ID

**Testing**: pytest; deterministic unit, repository/persistence, CLI contract, and end-to-end behavior tests

**Target Platform**: Local machine with Python 3.13; command-line only

**Project Type**: Single Python CLI application

**Performance Goals**: No latency or throughput target is specified; support the assignment's 100-task verification scenarios with straightforward in-memory operations.

**Constraints**: Offline/local use; no web UI, authentication, database, cloud services, microservices, Docker, Kubernetes, or unrelated features. Invalid persisted JSON must produce `INVALID_DATA`, load no tasks, and remain unchanged. Harness results and genuine failures must be preserved.

**Scale/Scope**: One local user and a small task collection. Required measured scenarios include 100 tasks and 100 repeated deterministic executions.

## Constitution Check

*GATE: Must pass before Phase 0 research and again after Phase 1 design.*

| Principle / gate | Plan alignment | Result |
|---|---|---|
| I. Deterministic CLI and Controlled Task State | Explicit ordering, validation, stable IDs, and the two permitted state transitions are defined in the spec and contracts. | PASS |
| II. Requirements Traceability | Tests are mapped to FRs and ACs; acceptance evidence is retained. | PASS |
| III. Automated Deterministic Testing | pytest covers requirements and measurable acceptance criteria; quality/security gates are included. | PASS |
| IV. Harness Integrity and Evidence Preservation | Preserve initial results, failures, repair feedback, reruns, and final review; do not weaken gates. | PASS |
| V. Reproducible, Secure, and Maintainable Delivery | Standard-library runtime, local JSON, reproducible commands, and a deliberately small modular design. | PASS |
| Technology, Security and Data Integrity | Python 3.13, pytest, Ruff, Bandit, boundary validation, and fail-closed persistence are planned. | PASS |
| Verification, Evidence and Human Review | Automated PASS is necessary but final acceptance remains a documented human ACCEPT/REJECT. | PASS |

No constitution violations or scope exceptions are required.

## Design Decisions

- Start task IDs at 1 and persist `next_id`; increment it only when a valid task is created. A deleted ID is never made available again.
- Keep priorities and statuses as closed enumerations. Apply priority order HIGH, MEDIUM, LOW, then ascending ID; default and unprioritized listing order is ascending ID.
- Use exact, case-sensitive tag membership. Apply tag filtering before optional priority sorting.
- Store a single JSON document with `next_id` and `tasks`. A missing file starts as an empty collection; an unreadable existing file, malformed JSON, or structurally/semantically invalid document returns `INVALID_DATA`, loads no tasks, and is never replaced with an empty collection.
- For successful updates, validate all proposed fields before changing the in-memory task. Persist successful mutations by writing a temporary sibling file and replacing the target, so incomplete writes do not leave a partially serialized document. A write failure reports `IO_ERROR` and preserves the prior file.
- Keep the persistence path local to the working directory as `.smart-todo.json`; repository tests inject a temporary path. This avoids remote or platform-specific storage dependencies.
- Keep CLI output and error codes stable and deterministic. `NOT_FOUND`, `INVALID_DATA`, and `IO_ERROR` are stable identifiers; invalid user input and unsupported transitions are rejected without partial mutation.
- Keep the harness as a deterministic command runner that records commands, tool versions, available commit identifier, exit status, stdout, stderr, pytest report, and aggregate PASS/FAIL for each run. Each run's evidence is retained separately under `artifacts/harness/`; repairs do not overwrite initial failures and evidence excludes secrets and unnecessary user data.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo-cli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── cli.md
    └── persistence.md
```

### Source Code (repository root)

```text
src/
└── smart_todo/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py                 # Argument parsing, command dispatch, stable output
    ├── model.py               # Task types, enums, and input/data validation
    ├── service.py             # Task operations, ordering, filtering, transitions
    └── repository.py          # JSON load/validate/save and ID sequence persistence

tests/
├── unit/                      # Model validation and service behavior
├── repository/                # JSON schema, fail-closed, and restart behavior
├── contract/                  # CLI arguments, outputs, and error behavior
└── integration/               # End-to-end deterministic acceptance scenarios

harness/
└── runner.py                  # Fixed quality/test command sequence and evidence capture

artifacts/
└── harness/                   # Per-run logs/results and repair/final-review records
```

**Structure Decision**: One `smart_todo` package with four focused modules, supported by pytest suites organized by concern and one small harness runner. No framework, external service, or additional application layer is needed for a local single-user CLI.

## Test Strategy and Traceability

Every requirement and acceptance criterion has a planned deterministic pytest assertion. Test suites are separated by concern; tests use temporary JSON files and controlled inputs rather than developer state.

| Requirement | Acceptance coverage | Planned test focus |
|---|---|---|
| FR-001 | AC-001, AC-002 | Unit/CLI: valid title creation; empty and whitespace-only title rejected |
| FR-002 | AC-001, AC-016, AC-017, AC-019 | Service/repository: increasing stable IDs, restart stability, deterministic allocation, no reuse after delete/restart |
| FR-003 | AC-001, AC-004, AC-009 | Model/service: empty and supplied tags, replace tags, reject invalid/duplicate tags atomically |
| FR-004 | AC-001, AC-003, AC-007, AC-009 | Model/service: allowed values, MEDIUM default, priority sorting, invalid priority rejection |
| FR-005 | AC-001, AC-010 | Service: initial TODO status and valid first transition |
| FR-006 | AC-003 | Contract/integration: exactly-once listing with all fields, ascending IDs |
| FR-007 | AC-002, AC-004, AC-005, AC-009 | Service/CLI: partial-field updates preserve other fields; invalid update is atomic; unknown ID is NOT_FOUND |
| FR-008 | AC-014, AC-015, AC-019 | Service/repository: deletion, unknown-ID behavior, sequence remains monotonic |
| FR-009 | AC-006, AC-008 | Service/contract: exact case-sensitive tag matching and empty result |
| FR-010 | AC-007 | Service/contract: HIGH/MEDIUM/LOW ordering and ascending-ID ties |
| FR-011 | AC-010, AC-011, AC-012, AC-020 | Unit/contract: both permitted transitions succeed; all other and unsupported statuses reject without mutation |
| FR-012 | AC-005, AC-013, AC-015 | Service/CLI: update, status, and delete of unknown IDs return NOT_FOUND without changes |
| FR-013 | AC-016, AC-018 | Repository/integration: round-trip and restart preservation; malformed, unreadable, missing-field, duplicate-ID, or invalid-value files fail closed and remain unchanged; missing file initializes an empty first-run collection |
| FR-014 | AC-017 | Deterministic contract/integration: same input and state yield identical output and state |
| FR-015 | AC-001 through AC-016 | CLI contract/integration: required operations are available only through the command-line interface |

| Success criterion | Planned verification |
|---|---|
| SC-001 | Create/list 100 tasks; compare returned IDs and all required fields; assert uniqueness and exactly-once membership |
| SC-002 | Compare exact-tag filter results against independently constructed expected IDs, including case variants |
| SC-003 | Assert complete sorted sequence and tie ordering for mixed priorities |
| SC-004 | Exercise both accepted transitions and every rejected transition; compare state snapshots |
| SC-005 | Reconstruct/restart the application 10 times and compare all persisted fields |
| SC-006 | Run 100 executions from equivalent initial snapshots and compare visible outcomes and resulting state |
| SC-007 | Parameterize invalid values and unknown IDs; assert stable errors and unchanged task snapshots |

## Verification and Evidence Workflow

1. Run the fixed harness command sequence: pytest, Ruff lint, Ruff format check, then Bandit; record each command's output and status and aggregate as PASS only if all required gates pass.
2. Preserve the initial generated implementation's complete run evidence under `artifacts/harness/`, including genuine failures, tool versions, and commands. Do not edit or remove failed results.
3. Give failures to the implementer as repair feedback tied to the requirement/test and captured output.
4. After repair, rerun the same harness commands and acceptance scenarios; preserve that run separately and retain links to the initial failure and repair.
5. A human reviews the specification, changes, all harness evidence, and unresolved findings, then records ACCEPT or REJECT with rationale. A harness PASS alone is not acceptance.

## Complexity Tracking

No complexity or constitution exceptions.
