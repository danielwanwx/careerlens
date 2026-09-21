---
name: careerlens
description: Build or refresh a source-auditable career diagnosis and preparation runbook from authorized candidate evidence, target requirements, constraints, and timeline. Use for any profession; do not use it to submit applications, contact people, or invent candidate facts.
---

# CareerLens

Produce `personalized_runbook.v1` through this bounded loop:

```text
discover -> diagnose -> build -> validate -> render -> refresh
```

Keep candidate evidence separate from target research. Candidate facts may come
only from authorized candidate-owned material. Jobs, company guidance,
government sources, and learning resources describe the target; they never
prove the candidate has done something.

Use one of four modes:

- `discover`: record the target, evidence, constraints, timeline, and smallest
  missing inputs. Thin input is a valid input-gate outcome.
- `diagnose`: mark each target capability `proved`, `claimed`, `missing`, or
  `unknown`, with the evidence that would change its state.
- `build`: create resume guidance, shared preparation, sourced target deltas,
  interview questions, learning tracks, a feasible roadmap, and an application
  experiment. Link every Priority A action to a real gap or interview signal.
- `refresh`: incorporate new evidence, interview outcomes, or changed sources
  and emit a delta without silently changing an upstream score or gate.

Do not include raw resumes, full job descriptions, private profile text,
provider traces, secrets, unsupported metrics, or fabricated first-person
scripts in the artifact. When a fact is unknown, ask for it or preserve the
unknown state.

Priority controls sequence, not difficulty:

- `A / core_required`: required before the relevant decision;
- `B / important_extension`: add after Priority A is credible;
- `C / company_calibration`: activate for a concrete sourced target.

Read only the reference needed for the active step:

- Intake or evidence-state decisions: [intake and diagnosis](references/intake-and-diagnosis.md)
- Research or volatile claims: [evidence and research policy](references/evidence-and-research-policy.md)
- Optional public Ashby/Greenhouse acquisition before research: [public job monitor](references/public-job-monitor.md)
- Artifact assembly: [runbook contract](references/runbook-contract.md)
- Export or review: [quality gates](references/quality-gates.md)

Validate the final JSON with `scripts/validate_runbook.py`. Render a reviewable
Markdown projection with `scripts/render_runbook.py`; JSON remains canonical.

The optional public-job monitor is read-only target evidence, never candidate
evidence or an application action. It is local-only, needs Python 3.11+, and
requires each user to configure their own Jev credential if they choose its
observed-link selector. Do not send credentials, resumes, Coach data, or form
content through that monitor.

When the task is to collect known official Ashby or Greenhouse evidence and the
local Python 3.11+ monitor is configured, use its monitored fetch before
`diagnose`. Inspect its bounded evidence, `incomplete`, and `navigation`
signals; they are not evidence that a role is open. Keep other authorized,
source-auditable research in the normal CareerLens flow and preserve canonical
runbook JSON as the final artifact.
