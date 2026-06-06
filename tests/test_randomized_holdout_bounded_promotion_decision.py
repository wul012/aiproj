from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_bounded_promotion_decision import (
    RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME,
    build_randomized_holdout_bounded_promotion_decision,
    locate_randomized_holdout_bounded_promotion_gate,
    locate_randomized_holdout_candidate_packet,
    locate_randomized_holdout_candidate_packet_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_bounded_promotion_decision_artifacts import (
    render_randomized_holdout_bounded_promotion_decision_html,
    render_randomized_holdout_bounded_promotion_decision_markdown,
    render_randomized_holdout_bounded_promotion_decision_text,
    write_randomized_holdout_bounded_promotion_decision_outputs,
)
from minigpt.randomized_holdout_bounded_promotion_gate import (
    RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME,
    build_randomized_holdout_bounded_promotion_gate,
)
from minigpt.report_utils import write_json_payload
from scripts.decide_randomized_holdout_bounded_promotion import main as cli_main
from tests.test_randomized_holdout_bounded_promotion_gate import ready_gate_inputs


class RandomizedHoldoutBoundedPromotionDecisionTests(unittest.TestCase):
    def test_decision_accepts_bounded_randomized_holdout_claim_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(Path(tmp))
            report = build_randomized_holdout_bounded_promotion_decision(
                gate,
                review,
                packet,
                gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_bounded_promotion_decision_accepted")
        self.assertTrue(report["summary"]["randomized_holdout_bounded_promotion_decision_ready"])
        self.assertEqual(report["summary"]["final_decision"], "accept_bounded_randomized_holdout_claim")
        self.assertTrue(report["summary"]["bounded_promotion_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["claim_scope"], "randomized_target_hidden_20_case_tiny_checkpoint_only")
        self.assertEqual(report["summary"]["model_quality_claim"], "bounded_randomized_target_hidden_holdout_claim_only")
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_decision_index")
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True, require_bounded_acceptance=True), 0)
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True, require_promotion_ready=True), 1)

    def test_decision_fails_when_gate_does_not_approve_bounded_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(Path(tmp))
            gate["summary"]["approved_for_bounded_promotion_decision"] = False
            report = build_randomized_holdout_bounded_promotion_decision(
                gate,
                review,
                packet,
                gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("gate_allows_bounded_decision", [issue["id"] for issue in report["issues"]])

    def test_decision_fails_when_candidate_count_drops_below_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(Path(tmp))
            gate["summary"]["candidate_case_count"] = 10
            report = build_randomized_holdout_bounded_promotion_decision(
                gate,
                review,
                packet,
                gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("candidate_count_floor", [issue["id"] for issue in report["issues"]])

    def test_decision_fails_when_direct_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(Path(tmp))
            gate["summary"]["promotion_ready"] = True
            review["summary"]["promotion_ready"] = True
            packet["summary"]["promotion_ready"] = True
            report = build_randomized_holdout_bounded_promotion_decision(
                gate,
                review,
                packet,
                gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(root)
            self.assertEqual(locate_randomized_holdout_bounded_promotion_gate(gate_path.parent), gate_path)
            self.assertEqual(locate_randomized_holdout_candidate_packet_review(review_path.parent), review_path)
            self.assertEqual(locate_randomized_holdout_candidate_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_bounded_promotion_decision(
                gate,
                review,
                packet,
                gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_bounded_promotion_decision_outputs(report, root / "decision")
            cli_main(
                [
                    "--gate",
                    str(gate_path.parent),
                    "--candidate-packet-review",
                    str(review_path.parent),
                    "--candidate-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-decision"),
                    "--require-decision-ready",
                    "--require-bounded-acceptance",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME))
        self.assertIn("randomized_holdout_bounded_promotion_decision_ready=True", render_randomized_holdout_bounded_promotion_decision_text(report))
        self.assertIn("accept_bounded_randomized_holdout_claim", render_randomized_holdout_bounded_promotion_decision_markdown(report))
        self.assertIn("randomized holdout bounded promotion decision", render_randomized_holdout_bounded_promotion_decision_html(report))


def ready_decision_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path, Path, Path]:
    review, packet, review_path, packet_path = ready_gate_inputs(root / "gate-source")
    gate = build_randomized_holdout_bounded_promotion_gate(
        review,
        packet,
        candidate_packet_review_path=review_path,
        candidate_packet_path=packet_path,
    )
    gate_path = root / "gate" / RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME
    write_json_payload(gate, gate_path)
    return gate, review, packet, gate_path, review_path, packet_path


if __name__ == "__main__":
    unittest.main()
