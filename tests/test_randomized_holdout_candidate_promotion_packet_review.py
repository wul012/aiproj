from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_candidate_promotion_packet import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet_review import (
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME,
    build_randomized_holdout_candidate_promotion_packet_review,
    locate_randomized_holdout_candidate_promotion_packet,
    resolve_exit_code,
)
from minigpt.randomized_holdout_candidate_promotion_packet_review_artifacts import (
    render_randomized_holdout_candidate_promotion_packet_review_html,
    render_randomized_holdout_candidate_promotion_packet_review_markdown,
    render_randomized_holdout_candidate_promotion_packet_review_text,
    write_randomized_holdout_candidate_promotion_packet_review_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.review_randomized_holdout_candidate_promotion_packet import main as cli_main
from tests.test_randomized_holdout_candidate_promotion_packet import build_packet, write_inputs


class RandomizedHoldoutCandidatePromotionPacketReviewTests(unittest.TestCase):
    def test_review_accepts_candidate_packet_for_bounded_gate_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_candidate_packet(Path(tmp))
            report = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_candidate_promotion_packet_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_candidate_promotion_packet_review_ready"])
        self.assertEqual(report["summary"]["review_decision"], "accept_randomized_holdout_candidate_packet_for_bounded_gate")
        self.assertTrue(report["summary"]["approved_for_bounded_promotion_gate"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["model_quality_claim"], "candidate_packet_review_only")
        self.assertEqual(report["summary"]["review_scope"], "bounded_randomized_holdout_candidate_review_only")
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_bounded_promotion_gate")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_gate_approval=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_review_fails_when_packet_claim_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_candidate_packet(Path(tmp))
            packet["summary"]["model_quality_claim"] = "production_model_quality"
            packet["packet"]["model_quality_claim"] = "production_model_quality"
            report = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("claim_is_candidate_packet_only", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 1)

    def test_review_fails_when_negative_control_no_longer_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_candidate_packet(Path(tmp))
            packet["summary"]["negative_dry_run_passed_case_count"] = 1
            packet["packet"]["negative_dry_run_passed_case_count"] = 1
            report = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("negative_control_rejected", [issue["id"] for issue in report["issues"]])

    def test_review_fails_when_promotion_is_already_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_candidate_packet(Path(tmp))
            packet["summary"]["promotion_ready"] = True
            packet["packet"]["promotion_ready"] = True
            report = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("packet_keeps_promotion_false", [issue["id"] for issue in report["issues"]])
        self.assertFalse(report["summary"]["approved_for_bounded_promotion_gate"])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_candidate_packet(root)
            self.assertEqual(locate_randomized_holdout_candidate_promotion_packet(packet_path.parent), packet_path)

            report = build_randomized_holdout_candidate_promotion_packet_review(packet, candidate_packet_path=packet_path)
            outputs = write_randomized_holdout_candidate_promotion_packet_review_outputs(report, root / "review")
            cli_main(
                [
                    "--candidate-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-gate-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_candidate_promotion_packet_review_ready=True", render_randomized_holdout_candidate_promotion_packet_review_text(report))
        self.assertIn("bounded_randomized_holdout_candidate_review_only", render_randomized_holdout_candidate_promotion_packet_review_markdown(report))
        self.assertIn("candidate promotion packet review", render_randomized_holdout_candidate_promotion_packet_review_html(report))


def ready_candidate_packet(root: Path) -> tuple[dict[str, object], Path]:
    input_paths = write_inputs(root / "inputs")
    packet = build_packet(input_paths)
    packet_dir = root / "candidate-packet"
    packet_path = packet_dir / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
    write_json_payload(packet, packet_path)
    return packet, packet_path


if __name__ == "__main__":
    unittest.main()
