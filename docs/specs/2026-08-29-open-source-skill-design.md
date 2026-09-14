# CareerLens — Open-source Skill Design

## Decision

Publish a standalone, profession-neutral Codex skill under Apache-2.0. The
repository owns the portable workflow and `personalized_runbook.v1` contract;
LoopCoach remains an optional consumer and keeps its entitlement, sessions,
storage, model-provider integration, UI, and commercial behavior private.

## Public surface

The repository contains:

- `skill/careerlens/`: installable skill instructions;
- `schema/personalized_runbook.v1.schema.json`: portable artifact contract;
- deterministic validation and Markdown rendering scripts using Python stdlib;
- synthetic examples for thin-input and source-backed scenarios;
- tests and CI for schema, privacy, portability, and deterministic rendering.

The first release is `v0.1.0`. It does not include a hosted service, market
database, browser automation, application submission, or model-provider code.

## Trust boundary

Candidate claims require authorized candidate-owned evidence. Target claims
require target-side sources. Community material can calibrate preparation but
cannot establish official process or frequency. Thin input produces an input
gate, not a low synthetic score.

Artifacts must not contain raw resumes, full job descriptions, private profile
text, provider traces, secrets, local absolute paths, or unsupported metrics,
ownership, immigration, sponsorship, compensation, or interview claims.

## Portability

The skill must run without importing LoopCoach. Runtime scripts use only the
Python standard library. Product integrations may translate their accepted
diagnosis into the public schema, but the public validator never changes an
upstream score or readiness gate.

## Repository layout

```text
careerlens/
├── skill/careerlens/
├── schema/
├── examples/
├── tests/
├── docs/specs/
├── .github/workflows/
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── pyproject.toml
```

## Acceptance gates

- Codex skill quick validation passes.
- Every example passes strict artifact validation.
- Renderer output is deterministic for a fixed artifact.
- Tests demonstrate evidence separation, thin-input behavior, time-budget
  feasibility, resource deduplication, and privacy rejection.
- Repository scan finds no personal names, resume content, credentials, local
  absolute paths, or LoopCoach-only imports.
- Installation and use are understandable from the README without private
  repository context.

## Release boundary

Implementation may initialize and commit the local repository. Creating a
remote GitHub repository, making it public, or pushing commits requires a
separate explicit action after the release candidate passes review.
