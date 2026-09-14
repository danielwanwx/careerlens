# Contributing

Use synthetic examples and keep the core profession-neutral. A new rule should
protect a real invariant or improve a repeated decision; do not encode one
candidate, company, country, or interview anecdote as a universal workflow.

Before opening a change:

```bash
python -m unittest discover -s tests -v
python skill/careerlens/scripts/validate_runbook.py examples/source-backed.example.json --strict
python skill/careerlens/scripts/validate_runbook.py examples/thin-input.example.json --strict
```

Do not commit resumes, full job descriptions, private profile text, secrets,
provider traces, local absolute paths, or copyrighted course material. Cite or
link to authoritative material rather than copying it.
