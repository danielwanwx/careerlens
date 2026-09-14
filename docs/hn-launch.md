# CareerLens Show HN Launch Package

This document prepares the launch. It is not authorization to submit the post.

## Title

Preferred:

> Show HN: CareerLens – evidence-bounded career diagnosis for Codex

Alternative, if the preferred title feels too abstract:

> Show HN: Turn a resume and job postings into an auditable career plan

## Submission text

I built CareerLens because most AI career advice has a provenance problem. It
mixes what a candidate actually did, what a target role requires, and what the
model merely assumes.

CareerLens is an open-source Codex skill that keeps those categories separate.
It turns authorized candidate material and target-role sources into structured
resume guidance, an interview map, learning priorities, and a capacity-aware
preparation plan.

Missing evidence stays missing. The skill is explicitly instructed not to
invent experience or silently convert assumptions into candidate facts.

The canonical output is JSON validated against a public schema, with a
deterministic Markdown review view. The repository includes synthetic examples,
quality gates, tests, and standard-library validation and rendering scripts.

Repository: https://github.com/example-org/careerlens

I would especially value feedback on two questions:

1. Is the distinction between proved, claimed, missing, and unknown evidence
   understandable without reading the implementation?
2. What would you need to trust a career diagnosis produced from your own
   resume and target roles?

## Preflight

- [ ] GitHub Actions is green on Python 3.9 and 3.12.
- [ ] The strict validator accepts every checked-in JSON example.
- [ ] Regenerating `examples/source-backed.example.md` produces no diff.
- [ ] A person outside the project completes the README quickstart.
- [ ] The repository has accurate GitHub topics and a social preview image.
- [ ] The repository has a versioned release or a clearly identified commit.
- [ ] The maintainer can remain available to answer HN comments for several
      hours after submission.
- [ ] The post is submitted once; nobody is asked to upvote or manufacture
      comments.

## Response policy

- Answer technical criticism with the relevant schema, policy, or test.
- Acknowledge real onboarding failures and open a tracked issue.
- Do not defend generic model-generated prose; improve or remove it.
- Do not disclose candidate material or argue about an individual's career
  outcome in public.
- Separate measured facts from design intentions and future plans.

## Measurement

Record a baseline immediately before submission, then check at 2, 8, 24, and
72 hours:

- HN points and substantive comment threads;
- GitHub unique visitors and referrers;
- unique cloners and release downloads;
- validated runs reported by users;
- issues containing enough information to reproduce a problem;
- repeat use or a second target-role run.

Stars and impressions are secondary. The launch succeeds if strangers can run
CareerLens, identify unsupported conclusions, and provide actionable feedback.
