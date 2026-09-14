# Agentic and LLM Platform Job Evidence

Access date: 2026-08-29  
Geographic scope: United States  
Source policy: official employer career pages or employer-controlled applicant-tracking pages only

## Research decision

Use OpenAI's **Software Engineer, API Agents** role as the primary target. It is the cleanest test of the intended CareerLens case because the posting explicitly describes the work as backend and systems engineering rather than model training. Its requirements map directly to a senior backend or data-platform candidate while still exposing meaningful gaps in agent orchestration, secure execution, observability, evaluation, and long-running workflows.

The five baseline roles come from distinct employers. They are not treated as OpenAI requirements. They are used only to support repeated market-capability claims when at least two employers say substantially the same thing.

## Active-status verification

Each page below rendered a current title and application path when checked on 2026-08-29. OpenAI's page displayed an active **Apply now** control. The Ashby-hosted employer pages displayed **Apply for this Job** in their indexed official posting content. This is point-in-time evidence, not a guarantee that a role will remain open after the access date.

## Primary target

### P1. OpenAI, Software Engineer, API Agents

- Location: San Francisco, California
- Work arrangement: the posting identifies San Francisco; it does not advertise a US-remote option
- Official source: [OpenAI careers, Software Engineer, API Agents](https://openai.com/careers/software-engineer-api-agents-san-francisco/)
- Active on access date: yes; the page showed `Apply now`
- Why this is the primary role: it asks for an experienced backend engineer to turn agent capabilities into dependable production primitives and explicitly says the work is software and systems engineering, not model training
- Key responsibilities:
  - build and operate a shared agent harness and backend infrastructure for long-running workflows;
  - build reusable search and connected-context, memory, tool-execution, delegation, subagent, and multi-agent capabilities;
  - establish secure execution, identity and permissions, observability, evaluations, reliability, and cost and latency controls;
  - translate model progress, traces, evaluations, and real workflows into measurable improvements.
- Key candidate requirements:
  - 7+ years in backend, infrastructure, platform, or product engineering;
  - strong backend fundamentals and evidence of leading ambiguous systems into reliable production services;
  - proficiency in a backend language such as Python, Go, Rust, or TypeScript;
  - systems-design and operational judgment across distributed systems, APIs, orchestration, search or storage, compute, identity, observability, and reliability;
  - ability to turn complex infrastructure into durable abstractions for developers;
  - ownership of security, reliability, and operational excellence.
- Case implications:
  - candidate evidence for API design, AWS Bedrock integration, RAG, DynamoDB-backed sessions, testing, containers, and backend ownership is relevant;
  - the case must not convert that evidence into unsupported claims about secure sandboxes, identity and permissions, multi-agent delegation, production evaluation ownership, or operation of long-running agents at OpenAI-scale;
  - the defensible application decision is conditional, with interview risk concentrated in distributed agent runtime design, failure recovery, evaluation, security boundaries, and cost and latency tradeoffs.

## Market baseline roles

### B1. LiveKit, Software Engineer, Agents

- Location: NAMER, APJ, EMEA
- Work arrangement: remote; NAMER includes the United States
- Official source: [LiveKit careers, Software Engineer, Agents](https://jobs.ashbyhq.com/livekit/1757f49e-7e19-4c45-85f7-e4637dff66fb/)
- Active on access date: yes; the employer posting displayed `Apply for this Job`
- Key requirements and work:
  - build core abstractions and infrastructure for real-time voice, text, durable workflows, and agent-to-agent communication;
  - reason about state, concurrency, and asynchronous workflows;
  - design simple developer APIs over complex distributed and real-time systems;
  - use Python and TypeScript;
  - bring experience with LLM applications and agentic systems; developer tools, frameworks, or SDKs are advantageous.

### B2. Browserbase, Software Engineer, Agent Platform

- Location: San Francisco, California
- Work arrangement: on-site, five days per week; relocation openness is explicitly requested
- Official source: [Browserbase careers, Software Engineer, Agent Platform](https://jobs.ashbyhq.com/Browserbase/7724fbe3-6a27-4418-9705-2dcc40751a16)
- Active on access date: yes; the employer posting displayed an application section
- Key requirements and work:
  - build and operate developer-first agent APIs and an open-source browser-automation framework;
  - deploy production AI systems used by developers and customers;
  - work primarily in TypeScript, with Python and Go also valued;
  - bring experience in developer tools, frameworks, or libraries;
  - agent/LLM, distributed-systems, reinforcement-learning, or browser-automation experience is relevant;
  - demonstrate ownership, judgment under ambiguity, communication, and public engineering work.

### B3. Sage Care, Software Engineer, Agent Platform

- Location: `HQ`; the posting concerns a US healthcare company but does not name the city in its location field
- Work arrangement: hybrid
- Official source: [Sage Care careers, Software Engineer, Agent Platform](https://jobs.ashbyhq.com/sagecare/91ef00d3-f0f1-45bb-b26a-3164f0f68718/)
- Active on access date: yes; the employer posting displayed `Apply for this Job`
- Key requirements and work:
  - own agent orchestration, tool use, and control flow for production voice agents;
  - make multi-step workflows dependable through workflow selection, tool coordination, failure handling, and recovery;
  - debug non-deterministic production failures and regressions;
  - balance latency, correctness, reliability, and cost;
  - operate systems on call and improve them from real usage;
  - 7+ years of software engineering and production AI-system ownership are required.
- Location caveat: because the posting's visible location field is only `HQ`, downstream artifacts must not invent a city or remote eligibility.

### B4. Replit, Senior Software Engineer, Agent Platform

- Location: Foster City, California
- Work arrangement: hybrid
- Official source: [Replit careers, Senior Software Engineer, Agent Platform](https://jobs.ashbyhq.com/Replit/b82de6f8-aebf-47b8-8bdc-39ea33807975/)
- Active on access date: yes; the employer posting displayed `Apply for this Job`
- Key requirements and work:
  - build high-throughput backend services, including streaming between users and agents;
  - design shared state for human-agent collaboration across shells and filesystems;
  - build durable interfaces between agents, internal systems, and external agent systems such as MCP;
  - bring 5+ years of backend-service, systems, or platform experience;
  - AI-product experience, full-stack range, and collaborative-state technologies are preferred.

### B5. Whatnot, LLM Platform Engineer

- Location: San Francisco, Los Angeles, New York, or Seattle
- Work arrangement: the posting lists those four US offices and does not advertise US-remote status
- Official source: [Whatnot careers, LLM Platform Engineer](https://jobs.ashbyhq.com/whatnot/bbf75c51-3a20-4989-bd13-1f24b66dbb16/)
- Active on access date: yes; the employer posting remained in Whatnot's application system with an application flow
- Key requirements and work:
  - 4+ years of professional experience developing machine-learning systems and algorithms;
  - an explicitly LLM-platform-focused remit within a high-scale live-commerce engineering organization;
  - the role is materially more ML-specific than the primary OpenAI role and therefore acts as evidence of an adjacent, not interchangeable, role family.
- Evidence boundary: the currently accessible official page exposes less indexed responsibility text than the other sources. Do not infer detailed evaluation, serving, orchestration, or infrastructure requirements from the title alone.

## Cross-company capability claims

Only the claims below meet the two-employer support rule. A mention is counted only when the official posting expresses the capability in responsibilities or candidate requirements.

| Market capability | Supporting official roles | Evidence-backed interpretation for the case |
| --- | --- | --- |
| Strong backend and systems engineering remains foundational | OpenAI P1; Browserbase B2; Replit B4; Sage B3 | Agent-platform hiring is not a prompt-only track. Candidates need evidence of production services, APIs, systems judgment, and operational ownership. |
| Orchestration, tool use, and durable workflow control are central | OpenAI P1; LiveKit B1; Sage B3 | Prepare state machines, tool-call boundaries, retries, idempotency, checkpointing, delegation, and long-running workflow recovery. |
| Reliability and failure handling must account for non-deterministic model behavior | OpenAI P1; Sage B3; Replit B4 | A credible design must separate deterministic control-plane guarantees from probabilistic model output and explain fallback, recovery, and degraded modes. |
| State, concurrency, asynchronous execution, and shared context matter | LiveKit B1; Replit B4; OpenAI P1 | The candidate should be ready to design session state, concurrent tool execution, streaming, durable state, and coordination across long-lived work. |
| Developer-facing abstractions and APIs are a first-class product surface | OpenAI P1; LiveKit B1; Browserbase B2; Replit B4 | Interview preparation should include API ergonomics, stable contracts, SDK or framework boundaries, versioning, and how complexity is hidden without hiding failure semantics. |
| Observability, evaluation, and production feedback are expected platform concerns | OpenAI P1; Sage B3 | The Runbook should test whether the candidate can connect traces, outcome metrics, regression tests, evaluation datasets, and incident signals to release decisions. |
| Latency, cost, and reliability require explicit tradeoffs | OpenAI P1; Sage B3 | System-design answers must include budgets, model/provider routing, caching or retrieval tradeoffs, timeouts, and measurable service objectives rather than a generic scaling discussion. |
| Python and TypeScript recur as implementation languages | OpenAI P1; LiveKit B1; Browserbase B2 | Coding preparation should emphasize production-quality Python or TypeScript, async behavior, APIs, testing, and readable interfaces, not model-training notebooks alone. |
| Production ownership and judgment under ambiguity are repeatedly screened | OpenAI P1; Browserbase B2; Sage B3; Replit B4 | Recruiter, hiring-manager, and behavioral preparation should demand specific examples of ambiguous decisions, incidents, tradeoffs, rollout, and measurable ownership. |

## Claims that do not meet the market-wide threshold

- GPU serving and model training are not baseline requirements for this role set. The OpenAI primary role explicitly distinguishes itself from model training.
- Reinforcement learning appears as an alternative or bonus in Browserbase's posting, not a repeated requirement.
- Browser automation is Browserbase-specific.
- Voice and telephony are central to Sage and relevant to LiveKit, but they should not be represented as a universal Agent Platform requirement.
- CRDTs and Operational Transforms are Replit-specific preferences.
- Open-source contributions are emphasized by Browserbase and valued by LiveKit, but the postings do not establish them as a universal hard requirement.
- Whatnot's explicit ML-systems requirement is more specialized than the backend/platform center of gravity in the other roles.

## Recommended evidence mapping for the synthetic candidate

| Candidate evidence | Defensible mapping | Remaining gap or interview risk |
| --- | --- | --- |
| RESTful agent invoke endpoint | backend APIs; developer-facing interface; tool/provider integration | stable contract design, authorization boundaries, idempotency, streaming, versioning, and long-running execution are not yet proven |
| Bedrock, RAG, and knowledge-base integration | model/provider integration; connected context; retrieval-backed agent behavior | retrieval quality evaluation, provider failover, prompt-injection boundaries, and cost/latency measurement remain unproven |
| DynamoDB session persistence | session and workflow state | concurrency control, checkpointing, replay, consistency, retention, privacy, and cross-region failure behavior remain unproven |
| Unit and API tests | basic production engineering discipline | non-deterministic evals, regression datasets, trace-based diagnosis, and release gates remain unproven |
| Horizontal scaling across Docker containers | containerized scaling and stateless service instincts | workload isolation, sandbox security, Kubernetes or global scheduling, cold starts, durable orchestration, and cost controls remain unproven |
| Production backend/data-platform ownership | strong transfer evidence for the role family | direct ownership of a production agent platform and its evaluation or observability loop remains the main credibility gap |

## Case-selection conclusion

The primary role is ambitious but adjacent enough to be useful. CareerLens should recommend applying selectively while positioning the candidate as a senior backend and platform engineer who has shipped an agent-enabled service, not as an ML researcher or proven hyperscale agent-runtime owner. The Runbook should prioritize five interview-blocking areas:

1. durable agent orchestration and failure recovery;
2. secure tool execution, identity, and permission boundaries;
3. evaluation, tracing, and production feedback loops;
4. state, concurrency, streaming, and long-running workflow design; and
5. measurable latency, reliability, and cost tradeoffs.

These priorities come from the primary posting and repeated official market evidence. They are not inferred from forum anecdotes, course curricula, or the target job title alone.
