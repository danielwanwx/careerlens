# Public AI Case Study and Launch Assets Design

Date: 2026-08-29

## Objective

Make CareerLens launch-ready with a reproducible AI-engineering case study,
an evidence-auditable report, and a compact media package that lets a first-time
visitor understand the project before installing it.

The package must demonstrate the product without using any maintainer resume,
private candidate data, scraped profiles, or unsupported hiring claims.

## Success Criteria

A visitor should be able to:

1. understand the distinction between candidate evidence, target evidence,
   inference, and unknown information;
2. inspect a complete CareerLens result without providing personal data;
3. trace every material fit claim to the licensed sample resume or the dated
   target-role evidence;
4. reproduce validation and rendering locally;
5. understand the most important preparation actions in under five minutes.

The repository is launch-ready only when the canonical JSON, Markdown report,
HTML report, README summary, and static screenshots tell the same story.

## Selected Approach

Use a result-first presentation:

- the README and report hero lead with the conditional decision, evidence
  states, and next actions;
- the evidence trail immediately follows and explains why the result is
  trustworthy;
- the five-minute developer workflow remains the quickstart;
- the public case-study pages demonstrate the flow without collecting visitor
  data.

Alternatives rejected:

- a hosted demo would introduce privacy, deployment, cost, and retention
  concerns before demand is validated;
- a real person's public resume cannot be copied merely because it is visible;
- a developer-only command demo undersells the career outcome;
- a trust-only hero is differentiated but slower to understand.

## Case Sources

### Candidate input

Use `templates/baseline_resume.md` from
<https://github.com/aarangop/resume-mcp>.

- The profile is a fictional candidate named Jane Smith.
- It contains eight-plus years of software and machine-learning experience,
  including ML pipelines, LLM/RAG, APIs, streaming, cloud deployment,
  monitoring, and leadership.
- The repository declares the MIT License.
- Any copied or modified substantial portion must retain the original
  copyright and permission notice.

The case directory will include:

- a verbatim source snapshot or minimally normalized derivative;
- `ATTRIBUTION.md` with repository URL, source file URL, commit SHA, retrieval
  date, modification statement, copyright notice, and full MIT permission
  notice;
- a source hash so later changes cannot silently alter the demonstration.

The case must never imply that Jane Smith is a real applicant.

### Target input

Use OpenAI's official `Machine Learning Engineer, Integrity` role:
<https://openai.com/careers/machine-learning-engineer-integrity-san-francisco/>.

The snapshot will record:

- official URL and retrieval date;
- role title, team, location, responsibilities, requirements, and published
  compensation;
- a structured extraction of the role requirements;
- a source hash or frozen excerpt sufficient to reproduce the mapping.

If the live page later disappears, the case report will label the evidence as
an archived, dated demonstration input. It will not claim that the role remains
open.

## Expected Diagnosis

The case is intentionally non-trivial. The candidate has substantial adjacent
experience, so CareerLens must not reduce the result to keyword counting.

Expected evidence states include:

- `proved`: ML systems, transformers exposure, RAG, APIs, cloud deployment,
  monitoring, data pipelines, and cross-functional leadership;
- `claimed`: fine-tuning and related model work where the source lacks
  mechanism, evaluation, or ownership detail;
- `missing`: content-integrity or abuse-prevention evidence, distillation,
  supervised fine-tuning, and policy optimization;
- `unknown`: reliability judgment in adversarial misuse scenarios and the
  depth of direct post-training ownership.

The expected decision is `conditional`. The report must not contain a numeric
fit score or estimate an interview, offer, or hiring probability.

Priority preparation areas:

1. integrity classifier and abuse-detection system design;
2. LLM post-training concepts and trade-offs;
3. adversarial evaluation and production monitoring;
4. coding and ML-system fundamentals relevant to the official requirements;
5. behavioral evidence for end-to-end ownership in ambiguous environments.

The actual generated artifact may refine this list, but any deviation must be
explained by evidence rather than edited to force the expected result.

## Repository Structure

```text
case-studies/
  ai-engineer-integrity/
    README.md
    ATTRIBUTION.md
    input/
      candidate-resume.md
      target-role.md
      target-role.json
    output/
      runbook.json
      report.md
      report.html
assets/
  launch/
    social-preview.png
    case-report.png
docs/
  launch/
    show-hn.md
    channel-copy.md
    launch-checklist.md
    measurement-template.md
scripts/
  build_case_study.py
  verify_launch_assets.py
```

