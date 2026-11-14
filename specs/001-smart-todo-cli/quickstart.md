# Quickstart: Smart Todo & Task CLI

This is the planned validation guide for the CLI contract in [contracts/cli.md](./contracts/cli.md). It documents commands and expected outcomes, not implementation code.

## Prerequisites

- Python 3.13
- pytest, Ruff, and Bandit available in the project environment
- Run commands from the repository root unless noted otherwise

## Quality and test gates

Run the deterministic harness entry point:

```text
python harness/runner.py
```

The runner executes the same fixed checks in the same order:

```text
python -m pytest --junitxml=<run-dir>/pytest.xml
ruff check .
ruff format --check .
bandit -q -r src
```

The runner supplies a unique per-run path for `<run-dir>`. Expected: each check reports its command and exit status; overall `PASS` only when all checks pass. On any failure, overall result is `FAIL`, and the complete output remains in that run's separate evidence directory under `artifacts/harness/`. Bandit findings are reviewed, not suppressed merely to obtain a pass. Evidence includes available commit and tool versions and is retained without overwriting earlier failures; it must not contain secrets or unnecessary user data.

## Acceptance scenarios

Use an isolated temporary working directory for each scenario to avoid dependence on a developer's real task file.

1. Run `python -m smart_todo add --title "Review report" --tag work`, then list. Verify its positive ID, title, `MEDIUM` priority, `work` tag, and `TODO` status.
2. Create several tasks with all three priorities. Verify default list order by ascending ID and priority sort order `HIGH`, `MEDIUM`, `LOW`, ties by ascending ID.
3. Run `python -m smart_todo list --tag work` and verify exact case-sensitive membership; verify no match returns an empty list.
4. Reject empty/whitespace titles, invalid priority/tag input, and unsupported transitions; verify no partial task change.
5. Verify the only successful transitions are `TODO → IN_PROGRESS` and `IN_PROGRESS → DONE`. Verify other transitions and unknown IDs return errors and leave state unchanged.
6. Delete a task, restart the CLI, create another task, and verify the deleted ID is not reused.
7. Restart after saving tasks and verify every task field survives.
8. Start with no data file and verify the CLI initializes an empty collection. Then supply malformed, unreadable, or semantically invalid JSON. Verify `INVALID_DATA`, no loaded tasks, and byte-for-byte unchanged file contents.
9. Repeat the same operation 100 times from equivalent initial state snapshots. Verify identical visible results and resulting state.

The pytest cases are mapped to FRs, ACs, and measurable success criteria in the plan's [traceability section](./plan.md#test-strategy-and-traceability) and feature specification. Exact command arguments are defined in [contracts/cli.md](./contracts/cli.md).

## Harness feedback and final review

Preserve the initial full output and failed checks as immutable run evidence. Provide repair feedback with the requirement/test identifier and failure output, make the repair, and rerun the same harness command. Preserve the rerun separately and keep the link to the initial failure. A human reviewer then records final `ACCEPT` or `REJECT` and rationale after reviewing the specification, implementation, and all evidence; automated PASS alone is not acceptance.
