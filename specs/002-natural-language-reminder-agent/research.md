# Research: Natural-Language Reminder Agent

**Date**: 2026-11-15

## Decisions

### Hosted inference provider

**Decision**: Use the official OpenAI Python SDK with the Responses API and strict Structured
Outputs. Start with `gpt-4o-mini`, which supports Structured Outputs, and record the exact model
identifier and request settings with every evaluation run. Keep the application itself local;
the hosted model call is an explicitly approved external dependency.

**Rationale**:

- The user approved the hosted API option and can provide an API key securely later.
- A local CLI calling one hosted inference endpoint avoids deploying an application service or
  requiring users to download and operate a large model.
- The official Python library supports Python 3.10 and later, including Python 3.13, and the
  Responses API provides structured output with a JSON Schema contract.
- Schema-constrained generation reduces shape errors but does not prove that the interpretation
  is semantically correct. Local Layer 1, Layer 2, and human Layer 3 checks remain mandatory.

**Privacy and data handling**:

- The request text, reference context, system instructions, and output are sent to the provider.
  Do not use real sensitive reminders in the version-controlled evaluation corpus.
- OpenAI's current data-controls documentation says API data is not used for model training by
  default. Abuse-monitoring logs may contain prompts and responses and are retained for up to
  30 days by default. This is provider-side retention, not local app persistence.
- Set the Responses API `store` option to false to avoid application-state storage where the
  endpoint supports it. This does not disable default abuse-monitoring retention.
- Read `OPENAI_API_KEY` from the process environment. Never place it in source, test fixtures,
  prompts, logs, or evidence files.

**Alternatives considered**:

- **Ollama/local model**: Avoids sending prompts to a hosted provider, but adds a separately
  installed runtime, a large model download, and hardware requirements. The documented Windows
  example downloads a model of about 7.2 GB and recommends 8 GB of available VRAM. It is not the
  smallest setup for this assignment, so it was not selected after the user's hosted-provider
  approval.
- **Handwritten deterministic parser only**: Lightweight, but does not meet the approved
  requirement for an AI-assisted, non-deterministic natural-language interpretation.
- **Direct HTTP calls without the official SDK**: Could reduce dependencies but would duplicate
  API request/response handling and error behavior. The maintained SDK is the simpler boundary.

### Structured output and local validation

**Decision**: Keep `contracts/reminder-output.schema.json` as the single canonical external
JSON Schema. Supply its strict supported subset to the provider and validate the captured JSON
locally with `jsonschema`. Apply calendar validity and cross-field business rules separately in
deterministic Python code.

**Rationale**: The same contract must be checked at generation and validation boundaries.
Structural compliance cannot enforce all conditional reminder rules or semantic properties.
Keeping business validation separate makes those rules testable without relying on the model.

**Alternatives considered**:

- Duplicating the schema in the provider prompt and Python model would create drift risk.
- Relying only on provider Structured Outputs would not validate refusals, incomplete responses,
  or application-specific cross-field invariants.

### Local date/time context

**Decision**: Use `datetime` and `zoneinfo` with an explicitly configured local IANA time zone
and locale. Add the first-party `tzdata` package for platforms such as Windows that may not
provide an IANA time-zone database. Inject fixed context for every evaluation case.

**Rationale**: Python's standard `zoneinfo` module applies time-zone and daylight-saving
transitions; evaluation must not depend on the machine clock, locale, or zone.

### Evaluation reproducibility

**Decision**: Store the 24+ case corpus in version-controlled JSON. Separate offline deterministic
validation/replay from opt-in live inference. Preserve the exact captured output, context,
provider/model identifier, request settings, dataset version, and validator/rubric version in
each unique run record. A designated human scores Layer 3; a second reviewer adjudicates
disputed scores when available.

**Rationale**: Model generation may vary even with fixed context. Reproducibility means captured
outputs can be revalidated and rescored consistently, not that a later model call must reproduce
identical wording. If a second reviewer is unavailable, record that limitation honestly.

## Sources

- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) — JSON Schema-constrained output, supported models, and the need to handle refusals, incomplete responses, and errors separately.
- OpenAI, [Data controls](https://developers.openai.com/api/docs/guides/your-data) — default training and abuse-monitoring retention behavior; `store` and application-state distinctions.
- OpenAI Python library, [PyPI package metadata](https://pypi.org/project/openai/) — official SDK and Python version support.
- Python documentation, [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) — IANA time-zone behavior and the recommendation to declare `tzdata` for cross-platform use, especially Windows.
- `jsonschema`, [Schema validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/) — validating JSON instances against a reusable schema.

Sources reviewed on 2026-11-15. Provider retention and supported-model details can change; recheck
the cited official documentation before implementation.
