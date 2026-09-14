import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "scripts/build_pages_site.py"
    spec = importlib.util.spec_from_file_location("build_pages_site", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def tree_digest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def create_synthetic_source_root(
    root: Path,
    *,
    private_marker: str = "",
    fictional: bool = True,
) -> None:
    for slug in ("ai-engineer-integrity", "agentic-llm-platform"):
        source = root / "case-studies" / slug / "output/runbook-demo.html"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "<!doctype html><html><head><style></style></head>"
            f"<body>Public fictional candidate {private_marker}</body></html>",
            encoding="utf-8",
        )
        manifest = root / "case-studies" / slug / "source-manifest.json"
        manifest.write_text(
            json.dumps({"case_id": slug, "candidate": {"fictional": fictional}}),
            encoding="utf-8",
        )

    social_preview = root / "assets/launch/social-preview.png"
    social_preview.parent.mkdir(parents=True, exist_ok=True)
    social_preview.write_bytes(b"public preview media")


def output_files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class PagesSiteTests(unittest.TestCase):
    def test_build_contains_only_public_landing_media_and_case_studies(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            builder.build(output)

            expected = {
                ".careerlens-pages-build",
                ".nojekyll",
                "index.html",
                "media/social-preview.png",
                "cases/ai-engineer-integrity/index.html",
                "cases/agentic-llm-platform/index.html",
            }
            self.assertEqual(expected, set(output_files(output)))
            self.assertFalse((output / "runbook").exists())
            self.assertFalse((output / "application-tracker").exists())

            landing = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Public synthetic", landing)
            self.assertIn("/careerlens/cases/ai-engineer-integrity/", landing)
            self.assertIn("/careerlens/cases/agentic-llm-platform/", landing)
            self.assertNotIn("careerlens-demo", landing)
            self.assertNotIn("/careerlens/runbook/", landing)
            self.assertNotIn("/careerlens/application-tracker/", landing)

            synthetic_case = (
                output / "cases/agentic-llm-platform/index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("Public fictional candidate", synthetic_case)
            self.assertIn("Original synthetic backend", synthetic_case)

    def test_every_built_file_excludes_private_identifiers_and_routes(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            builder.build(output)

            for relative, payload in output_files(output).items():
                if Path(relative) not in builder.BINARY_PUBLIC_ARTIFACTS:
                    builder.assert_public_payload(payload, label=relative)

    def test_generic_synthetic_case_output_remains_buildable(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "public-root"
            create_synthetic_source_root(fake_root)
            output = Path(directory) / "site"

            builder.build(output, root=fake_root, base_path="/")

            page = (
                output / "cases/ai-engineer-integrity/index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("Public fictional candidate", page)
            self.assertIn('href="/#cases"', page)
            self.assertFalse((output / "runbook").exists())
            self.assertFalse((output / "application-tracker").exists())

    def test_adversarial_text_fails_before_replacing_existing_pages_output(self):
        builder = load_builder()
        adversarial_values = {
            "literal marker": "PRIVATE_PERSON_NAME",
            "HTML entity marker": "PRIVATE&#95;PERSON&#95;NAME",
            "unicode marker": r"PRIVATE\u005fPERSON\u005fNAME",
            "percent marker": "PRIVATE%5FPERSON%5FNAME",
            "literal email": "contact@example.test",
            "HTML entity email": "contact&#64;example&#46;test",
            "unicode email": r"contact\u0040example\u002etest",
            "percent email": "contact%40example%2Etest",
            "phone number": "+1 (555) 010-2048",
            "POSIX home path": "/Users/synthetic-account/notes.txt",
            "Windows home path": r"C:\Users\synthetic-account\notes.txt",
            "HTML entity route": "&#47;runbook&#47;",
            "unicode route": r"\u002fapplication-tracker\u002f",
            "percent data path": "data%2Fapplication-tracker%2Ejson",
            "relative tracker data path": "application-tracker/data.json",
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, private_marker in adversarial_values.items():
                with self.subTest(name=name):
                    fake_root = Path(directory) / name.replace(" ", "-")
                    create_synthetic_source_root(fake_root, private_marker=private_marker)
                    output = fake_root / "site"
                    output.mkdir()
                    (output / builder.BUILD_MARKER).write_text(
                        "existing build", encoding="utf-8"
                    )
                    sentinel = output / "index.html"
                    sentinel.write_text(
                        "existing safe public artifact", encoding="utf-8"
                    )

                    with self.assertRaises(RuntimeError):
                        builder.build(output, root=fake_root)

                    self.assertEqual(
                        "existing safe public artifact", sentinel.read_text(encoding="utf-8")
                    )

    def test_repository_urls_are_sanitized_without_an_owner_specific_rule(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "public-root"
            create_synthetic_source_root(fake_root)
            source = (
                fake_root
                / "case-studies/ai-engineer-integrity/output/runbook-demo.html"
            )
            source.write_text(
                source.read_text(encoding="utf-8")
                + '<a href="https://github.com/synthetic-account/careerlens/blob/main/README.md">citation</a>',
                encoding="utf-8",
            )
            output = Path(directory) / "site"

            builder.build(output, root=fake_root)

            page = (output / "cases/ai-engineer-integrity/index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="https://github.com/"', page)
            self.assertNotIn("synthetic-account", page)

    def test_binary_public_preview_is_not_interpreted_as_text(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "public-root"
            create_synthetic_source_root(fake_root)
            binary_media = fake_root / "assets/launch/social-preview.png"
            binary_media.write_bytes(b"\x00public preview media\xff")
            output = Path(directory) / "site"

            builder.build(output, root=fake_root)

            self.assertEqual(
                b"\x00public preview media\xff",
                (output / "media/social-preview.png").read_bytes(),
            )

    def test_final_text_artifact_guard_fails_before_replacing_marked_output(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            output.mkdir()
            (output / builder.BUILD_MARKER).write_text("existing build", encoding="utf-8")
            sentinel = output / "index.html"
            sentinel.write_text("existing safe public artifact", encoding="utf-8")

            with patch.object(
                builder,
                "landing_page",
                return_value=r"<html><body>\u002frunbook\u002f</body></html>",
            ), self.assertRaises(RuntimeError):
                builder.build(output)

            self.assertEqual("existing safe public artifact", sentinel.read_text(encoding="utf-8"))

    def test_nonfictional_case_manifest_fails_closed(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "private-source"
            create_synthetic_source_root(fake_root, fictional=False)
            output = Path(directory) / "site"

            with self.assertRaisesRegex(RuntimeError, "non-fictional"):
                builder.build(output, root=fake_root)

            self.assertFalse(output.exists())

    def test_build_is_byte_deterministic(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            builder.build(first)
            builder.build(second)
            self.assertEqual(tree_digest(first), tree_digest(second))

    def test_root_base_path_supports_public_case_navigation(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            builder.build(output, base_path="/")
            overview = (output / "index.html").read_text(encoding="utf-8")
            case = (
                output / "cases/ai-engineer-integrity/index.html"
            ).read_text(encoding="utf-8")

            self.assertIn('href="/cases/ai-engineer-integrity/"', overview)
            self.assertIn('href="/#cases"', case)
            self.assertIn('aria-label="Public case navigation"', case)

    def test_missing_required_public_source_fails_closed(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "public-root"
            create_synthetic_source_root(fake_root)
            (
                fake_root
                / "case-studies/agentic-llm-platform/output/runbook-demo.html"
            ).unlink()

            with self.assertRaises(FileNotFoundError):
                builder.build(Path(directory) / "site", root=fake_root)

    def test_unmarked_non_empty_output_is_not_replaced(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("user-owned", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                builder.build(output)
            self.assertEqual("user-owned", sentinel.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
