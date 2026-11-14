# CLI Contract: Smart Todo & Task CLI

This contract maps the approved task operations to a minimal command-line surface. It does not add behavior beyond [spec.md](../spec.md).

## Invocation

The planned entry point is `python -m smart_todo` (with the package available on `PYTHONPATH` or installed in the active environment). Commands are local and operate on `.smart-todo.json` in the current working directory. Tests use an isolated temporary working directory and file.

| Operation | Command form | Behavior |
|---|---|---|
| Create | `python -m smart_todo add --title TITLE [--priority LOW\|MEDIUM\|HIGH] [--tag TAG ...]` | Allocate a positive increasing ID; default priority to `MEDIUM`; set status to `TODO`. |
| List | `python -m smart_todo list [--tag TAG] [--sort priority]` | Without sorting, order by ascending ID. Filtering is exact and case-sensitive. If requested with filtering, filter before priority sorting. |
| Update | `python -m smart_todo update ID [--title TITLE] [--priority LOW\|MEDIUM\|HIGH] [--tag TAG ...]` | Change only supplied title/priority/tags after validating the complete update. |
| Change status | `python -m smart_todo status ID STATUS` | Accept only `TODO → IN_PROGRESS` and `IN_PROGRESS → DONE`. |
| Delete | `python -m smart_todo delete ID` | Remove the task but preserve the ID sequence. |

## Results and errors

- Successful commands report their result using a stable, deterministic representation. Listed task records contain `id`, `title`, `priority`, `tags`, and `status`; list order follows the rules above.
- An unknown task ID for update, status change, or delete reports `NOT_FOUND`.
- Invalid input, invalid transitions, or invalid persisted data are failures and must not report success.
- Unreadable, malformed, or invalid persisted data reports `INVALID_DATA`, exposes no tasks, and leaves the source file unchanged.
- Repeating an operation with the same valid inputs and starting state produces the same visible result and resulting state.

Exact prose/punctuation is an implementation-level choice, but error identifiers, task fields, operation semantics, and ordering are contractually stable.

## Requirement trace

| Contract behavior | Requirements / acceptance |
|---|---|
| Create, defaults, required fields | FR-001–FR-005; AC-001, AC-002 |
| List and ordering | FR-006, FR-010; AC-003, AC-007 |
| Update and not found | FR-007, FR-012; AC-002, AC-004, AC-005, AC-009 |
| Exact tag filter | FR-009; AC-006, AC-008 |
| Status transition | FR-011; AC-010–AC-013, AC-020 |
| Delete and non-reused ID | FR-002, FR-008; AC-014, AC-015, AC-019 |
| Persistence and determinism | FR-013, FR-014; AC-016–AC-018 |
