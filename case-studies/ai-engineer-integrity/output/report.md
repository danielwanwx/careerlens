# CareerLens public Machine Learning Engineer, Integrity case

> Reproducible demonstration using an MIT-licensed fictional candidate and a dated official target role. This is not a real application or hiring prediction.

## Executive decision

- **Target:** Machine Learning Engineer, Integrity
- **Decision:** conditional
- **Reason:** The candidate has strong adjacent production ML evidence, but the role-specific integrity and LLM post-training requirements are not yet supported by inspectable examples.
- **Next action:** build_integrity_and_post_training_evidence
- **Numeric fit score:** intentionally not used

## Evidence matrix

| Capability | State | Candidate evidence boundary |
|---|---|---|
| Production ML systems | `proved` | candidate:smartassist-api, candidate:aws-ml-pipelines, candidate:model-monitoring |
| Deep learning and transformers | `proved` | candidate:recommendation-deep-learning, candidate:transformer-nlp |
| Scalable data pipelines | `proved` | candidate:kafka-spark, candidate:dataflow-10tb |
| Model monitoring and evaluation | `proved` | candidate:prometheus-grafana, candidate:llm-eval-framework |
| Cross-functional delivery and leadership | `proved` | candidate:kpi-collaboration, candidate:mentoring |
| LLM post-training depth | `claimed` | The resume does not identify the method, dataset, evaluation, or individual ownership. |
| Content integrity and abuse prevention | `missing` | No candidate-owned proof |
| Adversarial misuse evaluation | `unknown` | No candidate-owned proof |

## Resume guidance

### A · integrity-domain-gap

- **Why it matters:** The target team protects the platform from content abuse and scaled attacks; general RAG and recommendation work does not prove that judgment.
- **Safe direction:** Add only candidate-confirmed integrity, trust-and-safety, fraud, anomaly, abuse, or adversarial evaluation work. If none exists, leave it as a preparation gap.
- **Truth boundary:** Do not relabel generic anomaly detection as abuse prevention without matching users, threats, labels, and decisions.
- **Done when:** A reviewer can identify the threat model, data, model decision, failure cost, and measured result.

### A · post-training-proof

- **Why it matters:** The posting names distillation, supervised fine-tuning, and policy optimization, while the resume says only 'fine-tuning techniques.'
- **Safe direction:** Replace the broad phrase with a candidate-confirmed method, dataset construction, objective, evaluation protocol, and trade-off, or remove the implication of depth.
- **Truth boundary:** Do not infer SFT, RLHF, DPO, distillation, or policy optimization from the generic fine-tuning phrase.
- **Done when:** The candidate can defend the exact post-training method and explain why it was selected.

### B · ownership-clarity

- **Why it matters:** Senior interviewers will separate platform scope from the candidate's personal technical decisions.
- **Safe direction:** For SmartAssist, identify one architecture decision, one failed approach, one model-quality trade-off, and the candidate's direct ownership.
- **Truth boundary:** Keep team outcomes and individual contributions distinct.
- **Done when:** The answer names the candidate's decision, alternatives, evidence, and consequence without expanding ownership.

## Interview preparation map

- **Recruiter screen:** Clarify motivation, location, seniority, and whether the candidate's ML background maps to integrity work.
- **Coding and algorithms:** Test data structures, implementation quality, complexity analysis, and reliable handling of edge cases.
- **ML and post-training depth:** Test transformers, training objectives, dataset quality, fine-tuning, evaluation, and model failure analysis.
- **ML integrity system design:** Design an abuse-detection system with data, modeling, serving, feedback, monitoring, and adversarial trade-offs.
- **Project and ownership deep dive:** Separate personal decisions from project scope and probe failed approaches, measurement, and operations.
- **Behavioral and cross-functional ownership:** Test judgment in ambiguity, competing priorities, disagreement, and end-to-end delivery.

> These are preparation-oriented round types inferred from the official requirements, not a confirmed OpenAI interview loop.

## 6-week preparation plan

### Evidence repair

- **A · Audit the SmartAssist fine-tuning claim** (180 minutes): Produce a one-page method, data, objective, evaluation, ownership, and limitation brief using only confirmed facts.
- **A · Design a coordinated content-abuse detection system** (420 minutes): Deliver a 35-minute design covering threats, data, labels, model/rules, serving, review, evaluation, monitoring, privacy, and rollback.

### Interview depth

- **B · Build a post-training comparison map** (300 minutes): Compare prompting, RAG, SFT, distillation, and policy optimization across data, cost, evaluation, and failure modes.
- **B · Practice integrity-flavored coding problems** (480 minutes): Solve and explain eight medium problems spanning hash maps, heaps, intervals, graphs, streams, and sliding windows with tests and complexity analysis.
- **B · Prepare the SmartAssist ownership deep dive** (240 minutes): Give a 12-minute narrative with architecture, personal decisions, failed approach, metrics, incident/rollback, and two trade-offs.

## Selected questions and answer boundaries

### Your background is strongest in production ML and RAG. Why move into platform integrity now?

**Why asked:** Tests motivation without assuming direct integrity experience.

**Answer structure:** start from verified production ML and model-quality work → explain the specific integrity problem that motivates the transition → acknowledge the direct domain gap → show the preparation artifact and learning plan

**Still missing:** candidate-specific motivation

**Do not claim:** prior abuse-prevention ownership

### Implement a bounded event counter that detects abusive burst patterns while handling late events.

**Why asked:** Connects algorithms and reliable implementation to the target domain.

### Walk through the exact fine-tuning method used in SmartAssist, including data, objective, evaluation, and failure cases.

**Why asked:** The resume uses a broad phrase that may not prove post-training depth.

**Answer structure:** state only the method actually used → describe data and objective → explain offline and online evaluation → name one failed approach and trade-off

