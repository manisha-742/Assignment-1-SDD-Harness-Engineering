# CLI Contract: Natural-Language Reminder Agent

This planned interface is local and single-request. It does not create, store, send, or execute
reminders.

## Runtime configuration

| Setting | Purpose |
|---|---|
| `GROQ_API_KEY` | Required for live interpretation; read from the process environment and never logged or committed. |
| `GROQ_MODEL` | Optional model override; defaults to `openai/gpt-oss-20b`. Record the effective value in each evaluation run. |
| Groq API base URL | `https://api.groq.com/openai/v1`, configured in the OpenAI-compatible Python client. |
| `REMINDER_TIME_ZONE` | Configured IANA time-zone name for normal runtime context. |
| `REMINDER_LOCALE` | Configured locale used when interpreting locale-sensitive numeric dates. |
| `REMINDER_REFERENCE_INSTANT` | Optional ISO 8601 date-time with UTC offset for a controlled runtime reference. If omitted, use the system clock. |

The evaluation runner supplies a fixed reference instant, time zone, and locale from each
hash-verified version-controlled case instead of reading host settings.

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
python -m reminder_agent evaluate --cases tests/data/reminder-evaluation-cases.json --repair-of artifacts/reminder-agent/<initial-run> --repair-feedback <feedback-file>
python -m reminder_agent replay --run-dir artifacts/reminder-agent/<run-id>
python -m reminder_agent finalize --run-dir artifacts/reminder-agent/<run-id>
```

`evaluate` accepts only the approved, hash-pinned `tests/data/reminder-evaluation-cases.json`
corpus, uses fixed per-case contexts, captures one output or sanitized provider error per case,
runs Layers 1 and 2, and creates a unique evidence directory. It requires `GROQ_API_KEY`; when
the key is missing, it stops before provider calls or evidence creation. The run directory
contains the corpus, captured results, layer reports, and templates for human review and the final
decision. Genuine failed cases are recorded separately. A repair rerun may use `--repair-of` and
`--repair-feedback` together; the source run must contain an actual recorded failure, and the
rerun preserves a link to those failures and the supplied feedback. Previous run directories are
never overwritten.

The designated human evaluator completes `semantic-review-template.json` and saves it as
`semantic-review.json`, recording five rubric scores and reasons for every case. A second
reviewer records adjudication only for disputed scores; if unavailable, record that honestly.
`finalize` validates the review record and computes the aggregate result. It never makes the
human ACCEPT/REJECT decision, which remains pending for the user.

`replay` reads captured outputs and reruns the deterministic layers offline. It does not call the
provider or modify the source run; it creates a linked, non-overwriting evidence directory.

The aggregate is `PASS` only when every case passes Layers 1 and 2, at least
`ceil(0.85 * case_count)` cases score 8/10 or higher in Layer 3, and no safety-critical failure
exists. At the 24-case minimum, at least 21 semantic cases must pass. The threshold is part of
the versioned evaluator contract and is not a command-line override.

## Error behavior

The application must distinguish configuration, provider, response/schema, and evaluation
failures in its error records. It must not report a successful JSON interpretation after an
API error or silently default missing configuration. Every failure must have a nonzero exit
status and a sanitized, actionable stderr message.
