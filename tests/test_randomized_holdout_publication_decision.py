from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_publication_packet_review import build_randomized_holdout_acceptance_publication_packet_review
from minigpt.randomized_holdout_acceptance_publication_packet_review_artifacts import write_randomized_holdout_acceptance_publication_packet_review_outputs
from minigpt.randomized_holdout_publication_decision import (
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME,
    build_randomized_holdout_publication_decision,
    locate_randomized_holdout_publication_packet_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_decision_artifacts import (
    render_randomized_holdout_publication_decision_html,
    render_randomized_holdout_publication_decision_markdown,
    render_randomized_holdout_publication_decision_text,
    write_randomized_holdout_publication_decision_outputs,
)
from scripts.decide_randomized_holdout_publication import main as cli_main
from tests.test_randomized_holdout_acceptance_publication_packet_review import ready_review_inputs


class RandomizedHoldoutPublicationDecisionTests(unittest.TestCase):
    def test_decision_accepts_bounded_publication_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_decision_inputs(Path(tmp))
            report = build_randomized_holdout_publication_decision(review, publication_review_path=review_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_decision_accepted")
        self.assertTrue(report["summary"]["randomized_holdout_publication_decision_ready"])
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["allowed_use"], "bounded_model_capability_governance_only")
        self.assertEqual(report["summary"]["decision_scope"], "bounded_randomized_holdout_publication_only")
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_decision")
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True, require_bounded_publication=True), 0)
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True, require_promotion_ready=True), 1)

    def test_decision_fails_when_review_does_not_approve_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_decision_inputs(Path(tmp))
            review["summary"]["approved_for_bounded_publication"] = False
            review["review"]["approved_for_bounded_publication"] = False
            report = build_randomized_holdout_publication_decision(review, publication_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_approves_bounded_publication", [issue["id"] for issue in report["issues"]])

    def test_decision_fails_when_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_decision_inputs(Path(tmp))
            review["summary"]["promotion_ready"] = True
            review["review"]["promotion_ready"] = True
            report = build_randomized_holdout_publication_decision(review, publication_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_decision_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_packet_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_decision(review, publication_review_path=review_path)
            outputs = write_randomized_holdout_publication_decision_outputs(report, root / "decision")
            cli_main(
                [
                    "--publication-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-decision"),
                    "--require-decision-ready",
                    "--require-bounded-publication",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_decision_ready=True", render_randomized_holdout_publication_decision_text(report))
        self.assertIn("bounded_randomized_holdout_publication_only", render_randomized_holdout_publication_decision_markdown(report))
        self.assertIn("publication decision", render_randomized_holdout_publication_decision_html(report))


def ready_decision_inputs(root: Path) -> tuple[dict[str, object], Path]:
    packet, packet_path = ready_review_inputs(root / "review-source")
    review = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)
    outputs = write_randomized_holdout_acceptance_publication_packet_review_outputs(review, root / "review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
