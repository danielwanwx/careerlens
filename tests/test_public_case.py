import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PublicCaseTests(unittest.TestCase):
    def test_every_public_case_is_strict_and_deterministic(self):
        builder = load_script("build_case_study")
        demo_builder = load_script("build_runbook_demo")
        validator_path = ROOT / "skill/careerlens/scripts/validate_runbook.py"
        spec = importlib.util.spec_from_file_location("runbook_validator", validator_path)
        validator = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(validator)
        case_dirs = sorted(
            path for path in (ROOT / "case-studies").iterdir()
            if (path / "source-manifest.json").is_file()
        )
        self.assertGreaterEqual(len(case_dirs), 2)
        for case_dir in case_dirs:
            with self.subTest(case=case_dir.name):
                runbook = json.loads((case_dir / "output/runbook.json").read_text())
                self.assertEqual([], validator.validate(runbook, strict=True)["errors"])
                self.assertEqual(
                    builder.build_markdown(runbook),
                    (case_dir / "output/report.md").read_text(),
                )
                self.assertEqual(
                    builder.build_html(runbook),
                    (case_dir / "output/report.html").read_text(),
                )
                self.assertEqual(
                    demo_builder.build(runbook),
                    (case_dir / "output/runbook-demo.html").read_text(),
                )

    def test_agentic_case_preserves_selection_provenance_and_capacity(self):
        case_dir = ROOT / "case-studies/agentic-llm-platform"
        runbook = json.loads((case_dir / "output/runbook.json").read_text())
        self.assertTrue(runbook["candidate_picture"]["fictional"])
        self.assertFalse(runbook["decision_state"]["show_numeric_score"])
        self.assertEqual("conditional", runbook["decision_state"]["kind"])
        for question in runbook["question_bank"]:
            self.assertTrue(question["selection_reason"])
            self.assertTrue(question["mapped_requirements"])
            self.assertTrue(question["completion_standard"])
        for track in runbook["learning_tracks"]:
            roles = [item["resource_role"] for item in track["resources"]]
            self.assertEqual(len(roles), len(set(roles)))
            for item in track["resources"]:
                self.assertTrue(item["reading_scope"])
                self.assertTrue(item["skip_guidance"])
                self.assertTrue(item["assigned_output"])
                self.assertTrue(item["completion_condition"])
        planned = sum(
            action["estimated_minutes"]
            for phase in runbook["roadmap"]["phases"]
            for action in phase["actions"]
        )
        capacity = (
            runbook["roadmap"]["weeks"]
            * runbook["roadmap"]["weekly_capacity_hours"]
            * 60
        )
        self.assertLessEqual(planned, capacity)

    def test_agentic_case_builder_has_no_other_case_dependency(self):
        builder = load_script("build_agentic_case")
        generated = builder.build()
        self.assertEqual(
            "public-agentic-llm-platform-case",
            generated["identity"]["runbook_id"],
        )
        source_text = (ROOT / "scripts/build_agentic_case.py").read_text()
        self.assertNotIn("ai-engineer-integrity", source_text)

    def test_dynamic_runbook_rejects_missing_selection_metadata(self):
        builder = load_script("build_agentic_case")
        validator_path = ROOT / "skill/careerlens/scripts/validate_runbook.py"
        spec = importlib.util.spec_from_file_location("strict_validator", validator_path)
        validator = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(validator)

        mutations = []
        without_method = deepcopy(builder.build())
        without_method.pop("selection_methodology")
        mutations.append(without_method)
        without_question_reason = deepcopy(builder.build())
        without_question_reason["question_bank"][0].pop("selection_reason")
        mutations.append(without_question_reason)
        without_resource_output = deepcopy(builder.build())
        without_resource_output["learning_tracks"][0]["resources"][0].pop(
            "assigned_output"
        )
        mutations.append(without_resource_output)
        without_action_gate = deepcopy(builder.build())
        without_action_gate["roadmap"]["phases"][0]["actions"][0].pop("exit_gate")
        mutations.append(without_action_gate)

        for runbook in mutations:
            with self.subTest(errors=validator.validate(runbook, strict=True)["errors"]):
                self.assertTrue(validator.validate(runbook, strict=True)["errors"])

    def test_case_build_is_deterministic(self):
        builder = load_script("build_case_study")
        runbook = json.loads(
            (ROOT / "case-studies/ai-engineer-integrity/output/runbook.json").read_text()
        )
        first_markdown = builder.build_markdown(runbook)
        second_markdown = builder.build_markdown(runbook)
        first_html = builder.build_html(runbook)
        second_html = builder.build_html(runbook)
        self.assertEqual(first_markdown, second_markdown)
        self.assertEqual(first_html, second_html)
        self.assertIn("conditional", first_markdown)
        self.assertIn("Reproducible, not predictive", first_html)

    def test_case_has_no_numeric_fit_score(self):
        runbook = json.loads(
            (ROOT / "case-studies/ai-engineer-integrity/output/runbook.json").read_text()
        )
        self.assertFalse(runbook["decision_state"]["show_numeric_score"])
        self.assertIsNone(runbook["decision_state"]["score"])

    def test_source_hashes_and_non_media_artifacts_verify(self):
        verifier = load_script("verify_launch_assets")
        verifier.media_metadata = lambda _path: (_ for _ in ()).throw(
            AssertionError("non-media verification must not inspect media")
        )
        errors = verifier.verify(allow_missing_media=True)
        self.assertEqual([], errors)

    def test_build_writes_both_projections(self):
        builder = load_script("build_case_study")
        runbook = json.loads(
            (ROOT / "case-studies/ai-engineer-integrity/output/runbook.json").read_text()
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "report.md").write_text(builder.build_markdown(runbook))
            (output / "report.html").write_text(builder.build_html(runbook))
            self.assertGreater((output / "report.md").stat().st_size, 1000)
            self.assertGreater((output / "report.html").stat().st_size, 5000)

    def test_runbook_demo_exposes_core_evidence_and_actions(self):
        builder = load_script("build_runbook_demo")
        runbook = json.loads(
            (ROOT / "case-studies/ai-engineer-integrity/output/runbook.json").read_text()
        )
        demo = (
            ROOT / "case-studies/ai-engineer-integrity/output/runbook-demo.html"
        ).read_text()
        self.assertEqual(builder.build(runbook), demo)
        for state in ("proved", "claimed", "missing", "unknown"):
            self.assertIn(f'"status": "{state}"', demo)
        self.assertIn("No made-up match percentage", demo)
        self.assertIn("Question bank", demo)
        self.assertIn("Learning paths", demo)
        self.assertIn("Preparation plan", demo)
        self.assertIn("Why selected:", demo)
        self.assertIn("Read only", demo)
        self.assertIn("Exit gate:", demo)


if __name__ == "__main__":
    unittest.main()
