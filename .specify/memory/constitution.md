<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Modified principles:
  - Specification-First -> Requirements Traceability
  - Evidence-Driven Delivery -> Harness Integrity and Evidence Preservation
  - Test-First and Regression Safety -> Automated Deterministic Testing
  - Reproducible Automation -> Deterministic CLI and Controlled Task State
  - Simplicity, Traceability, and Safe Change -> Reproducible, Secure, and Maintainable Delivery
- Added sections: Technology, Security and Data Integrity; Verification, Evidence and Human Review
- Removed sections: Security and Quality Standards; Review and Delivery Workflow (replaced by expanded sections)
- Follow-up TODOs: None
-->

# Assignment-1-SDD-Harness-Engineering Constitution

## Core Principles

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

**Version**: 1.1.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-14
