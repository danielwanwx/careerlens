# Application Tracker Implementation Plan

1. Add a standard-library exporter that validates the private Pilot CSV and emits an allowlisted, deterministic public JSON projection.
2. Commit the initial sanitized projection generated from the current Pilot tracker.
3. Extend the CareerLens Pages builder with an `/application-tracker/` route, dashboard HTML, and the generated data artifact.
4. Implement All, Board, and Stats views with shared filters, responsive role cards, accessible controls, and explicit empty/error states.
5. Add exporter, privacy, deterministic-build, route, and dashboard-content tests.
6. Add Tracker Publishing instructions to Pilot's runbook without changing its application approval boundary.
7. Run the full test suite, build Pages, serve `dist/pages` locally, and inspect the dashboard in the browser at desktop and mobile widths.
8. Stop before GitHub push so the user can review the complete local dashboard.
