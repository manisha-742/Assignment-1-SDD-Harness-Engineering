# CLI Contract: Natural-Language Reminder Agent

This planned interface is local and single-request. It does not create, store, send, or execute
reminders.

## Runtime configuration

| Setting | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required for live interpretation; read from the process environment and never logged or committed. |
| `OPENAI_MODEL` | Optional model override; defaults to `gpt-4o-mini`. Record the effective value in each evaluation run. |
| `REMINDER_TIME_ZONE` | Configured IANA time-zone name for normal runtime context. |
| `REMINDER_LOCALE` | Configured locale used when interpreting locale-sensitive numeric dates. |

The evaluation runner supplies a fixed reference instant, time zone, and locale from each
version-controlled case instead of reading host settings.

## Interpret a request

```text
python -m reminder_agent interpret "Remind me to submit my assignment tomorrow at 8 PM."
```

- A valid interpretation is exactly one JSON object conforming to
  [reminder-output.schema.json](./reminder-output.schema.json), written to stdout with a final
  newline and no prose or Markdown wrapper.
- Empty, malformed, unrelated, or unsupported requests that can be handled safely return the
  schema-valid `unsupported` result or a clarification result as defined in the feature spec.
- API/network/configuration failures are explicit errors on stderr with a nonzero exit status;
  they are not converted into fabricated reminder output.
- Provider refusals are recorded and may become a structured `unsupported` result only when its
  nullability and clarification invariants validate.

## Run and finalize an evaluation

```text
python -m reminder_agent evaluate --cases tests/data/reminder-evaluation-cases.json
python -m reminder_agent finalize --run-dir artifacts/reminder-agent/<run-id>
```

`evaluate` uses fixed per-case context, captures one live output per case, runs Layers 1 and 2,
and creates a unique evidence directory with a semantic-review form. The designated human
evaluator records the five rubric scores and reasons for each case. A second reviewer records
adjudication only for disputed scores; if unavailable, the form records that honestly.
`finalize` validates the review record and computes the aggregate result. A run is not finalized
until its semantic review is complete.

The aggregate is `PASS` only when every case passes Layers 1 and 2, at least
`ceil(0.85 * case_count)` cases score 8/10 or higher in Layer 3, and no safety-critical failure
exists. At the 24-case minimum, at least 21 semantic cases must pass. The threshold is part of
the versioned evaluator contract and is not a command-line override.

## Error behavior

The application must distinguish configuration, provider, response/schema, and evaluation
failures in its error records. It must not report a successful JSON interpretation after an
API error or silently default missing configuration. Detailed exit codes are implementation
work, but every failure must have a nonzero status and an actionable stderr message.
