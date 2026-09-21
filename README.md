# CareerLens

Found a role you want, but not sure what to fix first?

CareerLens compares your resume with the actual role and builds a personal
Runbook. It shows what already matches, what a recruiter may challenge, which
questions to practice, what to study or skip, and what to do each week. It does
not invent experience to fill the gaps.

- [Explore the public showcase](https://example-org.github.io/careerlens/)
- [Try the five-minute quickstart](#five-minute-quickstart)

CareerLens is an open-source skill for Codex. The source of truth is validated
JSON, with deterministic Markdown and HTML views for review and sharing.

## See the result first

The public AI-engineering case compares a licensed fictional candidate with a
dated official role page. It reaches a **conditional** decision without a
numeric fit score, preserves all four evidence states, and converts the gaps
into a capacity-checked 27-hour preparation plan.

- [Explore the interactive runbook demo](https://example-org.github.io/careerlens/cases/ai-engineer-integrity/)
- [Open the deterministic HTML report](case-studies/ai-engineer-integrity/output/report.html)
- [Read the Markdown report](case-studies/ai-engineer-integrity/output/report.md)
- [Inspect the canonical JSON](case-studies/ai-engineer-integrity/output/runbook.json)
- [Verify source attribution](case-studies/ai-engineer-integrity/ATTRIBUTION.md)

The candidate is fictional and derived from an MIT-licensed public sample; it
is not the maintainer's resume. The target-role evidence is dated and may
become stale. No organization named in the case endorses CareerLens.

## Agent Platform transition case

The second public case follows a synthetic senior backend and data platform
engineer who has shipped a Bedrock and RAG agent service, but has not proved
ownership of a durable, secure, hyperscale agent runtime.

It uses OpenAI's dated Software Engineer, API Agents posting as the primary
target and five additional official employer roles as a market baseline. Every
question, learning resource, and eight-week task explains why it was selected
for this candidate.

- [Explore the Agent Platform Runbook](https://example-org.github.io/careerlens/cases/agentic-llm-platform/)
- [Read the deterministic report](case-studies/agentic-llm-platform/output/report.html)
- [Inspect the canonical JSON](case-studies/agentic-llm-platform/output/runbook.json)
- [Review the official-role research](docs/research/2026-08-29-agentic-llm-platform-job-evidence.md)
- [Verify attribution and evidence boundaries](case-studies/agentic-llm-platform/ATTRIBUTION.md)

This candidate is original synthetic data. The case does not represent a real
person, application outcome, or employer endorsement.

## Smaller synthetic example

The included synthetic example identifies a capability that is mentioned but
not yet proved, then converts it into a bounded next action:

```text
Decision: conditional

Incident response   proved
Capacity planning   claimed

Resume guidance
Why:       The target expects production capacity decisions.
Direction: Add a candidate-confirmed example with mechanism, constraint,
           and result.
Boundary:  Do not invent scale or ownership.

Next action
Build a capacity decision brief that can survive two failure follow-ups.
```

Read the complete rendered artifact:
[source-backed example](examples/source-backed.example.md).

## Five-minute quickstart

### 1. Install the skill

Review the repository and scripts before copying them into your Codex skills
directory:

```bash
git clone https://github.com/example-org/careerlens.git
cd careerlens
CAREERLENS_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/careerlens"
if [ -e "$CAREERLENS_SKILL_DIR" ]; then
  echo "CareerLens is already installed at $CAREERLENS_SKILL_DIR" >&2
  exit 1
fi
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill/careerlens "$CAREERLENS_SKILL_DIR"
```

The guard intentionally stops if CareerLens is already installed. Inspect or
move the existing directory before installing a new copy; do not silently
merge two versions. You can also point Codex directly at
[`skill/careerlens/SKILL.md`](skill/careerlens/SKILL.md) from a workspace.

### 2. Try it with authorized inputs

In Codex, attach or reference material you are allowed to use, then ask:

```text
Use $careerlens to build a career plan from my resume, two target job
descriptions, my location constraints, and eight hours of preparation time per
week. Separate candidate facts, target evidence, inferences, and unknowns. Do
not invent missing experience.
```

Do not paste private resume content into a public issue. Remove contact details
and employer-confidential information before sharing an artifact for feedback.

### 3. Inspect the local example without a model

Validate the canonical JSON:

```bash
python3 skill/careerlens/scripts/validate_runbook.py \
  examples/source-backed.example.json --strict
```

Render the deterministic Markdown view:

```bash
python3 skill/careerlens/scripts/render_runbook.py \
  examples/source-backed.example.json
```

The scripts use only the Python standard library and support Python 3.9+.

### Optional: monitor public ATS evidence locally

CareerLens also includes an optional Python 3.11+ local monitor for bounded,
read-only public Ashby and Greenhouse job evidence. It is separate from the
Python 3.9+ runbook scripts, accepts no candidate data, submits no forms, and
does not establish that a role is open.

```bash
python3.11 skill/careerlens/scripts/public_job_monitor.py serve --prompt-key
```

It is fixed to `127.0.0.1` and exposes its form at `/acquire`; do not publish,
proxy, or add browser credentials to it. Jev can only select from already
observed public links. Each user supplies their own credential through
an already-set `TYPESAFE_API_KEY` process environment value, their current
macOS account's `typesafe-ai-jev` Keychain entry, or the one-process masked
prompt shown above:

```bash
python3.11 skill/careerlens/scripts/public_job_monitor.py serve
```

The key is never accepted by the browser, URL, report, or command-line option.
Without a credential, the monitor must show Jev as unavailable rather than
inventing a selection. See the [public job monitor reference](skill/careerlens/references/public-job-monitor.md)
for CLI usage, safety boundaries, and byte-exact vendor verification.

## What it produces

- candidate and target evidence separation;
- `proved`, `claimed`, `missing`, and `unknown` capability states;
- recruiter-readable resume guidance with explicit truth boundaries;
- shared role-family preparation and sourced company deltas;
- likely interview rounds, questions, answer outlines, and learning resources;
- a capacity-aware roadmap and bounded application experiment;
- machine-readable JSON plus deterministic Markdown.

CareerLens does not submit applications, message recruiters, scrape private
profiles, infer candidate facts, or guarantee interviews or offers. Job-market
claims require supplied or researched sources; missing evidence remains
missing.

## Contract and examples

- [JSON Schema](schema/personalized_runbook.v1.schema.json)
- [Source-backed JSON example](examples/source-backed.example.json)
- [Rendered source-backed example](examples/source-backed.example.md)
- [Thin-input example](examples/thin-input.example.json)
- [Non-technical example](examples/nontechnical-operations.example.json)
- [Evidence and research policy](skill/careerlens/references/evidence-and-research-policy.md)
- [Quality gates](skill/careerlens/references/quality-gates.md)

JSON is canonical. Markdown is a deterministic review projection.

## Feedback and contributions

The most useful feedback is a reproducible onboarding failure, an unsupported
conclusion, or a case where the evidence state is wrong. Open an issue without
including private candidate material. See [CONTRIBUTING.md](CONTRIBUTING.md)
before proposing schema or policy changes.

Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

All repository examples must remain synthetic.

## License

Apache-2.0. See [LICENSE](LICENSE).
