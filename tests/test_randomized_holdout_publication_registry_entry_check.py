from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_entry import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME,
    build_randomized_holdout_publication_registry_entry,
)
from minigpt.randomized_holdout_publication_registry_entry_artifacts import write_randomized_holdout_publication_registry_entry_outputs
from minigpt.randomized_holdout_publication_registry_entry_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_entry_check,
    locate_randomized_holdout_publication_registry_entry,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_entry_check_artifacts import (
    render_randomized_holdout_publication_registry_entry_check_html,
    render_randomized_holdout_publication_registry_entry_check_markdown,
    render_randomized_holdout_publication_registry_entry_check_text,
    write_randomized_holdout_publication_registry_entry_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_registry_entry import main as cli_main
from tests.test_randomized_holdout_publication_registry_entry import ready_entry_inputs


class RandomizedHoldoutPublicationRegistryEntryCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, entry_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_entry_check(entry, registry_entry_path=entry_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_entry_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_entry_id"], "randomized-holdout-publication-v928")
        self.assertEqual(report["summary"]["rebuilt_entry_id"], "randomized-holdout-publication-v928")
        self.assertEqual(report["summary"]["original_consumer_boundary"], "governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_consumer_boundary"], "governance_lookup_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_entry_boundary_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, entry_path = ready_check_inputs(Path(tmp))
            entry["summary"]["consumer_boundary"] = "production_lookup"
            entry["registry_entry"]["consumer_boundary"] = "production_lookup"
            report = build_randomized_holdout_publication_registry_entry_check(entry, registry_entry_path=entry_path)

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("summary.consumer_boundary", ids)
        self.assertIn("registry_entry.consumer_boundary", ids)

    def test_contract_check_fails_when_source_index_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, entry_path = ready_check_inputs(Path(tmp))
            entry["publication_decision_index_path"] = "missing-index.json"
            entry["registry_entry"]["source_index_path"] = "missing-index.json"
            report = build_randomized_holdout_publication_registry_entry_check(entry, registry_entry_path=entry_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_publication_decision_index_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, entry_path = ready_check_inputs(root)
            entry["registry_entry"]["allowed_use"] = "production_promotion"
            write_json_payload(entry, entry_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(entry_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, entry_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_entry(entry_path.parent), entry_path)
            report = build_randomized_holdout_publication_registry_entry_check(entry, registry_entry_path=entry_path)
            outputs = write_randomized_holdout_publication_registry_entry_check_outputs(report, root / "check")
            cli_main([str(entry_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_entry_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_entry_check_markdown(report))
        self.assertIn("contract check", render_randomized_holdout_publication_registry_entry_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index_report, index_path = ready_entry_inputs(root / "entry-source")
    entry = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)
    outputs = write_randomized_holdout_publication_registry_entry_outputs(entry, root / "entry")
    path = Path(outputs["json"])
    expected = root / "entry" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME
    assert path == expected
    return entry, path


if __name__ == "__main__":
    unittest.main()
