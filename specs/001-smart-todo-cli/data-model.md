# Data Model: Smart Todo & Task CLI

The model implements the entities and constraints in [spec.md](./spec.md). The persisted contract is defined in [contracts/persistence.md](./contracts/persistence.md).

## Task

A unit of work in the user's local collection.

| Field | Type | Constraints |
|---|---|---|
| `id` | positive integer | Unique within the collection; allocated from the persisted increasing sequence; stable across updates and restarts; never reused after deletion |
| `title` | string | Required; reject empty or whitespace-only input; trim outer whitespace before storing |
| `priority` | enum string | Exactly `LOW`, `MEDIUM`, or `HIGH`; new tasks default to `MEDIUM` |
| `tags` | list of strings | Zero or more; each trimmed, non-empty, case-sensitive; duplicate tags on one task rejected; no tags represented by an empty list |
| `status` | enum string | Exactly `TODO`, `IN_PROGRESS`, or `DONE`; new tasks start as `TODO` |

### Task validation and state

- Validate all fields before creating or updating a task. A rejected operation leaves task data unchanged.
- Updates may change title, priority, and/or tags; ID and status are not update fields.
- Status changes accept only `TODO → IN_PROGRESS` and `IN_PROGRESS → DONE`. A same-status request and every other transition are rejected without mutation.
- An unknown ID on update, delete, or status change produces `NOT_FOUND` and no collection change.
- List order is ascending ID. Priority order is `HIGH`, `MEDIUM`, `LOW`, with ascending ID within each priority.
- Tag membership uses exact, case-sensitive equality. If tag filtering and priority sorting are combined, filter first, then sort.

## Task Collection

The repository-owned collection holds tasks and the monotonic ID allocator state.

| Field | Type | Constraints |
|---|---|---|
| `tasks` | list of Task records | No duplicate IDs; each record must satisfy Task validation |
| `next_id` | positive integer | ID to allocate next; strictly greater than every task ID currently present; persists even when the task with the highest prior ID has been deleted |

An empty newly initialized collection has `next_id` equal to 1. A successful creation consumes the current `next_id` and advances it by one. Failed creation and deletion do not decrement or reset the sequence.

## Invalid persisted data

The repository validates the entire document before accepting any tasks. Missing required fields, wrong types, invalid enum values, invalid titles/tags, duplicate or non-positive IDs, an invalid sequence, malformed JSON, or failure to read an existing file produce `INVALID_DATA` and an empty in-memory result. A missing file is a first-run empty collection. No partial task collection is exposed and no write is made to invalid source data.

## Determinism

For identical input and collection state, validation outcomes, operations, list/filter/sort results, status transitions, and user-visible outcomes are identical. No timestamps, random identifiers, or external state are required for task behavior.
