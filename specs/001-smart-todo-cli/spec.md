# Feature Specification: Smart Todo & Task CLI

**Feature Branch**: `not-created`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: Create a deterministic local command-line task manager with task creation, listing, updates, deletion, tag filtering, priority sorting, controlled status transitions, and JSON persistence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture and review tasks (Priority: P1)

As a person managing daily work, I want to create tasks and review my task list so that I can
keep track of what needs to be done.

**Why this priority**: Task capture and review form the minimum useful task-management workflow.

**Independent Test**: Create tasks with and without tags, then list them and verify their
identifiers, titles, priorities, tags, and initial statuses.

**Acceptance Scenarios**:

1. **AC-001** **Given** a task collection, **When** the user creates a task with a non-empty
   title and zero or more valid tags, with or without a supplied priority, **Then** the system
   assigns a unique ID, sets status to TODO, uses the supplied priority or MEDIUM by default,
   stores the tags, and confirms creation.
2. **AC-002** **Given** a task collection or existing task, **When** the user creates a task
   or updates its title to an empty or whitespace-only value, **Then** the system rejects the
   request and leaves the collection unchanged.
3. **AC-003** **Given** stored tasks, **When** the user lists tasks, **Then** each task is
   returned once with its ID, title, priority, tags, and status in ascending ID order.

---

### User Story 2 - Find and maintain tasks (Priority: P2)

As a person managing daily work, I want to update task details, filter by tag, and sort by
priority so that I can keep task information current and focus on relevant work.

**Why this priority**: Updating and organizing tasks makes the task list useful beyond initial
capture.

**Independent Test**: Create several tasks, update one, filter by a tag, and sort the matching
results by priority.

**Acceptance Scenarios**:

1. **AC-004** **Given** an existing task, **When** the user updates its title, priority, or tags
   with valid values, **Then** those fields change and all other task fields remain unchanged.
2. **AC-005** **Given** no task exists for an ID, **When** the user updates that ID, **Then**
   the system returns NOT_FOUND and leaves the collection unchanged.
3. **AC-006** **Given** tasks with different tags, **When** the user filters by one tag,
   **Then** only tasks containing that exact tag are returned.
4. **AC-007** **Given** tasks with different priorities, **When** the user requests priority
   sorting, **Then** results are ordered HIGH, MEDIUM, LOW, with tasks of equal priority
   ordered by ascending ID.
5. **AC-008** **Given** a requested tag matches no task, **When** the user filters by that
   tag, **Then** the system returns an empty result without changing any task.
6. **AC-009** **Given** an invalid priority or tag value, **When** the user creates or updates
   a task with that value, **Then** the system rejects the request without changing task data.

---

### User Story 3 - Progress and remove tasks (Priority: P2)

As a person managing daily work, I want to move tasks through their permitted statuses and
remove tasks I no longer need so that the list reflects current work.

**Why this priority**: Status progression and removal keep saved tasks accurate and relevant.

**Independent Test**: Create a task, perform both permitted status transitions, verify
rejected transitions leave it unchanged, and remove it by ID.

**Acceptance Scenarios**:

1. **AC-010** **Given** a task in TODO, **When** the user changes its status to IN_PROGRESS,
   **Then** the new status is saved and reported.
2. **AC-011** **Given** a task in IN_PROGRESS, **When** the user changes its status to DONE,
   **Then** the new status is saved and reported.
3. **AC-012** **Given** a task and any transition other than TODO to IN_PROGRESS or
   IN_PROGRESS to DONE, **When** the user requests that transition, **Then** the system
   rejects it and leaves the task unchanged.
4. **AC-013** **Given** no task exists for an ID, **When** the user requests a status change
   for that ID, **Then** the system returns NOT_FOUND and leaves the collection unchanged.
5. **AC-014** **Given** an existing task, **When** the user deletes it by ID, **Then** it is
   absent from subsequent lists and the system confirms deletion.
6. **AC-015** **Given** no task exists for an ID, **When** the user deletes that ID, **Then**
   the system returns NOT_FOUND and leaves the collection unchanged.
7. **AC-016** **Given** saved tasks, **When** the application is restarted, **Then** every
   task retains its ID, title, priority, tags, and status.
8. **AC-019** **Given** a task has been deleted and the application restarted, **When**
   another task is created, **Then** the deleted task's ID is not reused.
9. **AC-020** **Given** an unsupported status value, **When** the user requests it for a
   task, **Then** the system rejects it and leaves the task unchanged.

### Edge Cases

- **AC-017** Repeating the same valid command against the same starting task state produces
  the same user-visible result and resulting task state.
- **AC-018** If persisted task data is invalid, missing required fields, or contains duplicate
  IDs, the system rejects it without silently resetting or partially accepting the collection.
- An update, deletion, or status change with an unknown ID returns NOT_FOUND and does not
  modify the collection.
- An unsupported status or priority is rejected without changing task data.
- A tag filter is an exact match; a task with no matching tag is not included.
- When a priority sort has ties, the result order remains stable by ascending task ID.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let users create tasks with a non-empty title. Titles MUST be
  rejected if empty or composed only of whitespace.
- **FR-002**: The system MUST assign each task a unique, stable ID deterministically. IDs
  MUST remain stable through updates and restarts and MUST NOT be reused after deletion.
- **FR-003**: A task MAY have zero or more tags. The system MUST allow valid tags to be
  added or replaced when creating or updating a task.
