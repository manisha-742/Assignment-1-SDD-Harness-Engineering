# Quickstart: Natural-Language Reminder Agent

## Prerequisites and setup

- Python 3.13.
- Install the project and development dependencies from the repository root:

  ```text
  python -m pip install -e ".[dev]"
  ```

- For live interpretation, provide `GROQ_API_KEY` through the process environment or an
  approved secret manager. The application uses Groq's OpenAI-compatible API at
  `https://api.groq.com/openai/v1` with model `openai/gpt-oss-20b` by default; optionally set
  `GROQ_MODEL` to override it. The application does not load `.env` files. Never put a real key
  in source code, Git, test fixtures, prompts, logs, or evaluation evidence.
- Configure `REMINDER_TIME_ZONE` with an IANA zone such as `America/Los_Angeles`. Optionally set
  `REMINDER_LOCALE` for numeric date interpretation and `REMINDER_REFERENCE_INSTANT` to an ISO
  8601 date-time with a UTC offset for a controlled runtime reference. If the reference instant
  is omitted, the current system instant is used. Evaluation never reads these runtime settings.

Reminder text, fixed context, and model output are sent to Groq for inference. Groq states that
inference customer data is not retained by default, but may be temporarily logged for system
reliability or abuse monitoring for up to 30 days; see [Groq's data policy](https://console.groq.com/docs/your-data).
The `store=false` request setting does not override the provider's data policy. Use only the
synthetic, committed evaluation cases for live evaluation; do not enter sensitive personal
reminder text unless you accept the provider's current data terms.

## Deterministic validation

Run Part 1B tests without network access or a real API key:

```text
python -m pytest tests/reminder_agent
```

Tests use fixed contexts and stubbed provider responses. The complete repository quality checks
are:

```text
python -m pytest
ruff check .
ruff format --check .
bandit -q -r src
```

Automated tests do not replace the live three-layer evaluation or its human semantic review.

## Interpret one request

```text
python -m reminder_agent interpret "Remind me to submit my assignment tomorrow at 8 PM."
```

The command writes exactly one JSON object to stdout. Configuration, provider, or response
failures are reported on stderr with a nonzero exit status. The application interprets the
request only; it does not persist, schedule, send, or execute a reminder.

## Evaluate and finalize

Run only the hash-pinned, version-controlled synthetic corpus:

```text
python -m reminder_agent evaluate --cases tests/data/reminder-evaluation-cases.json
```

Live evaluation requires `GROQ_API_KEY`. If it is unavailable, the command stops before making
provider calls or creating evaluation evidence. A successful run creates a unique directory under
`artifacts/reminder-agent/` containing the dataset, captured outputs or sanitized provider
errors, fixed contexts, Layer 1 and Layer 2 reports, a human scoring template, and a pending
human-decision template. The corpus is pinned at 25 cases and cannot be replaced by an arbitrary
live dataset.

The designated human scorer completes `semantic-review-template.json` and saves the completed
record as `semantic-review.json` in that run directory. Each of the five rubric criteria needs a
0–2 score and rationale for every case. For a disputed score, record an actual second review or
honestly record that a second reviewer was unavailable. Then run:

```text
python -m reminder_agent finalize --run-dir artifacts/reminder-agent/<run-id>
```

Finalization computes PASS/FAIL only. It does not decide human ACCEPT/REJECT. The human reviewer
must separately complete the decision record and document known limitations and residual risks.

To re-run structural and deterministic checks against the captured outputs without calling the
provider or changing the original run:

```text
python -m reminder_agent replay --run-dir artifacts/reminder-agent/<run-id>
```

Aggregate PASS requires 100% Layer 1, 100% Layer 2, at least 85% of Layer 3 scores at 8/10 or
higher (22 of 25 cases), and zero safety-critical failures. No CLI option can weaken these
thresholds. Every run directory is unique and evidence files are written without overwriting
earlier evidence.

For a rerun linked to a genuine failed run, provide both the prior run directory and a file with
the actual repair guidance:

```text
python -m reminder_agent evaluate --cases tests/data/reminder-evaluation-cases.json --repair-of artifacts/reminder-agent/<initial-run> --repair-feedback <feedback-file>
```

The evaluator rejects a repair link without a recorded failure and never changes the dataset,
expected facts, validators, or thresholds to accommodate a model output.
