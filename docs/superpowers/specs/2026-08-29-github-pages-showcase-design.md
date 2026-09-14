# GitHub Pages Showcase Design

## Purpose

Publish a small public CareerLens showcase at
`https://example-org.github.io/careerlens/`. The site gives visitors one clear
landing page and direct access to both interactive Runbooks.

## Public Routes

- `/careerlens/` provides the landing page.
- `/careerlens/cases/ai-engineer-integrity/` provides the AI Engineer Integrity
  Runbook.
- `/careerlens/cases/agentic-llm-platform/` provides the Agentic and LLM
  Platform Runbook.

The route structure must work under the repository subpath. No page may assume
deployment at the domain root.

## Landing Page

The landing page contains only the information needed to choose a next action:

- a plain-language explanation of CareerLens;
- one card for each public case;
- a link to the GitHub repository; and
- a link to the five-minute quickstart in the repository README.

It must not duplicate the full README or introduce a second set of product
claims that can drift from the repository.

## Source of Truth

The existing generated Runbook HTML files remain canonical public case views.
The Pages build copies those files into route-specific `index.html` files. It
does not maintain separate Runbook templates or regenerate content with a
different code path.

The Pages build copies only allowlisted safe static assets.

## Build Pipeline

Add a standard-library build script that creates a clean static output
directory. The script must:

1. create the landing page;
2. copy allowlisted safe static assets;
3. copy each existing Runbook to its public route;
4. fail when a required source artifact is missing; and
5. write deterministic output.

The build output is generated and is not committed unless GitHub Pages requires
it. Local tests use a temporary directory.

## GitHub Actions

Add a Pages workflow using GitHub's official artifact and deployment actions.
The workflow must:

1. check out the repository;
2. run the complete Python test suite;
3. run strict launch verification;
4. build the static site;
5. upload the Pages artifact; and
6. deploy only from the default branch.

The workflow requires `pages: write` and `id-token: write`. Pull requests and
non-default branches may verify the build but must not deploy.

## README Integration

Replace the two interactive Runbook links with public Pages URLs. Keep local
HTML, canonical JSON, reports, attribution, and research links pointed at the
repository so the evidence remains inspectable.

## Testing

Automated tests must verify:

- the landing page is generated;
- both route-specific Runbooks are present;
- only allowlisted safe static assets are present;
- required navigation URLs use the `/careerlens/` base path;
- no private filesystem path or secret-like value appears in generated text;
- repeated builds are byte-for-byte deterministic; and
- a missing required source artifact fails the build.

Before release, serve only the generated temporary site directory and inspect
the landing page plus both Runbook routes in a browser. Confirm there are no
console errors and that the layout remains usable at desktop and mobile widths.

## Security and Scope

- Use no third-party hosting service and add no runtime dependency.
- Publish only the landing page, allowlisted safe static assets, and the two
  generated public Runbooks.
- Do not publish private resume material, research working files, video editing
  caches, or repository internals.
- Do not enable analytics, cookies, forms, or user-data collection in this
  release.

## Acceptance Criteria

- The static build succeeds using the Python standard library.
- All repository tests and strict launch checks pass before deployment.
- The local site works from the `/careerlens/` base path.
- Both public Runbooks open from the landing page.
- README public links match the deployed routes.
- The workflow uses only official GitHub Pages actions.
- The committed workflow cannot deploy from a pull request or non-default
  branch.

## Out of Scope

- a custom domain;
- analytics or conversion tracking;
- a hosted diagnosis form;
- server-side APIs;
- authentication; and
- redesigning the approved Runbook.