Generated outputs are checked in so visitors can inspect them without a model.
The canonical CareerLens JSON remains the source of truth. Markdown and HTML are
deterministic projections.

## Report Design

The standalone HTML report uses the CareerLens design language and remains
readable as a local file without a server or external assets.

Sections:

1. **Case provenance** — license, attribution, retrieval dates, source hashes,
   and fictional-candidate disclosure.
2. **Executive decision** — conditional fit, bounded rationale, and three most
   important actions.
3. **Evidence matrix** — capability, status, candidate evidence, target
   requirement, inference, and confidence boundary.
4. **Recruiter and hiring-manager views** — likely first-pass signals and
   project-level technical follow-ups, clearly labeled as preparation guidance
   rather than a guaranteed company interview script.
5. **Preparation plan** — coding, ML system design, post-training, adversarial
   evaluation, and behavioral ownership, each with completion conditions and
   non-duplicative authoritative resources.
6. **Limitations** — fictional candidate, dated role input, no employment
   prediction, and no endorsement by the source projects or OpenAI.

The report must work at desktop and mobile widths, support dark and light
presentation, and print cleanly. It may use inline CSS and JavaScript but must
not fetch trackers, fonts, or third-party runtime assets.

## Media Design

Produce:

- `social-preview.png`: a GitHub/social sharing card;
- `case-report.png`: a report hero screenshot.

Static launch imagery must not contain private file paths, fabricated metrics,
or unlicensed imagery.

## README and Launch Documents

The README will add:

- the case report screenshot below the value proposition;
- a `View the complete AI Engineer case` action;
- a compact evidence trail;
- attribution and limitation language near the case link;
- the existing five-minute quickstart.

Launch documents will contain:

- final Show HN title and body;
- LinkedIn/X/DEV variants that do not duplicate the same promotional copy;
- a preflight checklist;
- a measurement template for HN points, visitors, referrers, unique cloners,
  validated runs, actionable issues, and repeat use.

No post, release, topic, social-preview setting, or external account will be
mutated by building these files. External publishing remains a separate action.

## Build and Validation Flow

```text
verify license and sources
        ↓
freeze inputs and hashes
        ↓
generate/assemble canonical runbook JSON
        ↓
strict schema and policy validation
        ↓
render Markdown and HTML
        ↓
capture report image and build media
        ↓
verify cross-format consistency and asset properties
```

`build_case_study.py` will be deterministic for checked-in inputs and canonical
JSON. It will not call a model or the network during normal rebuilds.

`verify_launch_assets.py` will check:

- required source and attribution fields;
- source hashes;
- canonical JSON strict validation;
- required decision and evidence-state text across Markdown and HTML;
- absence of private local paths, secret-like values, or unapproved personal
  identifiers;
- expected static launch images, dimensions, and non-zero size;
- local links referenced from README and launch documents.

## Failure Handling

- Missing or ambiguous license: stop before copying the candidate source.
- Source hash mismatch: require an explicit refresh and attribution review.
- Live role removed: retain the dated snapshot and label it archived.
- Canonical validation failure: do not render or publish derived assets.
- Projection disagreement: fail the build rather than hand-editing Markdown or
  HTML.
- Uncited number or claim: remove it or attach a source reference.
- Private path or candidate data: fail verification and regenerate the asset.
- Image tooling unavailable: ship the complete static report; do not block the
  evidence package on an optional preview image.

## Testing and Review

Required checks:

1. existing unit tests remain green on supported Python versions;
2. new tests cover attribution fields, source hashing, deterministic rendering,
   cross-format decision consistency, privacy scans, and failure modes;
3. source-backed case JSON passes strict validation;
4. two consecutive builds produce no diff;
5. HTML is inspected at desktop, mobile, light, dark, and print layouts;
6. static launch images are visually reviewed at their native dimensions;
7. README commands are tested from a fresh clone;
8. an independent quality review covers correctness, readability,
   architecture, security/privacy, media licensing, and launch claims.

## Evidence Limitations

The Research Engine run used to identify sources is local-only and configured
through `CAREERLENS_RESEARCH_RUN_DIR`.

It collected 57 rows and retained 13 eligible rows, but produced no supported
claim buckets and reported GitHub search and authenticated-browser warnings.
It therefore did not establish a reusable resume by itself. The selected
candidate source was separately verified against the public repository,
specific sample file, GitHub repository metadata, and MIT license text. The
target role was separately verified on OpenAI's official career page on
2026-08-29.
