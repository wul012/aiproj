from __future__ import annotations

import unittest


from tests._bootstrap import ROOT


class DependabotConfigTests(unittest.TestCase):
    def test_dependabot_tracks_actions_and_python_dependencies(self) -> None:
        config_path = ROOT / ".github" / "dependabot.yml"

        text = config_path.read_text(encoding="utf-8")

        self.assertIn("version: 2", text)
        self.assertIn('package-ecosystem: "github-actions"', text)
        self.assertIn('package-ecosystem: "pip"', text)
        self.assertGreaterEqual(text.count('directory: "/"'), 2)
        self.assertGreaterEqual(text.count('interval: "weekly"'), 2)


if __name__ == "__main__":
    unittest.main()
