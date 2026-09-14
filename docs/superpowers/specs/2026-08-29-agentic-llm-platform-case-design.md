# Agentic and LLM Platform Public Case Design

## Purpose

Add a second reproducible CareerLens case that demonstrates how a senior
backend or data platform engineer can evaluate and prepare for Agentic and LLM
Platform roles. The case must show why CareerLens chooses each resume change,
interview topic, learning resource, and preparation step.

The case is a product demonstration. It must not imply that the fictional
candidate is a real person or that any referenced employer endorses CareerLens.

## Inputs

### Primary role

Use one active official United States Agentic or LLM Platform Engineer job as
the primary target. Store a dated local snapshot, source URL, access date, and
content hash so the case remains inspectable after the live role changes or is
removed.

### Market baseline

Use four to six additional active official job pages from distinct employers.
These sources establish repeated market requirements. A market-wide claim must
be supported by at least two independent official job sources. Requirements
from the baseline must never be represented as requirements from the primary
role.

### Candidate

Create a fully synthetic senior backend and data platform engineer with
evidence of:

- RESTful Agent invoke endpoint design;
- RAG and knowledge-base integration;
- AWS Bedrock integration;
- DynamoDB session persistence;
- unit and API testing;
- container-based horizontal scaling; and
- production backend or data platform ownership.

The candidate must not claim model training, GPU serving, large-scale LLM
evaluation ownership, or ML research experience. Those limitations create the
case's meaningful evidence gaps.

## Evidence Model

Keep five categories separate throughout generation and rendering:

1. candidate facts;
2. primary-role requirements;
3. cross-company market requirements;
4. explicit inferences; and
5. unknowns.

Target-role evidence cannot prove candidate experience. Market evidence cannot
silently become a primary-role requirement. Unsupported candidate facts remain
missing or unknown.

The expected application decision is `conditional`. Do not show a numeric fit
score unless the existing input gate establishes that one is defensible.

## Runbook Output

### Application decision

Explain whether the candidate should apply now, which adjacent role families
are reasonable, which risks may block progression, and which resume changes
are evidence-safe. Each recommendation must include its evidence boundary.

### Interview map

Cover these stages:

- recruiter screen;
- hiring manager screen;
- coding;
- AI coding;
- system design;
- Agent and LLM project deep dive; and
- behavioral interview.

Every core question must identify why it was selected. Valid reasons include a
specific resume project, a primary-role requirement, a repeated market
requirement, or an evidence gap. Each question must also include likely
follow-ups and a concrete completion standard.

### Topic selection

For every Priority A topic, provide:

- the linked capability gap;
- the reason it is urgent for this candidate;
- how an interviewer is likely to test it;
- the required mastery level; and
- a stopping boundary that prevents unnecessary study.

### Learning path

Resources must be customized, not merely deduplicated. Each resource must have
a distinct job in the learning sequence, a specified section to consume, a
learning objective, and a stopping condition. Prefer a short sequence that
moves from mental model to mechanism to interview application.

### Capacity plan

Produce an eight-week plan constrained by the candidate's declared weekly time
budget. Schedule interview-blocking risks first, shared role-family skills
second, and company-specific preparation last. Planned hours must not exceed
available hours.

### Application test

Define a bounded application experiment that records resume version, target
cohort, response rate, rejection stage, and interview feedback. Strategy
changes must be driven by observed signals rather than one-off edits for every
job.

## Data Flow

The case follows this traceable pipeline:

1. ingest the synthetic resume and dated official job evidence;
2. normalize capability terminology without merging evidence categories;
3. assign evidence states;
4. rank application and interview risks;
5. select questions and learning resources from those risks;
6. enforce the time budget; and
7. render canonical JSON plus deterministic Markdown and HTML projections.

## Repository Changes

- Add a new directory under `case-studies/` for the Agentic and LLM Platform
  case.
- Preserve the existing AI Engineer case without changing its inputs.
- Store the synthetic resume, primary-role snapshot, market evidence, source
  manifest, and hashes.
- Generate canonical JSON, Markdown, HTML, and an interactive Runbook.
- Add a second-case entry to the README with an explicit synthetic-data notice.
- Generalize launch verification so multiple cases use the same validation
  path instead of copied case-specific logic.
- Add tests for evidence isolation, topic provenance, resource roles, capacity
  enforcement, deterministic generation, and private-data checks.

## Error Handling

- Reject a market claim supported by fewer than two independent official job
  sources.
- Reject missing or stale local source files when their recorded hash differs.
- Reject Priority A tasks without a linked gap.
- Reject core questions without selection provenance or completion criteria.
- Reject learning resources without scope, objective, or stopping condition.
- Reject plans that exceed the declared capacity.
- Reject private paths, secret-like values, or person-specific identifiers in
  public artifacts.

## Acceptance Criteria

- All job links are active when captured and include an access date.
- The primary role and market baseline remain distinguishable in every output.
- Every market-wide requirement has at least two independent official sources.
- Every Priority A task traces to an explicit gap.
- Every core interview question includes its rationale, follow-up path, and
  completion standard.
- Every learning link includes the exact reading scope, learning target, and
  stopping boundary.
- The eight-week plan stays within the stated weekly capacity.
- No private candidate data or unsupported experience appears in the case.
- No unexplained numeric fit score appears.
- Both public cases pass the same strict validator and automated tests.
- Generated Markdown and HTML are deterministic.
- The interactive HTML opens locally and the README clearly distinguishes the
  two use cases.

## Out of Scope

- a third public case;
- a continuously running job-monitoring crawler;
- automatic job applications or recruiter outreach; and
- changes to the approved launch video.
