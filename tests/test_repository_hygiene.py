from __future__ import annotations

import unittest

from tests._bootstrap import ROOT


def gitignore_entries() -> set[str]:
    return {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


class RepositoryHygieneTests(unittest.TestCase):
    def test_common_local_and_generated_paths_are_ignored(self) -> None:
        entries = gitignore_entries()

        expected = {
            "__pycache__/",
            "*.py[cod]",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            ".coverage",
            "htmlcov/",
            ".venv/",
            "venv/",
            "build/",
            "dist/",
            "*.egg-info/",
        }

        self.assertTrue(expected.issubset(entries), sorted(expected - entries))

    def test_workspace_specific_non_source_paths_are_ignored(self) -> None:
        entries = gitignore_entries()

        expected = {
            ".codegraph/",
            ".idea/",
            ".vscode/",
            "ignoreit.py",
            "runs/",
            "tmp/",
            ".tmp/",
            "output/",
            "test-output/",
            "playwright-report/",
        }

        self.assertTrue(expected.issubset(entries), sorted(expected - entries))


if __name__ == "__main__":
    unittest.main()
