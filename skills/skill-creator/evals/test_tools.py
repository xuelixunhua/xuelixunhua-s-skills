"""Focused helper regressions. Run with Python and PyYAML; no model calls.

Temporary cases live under cwd/work (or SKILL_CREATOR_TEST_WORK).
"""

import copy
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
WORK_ROOT = Path(os.environ.get("SKILL_CREATOR_TEST_WORK", Path.cwd() / "work")).resolve()
sys.path.insert(0, str(SCRIPTS))
from quick_validate import validate_skill
from generate_openai_yaml import write_openai_yaml


class ToolRegressionTests(unittest.TestCase):
    def setUp(self):
        WORK_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="creator-test-", dir=WORK_ROOT)
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        if not self.root.is_relative_to(WORK_ROOT) or self.root == WORK_ROOT:
            raise RuntimeError("Refusing cleanup outside the test workspace")
        self.temporary.cleanup()

    def fixture(self, name="sample-skill", body="# Method\nUse source evidence to answer the request.\n"):
        directory = self.root / name
        directory.mkdir()
        (directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: A reusable workflow for a bounded task.\n---\n\n{body}",
            encoding="utf-8",
        )
        return directory

    def run_script(self, script, *args):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / script), *map(str, args)],
            capture_output=True,
        )
        return result

    def metadata(self, directory, content):
        path = directory / "agents" / "openai.yaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_scaffold_keeps_philosophy_and_requires_completion(self):
        result = self.run_script("init_skill.py", "new-skill", "--path", self.root, "--resources", "references", "--examples")
        self.assertEqual(result.returncode, 0, result.stderr)
        directory = self.root / "new-skill"
        self.assertIn("## Strategy Philosophy", (directory / "SKILL.md").read_text(encoding="utf-8"))
        self.assertTrue(validate_skill(directory)[0])
        valid, message, _ = validate_skill(directory, ready=True)
        self.assertFalse(valid)
        self.assertIn("Unfinished scaffold", message)

    def test_ready_catches_missing_files_and_accepts_completed_resources(self):
        directory = self.fixture(body="Read `references/required.md` and [schema](references/schema.json).\n")
        self.assertTrue(validate_skill(directory)[0])
        valid, message, _ = validate_skill(directory, ready=True)
        self.assertFalse(valid)
        self.assertIn("required.md", message)
        self.assertIn("schema.json", message)
        (directory / "references").mkdir()
        (directory / "references" / "required.md").write_text("# Evidence\n", encoding="utf-8")
        (directory / "references" / "schema.json").write_text("{}", encoding="utf-8")
        self.assertTrue(validate_skill(directory, ready=True)[0])

    def test_ready_understands_relative_paths_spaces_and_fragments(self):
        directory = self.fixture(body="Read [details](<./references/deep method.md#start>).\n")
        (directory / "references").mkdir()
        (directory / "references" / "deep method.md").write_text("# Start\n", encoding="utf-8")
        self.assertTrue(validate_skill(directory, ready=True)[0])

    def test_ready_does_not_claim_to_check_globs(self):
        directory = self.fixture(body="Inspect `references/*.md` as needed.\n")
        self.assertTrue(validate_skill(directory, ready=True)[0])

    def test_refresh_preserves_configuration_and_is_idempotent(self):
        directory = self.fixture()
        original = {
            "interface": {"display_name": "Original", "short_description": "A useful description for the original skill", "icon_small": "./assets/icon.png", "default_prompt": "Use $sample-skill to handle the task.", "custom_field": "keep"},
            "policy": {"allow_implicit_invocation": False},
            "dependencies": {"tools": [{"type": "mcp", "value": "example"}]},
            "custom_section": {"enabled": True, "values": [1, "two", None]},
        }
        path = self.metadata(directory, yaml.safe_dump(original))
        result = self.run_script("generate_openai_yaml.py", directory, "--interface", "display_name=Changed")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = copy.deepcopy(original)
        expected["interface"]["display_name"] = "Changed"
        self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8")), expected)
        previous = path.read_bytes()
        result = self.run_script("generate_openai_yaml.py", directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_bytes(), previous)

    def test_utf8_source_and_chinese_ui_round_trip(self):
        directory = self.fixture(body="# \u7b56\u7565\u54f2\u5b66\n\u4fdd\u7559\u65b9\u5411\u548c\u53d6\u820d\u3002\U0001f9ed\n")
        result = self.run_script("generate_openai_yaml.py", directory, "--interface", "display_name=\u4e2d\u6587\u6280\u80fd", "--interface", "short_description=\u4fdd\u7559\u65b9\u5411\u548c\u53d6\u820d")
        self.assertEqual(result.returncode, 0, result.stderr)
        content = (directory / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(content)["interface"]["display_name"], "\u4e2d\u6587\u6280\u80fd")
        self.assertTrue(validate_skill(directory, ready=True)[0])

    def test_bad_existing_yaml_is_not_overwritten(self):
        directory = self.fixture()
        for content in ("interface: [\n", "- a list\n", "interface: null\n"):
            with self.subTest(content=content):
                path = self.metadata(directory, content)
                previous = path.read_bytes()
                result = self.run_script("generate_openai_yaml.py", directory)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(path.read_bytes(), previous)

    def test_invalid_override_is_not_written(self):
        directory = self.fixture()
        path = self.metadata(directory, 'interface:\n  display_name: "Keep"\n')
        previous = path.read_bytes()
        for override in ("unknown=value", "display_name=", "missing-equals"):
            with self.subTest(override=override):
                result = self.run_script("generate_openai_yaml.py", directory, "--interface", override)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(path.read_bytes(), previous)

    def test_failed_file_replacement_preserves_original_and_cleans_temp(self):
        directory = self.fixture()
        path = self.metadata(directory, 'interface:\n  display_name: "Keep"\n')
        previous = path.read_bytes()
        with patch("generate_openai_yaml.Path.replace", side_effect=PermissionError("file locked")):
            with contextlib.redirect_stdout(io.StringIO()):
                result = write_openai_yaml(directory, "sample-skill", ["display_name=Changed"])
        self.assertIsNone(result)
        self.assertEqual(path.read_bytes(), previous)
        self.assertEqual(list(path.parent.glob(".openai-*.tmp")), [])

    def test_optional_ui_and_policy_types(self):
        directory = self.fixture()
        for content in ('policy:\n  allow_implicit_invocation: false\n', 'dependencies:\n  tools: []\n', 'interface:\n  display_name: "Only a title"\n'):
            with self.subTest(content=content):
                self.metadata(directory, content)
                self.assertTrue(validate_skill(directory)[0])
        self.metadata(directory, 'policy:\n  allow_implicit_invocation: "false"\n')
        self.assertFalse(validate_skill(directory)[0])

    def test_ready_cli_reports_failure_and_evidence_limit(self):
        directory = self.fixture(body="Read `references/required.md`.\n")
        result = self.run_script("quick_validate.py", directory, "--ready")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"Missing bundled file", result.stdout)
        result = self.run_script("quick_validate.py", directory)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"model behavior not evaluated", result.stdout)

    def test_prompt_scaffolder_still_creates_both_artifacts(self):
        result = self.run_script("init_prompt.py", "sample-prompt", "--path", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "sample-prompt" / "PROMPT.md").is_file())
        self.assertTrue((self.root / "sample-prompt" / "TEST_INPUTS.md").is_file())


if __name__ == "__main__":
    unittest.main()
