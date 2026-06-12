from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.project_docs_readability import (
    DOC_TARGETS,
    build_project_docs_readability_report,
    resolve_exit_code,
    write_project_docs_readability_outputs,
)
from scripts.devtools.check_project_docs_readability_v1131 import main as cli_main


class ProjectDocsReadabilityTests(unittest.TestCase):
    def test_docs_split_passes_when_targets_and_links_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            report = build_project_docs_readability_report(root, generated_at="2026-06-12T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["doc_target_count"], len(DOC_TARGETS))
        self.assertEqual(report["summary"]["missing_readme_link_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_docs_split_fails_when_readme_link_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            (root / "README.md").write_text("# MiniGPT\n\n[Overview](docs/overview.md)\n", encoding="utf-8")
            report = build_project_docs_readability_report(root)

        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["summary"]["missing_readme_link_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            report = build_project_docs_readability_report(root)
            outputs = write_project_docs_readability_outputs(report, root / "out")
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _write_docs_fixture(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True)
    links = []
    for target in DOC_TARGETS:
        path = root / str(target["path"])
        body = [str(target["title"]), "", "MiniGPT AI governance publication receipt training evaluation holdout contract check lookup-only promotion model quality governance f/ screenshot artifact"]
        path.write_text("\n".join(body), encoding="utf-8")
        links.append(f"- [{path.stem}]({target['path']})")
    (root / "README.md").write_text("# MiniGPT\n\n" + "\n".join(links) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
