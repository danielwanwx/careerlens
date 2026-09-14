from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skill" / "careerlens" / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


validator = _load("validate_runbook")
renderer = _load("render_runbook")


class RunbookTests(unittest.TestCase):
    def load(self, name: str):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_examples_pass_strict_validation(self):
        for path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertTrue(validator.validate(json.loads(path.read_text()), strict=True)["valid"])

    def test_input_gate_never_displays_numeric_score(self):
        data = self.load("thin-input.example.json")
        data["decision_state"].update({"show_numeric_score": True, "score": 8})
        receipt = validator.validate(data)
        self.assertFalse(receipt["valid"])
        self.assertIn("input_gate must not display a numeric score", receipt["errors"])

    def test_priority_a_requires_a_linked_gap(self):
        data = self.load("source-backed.example.json")
        data["roadmap"]["phases"][0]["actions"][0]["linked_refs"] = []
        self.assertFalse(validator.validate(data)["valid"])

    def test_target_source_cannot_be_candidate_proof(self):
        data = self.load("source-backed.example.json")
        data["fit_assessment"][0]["proof_refs"] = ["target:job-1"]
        receipt = validator.validate(data)
        self.assertFalse(receipt["valid"])
        self.assertTrue(any("candidate-owned proof_refs" in item for item in receipt["errors"]))

    def test_capacity_is_enforced(self):
        data = self.load("source-backed.example.json")
        data["roadmap"]["phases"][0]["actions"][0]["estimated_minutes"] = 99999
        self.assertFalse(validator.validate(data)["valid"])

    def test_duplicate_resources_are_rejected(self):
        data = self.load("source-backed.example.json")
        resource = dict(data["learning_tracks"][0]["resources"][0])
        resource["resource_id"] = "duplicate"
        data["learning_tracks"][0]["resources"].append(resource)
        self.assertFalse(validator.validate(data)["valid"])

    def test_private_paths_and_secret_like_values_are_rejected(self):
        for value in ("/Users/example/private-resume.pdf", "api_key=abcdefghijklmnop"):
            data = self.load("source-backed.example.json")
            data["strategy"]["positioning"] = value
            with self.subTest(value=value):
                self.assertFalse(validator.validate(data)["valid"])

    def test_markdown_is_deterministic_and_contains_decision(self):
        data = self.load("source-backed.example.json")
        first = renderer.render(data)
        self.assertEqual(first, renderer.render(data))
        self.assertIn("## Decision", first)
        self.assertIn("## Resume guidance", first)
        self.assertIn("[Synthetic target requirement](https://example.com/jobs/reliability-engineer)", first)

    def test_cli_returns_machine_readable_receipt(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_runbook.py"), str(ROOT / "examples" / "source-backed.example.json"), "--strict"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode)
        self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_schema_is_parseable_and_covers_public_sections(self):
        schema = json.loads((ROOT / "schema" / "personalized_runbook.v1.schema.json").read_text())
        self.assertEqual("personalized_runbook.v1", schema["properties"]["identity"]["properties"]["schema_version"]["const"])
        self.assertTrue(validator.REQUIRED.issubset(set(schema["required"])))

    def test_public_artifacts_have_no_project_or_person_specific_markers(self):
        roots = [ROOT / "skill", ROOT / "schema", ROOT / "examples"]
        files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md", ROOT / "pyproject.toml"]
        files.extend(path for base in roots for path in base.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files).lower()
        for marker in (
            "/users/private-account",
            "private person name",
            "private employer",
            "private account name",
            "private-runbook.example",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
