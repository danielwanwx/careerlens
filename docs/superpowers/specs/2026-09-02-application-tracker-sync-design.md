# Application Tracker Sync Design

## Goal

Prevent submitted applications and later pipeline changes from being omitted
from the local dashboard. One transactional local database is
the source of truth; every other representation is generated and checked.

## Scope

This change covers application records, status history, private CSV export,
the allowlisted local JSON projection, the loopback dashboard, and local
refresh. It does not discover job
outcomes, scrape email, submit applications, or infer status changes.

## Source of truth

The canonical store is a private SQLite database outside the public repository:

`$CAREERLENS_PRIVATE_DATA_DIR/applications.sqlite3`

The existing private CSV is migrated into the database and remains a generated
compatibility artifact for Pilot and manual inspection. It is never an input to
the static Pages build.

### Tables

`applications` stores the latest state. It retains the existing tracker fields
and uses an integer primary key. `official_url` is unique so the same posting
cannot be inserted twice. Company and role are required.

`application_events` is append-only. Every create or update records the
application ID, event time, event type, old status, new status, source, and a
short reason. Event rows make omissions and unexpected transitions auditable.

`sync_runs` records each synchronization attempt, database revision, result,
checks completed, published commit when applicable, and error summary.

The database uses foreign keys, WAL mode, busy timeout, and explicit
transactions. Schema migrations use a version table and are idempotent.

## Write contract

A single CLI is the supported mutation boundary:

```text
python scripts/application_store.py upsert ...
python scripts/application_store.py transition ...
python scripts/application_store.py import-csv ...
python scripts/application_store.py export-private-csv ...
```

Pilot must call this boundary immediately after every material state change.
It must not report an application as recorded until the transaction commits.
The transition command validates canonical statuses and required dates. In
particular, `submitted` requires `submitted_date`; status transitions cannot
silently clear an existing submission date.

## Synchronization loop

The loop contract is:

- Goal: make all generated tracker views match the committed SQLite revision.
- Input: the private SQLite database and repository source files only.
- Execute: lock, export private CSV, generate an allowlisted local JSON payload,
  run checks, and refresh the local loopback view.
- Check: database integrity, record-count/state invariants, deterministic
  export, privacy allowlist, repository tests, and HTTP smoke checks.
- Feedback: any failure stops the run, records the error, preserves the last
  successful local and public versions, and exits nonzero. The next scheduled
  run retries from the unchanged database.
- Record: write a `sync_runs` row and structured local log for every attempt.
- Stop: success after local refresh; stop immediately on privacy, validation,
  or test failure.
- Human gates: application submission and uncertain application answers remain
  governed by Pilot. No private field may cross the loopback boundary.

The loop uses a filesystem lock so manual and scheduled runs cannot overlap.
No database change means no local refresh. A tracker change never creates a
repository commit or push.

## Scheduling

A macOS LaunchAgent may run the synchronization command every 15 minutes and
once at login. It does not need Codex to be open. If the Mac is asleep or
powered off, macOS runs the next eligible invocation after login.

The existing local HTTP LaunchAgent continues serving port 8766. Synchronizing
copies the completed refresh into a staging directory and then swaps the completed
directory into place, preventing partially generated pages from being served.

## Privacy and security

The SQLite database, private CSV, event history, local payload, and logs stay
outside the public repository. The local exporter maintains an explicit field
allowlist and conservative text filter. Tracker synchronization does not invoke
Git. Credentials are not stored in the database, scripts, LaunchAgent, or logs.

## Failure handling

- Invalid state or missing required date: reject the write transaction.
- Corrupt database or failed integrity check: stop before any export.
- Privacy check or test failure: keep the prior dashboard and do not replace it.
- Local-refresh failure: retain the prior local view and record the failure.

## Migration

1. Back up the current CSV without altering it.
2. Create the database and import every CSV row in one transaction.
3. Compare row counts and normalized field values.
4. Generate a replacement CSV and local-only JSON payload from SQLite.
5. Require byte-equivalent local meaning and passing tests before switching
   Pilot to the database write contract.
6. Install and smoke-test the LaunchAgent.

Migration is reversible: the generated private CSV remains complete and can be
used to reconstruct the database.

## Acceptance criteria

- All current roles exist in SQLite and in the correct local generated view.
- A test transition to `submitted` produces an event, private CSV row, and
  local dashboard update.
- Re-running with no changes produces no repository mutation.
- Injected private values never appear in the local payload outside its
  allowlisted fields or in built Pages.
- An invalid record or failing test prevents local refresh and preserves the
  last successful dashboard.
- Unit, migration, determinism, privacy, and end-to-end dry-run tests pass.

## Non-goals

No Google Sheet or Airtable dependency, email outcome ingestion, automatic job
application, dashboard editing UI, multi-user database access, or cloud-hosted
private database is introduced in this phase.