- **FR-004**: Task priority MUST be one of LOW, MEDIUM, or HIGH. If the user omits priority
  when creating a task, it MUST default to MEDIUM.
- **FR-005**: Every new task MUST have status TODO.
- **FR-006**: The system MUST list all tasks. Each returned task MUST include ID, title,
  priority, tags, and status. Default list order MUST be ascending ID.
- **FR-007**: The system MUST let users update an existing task by ID, including its title,
  priority, and tags. Invalid values MUST be rejected without partial changes. An unknown ID
  MUST return a clear NOT_FOUND result or error.
- **FR-008**: The system MUST let users delete a task by ID. An unknown ID MUST return a
  clear NOT_FOUND result or error. A deleted ID MUST NOT be reused.
- **FR-009**: The system MUST filter tasks by tag and return only tasks containing the exact
  requested tag. A filter with no matches MUST return an empty result.
- **FR-010**: When priority sorting is requested, tasks MUST be ordered HIGH, then MEDIUM,
  then LOW. Tasks with equal priority MUST be ordered by ascending ID.
- **FR-011**: Supported statuses MUST be TODO, IN_PROGRESS, and DONE. The only permitted
  transitions MUST be TODO to IN_PROGRESS and IN_PROGRESS to DONE. The system MUST let
  users request a transition for a task by ID. All other status transitions MUST be rejected
  without changing task data.
- **FR-012**: An unknown ID used for update, deletion, or status change MUST return
  NOT_FOUND and MUST NOT change task data.
- **FR-013**: The system MUST persist task data locally as JSON and preserve every task's ID,
  title, priority, tags, and status, along with the identifier sequence, across application
  restarts. Required fields MUST be validated; invalid or duplicate records MUST be rejected
  rather than silently discarded.
- **FR-014**: For identical valid inputs and identical persisted task state, the system MUST
  produce identical user-visible results and resulting state changes. Listing, filtering,
  sorting, validation, and status-transition outcomes MUST be deterministic.
- **FR-015**: The system MUST provide the required task operations through a command-line
  interface only.

### Project Constraints

- The application MUST use Python 3.13 and local JSON persistence.
- Automated tests MUST use pytest. Python code MUST pass Ruff linting and static quality
  checks and Bandit security analysis.
- Bandit findings MUST be reviewed and MUST NOT be suppressed solely to obtain a passing
  result. The project constitution governs additional testing, harness integrity, evidence,
  and human-acceptance requirements.
- The feature MUST NOT add a web UI, authentication, a database, cloud services,
  microservices, Docker/Kubernetes, or unrelated functionality.

### Key Entities *(include if feature involves data)*

- **Task**: A unit of work with a unique ID, title, priority, tags, and status.
- **Task Collection**: The locally saved tasks and identifier sequence that remain available
  after application restarts.

### Acceptance Coverage

| Requirement | Acceptance criteria |
|---|---|
| FR-001 | AC-001, AC-002 |
| FR-002 | AC-001, AC-016, AC-017, AC-019 |
| FR-003 | AC-001, AC-004, AC-009 |
| FR-004 | AC-001, AC-003, AC-007, AC-009 |
| FR-005 | AC-001, AC-010 |
| FR-006 | AC-003 |
| FR-007 | AC-002, AC-004, AC-005, AC-009 |
| FR-008 | AC-014, AC-015, AC-019 |
| FR-009 | AC-006, AC-008 |
| FR-010 | AC-007 |
| FR-011 | AC-010, AC-011, AC-012, AC-020 |
| FR-012 | AC-005, AC-013, AC-015 |
| FR-013 | AC-016, AC-018 |
| FR-014 | AC-017 |
| FR-015 | AC-001 through AC-016 |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a collection of 100 tasks, every task is listed exactly once with its ID,
  title, priority, tags, and status, and no two tasks share an ID.
- **SC-002**: Filtering by a tag returns 100% of tasks containing that exact tag and 0 tasks
  that do not contain it.
- **SC-003**: Every priority-sorted result places all HIGH tasks before MEDIUM tasks and all
  MEDIUM tasks before LOW tasks; equal-priority tasks remain in ascending ID order.
- **SC-004**: Both permitted status transitions succeed, and every other transition is
  rejected with zero task-state changes.
- **SC-005**: After 10 application restarts, 100% of saved task IDs, titles, priorities, tags,
  and statuses retain their values.
- **SC-006**: For 100 repeated executions of the same valid command against the same initial
  task state, the user-visible result and resulting task state are identical.
- **SC-007**: All invalid values and unknown IDs covered by the requirements are rejected
  without partial task changes; unknown IDs return NOT_FOUND.

## Assumptions

- The application is for one local user; authentication, collaboration, and remote
  synchronization are out of scope.
- If priority is omitted during creation, it defaults to MEDIUM.
- Task IDs are positive integers assigned in increasing order and are never reused.
- Titles are trimmed at their outer whitespace before storage.
- Tags are trimmed, non-empty, case-sensitive strings; duplicate tags on one task are
  rejected. A task without tags has an empty tag list.
- Tag filtering is an exact, case-sensitive match. Filtering and priority sorting may be
  requested together; filtering is applied before sorting.
- Tasks with equal priority are ordered by ascending ID. Unsorted task lists are also in
  ascending ID order.
- A status request for the task's current status is rejected as an unsupported transition;
  only the two transitions listed in FR-011 are accepted.
- Project technology and engineering-quality constraints are fixed by the assignment and
  project constitution; this specification adds no other technical architecture.
