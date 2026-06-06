from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_decision_index import build_randomized_holdout_publication_decision_index
from minigpt.randomized_holdout_publication_decision_index_artifacts import write_randomized_holdout_publication_decision_index_outputs
from minigpt.randomized_holdout_publication_registry_entry import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME,
    build_randomized_holdout_publication_registry_entry,
    locate_randomized_holdout_publication_decision_index,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_entry_artifacts import (
    render_randomized_holdout_publication_registry_entry_html,
    render_randomized_holdout_publication_registry_entry_markdown,
    render_randomized_holdout_publication_registry_entry_text,
    write_randomized_holdout_publication_registry_entry_outputs,
)
from scripts.build_randomized_holdout_publication_registry_entry import main as cli_main
from tests.test_randomized_holdout_publication_decision_index import ready_index_inputs


class RandomizedHoldoutPublicationRegistryEntryTests(unittest.TestCase):
    def test_registry_entry_accepts_ready_publication_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_report, index_path = ready_entry_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_entry_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_entry_ready"])
        self.assertEqual(report["summary"]["entry_id"], "randomized-holdout-publication-v928")
        self.assertEqual(report["summary"]["registry_status"], "registered")
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["accepted_claim_count"], 1)
        self.assertEqual(report["summary"]["blocked_claim_count"], 3)
        self.assertEqual(report["summary"]["consumer_boundary"], "governance_lookup_only")
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_entry")
        self.assertEqual(resolve_exit_code(report, require_entry_ready=True, require_bounded_publication=True), 0)
        self.assertEqual(resolve_exit_code(report, require_entry_ready=True, require_promotion_ready=True), 1)

    def test_registry_entry_fails_when_index_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_report, index_path = ready_entry_inputs(Path(tmp))
            index_report["summary"]["randomized_holdout_publication_decision_index_ready"] = False
            report = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_index_summary_ready", [issue["id"] for issue in report["issues"]])

    def test_registry_entry_fails_when_allowed_use_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_report, index_path = ready_entry_inputs(Path(tmp))
            index_report["summary"]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_bounded", [issue["id"] for issue in report["issues"]])

    def test_registry_entry_fails_when_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_report, index_path = ready_entry_inputs(Path(tmp))
            index_report["index"]["promotion_ready"] = True
            report = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_report, index_path = ready_entry_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_decision_index(index_path.parent), index_path)
            report = build_randomized_holdout_publication_registry_entry(index_report, publication_decision_index_path=index_path)
            outputs = write_randomized_holdout_publication_registry_entry_outputs(report, root / "entry")
            cli_main(
                [
                    "--publication-decision-index",
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-entry"),
                    "--require-entry-ready",
                    "--require-bounded-publication",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_entry_ready=True", render_randomized_holdout_publication_registry_entry_text(report))
        self.assertIn("governance_lookup_only", render_randomized_holdout_publication_registry_entry_markdown(report))
        self.assertIn("publication registry entry", render_randomized_holdout_publication_registry_entry_html(report))


def ready_entry_inputs(root: Path) -> tuple[dict[str, object], Path]:
    decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(root / "index-source")
    index_report = build_randomized_holdout_publication_decision_index(
        decision,
        review,
        packet,
        publication_decision_path=decision_path,
        publication_review_path=review_path,
        publication_packet_path=packet_path,
    )
    index_outputs = write_randomized_holdout_publication_decision_index_outputs(index_report, root / "index")
    return index_report, Path(index_outputs["json"])


if __name__ == "__main__":
    unittest.main()
