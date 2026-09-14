#!/usr/bin/env python3
"""Build the canonical public Agentic and LLM Platform case."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case-studies/agentic-llm-platform"


def resource(
    resource_id: str,
    title: str,
    url: str,
    role: str,
    dimension: str,
    starting_state: str,
    why: str,
    read: str,
    skip: str,
    output: str,
    done: str,
    questions: list[str],
    minutes: int,
    sequence: int,
    dependencies: list[str] | None = None,
) -> dict:
    return {
        "resource_id": resource_id,
        "title": title,
        "url": url,
        "source_class": "official",
        "dimension": dimension,
        "why_it_fits": why,
        "candidate_starting_state": starting_state,
        "resource_role": role,
        "reading_scope": read,
        "skip_guidance": skip,
        "estimated_minutes": minutes,
        "assigned_output": output,
        "mapped_question_ids": questions,
        "completion_condition": done,
        "sequence": sequence,
        "dependencies": dependencies or [],
        "freshness": {"status": "verify_before_interview", "checked_at": "2026-08-29"},
        "verification_state": "verified",
    }


def question(
    question_id: str,
    kind: str,
    prompt: str,
    why: str,
    reason: str,
    priority: str,
    rounds: list[str],
    requirements: list[str],
    relevance: str,
    done: str,
) -> dict:
    return {
        "question_id": question_id,
        "kind": kind,
        "prompt": prompt,
        "why_asked": why,
        "selection_reason": reason,
        "priority": priority,
        "confidence": "high",
        "mapped_rounds": rounds,
        "mapped_requirements": requirements,
        "candidate_relevance": relevance,
        "completion_standard": done,
    }


def build() -> dict:
    data = {
        "selection_methodology": {
            "question_factors": [
                {"factor": "target coverage", "weight": "highest", "meaning": "Does the question test an explicit requirement or likely round?"},
                {"factor": "gap severity", "weight": "highest", "meaning": "Could this gap materially block the candidate?"},
                {"factor": "transfer value", "weight": "high", "meaning": "Will mastery help across adjacent Agent Platform roles?"},
                {"factor": "candidate adjacency", "weight": "high", "meaning": "Can confirmed experience support a truthful answer or implementation?"},
                {"factor": "frequency confidence", "weight": "supporting", "meaning": "Repeated official role evidence outranks anecdotes; no leak frequency is claimed."},
            ],
            "resource_factors": [
                {"factor": "candidate starting state", "rule": "Assign material based on the diagnosed starting point rather than the role title alone."},
                {"factor": "distinct resource job", "rule": "Keep at most one framework, mechanism, production, and practice resource per path."},
                {"factor": "reading efficiency", "rule": "Specify exact scope, skip scope, time, output, and stopping condition."},
                {"factor": "authority and fit", "rule": "Use primary sources for mechanisms and assign only content that changes an interview artifact."},
            ],
            "plan_factors": [
                {"factor": "risk × transfer", "rule": "Schedule high-risk gaps that recur across target roles first."},
                {"factor": "dependency order", "rule": "Mechanism learning precedes designs, implementations, and mocks that require it."},
                {"factor": "retrieval practice", "rule": "Every study block produces an artifact and later recall or mock."},
                {"factor": "capacity", "rule": "The plan must fit 56 declared hours across eight weeks; SQL is deferred and model training is suppressed in this case."},
            ],
        }
    }
    data.update({
        "identity": {
            "schema_version": "personalized_runbook.v1",
            "runbook_id": "public-agentic-llm-platform-case",
            "generated_at": "2026-08-29T00:00:00Z",
            "locale": "en-US",
        },
        "input_status": {
            "present_inputs": [
                "original_synthetic_candidate_evidence",
                "dated_primary_official_role",
                "five_role_official_market_baseline",
                "preparation_capacity",
            ],
            "missing_critical_inputs": [],
            "constraints": {"weeks": 8, "weekly_capacity_hours": 7, "public_demonstration": True},
        },
        "candidate_picture": {
            "evidence_unit_count": 17,
            "scorable_unit_count": 15,
            "source_safe": True,
            "fictional": True,
            "profile_summary": "Senior backend and data platform engineer with production API, Bedrock, RAG, DynamoDB, testing, container scaling, and high-throughput data evidence; durable agent runtime, secure execution, and evaluation-platform ownership are not proved.",
        },
        "target_picture": {
            "role_label": "Software Engineer, API Agents",
            "role_families": ["agent_platform_engineering", "backend_platform_engineering", "applied_ai_engineering"],
            "confidence": "high",
        },
        "target_portfolio": {
            "shared_core": [
                {"capability": "backend_systems", "candidate_state": "proved"},
                {"capability": "developer_facing_apis", "candidate_state": "proved"},
                {"capability": "agent_provider_integration", "candidate_state": "proved"},
                {"capability": "durable_orchestration", "candidate_state": "claimed"},
                {"capability": "evaluation_observability", "candidate_state": "claimed"},
            ],
            "company_deltas": [
                {"company": "OpenAI", "role": "Software Engineer, API Agents", "deltas": ["shared agent harness", "secure execution and identity", "long-running multi-agent workflows"]},
                {"company": "LiveKit", "role": "Software Engineer, Agents", "deltas": ["real-time concurrency", "voice and agent-to-agent communication"]},
                {"company": "Browserbase", "role": "Software Engineer, Agent Platform", "deltas": ["browser automation", "developer tooling and open source"]},
                {"company": "Replit", "role": "Senior Software Engineer, Agent Platform", "deltas": ["shared human-agent state", "MCP and filesystem interfaces"]},
            ],
        },
        "strategy": {
            "positioning": "Lead as a senior backend and data platform engineer who has shipped an agent-enabled service. Use API, session-state, testing, scaling, and operations evidence. Treat durable orchestration, secure execution, evaluation infrastructure, and hyperscale runtime ownership as explicit preparation gaps.",
            "application_posture": "Apply selectively now to backend-centered Agent Platform roles while repairing the four interview-blocking proof gaps before interviews.",
            "stop_rules": [
                "Do not describe multi-container scaling as a hyperscale agent runtime.",
                "Do not convert prompt routing tests into production LLM evaluation-platform ownership.",
                "Do not claim secure sandboxes, identity systems, Kubernetes, model training, or GPU serving.",
                "Do not use a numeric fit score or hiring probability.",
            ],
        },
        "decision_state": {
            "kind": "conditional",
            "show_numeric_score": False,
            "score": None,
            "reason": "The candidate clears the backend foundation and has shipped an agent-enabled service, but the primary role expects durable orchestration, secure execution, evaluation and observability, and long-running workflow ownership that the supplied resume does not yet prove.",
            "next_action": "repair_agent_runtime_evidence_and_prepare_designs",
        },
        "quality": {
            "runbook_depth": "dynamic_full",
            "source_safe": True,
            "export_ready": True,
            "fictional_candidate_disclosed": True,
            "numeric_fit_score_suppressed": True,
            "unresolved_gaps": ["durable_orchestration", "secure_tool_execution", "agent_evaluation_platform", "long_running_runtime_operations"],
        },
    })

    data["sources"] = [
        {
            "source_id": "synthetic-candidate-agent-platform",
            "title": "Original synthetic backend and agent-service resume",
            "url": "https://example.com/synthetic-sources/agentic-llm-platform/candidate-evidence",
            "source_class": "candidate_owned",
            "claim_scope": "Candidate facts for this fictional demonstration only",
            "freshness": {"status": "frozen", "retrieved_at": "2026-08-29"},
        },
        {
            "source_id": "openai-api-agents-role",
            "title": "OpenAI Software Engineer, API Agents",
            "url": "https://openai.com/careers/software-engineer-api-agents-san-francisco/",
            "source_class": "official",
            "claim_scope": "Primary target responsibilities, requirements, location, and role boundary",
            "freshness": {"status": "active_at_retrieval", "retrieved_at": "2026-08-29"},
        },
        {
            "source_id": "agent-platform-market-baseline",
            "title": "Five-role official Agent Platform market baseline",
            "url": "https://example.com/synthetic-sources/agentic-llm-platform/market-baseline",
            "source_class": "official",
            "claim_scope": "Cross-company claims supported by at least two official employer roles",
            "freshness": {"status": "active_at_retrieval", "retrieved_at": "2026-08-29"},
        },
    ]

    data["fit_assessment"] = [
        {"cluster": "backend_systems", "label": "Backend and distributed systems", "status": "proved", "proof_refs": ["candidate:event-platform", "candidate:async-services"]},
        {"cluster": "developer_facing_apis", "label": "Developer-facing API design", "status": "proved", "proof_refs": ["candidate:invoke-api", "candidate:idempotent-apis"]},
        {"cluster": "agent_integration", "label": "Agent, model, and retrieval integration", "status": "proved", "proof_refs": ["candidate:bedrock-strands-rag"]},
        {"cluster": "session_state", "label": "Session and workflow state", "status": "proved", "proof_refs": ["candidate:dynamodb-sessions"]},
        {"cluster": "testing_scaling", "label": "Testing and container scaling", "status": "proved", "proof_refs": ["candidate:unit-api-tests", "candidate:multi-container"]},
        {"cluster": "durable_orchestration", "label": "Durable agent orchestration and recovery", "status": "claimed", "proof_refs": ["candidate:session-status"], "boundary": "Session status and retries exist, but checkpointing, replay, idempotent tool execution, and multi-step recovery are not described."},
        {"cluster": "evaluation_observability", "label": "Agent evaluation and trace-driven release gates", "status": "claimed", "proof_refs": ["candidate:prompt-delivery-tests", "candidate:request-logs"], "boundary": "Prompt routing tests and logs do not prove golden datasets, outcome graders, trace analysis, or release gates."},
        {"cluster": "secure_execution", "label": "Secure tool execution, identity, and permissions", "status": "missing", "proof_refs": []},
        {"cluster": "long_running_runtime", "label": "Long-running and multi-agent runtime ownership", "status": "unknown", "proof_refs": []},
    ]

    data["resume_guidance"] = [
        {
            "finding_id": "agent-api-mechanism",
            "defect_type": "mechanism_and_ownership_underexplained",
            "priority": "A",
            "why_it_matters": "The strongest transferable project is described as an integration list instead of a defensible backend system.",
            "safe_direction": "Describe the invoke contract, session lifecycle, routing boundary, failure policy, tests, scaling trigger, and the candidate's architecture decision.",
            "truth_boundary": "Do not add multi-agent delegation, sandboxing, cross-region durability, or Kubernetes unless separately confirmed.",
            "completion_check": "A reviewer can trace one request from authentication through model and knowledge retrieval to persisted session state and failure handling.",
        },
        {
            "finding_id": "evaluation-language",
            "defect_type": "test_and_evaluation_conflation",
            "priority": "A",
            "why_it_matters": "The market repeatedly expects evaluation and observability; the resume currently proves deterministic tests and request logs only.",
            "safe_direction": "Name unit, API, prompt-delivery, and routing tests precisely. Add model-quality or trace-based evaluation only if a real dataset, metric, and release decision can be confirmed.",
            "truth_boundary": "Do not rename API tests as LLM evaluations or claim an evaluation flywheel.",
            "completion_check": "Every testing claim identifies its input, oracle, failure caught, and release consequence.",
        },
        {
            "finding_id": "scaling-boundary",
            "defect_type": "scale_scope_ambiguity",
            "priority": "B",
            "why_it_matters": "Senior interviewers will distinguish adding containers from designing a durable global scheduler.",
            "safe_direction": "State the original single-container constraint, concurrency signal, stateless boundary, health checks, and observed operational improvement.",
            "truth_boundary": "Keep agent-service scale separate from the independently proved 10-billion-event data platform scale.",
            "completion_check": "The bullet makes workload, mechanism, measurement, and ownership distinct without combining two systems.",
        },
    ]

    data["interview_map"] = {
        "rounds": [
            {"round_id": "recruiter_screen", "label": "Recruiter screen", "purpose": "Test seniority, motivation, location, and whether the backend-to-agent-platform transition is credible."},
            {"round_id": "hiring_manager", "label": "Hiring manager", "purpose": "Probe product judgment, platform ownership, ambiguity, and the boundary between shipped agent work and unproved runtime depth."},
            {"round_id": "coding", "label": "Coding and backend implementation", "purpose": "Test production-quality Python or TypeScript, async control flow, data structures, tests, and API clarity."},
            {"round_id": "ai_coding", "label": "AI coding", "purpose": "Implement a tool-using agent loop with typed boundaries, timeouts, deterministic fakes, and evaluation hooks."},
            {"round_id": "system_design", "label": "Agent platform system design", "purpose": "Design durable workflows, session state, tool execution, streaming, observability, security, and cost controls."},
            {"round_id": "project_deep_dive", "label": "Agent project deep dive", "purpose": "Trace the invoke service and separate confirmed personal decisions from adjacent or missing platform capabilities."},
            {"round_id": "behavioral", "label": "Behavioral and ownership", "purpose": "Test incidents, tradeoffs, disagreement, rollout judgment, and learning under uncertainty."},
        ],
        "boundary": "These are preparation categories inferred from the primary posting and repeated official market requirements, not a confirmed OpenAI interview loop.",
    }

    data["question_bank"] = [
        question("q-transition", "recruiter", "Why are you targeting Agent Platform roles instead of a conventional backend or data platform role?", "Tests whether the move follows from shipped work rather than title chasing.", "Priority A because the resume shows one agent service but a longer backend history.", "A", ["recruiter_screen", "hiring_manager"], ["backend_systems", "agent_integration"], "The candidate has a truthful bridge through the invoke service and must state the remaining gaps.", "Deliver a 90-second answer with one proved strength, one honest gap, and one reason this role family is the next logical scope."),
        question("q-workflow-design", "system_design", "Design a multi-tenant platform for long-running agents that call external tools and can resume after failures.", "Tests the central primary-role requirement and three repeated market capabilities.", "Priority A because durable orchestration is only claimed and touches state, concurrency, reliability, and developer APIs.", "A", ["system_design"], ["durable_orchestration", "session_state", "developer_facing_apis"], "DynamoDB sessions and invoke APIs provide adjacency; checkpointing and replay are gaps.", "Complete a 40-minute design covering contracts, state machine, idempotency, leases, retries, checkpoints, streaming, quotas, recovery, and SLOs."),
        question("q-secure-tools", "system_design", "How would you isolate tool execution and enforce identity and permissions for an enterprise agent?", "Tests the largest missing capability in the primary role.", "Priority A because tool access creates a hard security boundary and the resume contains no secure-execution evidence.", "A", ["system_design", "hiring_manager"], ["secure_execution"], "The current service invokes approved backends but does not prove sandboxes or delegated authorization.", "Define trust zones, short-lived credentials, allowlists, policy checks, credential handling, network limits, audit logs, and revocation without claiming prior ownership."),
        question("q-agent-loop", "ai_coding", "Implement a typed agent loop that calls tools with deadlines, retries, cancellation, and deterministic tests.", "Tests whether the candidate can turn model calls into reliable software.", "Priority A because Python or TypeScript implementation, async control flow, and failure handling recur across official roles.", "A", ["ai_coding", "coding"], ["durable_orchestration", "backend_systems"], "The candidate has API and test evidence but not a durable loop implementation.", "Finish in 60 minutes with interfaces, fake model and tool clients, retry classification, cancellation, trace hooks, and edge-case tests."),
        question("q-eval-release", "ai_coding", "Design and implement the release gate for a change to agent routing or tool selection.", "Tests evaluation, observability, and production feedback.", "Priority A because current prompt tests do not prove outcome evaluation or trace-driven release decisions.", "A", ["ai_coding", "hiring_manager"], ["evaluation_observability"], "Prompt-delivery tests are a useful starting point but not an evaluation platform.", "Produce a golden set, deterministic and model-based graders, slice metrics, trace schema, threshold policy, disagreement review, and rollback rule."),
        question("q-session-race", "coding", "Implement an idempotent session update that handles duplicate callbacks and concurrent tool results.", "Tests APIs, state, concurrency, and production correctness in one bounded problem.", "Selected over generic array volume because it maps directly to the candidate's DynamoDB session claim and market requirements.", "B", ["coding"], ["session_state", "backend_systems"], "Session persistence is proved; concurrent update policy is not.", "Implement in 40 minutes with version checks or conditional writes, duplicate detection, tests, and a clear consistency explanation."),
        question("q-incident", "behavioral", "Tell me about a production failure where retries or scaling made the problem worse. What did you change?", "Tests operational judgment and learning from failure.", "Priority B because production ownership recurs across four official role sources and the resume lacks a detailed incident story.", "B", ["behavioral", "project_deep_dive"], ["production_ownership", "reliability"], "The candidate can draw from the event platform or invoke service but must confirm the real incident.", "Deliver a six-minute story separating personal action, system mechanism, customer effect, decision, metric, and prevention work."),
    ]

    data["answer_guidance"] = [
        {"question_id": "q-transition", "outline": ["start with backend platform identity", "name the invoke service and exact ownership", "connect the next scope to durable developer primitives", "state security and evaluation gaps honestly"], "supported_refs": ["candidate:invoke-api", "candidate:event-platform"], "missing_facts": ["candidate-specific motivation"], "prohibited_claims": ["proven hyperscale agent-runtime ownership"]},
        {"question_id": "q-workflow-design", "outline": ["define tenants, workflow duration, tools, and SLOs", "separate control plane, execution plane, and event log", "design idempotency, checkpoints, leases, and recovery", "close with quotas, observability, cost, and degraded modes"], "supported_refs": ["candidate:invoke-api", "candidate:dynamodb-sessions", "candidate:multi-container"], "missing_facts": ["production checkpoint and replay ownership"], "prohibited_claims": ["prior global agent scheduler ownership"]},
        {"question_id": "q-secure-tools", "outline": ["name assets and trust boundaries", "authenticate user and authorize each delegated action", "isolate execution and limit network, credentials, time, and resources", "audit decisions and support revocation and incident response"], "supported_refs": ["candidate:authenticated-invoke"], "missing_facts": ["sandbox and delegated identity experience"], "prohibited_claims": ["production sandbox ownership"]},
        {"question_id": "q-eval-release", "outline": ["define user outcome and failure taxonomy", "build representative and adversarial datasets", "combine deterministic, model-based, and human review", "gate rollout using slices, traces, canary metrics, and rollback"], "supported_refs": ["candidate:prompt-delivery-tests", "candidate:request-logs"], "missing_facts": ["production LLM evaluation platform"], "prohibited_claims": ["existing evaluation flywheel"]},
    ]

    data["learning_tracks"] = [
        {
            "track_id": "durable_agent_runtime",
            "title": "Durable agent runtime and recovery",
            "resources": [
                resource("temporal-durable-execution", "Temporal durable execution overview", "https://docs.temporal.io/", "framework", "durable_orchestration", "Knows sessions and retries but has not proved workflow replay or durable execution.", "Provides the clearest mental model for event history, replay, activities, retries, and recovery.", "Read the durable execution, workflows, activities, event history, retries, and failure-detection concepts.", "Skip SDK tutorials after the replay and activity boundary can be explained.", "One state-machine diagram mapping the invoke service to workflow, activity, event history, and retry boundaries.", "Defend replay, idempotency, and recovery for three crash points without notes.", ["q-workflow-design"], 75, 1),
                resource("aws-retries-timeouts", "AWS Builders' Library: Timeouts, retries, and backoff with jitter", "https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/", "mechanism", "reliability", "Has retry experience but no documented retry budget for agent and tool calls.", "Adds concrete overload, retry amplification, timeout, and idempotency reasoning.", "Read timeout selection, retry side effects, exponential backoff, jitter, and idempotency sections.", "Skip AWS-specific client setup.", "A retry matrix for model, retrieval, tool, and persistence calls with timeout, retry owner, budget, and terminal state.", "Explain why each layer does or does not retry and prevent multiplicative retries.", ["q-workflow-design", "q-agent-loop", "q-incident"], 50, 2, ["temporal-durable-execution"]),
            ],
        },
        {
            "track_id": "secure_agent_execution",
            "title": "Secure tool execution and identity",
            "resources": [
                resource("owasp-agentic-top10", "OWASP Top 10 for Agentic Applications", "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/", "framework", "secure_execution", "Can authenticate an API but has no proved agent sandbox or delegated authorization design.", "Provides a bounded threat taxonomy for goal hijacking, tool misuse, identity abuse, memory poisoning, and cascading failures.", "Read the risks on agent goal hijack, tool misuse, identity and privilege abuse, memory poisoning, and cascading failures.", "Skip risks that do not alter the selected enterprise-tool design on the first pass.", "Threat table with asset, attacker, boundary, control, detection, and residual risk for five threats.", "Apply the threat table to the system design and answer one bypass follow-up per control.", ["q-secure-tools", "q-workflow-design"], 70, 1),
                resource("aws-data-perimeters", "AWS guidance on data perimeters", "https://docs.aws.amazon.com/prescriptive-guidance/latest/data-perimeters-introduction/welcome.html", "mechanism", "identity_permissions", "Understands IAM integration but has not articulated delegated identity and perimeter controls.", "Turns generic least privilege into identity, resource, and network perimeter decisions.", "Read the overview and identity, resource, and network perimeter concepts.", "Skip organization rollout details after the policy boundaries are clear.", "An authorization flow showing user identity, agent identity, tool role, short-lived credential, policy decision, and audit event.", "Explain confused-deputy prevention, credential expiry, revocation, and tenant isolation.", ["q-secure-tools"], 55, 2, ["owasp-agentic-top10"]),
            ],
        },
        {
            "track_id": "agent_evaluation",
            "title": "Agent evaluation and trace-driven release",
            "resources": [
                resource("openai-evals", "OpenAI evaluation best practices", "https://platform.openai.com/docs/guides/evals", "framework", "evaluation_observability", "Has routing tests and logs but no proved outcome dataset, graders, or release gate.", "Provides the shortest route from prompt tests to datasets, graders, continuous evaluation, and failure analysis.", "Read eval design, dataset construction, grader choice, continuous evaluation, and failure-analysis sections.", "Skip SDK syntax until the evaluation contract is written with fake clients.", "A ten-case golden set, failure taxonomy, two graders, slice metrics, and a release-gate rule.", "Run the gate twice, explain grader disagreement, and show which regression blocks release.", ["q-eval-release", "q-agent-loop"], 70, 1),
                resource("opentelemetry-traces", "OpenTelemetry traces documentation", "https://opentelemetry.io/docs/concepts/signals/traces/", "mechanism", "observability", "Has request logs but no trace model spanning agent, model, retrieval, and tool steps.", "Adds a vendor-neutral trace model that connects latency, errors, attributes, and workflow steps.", "Read traces, spans, span context, attributes, events, links, and status.", "Skip collector deployment and language SDK setup.", "A trace schema for invoke, retrieval, model, tool, persistence, and evaluation spans with redaction rules.", "Use one trace to diagnose a wrong tool choice, a timeout, and a high-cost request.", ["q-eval-release", "q-workflow-design"], 45, 2, ["openai-evals"]),
            ],
        },
        {
            "track_id": "implementation_practice",
            "title": "Backend and AI implementation practice",
            "resources": [
                resource("python-asyncio", "Python asyncio synchronization primitives", "https://docs.python.org/3/library/asyncio-sync.html", "mechanism", "async_coding", "Writes Python services but recent timed async implementation evidence is not supplied.", "Directly supports locks, events, conditions, semaphores, and barriers used in concurrent tool execution.", "Read Lock, Event, Condition, Semaphore, and timeout behavior; implement one bounded fan-out example.", "Skip low-level event-loop internals.", "Typed concurrent tool runner with semaphore, cancellation, deadline, ordered results, and deterministic tests.", "Implement an unseen variant in 45 minutes and explain cancellation and race behavior.", ["q-agent-loop", "q-session-race"], 150, 1),
            ],
        },
    ]

    data["module_selection"] = [
        {"module_id": "system_design", "label": "Agent platform system design", "state": "enabled", "reason": "Durable workflows, secure execution, state, observability, and reliability are explicit primary-role requirements and repeated market concerns.", "evidence_refs": ["target:openai-api-agents", "market:durable-workflows", "gap:secure-execution"], "confidence": "high"},
        {"module_id": "algorithms", "label": "Backend coding and data structures", "state": "enabled", "reason": "Official roles repeatedly require production backend implementation; practice is narrowed to concurrency, state, queues, and idempotency.", "evidence_refs": ["market:backend-systems", "candidate:python-java-typescript"], "confidence": "high"},
        {"module_id": "ai_coding", "label": "Agent-loop implementation and evaluation", "state": "enabled", "reason": "The candidate must prove reliable model and tool integration beyond deterministic API tests.", "evidence_refs": ["target:tool-execution", "gap:evaluation-observability"], "confidence": "high"},
        {"module_id": "project_deep_dive", "label": "Invoke service project deep dive", "state": "enabled", "reason": "This is the strongest bridge to the role and the most likely place for ownership and scale challenges.", "evidence_refs": ["candidate:invoke-api", "candidate:multi-container"], "confidence": "high"},
        {"module_id": "behavioral", "label": "Production ownership and judgment", "state": "enabled", "reason": "Ownership under ambiguity recurs across four official role sources.", "evidence_refs": ["market:production-ownership"], "confidence": "high"},
        {"module_id": "sql_data", "label": "SQL and data reasoning", "state": "deferred", "reason": "The candidate already has strong data-platform evidence, while orchestration, security, and evaluation are interview-blocking gaps.", "evidence_refs": ["candidate:event-platform", "constraint:56-hours"], "confidence": "high"},
        {"module_id": "ml_training", "label": "Model training and GPU serving", "state": "suppressed", "reason": "The primary role explicitly centers software and systems engineering, and the market baseline does not establish training or GPU serving as a shared requirement.", "evidence_refs": ["target:role-boundary", "market:excluded-generalizations"], "confidence": "high"},
    ]

    data["roadmap"] = {
        "weeks": 8,
        "weekly_capacity_hours": 7,
        "phases": [
            {
                "phase_id": "evidence_repair",
                "label": "Evidence repair and interview positioning",
                "week_range": "Weeks 1 to 2",
                "rationale": "Fix the resume claims and ownership boundary before broad preparation so every later answer starts from defensible evidence.",
                "exit_gate": "The invoke project survives a 15-minute ownership drill without implying evaluation, sandbox, or hyperscale runtime experience.",
                "actions": [
                    {"action_id": "a-resume-audit", "priority": "A", "title": "Rewrite and fact-check the invoke project", "linked_refs": ["gap:agent-api-mechanism", "gap:evaluation-language"], "estimated_minutes": 240, "artifact": "Evidence ledger, two resume bullets, and a 12-minute architecture narrative", "dependencies": [], "linked_question_ids": ["q-transition", "q-incident"], "exit_gate": "Every mechanism, metric, and ownership statement is either confirmed or removed.", "completion_condition": "Trace request, state, routing, tests, scaling, failure behavior, and personal decisions using only confirmed facts."},
                    {"action_id": "a-runtime-design", "priority": "A", "title": "Design the durable agent workflow platform", "linked_refs": ["gap:durable-orchestration", "target:long-running-workflows"], "estimated_minutes": 480, "artifact": "Architecture, state machine, failure matrix, and 40-minute talk track", "dependencies": ["a-resume-audit"], "linked_question_ids": ["q-workflow-design", "q-session-race"], "exit_gate": "Two timed runs cover replay, duplicate execution, concurrency, overload, and recovery follow-ups.", "completion_condition": "Deliver the full design within 40 minutes and answer six failure-injection follow-ups."},
                ],
            },
            {
                "phase_id": "security_and_evaluation",
                "label": "Security and evaluation depth",
                "week_range": "Weeks 3 to 5",
                "rationale": "Secure tools and release-grade evaluation are the two largest missing capabilities after the runtime foundation.",
                "exit_gate": "The candidate can connect threat controls, traces, graders, rollout thresholds, and rollback to the same system design.",
                "actions": [
                    {"action_id": "a-security-design", "priority": "A", "title": "Build the secure tool-execution design", "linked_refs": ["gap:secure-tool-execution"], "estimated_minutes": 420, "artifact": "Threat model, authorization sequence, sandbox boundary, and audit schema", "dependencies": ["a-runtime-design"], "linked_question_ids": ["q-secure-tools"], "exit_gate": "Answer five bypass and tenant-isolation follow-ups without relying on generic least-privilege language.", "completion_condition": "Map five threats to preventive, detective, revocation, and residual-risk controls."},
                    {"action_id": "a-eval-gate", "priority": "A", "title": "Implement the agent evaluation release gate", "linked_refs": ["gap:agent-evaluation-platform"], "estimated_minutes": 540, "artifact": "Golden dataset, graders, trace schema, regression report, and release rule", "dependencies": ["a-resume-audit"], "linked_question_ids": ["q-eval-release", "q-agent-loop"], "exit_gate": "A seeded routing regression is detected, explained by traces, and blocked by the documented threshold.", "completion_condition": "Implement deterministic fakes, ten cases, two grader types, slice metrics, trace links, and a rollback decision."},
                ],
            },
            {
                "phase_id": "implementation_and_mocks",
                "label": "Implementation, retrieval, and application test",
                "week_range": "Weeks 6 to 8",
                "rationale": "Timed implementation and repeated retrieval now integrate the repaired evidence and new mechanisms under interview pressure.",
                "exit_gate": "Three consecutive mock loops meet the coding, design, project, and behavioral completion standards.",
                "actions": [
                    {"action_id": "a-coding", "priority": "B", "title": "Complete six agent-platform coding drills", "linked_refs": ["market:python-typescript", "target:backend-language"], "estimated_minutes": 600, "artifact": "Six tested solutions and a retry log", "dependencies": ["a-runtime-design"], "linked_question_ids": ["q-agent-loop", "q-session-race"], "exit_gate": "Two unseen variants finish within 45 minutes with tests and complexity or concurrency analysis.", "completion_condition": "Cover async fan-out, idempotent updates, bounded queues, TTL cache, streaming aggregation, and retry classification."},
                    {"action_id": "a-mocks-applications", "priority": "B", "title": "Run three full mock loops and a bounded application test", "linked_refs": ["risk:interview-integration", "strategy:application-experiment"], "estimated_minutes": 480, "artifact": "Mock scorecards and application experiment log", "dependencies": ["a-security-design", "a-eval-gate", "a-coding"], "linked_question_ids": ["q-transition", "q-workflow-design", "q-secure-tools", "q-incident"], "exit_gate": "Three mocks pass and application feedback can be attributed to a recorded cohort and resume version.", "completion_condition": "Run recruiter, coding, design, deep-dive, and behavioral sections; record misses, retries, resume version, target cohort, and stage outcomes."},
                ],
            },
        ],
    }

    data["application_experiment"] = {
        "hypothesis": "Positioning the candidate as a senior backend platform engineer with a shipped agent service will outperform broad LLM branding for backend-centered Agent Platform roles.",
        "cohorts": [
            {"name": "backend-centered-agent-platform", "purpose": "Test the primary positioning against roles emphasizing APIs, orchestration, state, reliability, and developer abstractions."},
            {"name": "ml-heavy-llm-platform", "purpose": "Measure whether model-training or ML-systems requirements create an earlier rejection boundary."},
        ],
        "success_signal": "Across a small recorded batch, recruiter or hiring feedback recognizes backend and platform strengths and identifies the same durable-runtime, security, or evaluation gaps; volume alone is not success.",
    }
    return data


def main() -> int:
    output = CASE / "output"
    output.mkdir(parents=True, exist_ok=True)
    (output / "runbook.json").write_text(
        json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
