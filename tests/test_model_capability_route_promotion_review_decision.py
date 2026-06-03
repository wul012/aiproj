from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_release_packet_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME,
    build_model_capability_route_promotion_release_packet_review,
)
from minigpt.model_capability_route_promotion_review_decision import (
    build_model_capability_route_promotion_review_decision,
    locate_route_promotion_release_packet_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_review_decision_artifacts import (
    render_model_capability_route_promotion_review_decision_html,
    render_model_capability_route_promotion_review_decision_markdown,
    render_model_capability_route_promotion_review_decision_text,
    write_model_capability_route_promotion_review_decision_outputs,
)
from scripts.decide_model_capability_route_promotion_review import main as cli_main
from tests.test_model_capability_route_promotion_release_packet_review import ready_release_packet


def ready_packet_review(root: Path) -> tuple[dict, Path]:
    packet, packet_path = ready_release_packet(root)
    review = build_model_capability_route_promotion_release_packet_review(packet, release_packet_path=packet_path)
    review_dir = root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME
    review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    return review, review_path


class ModelCapabilityRoutePromotionReviewDecisionTests(unittest.TestCase):
    def test_decision_accepts_ready_packet_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_review(Path(tmp))
            report = build_model_capability_route_promotion_review_decision(review, release_packet_review_path=review_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_final_review_accepted")
        self.assertTrue(report["summary"]["route_promotion_review_decision_ready"])
        self.assertEqual(report["summary"]["final_decision"], "accept_bounded_route_promotion")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decision_fails_when_review_scope_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, _ = ready_packet_review(Path(tmp))
            review["review"]["review_scope"] = "production_release_review"

            report = build_model_capability_route_promotion_review_decision(review)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_scope_bounded", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_packet_review(root)
            self.assertEqual(locate_route_promotion_release_packet_review(review_path.parent), review_path)

            report = build_model_capability_route_promotion_review_decision(review, release_packet_review_path=review_path)
            outputs = write_model_capability_route_promotion_review_decision_outputs(report, root / "decision")
            cli_main(["--release-packet-review", str(review_path.parent), "--out-dir", str(root / "cli-decision"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("route_promotion_review_decision_ready=True", render_model_capability_route_promotion_review_decision_text(report))
        self.assertIn("accept_bounded_route_promotion", render_model_capability_route_promotion_review_decision_markdown(report))
        self.assertIn("route promotion review decision", render_model_capability_route_promotion_review_decision_html(report))


if __name__ == "__main__":
    unittest.main()
