from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_bounded_promotion_gate import (
    RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME,
    build_randomized_holdout_bounded_promotion_gate,
    locate_randomized_holdout_candidate_packet,
    locate_randomized_holdout_candidate_packet_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_bounded_promotion_gate_artifacts import (
    render_randomized_holdout_bounded_promotion_gate_html,
    render_randomized_holdout_bounded_promotion_gate_markdown,
    render_randomized_holdout_bounded_promotion_gate_text,
    write_randomized_holdout_bounded_promotion_gate_outputs,
)
from minigpt.randomized_holdout_candidate_promotion_packet_review import (
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME,
    build_randomized_holdout_candidate_promotion_packet_review,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_bounded_promotion_gate import main as cli_main
from tests.test_randomized_holdout_candidate_promotion_packet_review import ready_candidate_packet


class RandomizedHoldoutBoundedPromotionGateTests(unittest.TestCase):
    def test_gate_passes_clean_candidate_packet_review_and_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, packet, review_path, packet_path = ready_gate_inputs(Path(tmp))
            report = build_randomized_holdout_bounded_promotion_gate(
                review,
                packet,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_bounded_promotion_gate_passed")
        self.assertTrue(report["summary"]["randomized_holdout_bounded_promotion_gate_ready"])
        self.assertTrue(report["summary"]["approved_for_bounded_promotion_decision"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["model_quality_claim"], "bounded_gate_only")
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_bounded_promotion_decision")
        self.assertIn("record_randomized_holdout_bounded_promotion_decision", report["gate"]["allowed_next_steps"])
        self.assertEqual(resolve_exit_code(report, require_gate_ready=True, require_decision_approval=True), 0)
        self.assertEqual(resolve_exit_code(report, require_gate_ready=True, require_promotion_ready=True), 1)

    def test_gate_fails_when_review_does_not_approve_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, packet, review_path, packet_path = ready_gate_inputs(Path(tmp))
            review["summary"]["approved_for_bounded_promotion_gate"] = False
            report = build_randomized_holdout_bounded_promotion_gate(
                review,
                packet,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_approves_bounded_gate", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_gate_ready=True), 1)

    def test_gate_fails_when_packet_seed_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, packet, review_path, packet_path = ready_gate_inputs(Path(tmp))
            packet["summary"]["random_seed"] = 123
            packet["packet"]["random_seed"] = 123
            report = build_randomized_holdout_bounded_promotion_gate(
                review,
                packet,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("random_seed_matches", [issue["id"] for issue in report["issues"]])

    def test_gate_fails_when_direct_promotion_is_already_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, packet, review_path, packet_path = ready_gate_inputs(Path(tmp))
            review["summary"]["promotion_ready"] = True
            packet["summary"]["promotion_ready"] = True
            packet["packet"]["promotion_ready"] = True
            report = build_randomized_holdout_bounded_promotion_gate(
                review,
                packet,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, packet, review_path, packet_path = ready_gate_inputs(root)
            self.assertEqual(locate_randomized_holdout_candidate_packet_review(review_path.parent), review_path)
            self.assertEqual(locate_randomized_holdout_candidate_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_bounded_promotion_gate(
                review,
                packet,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_bounded_promotion_gate_outputs(report, root / "gate")
            cli_main(
                [
                    "--candidate-packet-review",
                    str(review_path.parent),
                    "--candidate-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-gate"),
                    "--require-gate-ready",
                    "--require-decision-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME))
        self.assertIn("randomized_holdout_bounded_promotion_gate_ready=True", render_randomized_holdout_bounded_promotion_gate_text(report))
        self.assertIn("record_randomized_holdout_bounded_promotion_decision", render_randomized_holdout_bounded_promotion_gate_markdown(report))
        self.assertIn("randomized holdout bounded promotion gate", render_randomized_holdout_bounded_promotion_gate_html(report))


def ready_gate_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    packet, packet_path = ready_candidate_packet(root / "packet-source")
    review = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)
    review_dir = root / "review"
    review_path = review_dir / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
    write_json_payload(review, review_path)
    return review, packet, review_path, packet_path


if __name__ == "__main__":
    unittest.main()
