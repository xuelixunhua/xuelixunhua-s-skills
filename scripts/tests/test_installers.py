"""Exercise installers against disposable destinations, never global settings."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(SHELL, "PowerShell is required")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skills-install-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_script(self, script, *args):
        return subprocess.run(
            [SHELL, "-NoProfile", "-NonInteractive", "-File", str(REPO / script), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )

    def test_selected_install_preserves_then_replaces_existing_copy(self):
        dest = self.root / "installed"
        script = "scripts/install-codex.ps1"
        for name in ("content-master", "skill-creator", "web-access", "chief-of-staff-collaboration"):
            result = self.run_script(script, "-Skills", name, "-Destination", dest)
            self.assertEqual(result.returncode, 0, result.stderr)
            source = REPO / "skills" / name
            expected = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob("*") if p.is_file()}
            actual = {str(p.relative_to(dest / name)): p.read_bytes() for p in (dest / name).rglob("*") if p.is_file()}
            self.assertEqual(expected, actual)
        target = dest / "content-master/SKILL.md"
        target.write_text("user edit\n", encoding="utf-8")
        self.assertEqual(self.run_script(script, "-Skills", "content-master", "-Destination", dest).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), "user edit\n")
        self.assertEqual(self.run_script(script, "-Skills", "content-master", "-Destination", dest, "-Force").returncode, 0)
        self.assertEqual(target.read_bytes(), (REPO / "skills/content-master/SKILL.md").read_bytes())

    def test_route_preview_backup_preservation_and_idempotency(self):
        path = self.root / "AGENTS.md"
        original = "# Existing rules\nKeep user content.\n"
        path.write_text(original, encoding="utf-8")
        script = "skills/chief-of-staff-collaboration/scripts/install-global-agents-route.ps1"
        result = self.run_script(script, "-AgentsPath", path, "-WhatIf")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_text(encoding="utf-8"), original)
        self.assertEqual(len(list(self.root.glob("*.backup-*"))), 0)
        result = self.run_script(script, "-AgentsPath", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        first = path.read_bytes()
        self.assertTrue(path.read_text(encoding="utf-8").startswith(original.rstrip()))
        self.assertEqual(path.read_text(encoding="utf-8").count("<!-- BEGIN chief-of-staff-collaboration route -->"), 1)
        backups = list(self.root.glob("*.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
        self.assertEqual(self.run_script(script, "-AgentsPath", path).returncode, 0)
        self.assertEqual(first, path.read_bytes())
        self.assertEqual(len(list(self.root.glob("*.backup-*"))), 1)

    def test_partial_route_marker_is_not_overwritten(self):
        path = self.root / "AGENTS.md"
        path.write_text("<!-- BEGIN chief-of-staff-collaboration route -->\nkeep\n", encoding="utf-8")
        before = path.read_bytes()
        result = self.run_script(
            "skills/chief-of-staff-collaboration/scripts/install-global-agents-route.ps1", "-AgentsPath", path,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
