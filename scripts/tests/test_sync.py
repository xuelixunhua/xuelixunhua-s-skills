"""Disposable sync regressions; no installed skills, network, or model calls."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "sync-from-local.ps1"
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(SHELL, "PowerShell is required")
class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skills-sync-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.source = self.root / "local"
        self.script = self.repo / "scripts" / SCRIPT.name
        self.script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.entries = [
            {"name": name, "path": f"skills/{name}", "source": f"~/.codex/skills/{name}"}
            for name in ("alpha", "beta")
        ]
        self.manifest()
        for name in ("alpha", "beta"):
            self.write(self.source / name / "SKILL.md", f"# {name}\n")
            self.write(self.repo / "skills" / name / "obsolete.txt", "old\n")

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def manifest(self):
        self.write(self.repo / "manifest.json", json.dumps({"skills": self.entries}))

    def run_sync(self, *args, source=None):
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"

        command = f"& {quote(self.script)} -SourceRoot {quote(source or self.source)} {' '.join(args)}"
        return subprocess.run(
            [SHELL, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )

    def snapshot(self):
        return {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}

    def test_selected_sync_is_filtered_and_repeatable(self):
        private = [
            "config.env", ".env", ".env.local", "auth.json", "credentials.json",
            ".learnings/ERRORS.md", "nested/__pycache__/x.pyc", "node_modules/x.js",
            "evals/results/latest.json", "evals/completed-work-regressions-20260905.json",
            "references/site-patterns/tingwu.aliyun.com.md", "trace.log", "work/output.md",
        ]
        for name in private:
            self.write(self.source / "alpha" / name, "private fixture\n")
        self.write(self.source / "alpha" / "templates/config.env.template", "PORT=3456\n")
        self.write(self.source / "alpha" / "evals/evals.json", "{}\n")
        result = self.run_sync("-Skills alpha")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / "skills/beta/obsolete.txt").exists())
        self.assertFalse((self.repo / "skills/alpha/obsolete.txt").exists())
        for name in private:
            self.assertFalse((self.repo / "skills/alpha" / name).exists(), name)
        self.assertTrue((self.repo / "skills/alpha/templates/config.env.template").exists())
        self.assertTrue((self.repo / "skills/alpha/evals/evals.json").exists())
        before = self.snapshot()
        self.assertEqual(self.run_sync("-Skills alpha").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_whatif_is_read_only(self):
        before = self.snapshot()
        result = self.run_sync("-WhatIf")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_missing_later_source_does_not_replace_first(self):
        (self.source / "beta/SKILL.md").unlink()
        before = self.snapshot()
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_unknown_selection_is_read_only(self):
        before = self.snapshot()
        self.assertNotEqual(self.run_sync("-Skills missing").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_invalid_mapping_is_read_only(self):
        self.entries[1]["path"] = "skills/../outside"
        self.manifest()
        before = self.snapshot()
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_identical_source_is_rejected(self):
        self.write(self.repo / "skills/alpha/SKILL.md", "keep\n")
        before = self.snapshot()
        self.assertNotEqual(self.run_sync("-Skills alpha", source=self.repo / "skills").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_nested_source_is_rejected(self):
        nested = self.repo / "skills/alpha/local"
        self.write(nested / "alpha/SKILL.md", "keep\n")
        before = self.snapshot()
        self.assertNotEqual(self.run_sync("-Skills alpha", source=nested).returncode, 0)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
