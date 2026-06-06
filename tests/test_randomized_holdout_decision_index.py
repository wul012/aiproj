from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_bounded_promotion_decision import (
    RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME,
    build_randomized_holdout_bounded_promotion_decision,
)
from minigpt.randomized_holdout_decision_index import (
    RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME,
    build_randomized_holdout_decision_index,
    locate_randomized_holdout_bounded_promotion_decision,
    locate_randomized_holdout_bounded_promotion_gate,
    locate_randomized_holdout_candidate_packet,
    locate_randomized_holdout_candidate_packet_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_decision_index_artifacts import (
    render_randomized_holdout_decision_index_html,
    render_randomized_holdout_decision_index_markdown,
    render_randomized_holdout_decision_index_text,
    write_randomized_holdout_decision_index_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_decision_index import main as cli_main
from tests.test_randomized_holdout_bounded_promotion_decision import ready_decision_inputs


class RandomizedHoldoutDecisionIndexTests(unittest.TestCase):
    def test_indexes_clean_bounded_decision_chain_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_decision_index(
                decision,
                gate,
                review,
                packet,
                bounded_decision_path=decision_path,
                bounded_gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_decision_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_decision_index_ready"])
        self.assertTrue(report["summary"]["bounded_promotion_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["candidate_case_count"], 20)
        self.assertEqual(report["summary"]["random_seed"], 914)
        self.assertEqual(report["summary"]["pass_rate"], 1.0)
        self.assertEqual(report["summary"]["model_quality_claim"], "bounded_randomized_target_hidden_holdout_claim_only")
        self.assertEqual(report["summary"]["source_count"], 4)
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_acceptance_summary")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_bounded_acceptance=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_rejects_unaccepted_bounded_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            decision["summary"]["bounded_promotion_accepted"] = False
            report = build_randomized_holdout_decision_index(
                decision,
                gate,
                review,
                packet,
                bounded_decision_path=decision_path,
                bounded_gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("bounded_acceptance_true", [issue["id"] for issue in report["issues"]])

    def test_rejects_seed_drift_between_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            gate["summary"]["random_seed"] = 123
            report = build_randomized_holdout_decision_index(
                decision,
                gate,
                review,
                packet,
                bounded_decision_path=decision_path,
                bounded_gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("random_seed_matches", [issue["id"] for issue in report["issues"]])

    def test_rejects_direct_promotion_widening(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(Path(tmp))
            packet["summary"]["promotion_ready"] = True
            report = build_randomized_holdout_decision_index(
                decision,
                gate,
                review,
                packet,
                bounded_decision_path=decision_path,
                bounded_gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_bounded_promotion_decision(decision_path.parent), decision_path)
            self.assertEqual(locate_randomized_holdout_bounded_promotion_gate(gate_path.parent), gate_path)
            self.assertEqual(locate_randomized_holdout_candidate_packet_review(review_path.parent), review_path)
            self.assertEqual(locate_randomized_holdout_candidate_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_decision_index(
                decision,
                gate,
                review,
                packet,
                bounded_decision_path=decision_path,
                bounded_gate_path=gate_path,
                candidate_packet_review_path=review_path,
                candidate_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_decision_index_outputs(report, root / "index")
            cli_main(
                [
                    "--bounded-decision",
                    str(decision_path.parent),
                    "--bounded-gate",
                    str(gate_path.parent),
                    "--candidate-packet-review",
                    str(review_path.parent),
                    "--candidate-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-bounded-acceptance",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_decision_index_ready=True", render_randomized_holdout_decision_index_text(report))
        self.assertIn("Source Rows", render_randomized_holdout_decision_index_markdown(report))
        self.assertIn("randomized holdout decision index", render_randomized_holdout_decision_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], Path, Path, Path, Path]:
    gate, review, packet, gate_path, review_path, packet_path = ready_decision_inputs(root / "decision-source")
    decision = build_randomized_holdout_bounded_promotion_decision(
        gate,
        review,
        packet,
        gate_path=gate_path,
        candidate_packet_review_path=review_path,
        candidate_packet_path=packet_path,
    )
    decision_path = root / "decision" / RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME
    write_json_payload(decision, decision_path)
    return decision, gate, review, packet, decision_path, gate_path, review_path, packet_path


if __name__ == "__main__":
    unittest.main()
