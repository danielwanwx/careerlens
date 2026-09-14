# Unified Career Workspace Design

## Goal

Turn the public CareerLens site into a coherent synthetic-case showcase. Local
career tracking remains a separate loopback-only tool and is never part of the
public site.

## Information architecture

The public application shell has two first-level destinations:

- **Overview** — a public introduction to the synthetic case studies.
- **Runbook** — the synthetic Agentic LLM Platform Runbook, with its existing
  module-level navigation.

The AI Engineer Integrity case remains available as a secondary example from
the Overview footer or supporting resources. It is not a first-level workspace
destination.

## Routes and compatibility

- `/careerlens/` serves the combined workspace Overview.
- `/careerlens/cases/agentic-llm-platform/` serves the Runbook and retains its
  current deep link.
- `/careerlens/cases/ai-engineer-integrity/` remains available unchanged apart
  from a clear route back to the workspace.

Existing shared links continue to resolve. Each primary route identifies the
active first-level section.

## Shared application shell

Overview and Runbook use the same fixed visual identity, header, spacing,
colors, responsive behavior, and first-level navigation. The header contains
the CareerLens identity and links to public synthetic cases.

Desktop uses a compact top bar. Mobile uses a horizontally scrollable or
wrapped control that keeps public destinations reachable without a hidden menu
dependency. Active state is visible and keyboard accessible.

The integration must not use an iframe. Public Runbooks remain independent
static documents generated at build time and preserve direct URLs, refresh,
browser history, and accessibility.

## Overview content

The first viewport presents a public case-study surface rather than a personal
dashboard. It shows a primary action to explore a synthetic Runbook and links
to the other public case study.

Below the summary, public case-study cards explain the current focus:

- **Runbook** links to preparation modules and describes evidence, interview,
  learning, and story work.

The existing product demo and secondary synthetic case may remain below the
public case-study surface.

Overview reads only checked-in synthetic case-study artifacts. It does not read
private SQLite, CSV, tracker JSON, or local tracker fields.

## Runbook integration

The Agentic LLM Platform Runbook keeps its nine existing internal modules:
Overview, Module Logic, Evidence Map, Interview Map, Question Bank, Learning
Paths, Preparation Plan, Resume & Stories, and Method & Sources.

Its current module navigation becomes the Runbook section's second-level
navigation. The shared first-level shell is visually distinct so `Runbook`
means the workspace section while `Overview` inside it means the Runbook's own
overview module.

The Runbook content and evidence model are not rewritten in this change.

## Build strategy

`scripts/build_pages_site.py` owns the shared-shell fragments and Overview.
It injects or composes public navigation into the copied synthetic Runbooks. The integration should
reuse existing styles and generated artifacts rather than introduce a frontend
framework or dependency.

The source Runbook generator is updated when necessary so rebuilding its source
does not erase the shared navigation contract. Build output remains static and
compatible with GitHub Pages and the local port 8766 server.

## Checks and failure handling

- Unit tests assert public pages contain only synthetic-case links and the
  correct active section.
- Existing route, privacy, deterministic build, and Runbook tests stay
  green.
- Mobile CSS keeps first- and second-level navigation usable at 320px width.
- Keyboard focus and active states remain visible.
- Private tracker data is never a build input.
- The SQLite sync loop remains local-only.

## Acceptance criteria

- One URL, `/careerlens/`, exposes both preparation and pipeline status in the
  first viewport.
- Users can reach Runbook and Tracker from every primary page with one click.
- Runbook and Tracker each retain clear second-level navigation.
- Direct Runbook and Tracker links continue to work.
- No iframe, new dependency, private data exposure, or duplicated tracker
  source is introduced.
- Local port 8766 and GitHub Pages render the same successful build.
- Automated tests and a browser smoke review pass before publication.

## Non-goals

This change does not add authentication, editing, private data to GitHub Pages,
new Runbook content, application submission controls, or a replacement UI
framework.
