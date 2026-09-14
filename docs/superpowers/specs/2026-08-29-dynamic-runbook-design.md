# CareerLens Dynamic Runbook Design

Date: 2026-08-29  
Status: approved for implementation planning

## 1. Objective

CareerLens must produce a personalized, executable career runbook rather than a
short diagnosis dashboard. The reference quality bar is the existing US AI
Platform job-market report: deep navigation, inspectable evidence, explicit
selection logic, searchable question banks, customized learning paths, and a
time-bounded preparation plan.

The runbook is dynamic. Every candidate receives the common decision and
evidence spine, while role-specific modules such as system design, algorithms,
AI coding, SQL, OOD/LLD, domain knowledge, and behavioral preparation are
enabled only when supported by the target-role evidence.

## 2. Success Criteria

A generated runbook must let a candidate answer five questions without another
analysis pass:

1. Which roles should I pursue, and why?
2. Which requirements are proved, claimed, missing, or unknown?
3. What will each interview round test, and what will interviewers challenge?
4. Which questions and learning resources should I complete, in what order?
5. What exactly should I do each day, and how do I know I am ready to advance?

The product fails this design if it produces a generic link library, a numeric
fit score without sufficient evidence, an unprioritized question dump, or a
plan whose hours exceed the candidate's declared capacity.

## 3. Information Architecture

The page follows the reference report's dense, navigable design language:

- persistent left navigation with section status and progress;
- an overview page with decision, role families, evidence boundary, and next
  actions;
- target strategy with inclusion and exclusion rationale;
- capability evidence map;
- interview-loop map;
- role-enabled preparation modules;
- behavioral and resume guidance;
- capacity-aware roadmap;
- methodology, sources, limitations, and freshness metadata.

Desktop uses a fixed sidebar and content canvas. Mobile uses a compact section
switcher without removing content. Search, filters, checkboxes, expandable
answer guidance, and progress state remain available at both sizes.

## 4. Common Runbook Spine

Every runbook contains:

### 4.1 Overview

- target role families and current application decision;
- concise explanation of why the decision is conditional, proceed, or hold;
- strongest candidate evidence;
- decisive gaps and unknowns;
- immediate application and preparation actions;
- no numeric score unless the input-quality gate explicitly permits one.

### 4.2 Target Strategy

Each target includes role title, company, location, source, capture date,
freshness, inclusion reason, exclusion risk, candidate match evidence, and
unresolved constraints. The UI exposes why a role entered the target list and
why an adjacent role did not.

### 4.3 Evidence Map

Every requirement is classified as `proved`, `claimed`, `missing`, or
`unknown`. Candidate evidence and target evidence remain separate. An inference
cannot become candidate experience. Each state links back to the source span
or explicitly states that no supporting candidate evidence exists.

### 4.4 Interview Map

For each likely round, show the evaluation signal, likely format, candidate
risk, preparation module, and confidence. Company-specific formats require a
dated source. Unsourced company detail is labeled as an inference or omitted.

### 4.5 Resume and Story Guidance

Guidance states the reason for a change, the truthful direction, the evidence
needed, and the boundary that must not be invented. Project stories include
personal ownership, alternatives, failures, metrics, and likely follow-ups.

### 4.6 Preparation Roadmap

The roadmap has phases, dependencies, hours, daily or weekly work, spaced
review, mock cadence, artifacts, exit criteria, and stop conditions. Planned
hours cannot exceed declared capacity.

## 5. Dynamic Module Selection

Modules are activated by target requirements, interview evidence, and candidate
gaps, not by a fixed engineering template.

| Module | Enable when | Suppress when |
| --- | --- | --- |
| System design | Target or interview evidence requires architecture, scale, reliability, or distributed systems | No credible design signal exists |
| Algorithms | Coding assessment is stated or strongly supported for the role family | The role has no technical implementation screen |
| AI coding | Role requires RAG, agents, evaluation, model APIs, or applied AI implementation | AI is only incidental to the target |
| SQL/data design | Role requires analytics, data platform, pipelines, databases, or query reasoning | No data manipulation requirement exists |
| OOD/LLD | Backend or product engineering work requires object boundaries, state, testing, or concurrency | The role is non-implementation or purely analytical |
| Domain depth | Specialized domain knowledge is a decisive hiring signal | Generic knowledge would not change the hiring decision |
| Behavioral | Always enabled, but topics are selected from actual ownership and risk evidence | Never fully suppressed |

Each activation records its evidence and confidence. Users can see why a module
is present.

## 6. Question Selection Engine

Questions are selected by coverage and candidate value, not by claimed leak
frequency. The engine uses:

- target-requirement coverage;
- likely interview-round relevance;
- gap severity;
- reuse across multiple target roles;
- candidate baseline and project adjacency;
- recency and confidence of frequency signals;
- preparation cost;
- prerequisite relationships;
- redundancy with already selected questions.

Every selected question exposes:

- selection reason;
- mapped role requirements and interview rounds;
- candidate-specific relevance;
- priority and confidence;
- knowledge and implementation prerequisites;
- required mastery points;
- expected follow-ups;
- completion standard;
- linked learning path.

Priority A means the candidate must complete the question within the current
preparation horizon. Priority B expands coverage after the core gate. Priority
C is enabled only after a target company or interview format justifies it.

