# CareerLens public Software Engineer, API Agents case

> Reproducible demonstration using an MIT-licensed fictional candidate and a dated official target role. This is not a real application or hiring prediction.

## Executive decision

- **Target:** Software Engineer, API Agents
- **Decision:** conditional
- **Reason:** The candidate clears the backend foundation and has shipped an agent-enabled service, but the primary role expects durable orchestration, secure execution, evaluation and observability, and long-running workflow ownership that the supplied resume does not yet prove.
- **Next action:** repair_agent_runtime_evidence_and_prepare_designs
- **Numeric fit score:** intentionally not used

## Evidence matrix

| Capability | State | Candidate evidence boundary |
|---|---|---|
| Backend and distributed systems | `proved` | candidate:event-platform, candidate:async-services |
| Developer-facing API design | `proved` | candidate:invoke-api, candidate:idempotent-apis |
| Agent, model, and retrieval integration | `proved` | candidate:bedrock-strands-rag |
| Session and workflow state | `proved` | candidate:dynamodb-sessions |
| Testing and container scaling | `proved` | candidate:unit-api-tests, candidate:multi-container |
| Durable agent orchestration and recovery | `claimed` | Session status and retries exist, but checkpointing, replay, idempotent tool execution, and multi-step recovery are not described. |
| Agent evaluation and trace-driven release gates | `claimed` | Prompt routing tests and logs do not prove golden datasets, outcome graders, trace analysis, or release gates. |
| Secure tool execution, identity, and permissions | `missing` | No candidate-owned proof |
| Long-running and multi-agent runtime ownership | `unknown` | No candidate-owned proof |

## Resume guidance

### A · agent-api-mechanism

- **Why it matters:** The strongest transferable project is described as an integration list instead of a defensible backend system.
- **Safe direction:** Describe the invoke contract, session lifecycle, routing boundary, failure policy, tests, scaling trigger, and the candidate's architecture decision.
- **Truth boundary:** Do not add multi-agent delegation, sandboxing, cross-region durability, or Kubernetes unless separately confirmed.
- **Done when:** A reviewer can trace one request from authentication through model and knowledge retrieval to persisted session state and failure handling.

### A · evaluation-language

- **Why it matters:** The market repeatedly expects evaluation and observability; the resume currently proves deterministic tests and request logs only.
- **Safe direction:** Name unit, API, prompt-delivery, and routing tests precisely. Add model-quality or trace-based evaluation only if a real dataset, metric, and release decision can be confirmed.
- **Truth boundary:** Do not rename API tests as LLM evaluations or claim an evaluation flywheel.
- **Done when:** Every testing claim identifies its input, oracle, failure caught, and release consequence.

### B · scaling-boundary

- **Why it matters:** Senior interviewers will distinguish adding containers from designing a durable global scheduler.
- **Safe direction:** State the original single-container constraint, concurrency signal, stateless boundary, health checks, and observed operational improvement.
- **Truth boundary:** Keep agent-service scale separate from the independently proved 10-billion-event data platform scale.
- **Done when:** The bullet makes workload, mechanism, measurement, and ownership distinct without combining two systems.

## Interview preparation map

- **Recruiter screen:** Test seniority, motivation, location, and whether the backend-to-agent-platform transition is credible.
- **Hiring manager:** Probe product judgment, platform ownership, ambiguity, and the boundary between shipped agent work and unproved runtime depth.
- **Coding and backend implementation:** Test production-quality Python or TypeScript, async control flow, data structures, tests, and API clarity.
- **AI coding:** Implement a tool-using agent loop with typed boundaries, timeouts, deterministic fakes, and evaluation hooks.
- **Agent platform system design:** Design durable workflows, session state, tool execution, streaming, observability, security, and cost controls.
- **Agent project deep dive:** Trace the invoke service and separate confirmed personal decisions from adjacent or missing platform capabilities.
- **Behavioral and ownership:** Test incidents, tradeoffs, disagreement, rollout judgment, and learning under uncertainty.

> These are preparation categories inferred from the primary posting and repeated official market requirements, not a confirmed OpenAI interview loop.

## 8-week preparation plan

### Evidence repair and interview positioning

- **A · Rewrite and fact-check the invoke project** (240 minutes): Trace request, state, routing, tests, scaling, failure behavior, and personal decisions using only confirmed facts.
- **A · Design the durable agent workflow platform** (480 minutes): Deliver the full design within 40 minutes and answer six failure-injection follow-ups.

### Security and evaluation depth

- **A · Build the secure tool-execution design** (420 minutes): Map five threats to preventive, detective, revocation, and residual-risk controls.
- **A · Implement the agent evaluation release gate** (540 minutes): Implement deterministic fakes, ten cases, two grader types, slice metrics, trace links, and a rollback decision.

### Implementation, retrieval, and application test

- **B · Complete six agent-platform coding drills** (600 minutes): Cover async fan-out, idempotent updates, bounded queues, TTL cache, streaming aggregation, and retry classification.
- **B · Run three full mock loops and a bounded application test** (480 minutes): Run recruiter, coding, design, deep-dive, and behavioral sections; record misses, retries, resume version, target cohort, and stage outcomes.

## Selected questions and answer boundaries

### Why are you targeting Agent Platform roles instead of a conventional backend or data platform role?

**Why asked:** Tests whether the move follows from shipped work rather than title chasing.

