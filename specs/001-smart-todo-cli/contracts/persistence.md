# Persistence Contract: Smart Todo & Task CLI

## File format

The repository stores one UTF-8 JSON document in `.smart-todo.json` relative to the current working directory:

```json
{
  "next_id": 1,
  "tasks": []
}
```

Each task record contains exactly the persisted task fields `id`, `title`, `priority`, `tags`, and `status`, as defined in [data-model.md](../data-model.md). `next_id` is persisted independently of the current tasks so deleted IDs cannot be reused after a restart.

## Load and validation

- Parse the full JSON document and validate its structure and every task before making the collection available.
- IDs must be positive integers, unique, and less than `next_id`. `next_id` must be a positive integer greater than every persisted task ID.
- Validate title, priority, tags, and status using the data-model rules. Reject duplicates in tags.
- A missing file is a first-run empty collection with `next_id` 1. An unreadable existing file, malformed JSON, or any invalid record is reported as `INVALID_DATA` under FR-013 and AC-018. Load no tasks and do not modify the file.
- Do not silently initialize, truncate, partially accept, or overwrite an invalid existing file.

## Save and restart behavior

- Serialize fields in a stable order and task records in ascending ID order.
- For a successful mutation, write the complete next state to a temporary file beside the target, flush/close it, then replace the target. A failed operation does not save.
- A failed write/replacement reports `IO_ERROR` and preserves the prior valid file; it must not be reported as a successful mutation.
- Persist `next_id` on every successful create so deletion and restart do not reset the allocator.
- Reloading a valid saved file restores all task fields and the sequence. Tests verify persistence through repeated repository reconstruction/application restarts.

The file is local and is not shared or synchronized. Cross-process concurrent writers and migration of future schema versions are outside this feature's scope.