The engine favors transferable patterns before recent company-calibration
variants. It must not present community reports as official company questions.

## 7. Customized Learning Resource Engine

Resource selection begins with a knowledge-gap specification, not a web search.
For each question or topic, the engine identifies required mechanisms, design
judgment, implementation ability, testing ability, and verbal delivery.

### 7.1 Candidate Starting State

The engine classifies the candidate as one of:

- performed and needs answer packaging;
- conceptually familiar but structurally incomplete;
- able to design but not implement;
- able to implement but missing production trade-offs;
- unfamiliar and requiring a foundation.

The same topic therefore produces different learning paths for different
candidates.

### 7.2 Role-Specific Depth

Resources are evaluated against the target role. For example, RAG preparation
emphasizes API concurrency and failure handling for Backend SDE, serving and
evaluation for AI Platform, tool routing and guardrails for Agentic roles, and
retrieval quality and experiment design for ML Engineering.

### 7.3 Resource Roles

A learning path normally contains no more than one resource for each distinct
job:

1. framework resource;
2. authoritative mechanism reference;
3. production case study;
4. implementation exercise or mock.

A later resource must add uncovered value. Mere topical overlap is not enough
to include it.

### 7.4 Required Resource Annotation

Every resource must state:

- why it is assigned to this candidate;
- exact chapters, sections, examples, or timestamps to consume;
- what must be learned;
- what can be skipped;
- prerequisites;
- estimated time;
- required output after study;
- mapped question and interview round.

### 7.5 Quality Evaluation

Resources are ranked on authority, target-role relevance, candidate fit,
information density, freshness, actionability, and time cost. A long official
document can lose to a more useful learning resource, but primary sources remain
the authority for mechanisms, product behavior, and formal interview guidance.

Rejected or deferred resources record a reason such as redundant coverage,
excessive prerequisite cost, stale information, weak authority, or poor fit for
the candidate's current stage.

### 7.6 Completion Definition

Reading is not completion. A candidate must be able to explain the mechanism
without notes, articulate at least two relevant trade-offs, connect it to a
confirmed project or state the boundary, answer mapped follow-ups, and produce
the required design, code, test, or written artifact.

## 8. Plan Generation

Plan priority is computed from gap severity, interview likelihood, target-role
coverage, transfer value, candidate baseline, dependency order, decay risk,
and time cost. The ordering and its factors are visible in the runbook.

The planner must:

- schedule prerequisites before dependent work;
- mix learning, production, recall, and mock practice;
- include spaced repetition rather than one-pass completion;
- place high-risk, high-transfer tasks early;
- reserve company-specific calibration until an interview or target warrants it;
- fit declared weekly and total capacity;
- name what was deferred and why;
- define an exit gate for each phase.

A task has a verb, artifact, duration, dependency, linked gap, linked questions,
resources, and an objective completion check. Generic tasks such as “study
system design” are invalid.

## 9. Data and Rendering Contract

Canonical JSON remains the source of truth. The interactive HTML is a richer
projection of validated JSON, not an independently authored conclusion.

The schema must represent:

- module activation rationale;
- question selection rationale and confidence;
- candidate starting state per topic;
- resource role, reading scope, skip scope, output, and rejection rationale;
- plan dependencies, effort, review cadence, and exit gates;
- source freshness and evidence class.

The renderer must tolerate an absent optional module, show empty-state reasons,
and never replace missing evidence with generic filler.

## 10. Interaction Design

- search across questions, companies, capabilities, and resources;
- filter by module, round, priority, evidence state, and completion;
- expandable answer guidance and resource instructions;
- persistent local completion state without storing resume content;
- progress by module and phase;
- reset with explicit confirmation;
- shareable anchors for every section and question;
- reduced-motion support and keyboard-visible focus.

The launch demo uses the public fictional candidate and dated public target.
It must contain enough real questions, resource paths, and plan phases to prove
the product behavior; it cannot return to the previous eight-card summary.

## 11. Validation and Quality Gates

Automated checks must verify:

- all conclusions have valid evidence states;
- module activation has a reason;
- every selected question maps to a requirement or round;
- every resource has scoped reading instructions and an output;
- no duplicate resource performs the same role for the same topic;
- plan effort stays within capacity;
- every plan phase has an exit gate;
- source dates and evidence classes are present;
- private paths, secret-like values, and real candidate data are absent from the
  public case;
- interactive controls work at desktop and mobile sizes;
- deterministic report projections remain reproducible.

Manual review covers question usefulness, resource-path coherence, plan
feasibility, visual fidelity to the reference report, and truth-boundary
language.

## 12. Launch Video Implications

The product video will show the real runbook workflow:

1. candidate and target evidence;
2. role and module selection rationale;
3. a filtered question bank with a visible selection reason;
4. a customized multi-resource learning path;
5. a capacity-aware plan with phase gates;
6. the evidence and uncertainty boundary.

The video must not use the current summary-only screenshot as proof of the
runbook's value. Final rendering waits until the rebuilt runbook is visually
approved.

## 13. Explicit Non-Goals

- claiming guaranteed interview questions or live frequency precision;
- generating the same technical curriculum for every profession;
- copying private candidate data into a public demo;
- measuring value by link count or question count;
- automatically applying to jobs;
- replacing validated JSON with UI-only logic.