**Answer structure:** start with backend platform identity → name the invoke service and exact ownership → connect the next scope to durable developer primitives → state security and evaluation gaps honestly

**Still missing:** candidate-specific motivation

**Do not claim:** proven hyperscale agent-runtime ownership

### Design a multi-tenant platform for long-running agents that call external tools and can resume after failures.

**Why asked:** Tests the central primary-role requirement and three repeated market capabilities.

**Answer structure:** define tenants, workflow duration, tools, and SLOs → separate control plane, execution plane, and event log → design idempotency, checkpoints, leases, and recovery → close with quotas, observability, cost, and degraded modes

**Still missing:** production checkpoint and replay ownership

**Do not claim:** prior global agent scheduler ownership

### How would you isolate tool execution and enforce identity and permissions for an enterprise agent?

**Why asked:** Tests the largest missing capability in the primary role.

**Answer structure:** name assets and trust boundaries → authenticate user and authorize each delegated action → isolate execution and limit network, credentials, time, and resources → audit decisions and support revocation and incident response

**Still missing:** sandbox and delegated identity experience

**Do not claim:** production sandbox ownership

### Implement a typed agent loop that calls tools with deadlines, retries, cancellation, and deterministic tests.

**Why asked:** Tests whether the candidate can turn model calls into reliable software.

### Design and implement the release gate for a change to agent routing or tool selection.

**Why asked:** Tests evaluation, observability, and production feedback.

**Answer structure:** define user outcome and failure taxonomy → build representative and adversarial datasets → combine deterministic, model-based, and human review → gate rollout using slices, traces, canary metrics, and rollback

**Still missing:** production LLM evaluation platform

**Do not claim:** existing evaluation flywheel

### Implement an idempotent session update that handles duplicate callbacks and concurrent tool results.

**Why asked:** Tests APIs, state, concurrency, and production correctness in one bounded problem.

### Tell me about a production failure where retries or scaling made the problem worse. What did you change?

**Why asked:** Tests operational judgment and learning from failure.

## Learning sequence

### Durable agent runtime and recovery

1. [Temporal durable execution overview](https://docs.temporal.io/)
   - Read: Read the durable execution, workflows, activities, event history, retries, and failure-detection concepts.
   - Skip: Skip SDK tutorials after the replay and activity boundary can be explained.
   - Mastery check: Defend replay, idempotency, and recovery for three crash points without notes.
2. [AWS Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
   - Read: Read timeout selection, retry side effects, exponential backoff, jitter, and idempotency sections.
   - Skip: Skip AWS-specific client setup.
   - Mastery check: Explain why each layer does or does not retry and prevent multiplicative retries.

### Secure tool execution and identity

1. [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
   - Read: Read the risks on agent goal hijack, tool misuse, identity and privilege abuse, memory poisoning, and cascading failures.
   - Skip: Skip risks that do not alter the selected enterprise-tool design on the first pass.
   - Mastery check: Apply the threat table to the system design and answer one bypass follow-up per control.
2. [AWS guidance on data perimeters](https://docs.aws.amazon.com/prescriptive-guidance/latest/data-perimeters-introduction/welcome.html)
   - Read: Read the overview and identity, resource, and network perimeter concepts.
   - Skip: Skip organization rollout details after the policy boundaries are clear.
   - Mastery check: Explain confused-deputy prevention, credential expiry, revocation, and tenant isolation.

### Agent evaluation and trace-driven release

1. [OpenAI evaluation best practices](https://platform.openai.com/docs/guides/evals)
   - Read: Read eval design, dataset construction, grader choice, continuous evaluation, and failure-analysis sections.
   - Skip: Skip SDK syntax until the evaluation contract is written with fake clients.
   - Mastery check: Run the gate twice, explain grader disagreement, and show which regression blocks release.
2. [OpenTelemetry traces documentation](https://opentelemetry.io/docs/concepts/signals/traces/)
   - Read: Read traces, spans, span context, attributes, events, links, and status.
   - Skip: Skip collector deployment and language SDK setup.
   - Mastery check: Use one trace to diagnose a wrong tool choice, a timeout, and a high-cost request.

### Backend and AI implementation practice

1. [Python asyncio synchronization primitives](https://docs.python.org/3/library/asyncio-sync.html)
   - Read: Read Lock, Event, Condition, Semaphore, and timeout behavior; implement one bounded fan-out example.
   - Skip: Skip low-level event-loop internals.
   - Mastery check: Implement an unseen variant in 45 minutes and explain cancellation and race behavior.

## Provenance and limitations

- [Original synthetic backend and agent-service resume](https://example.com/synthetic-sources/agentic-llm-platform/candidate-evidence): Candidate facts for this fictional demonstration only
- [OpenAI Software Engineer, API Agents](https://openai.com/careers/software-engineer-api-agents-san-francisco/): Primary target responsibilities, requirements, location, and role boundary
- [Five-role official Agent Platform market baseline](https://example.com/synthetic-sources/agentic-llm-platform/market-baseline): Cross-company claims supported by at least two official employer roles
- Official role pages were active when retrieved; this report does not promise that they remain open.
- Interview rounds and questions are preparation guidance inferred from supplied requirements, not a confirmed employer interview loop.
- No referenced organization endorses CareerLens.
- No numeric fit score, interview probability, offer probability, or employment prediction is produced.

See [ATTRIBUTION.md](../ATTRIBUTION.md) and [source-manifest.json](../source-manifest.json).
