# Public job monitor

Use this optional local monitor only to collect public job evidence before a
CareerLens diagnosis. It is a read-only, bounded acquisition aid, not a
candidate-data workflow and not an application agent.

It accepts up to four official HTTPS Ashby or Greenhouse ATS seed URLs and
fetches at most eight public documents. It never submits a form, follows an
apply/login URL, reads a resume, opens Coach data, persists runs to disk, or
establishes that a role is open. Returned roles and links are target evidence
only; keep candidate facts and the canonical `personalized_runbook.v1` JSON
separate.

When collecting known Ashby or Greenhouse evidence for a diagnosis, prefer this
monitored fetch before `diagnose` when Python 3.11+ is available. Retain the
ordinary CareerLens research path for other authorized sources. Inspect each
result's `incomplete` and `navigation` fields before using it: they describe
the bounded retrieval path, not global coverage, an open role, or a reason to
apply.

## Start it locally

The existing runbook scripts remain Python 3.9+. The monitor and its vendored
runtime require Python 3.11+ and only the standard library.

From an installed skill directory:

```bash
python3.11 scripts/public_job_monitor.py serve --prompt-key
```

It binds only to `http://127.0.0.1:8768/acquire`. The browser form and API are
same-origin and loopback-only; do not publish this page, proxy it, expose it on
a network interface, or add CORS. The page keeps run state in the local server
process only. Refreshing the page reconnects to its bounded in-memory history.
If that port is already in use, start a separate local monitor explicitly, for
example `python3.11 scripts/public_job_monitor.py serve --port 8769`.

To start a run from another terminal and stream the same safe events, use:

```bash
python3.11 scripts/public_job_monitor.py fetch \
  --task "Find public platform-engineering roles relevant to reliable AI systems" \
  --seed-url https://job-boards.greenhouse.io/example \
  --seed-url https://jobs.ashbyhq.com/example
```

For a monitor on the alternate port above, add
`--monitor-url http://127.0.0.1:8769`. For a known exact role, use its official
ATS role URL as a seed and add `--detail` only when the returned evidence
excerpt is insufficient; `--detail` remains bounded public source text.

The command writes incremental events to stderr and one terminal JSON result to
stdout. It talks only to an existing `http://127.0.0.1:<port>` monitor; it will
not use an arbitrary URL. Use `--no-jev` when an observed-link choice is not
needed. A partial result is evidence of limited retrieval, not a claim of
coverage or a recommendation to apply.

## Optional Jev selection

Jev is only allowed to choose from links already observed in the public ATS
scope. It receives one Choice question per call, never a resume, full private
profile, browser credential, or application form. Its output is an observed
link-selection aid, not proof that a job is open or that a candidate qualifies.

Each user must configure their own Jev credential. The quickest local option is
the masked prompt already shown above. It retains the key only in that server
process. A server can instead inherit an already-set process environment value,
or read the current macOS account's `typesafe-ai-jev` Keychain service entry:

```bash
python3.11 scripts/public_job_monitor.py serve
```

`serve --prompt-key` performs a masked terminal prompt and places the value
only in that server process environment. It is not written to a `.env` file,
command history, URL, browser request, log, report, or storage. Do not pass an
API key as a command-line option, paste it into the web form, or add it to a
repository.

If no usable credential is available, keep Jev enabled only if the monitor
reports it as unavailable; do not fabricate a Choice result. The public fetch
can still run with `--no-jev`.

## Verify the vendored runtime

The package contains byte-exact copies of the public CareerOS modules and
static assets, recorded in
`scripts/public_acquisition/VENDORED_FROM_CAREEROS.json`. A maintainer updates
or verifies those copies only against an explicit CareerOS checkout:

```bash
python3 scripts/sync_public_acquisition.py \
  --source-root /path/to/career-os
python3 scripts/sync_public_acquisition.py \
  --source-root /path/to/career-os --check
```

There is intentionally no default source path. The installed skill must run
without CareerOS, Research Engine, a private database, a home-directory
assumption, or an existing user credential.
