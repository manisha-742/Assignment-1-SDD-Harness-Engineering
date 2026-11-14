# Research: Smart Todo & Task CLI

Research resolves implementation choices within the approved scope in [spec.md](./spec.md). The language, CLI-only interface, local JSON storage, pytest, Ruff, and Bandit are fixed by the assignment and constitution; no additional service or runtime dependency is needed.

## Local JSON persistence

**Decision**: Use Python's standard-library `json`, `tempfile`, and `os.replace`. A missing data file represents a first run and loads an empty collection with `next_id` 1. For a successful mutation, serialize and validate the complete candidate document before touching the destination, stage it in the same directory, flush and close it, then replace the destination. On write failure, report `IO_ERROR` and preserve the prior file. Malformed, unreadable, or semantically invalid existing data reports `INVALID_DATA`, loads no tasks, and is never overwritten. The loader accepts the entire document or none of it.

**Rationale**: Same-directory staging avoids cross-filesystem replacement; replacing only after a complete write avoids truncating valid state on ordinary write failures. Distinguishing a missing file from an unreadable existing file supports first use without weakening the explicit fail-closed behavior for corrupt data. `IO_ERROR` keeps write failures distinct from invalid input data.

**Alternatives considered**:
- Directly overwrite the JSON file: simpler but a failed write can leave it truncated.
- Treat a missing file as `INVALID_DATA`: would prevent initial use before a task file exists.
- Accept partial records or reset invalid files: explicitly conflicts with FR-013 and AC-018.
- Add file locking or multi-writer coordination: unnecessary for the stated local single-user scope; concurrent writers are out of scope.

**References**: [Python `os.replace`](https://docs.python.org/3.13/library/os.html#os.replace), [Python `tempfile`](https://docs.python.org/3.13/library/tempfile.html), [Python `json`](https://docs.python.org/3.13/library/json.html).

## Deterministic pytest strategy

**Decision**: Use pytest with `tmp_path` for isolated files, controlled fixtures, captured CLI output, explicit exit-status and resulting-state assertions, and deterministic parameterized cases. Exercise unit behavior, repository persistence, CLI contracts, restart behavior, corruption handling, and repeated execution without ambient user data or network access.

**Rationale**: Isolated temporary paths prevent order-dependent or developer-state-dependent tests. Exact assertions on command results and serialized state directly verify deterministic behavior and acceptance criteria.

**Alternatives considered**:
- Unit tests alone: fast but do not validate the CLI contract and user-visible outcomes.
- Shared real home-directory files: less setup but risks cross-test and user-data interference.
- Network-dependent checks: not applicable to this offline local feature.

**References**: [pytest `tmp_path`](https://docs.pytest.org/en/stable/how-to/tmp_path.html), [pytest output capture](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html), [pytest flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html), [pytest JUnit XML output](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files).

## Ruff and Bandit quality gates

**Decision**: Configure Ruff for Python 3.13 with an explicit rule set and run both `ruff check` and `ruff format --check` as non-mutating gates. Run Bandit recursively over application source. Record versions, commands, outputs, and exit codes; review Bandit findings rather than suppressing them to force a pass.

**Rationale**: Separate lint and formatting checks make the quality gate reproducible and prevent the gate itself from changing files. A declared Python target avoids checking against an unintended language version. Keeping Bandit results visible preserves security signal.

**Alternatives considered**:
- Running an auto-fixer as the gate: mutates the implementation during verification and obscures the exact checked input.
- Enabling every possible Ruff rule immediately: may add unrelated noise; the rule set should remain explicit and relevant.
- Bandit `--exit-zero` or unreviewed exclusions: hides failures and conflicts with harness-integrity principles.
- A baseline for findings: may be useful for existing code later but is unnecessary for this new application and must not hide new findings.

**References**: [Ruff configuration](https://docs.astral.sh/ruff/configuration/), [Ruff linter](https://docs.astral.sh/ruff/linter/), [Bandit usage](https://bandit.readthedocs.io/en/latest/start.html), [Bandit options](https://bandit.readthedocs.io/en/latest/man/bandit.html).

## Harness evidence and repair

**Decision**: Each harness run writes a separate bundle under `artifacts/harness/` containing the exact commands, commit identifier when available, Python and tool versions, stdout, stderr, per-command exit status, pytest machine-readable report, and aggregate PASS/FAIL. Never overwrite initial, failed, repaired, or final run results. Record repair feedback against the failing requirement/test and retain the human ACCEPT/REJECT decision with its rationale. Evidence must exclude secrets and unnecessary user data.

**Rationale**: Run-specific bundles preserve the audit trail required by the constitution, while machine-readable test reports and captured output make failures actionable and reruns comparable. Local artifacts satisfy the assignment without adding an external workflow service.

**Alternatives considered**:
- Keep only the latest run: destroys genuine failure history.
- Upload evidence to a hosted artifact service: adds an out-of-scope external dependency.
- Capture only an aggregate status: insufficient to diagnose and preserve genuine failures.

**References**: [pytest reports and JUnit XML](https://docs.pytest.org/en/stable/how-to/output.html), [GitHub workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts) (considered but not selected).
