from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_release_packet import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME,
    build_model_capability_route_promotion_release_packet,
)
from minigpt.model_capability_route_promotion_release_packet_review import (
    build_model_capability_route_promotion_release_packet_review,
    locate_route_promotion_release_packet,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_packet_review_artifacts import (
    render_model_capability_route_promotion_release_packet_review_html,
    render_model_capability_route_promotion_release_packet_review_markdown,
    render_model_capability_route_promotion_release_packet_review_text,
    write_model_capability_route_promotion_release_packet_review_outputs,
)
from scripts.review_model_capability_route_promotion_release_packet import main as cli_main
from tests.test_model_capability_route_promotion_release_packet import ready_packet_inputs


def ready_release_packet(root: Path) -> tuple[dict, Path]:
    portfolio, monitor, gate, portfolio_path, monitor_path, gate_path = ready_packet_inputs(root)
    packet = build_model_capability_route_promotion_release_packet(
        portfolio,
        monitor,
        gate,
        portfolio_path=portfolio_path,
        regression_monitor_path=monitor_path,
        gate_path=gate_path,
    )
    packet_dir = root / "packet"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME
    packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
    return packet, packet_path


class ModelCapabilityRoutePromotionReleasePacketReviewTests(unittest.TestCase):
    def test_review_passes_ready_release_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_release_packet(Path(tmp))
            report = build_model_capability_route_promotion_release_packet_review(packet, release_packet_path=packet_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_packet_review_ready")
        self.assertTrue(report["summary"]["release_packet_review_ready"])
        self.assertEqual(report["summary"]["review_scope"], "bounded_route_promotion_review_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_review_fails_when_claim_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, _ = ready_release_packet(Path(tmp))
            packet["packet"]["model_quality_claim"] = "production_model_quality"

            report = build_model_capability_route_promotion_release_packet_review(packet)

        self.assertEqual(report["status"], "fail")
        self.assertIn("claim_bounded", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_release_packet(root)
            self.assertEqual(locate_route_promotion_release_packet(packet_path.parent), packet_path)

            report = build_model_capability_route_promotion_release_packet_review(packet, release_packet_path=packet_path)
            outputs = write_model_capability_route_promotion_release_packet_review_outputs(report, root / "review")
            cli_main(["--release-packet", str(packet_path.parent), "--out-dir", str(root / "cli-review"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("release_packet_review_ready=True", render_model_capability_route_promotion_release_packet_review_text(report))
        self.assertIn("bounded_route_promotion_review_only", render_model_capability_route_promotion_release_packet_review_markdown(report))
        self.assertIn("route promotion release packet review", render_model_capability_route_promotion_release_packet_review_html(report))


if __name__ == "__main__":
    unittest.main()
