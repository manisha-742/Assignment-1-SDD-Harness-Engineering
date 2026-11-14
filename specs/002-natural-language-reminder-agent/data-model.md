# Data Model: Natural-Language Reminder Agent

The model defines request context, a single reminder interpretation, evaluation cases, and
immutable per-run evidence. It does not define or persist reminder records.

## Runtime Context

One context accompanies each interpretation.

| Field | Type | Constraints |
|---|---|---|
| `reference_instant` | timezone-aware date-time | In normal use, derived from the local system clock. In evaluation, fixed explicitly per case. |
| `time_zone` | IANA time-zone name | Must resolve through `zoneinfo`; all response date/time values use this zone. |
| `locale` | configured locale identifier | Used for locale-sensitive numeric date interpretation. If absent or not established for a case, ambiguous numeric dates require clarification. |
| `source` | enum: `runtime`, `evaluation` | Identifies normal context versus fixed fixture context; not included in model output. |

Evaluation contexts are immutable case inputs. Tests never read the host wall clock or locale.

## Reminder Interpretation

One response for one input. All eight fields are required in JSON; nullable values are explicit
JSON `null`. The published structure is [reminder-output.schema.json](./contracts/reminder-output.schema.json);
conditional rules below are enforced by the application validator.

| Field | Type | Constraints |
|---|---|---|
| `intent` | enum string | Exactly `create_reminder`, `reschedule_reminder`, `snooze_reminder`, or `unsupported`. |
| `task` | string or null | The underlying reminder action/object, including for changes. Non-empty when supplied; null for unsupported or unresolved action. |
| `date` | ISO date string or null | A real Gregorian date in `YYYY-MM-DD`; null if unresolved. Required for a fully resolved supported intent. |
| `time` | 24-hour time string or null | Valid local `HH:MM` from `00:00` through `23:59`; null if unresolved. Required for a fully resolved supported intent. |
| `needs_clarification` | boolean | True only for a recognizable supported intent with materially missing or ambiguous information. |
| `clarification_question` | string or null | Non-empty and focused exactly when clarification is needed; null otherwise. |
| `target_reminder` | string or null | User-provided description for a resolved reschedule/snooze target; no database lookup or existence claim. Null for create/unsupported or unresolved target. |
| `snooze_duration_minutes` | positive integer or null | Positive whole minutes for a resolved snooze; null for other intents or unresolved duration. |

### Cross-field invariants

- `create_reminder`: task, date, and time are non-null when resolved; target and snooze duration
  are null.
- `reschedule_reminder`: a resolved interpretation includes task, target, complete resulting
  date, and complete resulting time; snooze duration is null.
- `snooze_reminder`: a resolved interpretation includes task, target, positive duration, and
  resulting date/time calculated from the fixed or runtime reference instant.
- `unsupported`: task, date, time, target, and snooze duration are null; clarification is false
  and its question is null.
- A supported clarification response has a non-empty question. Known valid values may remain;
  unresolved critical values are null.
- Unknown or invalid values are never populated with guessed facts. A valid but past schedule is
  retained only as user-provided information and is accompanied by a confirmation question.

## Evaluation Case

Each version-controlled JSON case is a synthetic, meaningfully distinct test input.

| Field | Type | Constraints |
|---|---|---|
| `case_id` | string | Stable and unique; the initial corpus uses E01–E24. |
| `input` | string | Natural-language request; may be empty for the empty-input case. |
| `context` | object | Fixed reference instant, time zone, and locale; never inherited from the host during evaluation. |
| `expected` | object | Expected intent, task facts, target facts, schedule values/nulls, clarification state, and clarification purpose. |
| `allowed_normalizations` | object | Case-specific permitted task/target wording variants or normalized facts; fixed before evaluation and never broadened merely to obtain PASS. |
| `safety_assertions` | array | Critical prohibited assumptions or required safe behaviors for Layer 2. |
| `categories` | array of strings | Coverage labels such as boundary, missing-information, unsupported, or guardrail. |

Every case must include enough expected facts for deterministic checks. The current 24 cases and
their expected outcomes are defined in [spec.md](./spec.md).

## Evaluation Case Result

Each case result records the captured provider output or explicit provider error, schema result,
deterministic property result, semantic scores/rationales, safety failures, and case PASS/FAIL.
Every Layer 3 result contains five scores in the range 0–2 and a rationale for each. The
designated human evaluator enters these scores; a model does not score itself.

## Evaluation Run and Evidence

Each run has a unique ID and records:

- UTC start time, source revision, dataset and schema identifiers/digests, provider/model, and
  generation settings.
- Fixed case contexts, captured outputs, Layer 1/2 outcomes, Layer 3 review records, and the
  unchanged acceptance threshold.
- Aggregate `PASS` or `FAIL`, failure reasons, known scoring disputes, and reviewer availability.

Runs are written to distinct directories and are never overwritten. Initial failures, repair
feedback, repaired outputs, reruns, and final human decisions remain separately attributable.
Credentials and real user reminder text are excluded from evidence.

### Evaluation lifecycle

1. **Generated**: one captured response or explicit provider error per case.
2. **Validated**: Layer 1 and Layer 2 facts and safety checks recorded for every case.
3. **Semantically scored**: one human's five criterion scores and rationales recorded for each
   case; disputed scores include a second-review outcome or an honest unavailable-review note.
4. **Finalized**: the aggregate threshold is computed and the run records PASS or FAIL. A final
   human acceptance record separately records ACCEPT or REJECT and limitations.
