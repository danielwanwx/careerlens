# Local Application Tracker Privacy Design

## Objective

Keep a durable Application Tracker as a loopback-only local tool. Pilot continues to own job-search operations and writes the complete local tracker. The public CareerLens Pages site publishes only synthetic case studies and must never include tracker data or tracker routes.

The local route is:

`http://127.0.0.1:<port>/application-tracker/`

## Source of Truth

The canonical private tracker is configured outside the repository:

`$CAREERLENS_PRIVATE_DATA_DIR/applications.sqlite3`

The loopback UI is a projection, not an editable database. Pilot updates the private tracker after discoveries, approvals, submissions, interviews, rejections, offers, withdrawals, and expired-role checks. A deterministic export step may produce a local-only view, never a tracked or deployable site artifact.

## Privacy Boundary

### Allowed on the loopback-only page

- Company
- Role title
- Official public job URL
- Public location and work mode
- Pipeline tier
- Fit score
- Resume track
- Normalized public status
- Verification date
- Application date
- Generic next action
- Non-sensitive public notes such as technology fit or official-page expiration

### Never exposed outside the local loopback server

- Candidate email, phone, street address, immigration status, or application answers
- Recruiter or employee contact names, emails, phone numbers, or private messages
- Compensation answers, demographic disclosures, legal declarations, or internal concerns
- Approval timestamps that expose private interaction details
- Confirmation identifiers, browser/session details, or private application notes
- Any field not explicitly included in the public export schema

The exporter must use an allowlist. It must not copy arbitrary CSV columns into the public artifact.

## Public Data Model

Each public role record contains:

- `company`
- `role`
- `job_url`
- `location`
- `work_mode`
- `tier`
- `fit_score`
- `resume_track`
- `status`
- `verified_date`
- `applied_date`
- `next_action`
- `public_note`

Public status values are:

- `Discovered`
- `Verified`
- `Review`
- `Approved`
- `Submitted`
- `Interview`
- `Offer`
- `Closed`

Private terminal states such as rejected, expired, withdrawn, blocked, and skipped map to `Closed`. The public note may distinguish `Expired` when that fact is already visible on the official job page; it must not reveal private rejection content.

## Views

### All

A compact table modeled after the referenced Notion tracker. It supports text search, status filtering, track filtering, tier filtering, and sortable fit/application-date columns. Company and role link to the official job page.

### Board

A responsive pipeline board with columns for Discovered, Review, Submitted, Interview, Offer, and Closed. Verified and Approved are grouped into the nearest operational stage when necessary to keep the board readable.

### Stats

Summary cards and lightweight charts show:

- Total active roles
- Applications this week
- Submitted applications
- Interviews
- Offers
- Response rate, defined explicitly as roles reaching Interview divided by Submitted roles
- Status distribution
- Resume-track distribution

Stats must show `0` rather than omit empty categories. Dates use the viewer's local display only when the underlying value is a complete ISO date.

## Page Structure and Visual Direction

The tracker becomes a first-class CareerLens route and uses the site's existing design language rather than copying Notion branding. The page includes:

- Header with `Application Tracker` title and last generated timestamp
- View switcher for All, Board, and Stats
- Filter/search controls shared by All and Board
- Clear status badges and accessible contrast
- Mobile fallback that converts the wide table into stacked role cards
- Empty-state and data-load error messages

The page is read-only. It has no public create, edit, delete, or submit controls.

## Build and Local Refresh Flow

1. Pilot updates the canonical private SQLite database and optional compatibility CSV.
2. A local export script reads the database, validates required columns and canonical states, applies the privacy allowlist, and serves a generated JSON payload only from the loopback server.
3. `scripts/build_pages_site.py` builds only the public synthetic case-study site; it does not read tracker inputs or produce a tracker route.
4. Tests scan local payloads and static Pages output for forbidden private field names and known sensitive values.
5. No tracker artifact is committed, pushed, or included in the GitHub Pages workflow.

The GitHub Action must not read private tracker storage. Updating local tracker data never changes the Pages release artifact.

## Pilot Integration

Pilot's hiring runbook gains a Tracker Publishing section:

- Always update the private CSV immediately after a material pipeline change.
- Generate and validate the public projection when the user asks to publish/sync or at the end of an approved application batch.
- Show a summary of public additions, changes, and removals before committing.
- Never push automatically merely because a private tracker row changed.
- Push only when the user has authorized publication of the current sanitized delta.

This preserves the existing rule that remote mutations require explicit scope while keeping routine local tracking automatic.

## Failure Handling

- Missing required CSV columns: fail the export with a clear message; do not produce partial JSON.
- Unknown status: fail closed and require a mapping update.
- Invalid URL or date: flag the row and stop publication.
- Sensitive-field detection: fail the build and identify the prohibited field category without printing sensitive values.
- Empty tracker: render a valid empty state rather than failing the site.
- GitHub Pages deployment failure: keep the last successful public version and report the failed workflow.

## Testing

- Unit tests for CSV parsing, state normalization, status grouping, date handling, and response-rate calculation.
- Privacy tests proving excluded columns and known sensitive values never appear in generated JSON or HTML.
- Build test confirming `/application-tracker/index.html` and its data artifact exist.
- Browser checks for All, Board, and Stats views at desktop and mobile widths.
- Accessibility checks for keyboard navigation, labels, table semantics, focus state, and badge contrast.
- Regression check confirming existing CareerLens routes still build.

## Initial Data

The local projection may include the current tracker queue. Work-authorization details, contact details, form answers, employer-specific notes, and internal submission notes remain private and are never written to the repository or public Pages output.

## Acceptance Criteria

- The route is reachable only through the loopback local server.
- All, Board, and Stats display the same filtered underlying data consistently.
- No public artifact contains candidate contact, work-authorization, recruiter-contact, or private-answer data because the tracker has no public artifact.
- Synthetic fixture records are represented accurately in local tests.
- A deterministic command regenerates the local projection from the canonical private tracker.
- The Pages workflow deploys only synthetic public case studies.
- Pilot's runbook documents that local tracking is automatic and never publishes tracker content.

## Deferred Scope

- Editing applications from the public page
- Notion synchronization
- Authentication or private GitHub Pages access
- Automatic recruiter-email ingestion
- Automatic scheduled publishing
- Multi-user accounts
