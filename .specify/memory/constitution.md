<!--
Sync Impact Report
- Version change: 1.1.0 -> 1.2.0
- Modified principles:
  - None; existing Part 1A principles are preserved unchanged
- Added sections: Part 1B: Natural-Language Reminder Agent Governance
- Removed sections: None
- Follow-up TODOs: None
-->

# Assignment-1-SDD-Harness-Engineering Constitution

## Core Principles

Principles I–V below are the completed Part 1A deterministic governance. They remain
unchanged and continue to govern Part 1A.

### I. Deterministic CLI and Controlled Task State
For identical valid inputs and the same persisted state, the Smart Todo CLI MUST produce
identical outputs and state changes. Task statuses and allowed transitions MUST follow the
approved specification. Invalid or unspecified transitions MUST be rejected deterministically.

Determinism makes behavior reproducible and enables reliable automated evaluation.

### II. Requirements Traceability
Every implemented feature MUST trace to an approved functional requirement, acceptance
criterion, and implementation task. These links MUST be recorded in the project artifacts
before the feature is considered complete. The approved specification is the source of truth
for scope and expected behavior.

This prevents implementation drift and makes each delivered behavior auditable.

### III. Automated Deterministic Testing
Every functional requirement and measurable acceptance criterion MUST be verifiable by
automated pytest tests. Tests MUST be deterministic, cover regression behavior, and run
against the specified CLI and persisted state. A feature is not complete until its applicable
tests pass.

Testing is part of delivery, not a substitute for specifying the behavior first.

### IV. Harness Integrity and Evidence Preservation
Tests, assertions, requirements, lint rules, security checks, and evaluation thresholds MUST
NOT be deleted, disabled, bypassed, weakened, or silently changed to obtain a PASS result.
Any approved change to these controls MUST be traceable and explained.

Evidence MUST be preserved for the initial generated implementation, harness executions,
genuine failures, repair feedback, repaired implementation, reruns, and final validation
results. Records MUST not be altered to conceal failures.

### V. Reproducible, Secure, and Maintainable Delivery
Automation and harnesses MUST be deterministic, versioned, and runnable without secret state
or one-off local fixes. The project MUST favor the smallest clear solution; changes affecting
interfaces, data contracts, or operational behavior MUST include a traceable impact rationale.
Credentials, tokens, and environment-specific secrets MUST NOT be committed.

Reproducible commands and explicit change records reduce environment drift and make the
project maintainable.

### Part 1B: Natural-Language Reminder Agent Governance

The following requirements apply specifically to the non-deterministic Part 1B Natural-Language
Reminder Agent. They supplement, and MUST NOT remove, weaken, or replace, the completed Part 1A
governance above.

#### VI. Specification-Driven AI Behaviour
Before implementation, the approved specification MUST define the intended AI behavior, the
structured output contract, clarification behavior, safety requirements, invariants,
semantic-quality expectations, and quantitative evaluation threshold. These requirements
MUST be testable and MUST guide implementation and evaluation.

#### VII. Structured Output Contract
Reminder interpretations MUST conform to a documented structured schema. The schema MUST
define every required field, allowed values, nullability, and validation rules. Outputs that
do not conform MUST fail structural validation and MUST NOT be treated as valid interpretations.

#### VIII. Clarification Instead of Unsupported Guessing
When information materially required to create or modify a reminder is missing or ambiguous,
the agent MUST request clarification rather than inventing critical facts, including unsupported
dates or times. The approved specification MUST define when clarification is required and how
it is represented in the output.

#### IX. Property and Invariant Validation
Every output MUST be checked against deterministic properties and invariants, even when its
wording legitimately varies. Checks MUST include valid intent, schema conformance, valid date
and time representations, required fields, consistency between clarification state and output,
and preservation of the user's requested reminder meaning. Invalid or unsupported values MUST
not pass because the response is plausible or fluent.

