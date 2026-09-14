# Show HN draft

## Title

Show HN: CareerLens – Evidence-first career diagnosis and preparation plans

## Post

I built CareerLens because most AI career advice quietly mixes four different
things: what a candidate proved, what they only claimed, what the role requires
but the resume does not show, and what the available evidence cannot answer.

CareerLens is an open-source Codex skill that keeps those states separate. Its
canonical artifact is schema-validated JSON; the Markdown and HTML reports are
deterministic projections. It also turns gaps into sourced interview guidance
and a capacity-checked preparation plan. It does not invent experience or hide
uncertainty behind a fit score.

The repository now includes a reproducible public AI-engineering case using a
fictional candidate derived from an MIT-licensed resume sample and a dated
official role page. The case reaches a conditional decision, shows the exact
evidence matrix, and produces a 27-hour plan inside a 48-hour boundary.

Repo: https://github.com/example-org/careerlens

Public case: https://github.com/example-org/careerlens/tree/main/case-studies/ai-engineer-integrity

I would especially value feedback on unsupported conclusions, incorrect
evidence states, or places where the validation contract is too weak. Please do
not post private resume data in issues.

## First comment

Technical notes: Python 3.9+, standard library only for validation/rendering,
JSON Schema included, deterministic output tests, and explicit source hashes
for the public case. There is no application automation or private-profile
scraping.