**Still missing:** method, dataset, objective, evaluation, individual ownership

**Do not claim:** SFT, distillation, policy optimization

### Design a real-time system that detects coordinated content abuse at platform scale.

**Why asked:** Tests the most important role-specific gap.

**Answer structure:** define abuse actors, protected users, decisions, and latency → design event ingestion, labels, features, model, rules, and human review → cover class imbalance, coordinated attacks, feedback loops, and privacy → define offline metrics, online guardrails, drift detection, and rollback

**Still missing:** real integrity-domain experience

**Do not claim:** production abuse-prevention ownership

### How would you evaluate a classifier when attackers adapt and the positive class is rare?

**Why asked:** Tests adversarial evaluation, calibration, cost trade-offs, and monitoring.

### Tell me about an ambiguous ML problem where you changed direction after production evidence contradicted the original plan.

**Why asked:** Tests end-to-end ownership and learning under uncertainty.

### Maintain the top K abusive actors over a sliding time window with bounded memory.

**Why asked:** Tests hash maps, heaps, window eviction, and correctness under updates.

### Given account-event links, identify suspicious coordinated components above a configurable threshold.

**Why asked:** Tests graph construction, traversal, component statistics, and scale-aware reasoning.

### Build a testable evaluation harness for an integrity classifier using a fake model client and configurable graders.

**Why asked:** Tests production-quality AI implementation rather than notebook-only model knowledge.

### Design the human-review and feedback loop for uncertain integrity decisions without creating label leakage or reviewer overload.

**Why asked:** Tests the operational system around the model, not only classifier architecture.

### How would you choose and change an enforcement threshold when false positives harm legitimate users?

**Why asked:** Tests calibration, cost-sensitive evaluation, staged rollout, and policy judgment.

### Tell me about a technical disagreement where you changed the decision process rather than merely winning the argument.

**Why asked:** Tests senior cross-functional influence and decision quality.

## Learning sequence

### LLM post-training

1. [OpenAI model optimization and fine-tuning guide](https://platform.openai.com/docs/guides/fine-tuning)
   - Read: Study when to fine-tune, data formatting, holdout evaluation, and iteration boundaries.
   - Skip: Skip provider-specific API syntax after you can explain the method-selection logic.
   - Mastery check: Compare prompting, retrieval, SFT, and distillation for one integrity classifier scenario.
2. [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)
   - Read: Read the method, data-collection, reward-model, PPO, and evaluation sections; capture the pipeline and failure modes.
   - Skip: Skip exhaustive appendix tables on the first pass.
   - Mastery check: Draw the SFT-to-reward-model-to-policy-optimization flow and name two sources of bias or reward misspecification.

### Integrity and adversarial evaluation

1. [OpenAI safety evaluations hub](https://openai.com/safety/evaluations-hub/)
   - Read: Study evaluation categories, measurement boundaries, and how results are communicated.
   - Skip: Do not attempt to memorize every benchmark result.
   - Mastery check: Define an abuse-evaluation suite with offline quality, adversarial coverage, and production monitoring layers.
2. [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
   - Read: Focus on prompt injection, sensitive information disclosure, excessive agency, and unbounded consumption.
   - Skip: Skip implementation checklists unrelated to the chosen integrity-system design.
   - Mastery check: Map four threats to signals, mitigations, residual risks, and measurable alarms.

### Production integrity systems

1. [Google Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml)
   - Read: Read rules 1–12, 21–28, and 32–39; focus on pipelines, first models, training-serving skew, feedback loops, and launch criteria.
   - Skip: Skip rules about organization-specific process that do not change the integrity-system design.
   - Mastery check: Explain how data, training, serving, monitoring, and retraining fail independently and name one guardrail for each.
2. [AWS Builders' Library: Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
   - Read: Read the sections on overload detection, request prioritization, load shedding, retry amplification, and testing.
   - Skip: Skip service-specific implementation details after the policy and failure interactions are clear.
   - Mastery check: Defend when the classifier path sheds, queues, degrades, or fails closed under three overload scenarios.

### Evaluation implementation and coding delivery

1. [OpenAI evaluation best practices](https://platform.openai.com/docs/guides/evals)
   - Read: Read eval design, dataset construction, grader choice, continuous evaluation, and failure analysis examples.
   - Skip: Skip SDK syntax until the evaluation contract and test cases are written with a fake model client.
   - Mastery check: Implement the harness with deterministic tests and explain grader disagreement, leakage, and regression thresholds.
2. [LeetCode Top Interview 150](https://leetcode.com/studyplan/top-interview-150/)
   - Read: Use only hash map, sliding window, heap, intervals, graph traversal, and design-a-data-structure sections; complete one new and one spaced-repeat problem per session.
   - Skip: Skip dynamic programming, advanced math, and unrelated hard problems during this six-week plan.
   - Mastery check: Solve two unseen medium variants in 35 minutes each with clarification, tests, and complexity analysis.

## Provenance and limitations

- [MIT-licensed fictional baseline resume](https://github.com/aarangop/resume-mcp/blob/main/templates/baseline_resume.md): Candidate facts for this fictional demonstration only
- [OpenAI Machine Learning Engineer, Integrity](https://openai.com/careers/machine-learning-engineer-integrity-san-francisco/): Dated target-role responsibilities, requirements, location, and published compensation
- Official role pages were active when retrieved; this report does not promise that they remain open.
- Interview rounds and questions are preparation guidance inferred from supplied requirements, not a confirmed employer interview loop.
- No referenced organization endorses CareerLens.
- No numeric fit score, interview probability, offer probability, or employment prediction is produced.

See [ATTRIBUTION.md](../ATTRIBUTION.md) and [source-manifest.json](../source-manifest.json).