#### X. Semantic Quality Evaluation
Outputs whose wording may legitimately vary MUST be evaluated against explicit semantic-quality
criteria. Exact string equality MUST NOT be the sole measure of semantic correctness. The
criteria MUST assess whether the response correctly represents the request and communicates
necessary clarification or safety outcomes.

#### XI. Diverse Evaluation Dataset
The Part 1B evaluation dataset MUST contain at least 15 meaningfully distinct cases, not merely
trivial paraphrases of one case. It MUST cover normal reminder requests, relative dates or times,
boundary cases, ambiguous requests, missing required information, malformed inputs, unsupported
requests, and adversarial or guardrail cases.

#### XII. Three-Layer Evaluation
Every evaluation run MUST report all three layers: (1) schema and structural validation;
(2) deterministic property and invariant checks; and (3) semantic or quality evaluation using
the documented criteria. A run MUST NOT report an overall PASS if a required layer is omitted.

#### XIII. Quantitative Acceptance Threshold
The evaluation harness MUST calculate reproducible per-case results and an aggregate PASS or
FAIL against an explicitly documented quantitative acceptance threshold. The threshold and
scoring method MUST be specified and approved before implementation; evaluation runs MUST record
their case-level results, aggregate result, and threshold used.

#### XIV. Evaluation Integrity
Part 1B evaluation cases, validators, scoring criteria, thresholds, safety checks, and required
properties MUST NOT be deleted, bypassed, weakened, or silently modified merely to obtain PASS.
Changes to evaluation controls MUST be reviewed, justified, and traceable. A failure MUST NOT be
manufactured solely to create assignment evidence.

#### XV. Evidence Preservation and Repair
For Part 1B, the project MUST preserve the initial generated implementation and output, initial
evaluation results, genuine failures, repair feedback, repaired implementation and output,
evaluation reruns, and final results. Evidence MUST remain attributable to the corresponding
implementation and evaluation run and MUST NOT be altered to conceal failures.

#### XVI. Human Accountability
An automated evaluation PASS is evidence and MUST NOT by itself constitute final acceptance.
The final human review MUST document ACCEPT or REJECT and identify known limitations and
residual risks.

## Technology, Security and Data Integrity

Part 1A is a Python 3.13 command-line application using JSON persistence, pytest, Ruff, and
Bandit. Python code MUST pass Ruff linting and static quality checks and MUST pass Bandit
security analysis. Security findings MUST be reviewed; suppressing findings solely to obtain a
passing result is prohibited.

Persisted task data MUST use unique task IDs and validate all required fields. Invalid data
MUST be rejected, and task data MUST remain consistent across application restarts. Inputs
and outputs at application boundaries MUST be validated. Changes affecting data handling or
user interaction MUST be reviewed for security and operational risk before acceptance.

## Verification, Evidence and Human Review

Every change MUST be reviewed for specification alignment, test coverage, and risk. Unless a
change is explicitly documented as trivial and low-risk, a second contributor MUST review it
before merge. Quality gates MUST NOT be bypassed because of urgency; any approved urgent
exception requires written approval, documentation, and a corrective follow-up plan.

Automated harness PASS is necessary evidence but does not constitute final acceptance. A
human MUST document the final ACCEPT or REJECT decision and its basis after reviewing the
specification, implementation, harness evidence, and any unresolved findings.

## Governance

This Constitution governs all project work in this repository and supersedes conflicting local
preferences and informal practices. Amendments require a written change proposal, rationale,
and review before adoption. The project owner or designated maintainer is responsible for
enforcement; violations MUST be corrected and material or repeated violations require a
documented remediation plan.

Constitution versions use semantic versioning: MAJOR for backward-incompatible governance
changes, MINOR for new principles or materially expanded requirements, and PATCH for
clarifications or non-semantic refinements. Compliance MUST be reviewed at specification,
planning, task-generation, implementation, harness-validation, and final-acceptance gates.
The review outcome and any remediation MUST be documented.

**Version**: 1.2.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-15
