# CareerLens HN Launch Readiness Design

Date: 2026-08-29

## Goal

Prepare CareerLens for a Show HN launch by making its value, trust boundary,
and first-run path understandable to a stranger in under five minutes.

The launch should optimize for validated runs and substantive feedback, not
stars alone.

## Scope

This change will:

- rewrite the README opening around the user problem and concrete outcome;
- add one copy-paste installation path;
- add a five-minute sample workflow using synthetic data;
- add a checked-in Markdown projection of the source-backed example;
- add an HN launch draft and a launch checklist;
- keep the existing schema, validators, renderer, examples, and privacy rules
  unchanged unless a documentation test exposes an actual defect.

This change will not:

- host a web application;
- collect resumes or analytics;
- publish to Hacker News or any other external platform;
- claim job-search outcomes that have not been measured;
- replace synthetic repository examples with private candidate material.

## Considered Approaches

### A. Documentation-first launch package (selected)

Improve the existing repository with a visible output, exact installation,
quickstart, and launch copy. This is the smallest change that addresses the
current visitor-to-run conversion gap and keeps the project honest about being
a Codex skill.

### B. Hosted interactive demo

This would reduce trial friction further, but it introduces deployment,
privacy, model-cost, authentication, and data-retention concerns. It is not
required to validate initial demand.

### C. Launch the repository unchanged

This is fastest, but the current README describes the contract better than it
demonstrates the result. HN traffic would likely produce curiosity without a
reliable first run.

## Visitor Journey

1. The visitor reads one sentence explaining that CareerLens separates
   candidate facts, target-role evidence, inferences, and unknowns.
2. The visitor sees a compact excerpt of the generated artifact.
3. The visitor copies the installation command.
4. The visitor runs CareerLens with either the supplied prompt or their own
   authorized inputs.
5. The visitor validates or renders the included synthetic artifact without
   needing third-party Python packages.
6. The visitor can report an unsupported conclusion or onboarding failure.

## Repository Changes

### README

The first screen will contain:

- a concrete one-sentence value proposition;
- a short “why this exists” explanation;
- an output excerpt showing evidence state, gap, and next action;
- a prominent five-minute quickstart.

Detailed contract information remains below the quickstart. Language must not
imply that the repository performs live job-market research without the
necessary source inputs and tools.

### Installation

Document an explicit local installation command that copies
`skill/careerlens` into `${CODEX_HOME:-$HOME/.codex}/skills/careerlens`. The
documentation must also provide a manual alternative and explain that users
should inspect scripts before executing copied commands.

No remote pipe-to-shell installer will be introduced.

### Demonstration Artifact

Render `examples/source-backed.example.json` with the checked-in renderer and
store the deterministic Markdown output under `examples/`. This gives visitors
a browsable result without requiring them to invoke a model.

The example remains synthetic and must pass strict validation.

### HN Launch Package

Add a document containing:

- final title;
- concise first-person launch text;
- disclosure of what the project does and does not do;
- two specific feedback questions;
- preflight checklist;
- post-launch response and measurement checklist.

The document is preparation only. Submission remains a separate, explicit
external action.

## Error and Trust Handling

- Missing Codex skill directory: create only the final `careerlens` directory
  during documented installation.
- Existing installation: tell the user to inspect the diff or move the old
  directory before copying; do not prescribe destructive overwrite.
- Invalid example: the strict validator blocks launch readiness.
- Unsupported claims: repository examples must remain synthetic, and launch
  copy must not state that CareerLens improves interview or offer rates.
- Private data: no resume content is committed, uploaded, or requested in a
  public issue.

## Verification

Launch readiness requires all of the following:

1. `python -m unittest discover -s tests -v` passes on the supported runtime.
2. The source-backed example passes strict validation.
3. Regenerating the Markdown demonstration produces no diff.
4. Every README command works from a fresh clone or clearly states its
   prerequisite.
5. Markdown links resolve locally.
6. `git diff --check` passes.

## Success Criteria

The repository is ready to submit to Show HN when a person unfamiliar with the
project can:

- state its distinction from an AI resume writer after reading the first
  screen;
- install the skill without guessing a destination path;
- inspect a realistic output before providing personal data;
- complete the documented sample workflow in five minutes;
- identify where to report unsupported evidence or a failed first run.

After launch, the primary signals are validated runs, unique cloners, useful
issues, and repeat use. HN points and GitHub stars are secondary indicators.
