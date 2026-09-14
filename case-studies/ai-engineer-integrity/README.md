# Public AI Engineer case study

This case demonstrates CareerLens against two inspectable inputs: a fictional
AI/ML candidate derived from an MIT-licensed public sample and a dated official
OpenAI role page. It is a product demonstration, not an employment claim or an
endorsement.

Start with the [interactive HTML report](output/report.html), then inspect the
[canonical JSON](output/runbook.json) and [attribution record](ATTRIBUTION.md).

Rebuild and verify from the repository root:

```bash
python3 scripts/build_case_study.py
python3 scripts/verify_launch_assets.py --allow-missing-media
python3 -m unittest discover -s tests -v
```

The output deliberately suppresses a numeric fit score. The decision remains
`conditional` because the supplied evidence does not prove several role-specific
requirements. Unknowns remain unknown instead of being filled by inference.
