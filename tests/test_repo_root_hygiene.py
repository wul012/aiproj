"""The repo root is an allowlist, not a denylist.

v1302 incident: a `git add -A` with a name-based exclusion list swept in six
personal payslip files that had appeared at the repo root, and they reached
a public remote. A denylist fails open — every newly-shaped personal file is
a leak until someone remembers to name it. This test inverts the default:
the repo root may contain ONLY the files listed here, so anything else that
gets tracked fails loudly and by name.

Adding a genuinely new root file is a deliberate act: add it below in the
same commit. If that feels like friction, that is the point — the root is
where stray personal documents land.
"""
from __future__ import annotations

import subprocess
import unittest

from tests._bootstrap import ROOT

ALLOWED_ROOT_FILES = {
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "START_HERE.md",
    "pyproject.toml",
    "requirements.txt",
    "文档分流说明.md",
    "解释代码格式说明",
}


def tracked_root_files() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", ":(top)*"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return {name for name in out.split("\0") if name and "/" not in name}


class RepoRootHygieneTests(unittest.TestCase):
    def test_only_allowlisted_files_are_tracked_at_the_repo_root(self) -> None:
        unexpected = sorted(tracked_root_files() - ALLOWED_ROOT_FILES)
        self.assertEqual(
            [], unexpected,
            "Untracked-by-policy files at the repo root. If one of these is a "
            "personal document, it must never be committed: remove it with "
            "`git rm --cached` and add a .gitignore rule. If it is a genuine "
            "project file, add it to ALLOWED_ROOT_FILES.",
        )

    def test_allowlist_has_no_stale_entries(self) -> None:
        """A name that no longer exists would silently widen the allowlist."""
        stale = sorted(ALLOWED_ROOT_FILES - tracked_root_files())
        self.assertEqual([], stale)


if __name__ == "__main__":
    unittest.main()
