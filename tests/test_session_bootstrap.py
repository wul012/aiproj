from __future__ import annotations

import unittest

from tests._bootstrap import ROOT


class SessionBootstrapTests(unittest.TestCase):
    def test_bootstrap_keeps_orientation_commands_and_ascii_output(self) -> None:
        text = (ROOT / "scripts" / "codex-bootstrap.ps1").read_text(encoding="utf-8")

        self.assertIn("git log --oneline -3", text)
        self.assertIn("git status -sb", text)
        self.assertIn("git tag --sort=-creatordate", text)
        self.assertIn("gh run list --limit 3", text)
        self.assertIn("production-excellence-aiproj-brief.md", text)
        self.assertTrue(text.isascii())


if __name__ == "__main__":
    unittest.main()
