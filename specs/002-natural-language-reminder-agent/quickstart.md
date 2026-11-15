# Quickstart: Natural-Language Reminder Agent

This is the planned validation guide for [contracts/cli.md](./contracts/cli.md). It documents
the future setup and expected outcomes; it does not implement the application.

## Prerequisites

- Python 3.13 and the repository's development environment.
- Runtime dependencies: OpenAI Python SDK, `jsonschema`, and `tzdata`.
- A hosted-provider API key supplied through a local secret/environment mechanism. Never paste
  it into source files, JSON cases, test output, or evidence.
- A configured IANA time zone and locale for normal operation. Evaluation cases provide their
  own fixed context.

Reminder text is sent to the hosted provider. API content is not used for training by default
according to the provider's current documentation, but abuse-monitoring logs may retain prompts
and responses for up to 30 days by default. `store=false` does not disable that retention. Use
only synthetic cases for live evaluation and do not enter sensitive personal reminder content
unless the user accepts the provider's current data terms.

## Deterministic validation

Run the Part 1B tests without network access:

```text
python -m pytest tests/reminder_agent
```

Expected: schema, fixed-context, Layer 2, and aggregate tests use local fixtures/stubbed
provider responses. No API key is required; no model output is generated.

Run the repository quality checks after implementation:

```text
python -m pytest
ruff check .
ruff format --check .
bandit -q -r src
```

These existing project checks do not replace the Part 1B three-layer evaluation.

## Local interpretation

After implementation and local configuration:

```text
python -m reminder_agent interpret "Remind me to submit my assignment tomorrow at 8 PM."
```

Expected: one JSON object with `create_reminder`, the action `submit my assignment`, the next
local calendar date, time `20:00`, and no clarification. The CLI does not persist or send a
reminder.

## Evaluation and evidence

1. Run the fixed version-controlled corpus of at least 25 synthetic cases with the live provider.
   Every case uses its stored reference instant, time zone, and locale.
2. Review Layer 1 schema/structural and Layer 2 expected-fact/safety results. A failed
   structural or deterministic check is a genuine failure and cannot be bypassed.
3. The designated human scorer scores all five Layer 3 criteria (0–2 each) and records reasons.
   A second reviewer adjudicates disputed scores when available. If unavailable, record that
   limitation; do not fabricate a second review.
4. Finalize the run. Expected `PASS` requires 100% Layer 1 and Layer 2 passes, at least
   `ceil(0.85 * case_count)` Layer 3 scores of 8/10 or higher, and zero safety-critical failures.
   For the initial 25 cases, at least 22 must pass Layer 3.
5. Preserve each initial, repaired, and rerun result in its own non-overwriting directory under
   `artifacts/reminder-agent/`, including outputs, failure evidence, repair feedback, model and
   context metadata, scores, threshold, and aggregate result.
6. A human records final ACCEPT or REJECT, known limitations, and residual risks after reviewing
   all evidence. An automated PASS alone is not final acceptance.

Exact CLI commands for the evaluation stages are specified in
[contracts/cli.md](./contracts/cli.md). The dataset and result structures are described in
[data-model.md](./data-model.md).
