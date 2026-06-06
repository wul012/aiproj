from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_publication_packet_review import (
    RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME,
    build_randomized_holdout_acceptance_publication_packet_review,
    locate_randomized_holdout_acceptance_publication_packet,
    resolve_exit_code,
)
from minigpt.randomized_holdout_acceptance_publication_packet_review_artifacts import (
    render_randomized_holdout_acceptance_publication_packet_review_html,
    render_randomized_holdout_acceptance_publication_packet_review_markdown,
    render_randomized_holdout_acceptance_publication_packet_review_text,
    write_randomized_holdout_acceptance_publication_packet_review_outputs,
)
from minigpt.randomized_holdout_acceptance_publication_packet_artifacts import write_randomized_holdout_acceptance_publication_packet_outputs
from scripts.review_randomized_holdout_acceptance_publication_packet import main as cli_main
from tests.test_randomized_holdout_acceptance_publication_packet import ready_publication_inputs
from minigpt.randomized_holdout_acceptance_publication_packet import build_randomized_holdout_acceptance_publication_packet


class RandomizedHoldoutAcceptancePublicationPacketReviewTests(unittest.TestCase):
    def test_review_accepts_bounded_publication_packet_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_acceptance_publication_packet_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_acceptance_publication_packet_review_ready"])
        self.assertTrue(report["summary"]["approved_for_bounded_publication"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["review_scope"], "bounded_randomized_holdout_publication_review_only")
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_decision")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_publication_approval=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_review_fails_when_allowed_use_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_review_inputs(Path(tmp))
            packet["summary"]["allowed_use"] = "production_promotion"
            packet["packet"]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_bounded", [issue["id"] for issue in report["issues"]])

    def test_review_fails_when_direct_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_review_inputs(Path(tmp))
            packet["summary"]["promotion_ready"] = True
            packet["packet"]["promotion_ready"] = True
            report = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_acceptance_publication_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_acceptance_publication_packet_review(packet, publication_packet_path=packet_path)
            outputs = write_randomized_holdout_acceptance_publication_packet_review_outputs(report, root / "review")
            cli_main(
                [
                    "--publication-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-publication-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_acceptance_publication_packet_review_ready=True", render_randomized_holdout_acceptance_publication_packet_review_text(report))
        self.assertIn("bounded_randomized_holdout_publication_review_only", render_randomized_holdout_acceptance_publication_packet_review_markdown(report))
        self.assertIn("publication packet review", render_randomized_holdout_acceptance_publication_packet_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    summary, check, summary_path, check_path = ready_publication_inputs(root / "publication-source")
    packet = build_randomized_holdout_acceptance_publication_packet(
        summary,
        check,
        acceptance_summary_path=summary_path,
        contract_check_path=check_path,
    )
    outputs = write_randomized_holdout_acceptance_publication_packet_outputs(packet, root / "packet")
    return packet, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
