from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_publication_packet_review import build_randomized_holdout_acceptance_publication_packet_review
from minigpt.randomized_holdout_acceptance_publication_packet_review_artifacts import write_randomized_holdout_acceptance_publication_packet_review_outputs
from minigpt.randomized_holdout_publication_decision import build_randomized_holdout_publication_decision
from minigpt.randomized_holdout_publication_decision_artifacts import write_randomized_holdout_publication_decision_outputs
from minigpt.randomized_holdout_publication_decision_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME,
    build_randomized_holdout_publication_decision_index,
    locate_randomized_holdout_acceptance_publication_packet,
    locate_randomized_holdout_publication_decision,
    locate_randomized_holdout_publication_packet_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_decision_index_artifacts import (
    render_randomized_holdout_publication_decision_index_html,
    render_randomized_holdout_publication_decision_index_markdown,
    render_randomized_holdout_publication_decision_index_text,
    write_randomized_holdout_publication_decision_index_outputs,
)
from scripts.index_randomized_holdout_publication_decision import main as cli_main
from tests.test_randomized_holdout_acceptance_publication_packet_review import ready_review_inputs


class RandomizedHoldoutPublicationDecisionIndexTests(unittest.TestCase):
    def test_index_accepts_publication_decision_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_decision_index(
                decision,
                review,
                packet,
                publication_decision_path=decision_path,
                publication_review_path=review_path,
                publication_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_decision_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_decision_index_ready"])
        self.assertEqual(report["summary"]["indexed_decision"], "accept_bounded_randomized_holdout_publication")
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["accepted_claim_count"], 1)
        self.assertEqual(report["summary"]["blocked_claim_count"], 3)
        self.assertEqual(report["summary"]["source_count"], 3)
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_publication_registry_entry")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_bounded_publication=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_index_fails_when_decision_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            decision["decision"] = "fix_randomized_holdout_publication_decision"
            report = build_randomized_holdout_publication_decision_index(
                decision,
                review,
                packet,
                publication_decision_path=decision_path,
                publication_review_path=review_path,
                publication_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("decision_accepted", [issue["id"] for issue in report["issues"]])

    def test_index_fails_when_review_allowed_use_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            review["summary"]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_publication_decision_index(
                decision,
                review,
                packet,
                publication_decision_path=decision_path,
                publication_review_path=review_path,
                publication_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_bounded", [issue["id"] for issue in report["issues"]])

    def test_index_fails_when_packet_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            packet["summary"]["promotion_ready"] = True
            report = build_randomized_holdout_publication_decision_index(
                decision,
                review,
                packet,
                publication_decision_path=decision_path,
                publication_review_path=review_path,
                publication_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision, review, packet, decision_path, review_path, packet_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_decision(decision_path.parent), decision_path)
            self.assertEqual(locate_randomized_holdout_publication_packet_review(review_path.parent), review_path)
            self.assertEqual(locate_randomized_holdout_acceptance_publication_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_publication_decision_index(
                decision,
                review,
                packet,
                publication_decision_path=decision_path,
                publication_review_path=review_path,
                publication_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_publication_decision_index_outputs(report, root / "index")
            cli_main(
                [
                    "--publication-decision",
                    str(decision_path.parent),
                    "--publication-review",
                    str(review_path.parent),
                    "--publication-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-bounded-publication",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_decision_index_ready=True", render_randomized_holdout_publication_decision_index_text(report))
        self.assertIn("build_randomized_holdout_publication_registry_entry", render_randomized_holdout_publication_decision_index_markdown(report))
        self.assertIn("publication decision index", render_randomized_holdout_publication_decision_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path, Path, Path]:
    packet, packet_path = ready_review_inputs(root / "packet-source")
    review = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)
    review_outputs = write_randomized_holdout_acceptance_publication_packet_review_outputs(review, root / "review")
    review_path = Path(review_outputs["json"])
    decision = build_randomized_holdout_publication_decision(review, publication_review_path=review_path)
    decision_outputs = write_randomized_holdout_publication_decision_outputs(decision, root / "decision")
    return decision, review, packet, Path(decision_outputs["json"]), review_path, packet_path


if __name__ == "__main__":
    unittest.main()
