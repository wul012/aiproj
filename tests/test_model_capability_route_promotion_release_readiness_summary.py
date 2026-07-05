from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import minigpt
from minigpt.model_capability_route_promotion_governance_snapshot import (
    build_model_capability_route_promotion_governance_snapshot,
)
from minigpt.model_capability_route_promotion_governance_snapshot_artifacts import (
    write_model_capability_route_promotion_governance_snapshot_outputs,
)
from minigpt.model_capability_route_promotion_release_packet_review import (
    build_model_capability_route_promotion_release_packet_review,
)
from minigpt.model_capability_route_promotion_release_packet_review_artifacts import (
    write_model_capability_route_promotion_release_packet_review_outputs,
)
from minigpt.model_capability_route_promotion_release_readiness_summary import (
    build_model_capability_route_promotion_release_readiness_summary,
    locate_route_promotion_governance_snapshot,
    locate_route_promotion_release_packet,
    locate_route_promotion_release_packet_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_artifacts import (
    render_model_capability_route_promotion_release_readiness_summary_html,
    render_model_capability_route_promotion_release_readiness_summary_markdown,
    render_model_capability_route_promotion_release_readiness_summary_text,
    write_model_capability_route_promotion_release_readiness_summary_outputs,
)
from scripts.summarize_model_capability_route_promotion_release_readiness import main as cli_main
from tests.test_model_capability_route_promotion_governance_snapshot import ready_snapshot_inputs
from tests.test_model_capability_route_promotion_release_packet_review import ready_release_packet


def ready_release_readiness_inputs(root: Path) -> tuple[dict, Path, dict, Path, dict, Path]:
    packet, packet_path = ready_release_packet(root / "packet-source")
    review = build_model_capability_route_promotion_release_packet_review(packet, release_packet_path=packet_path)
    review_outputs = write_model_capability_route_promotion_release_packet_review_outputs(review, root / "review")
    index, index_path, check, check_path = ready_snapshot_inputs(root / "snapshot-source")
    snapshot = build_model_capability_route_promotion_governance_snapshot(
        index,
        check,
        decision_index_path=index_path,
        index_contract_check_path=check_path,
    )
    snapshot_outputs = write_model_capability_route_promotion_governance_snapshot_outputs(snapshot, root / "snapshot")
    return packet, packet_path, review, Path(review_outputs["json"]), snapshot, Path(snapshot_outputs["json"])


class ModelCapabilityRoutePromotionReleaseReadinessSummaryTests(unittest.TestCase):
    def test_root_facade_exports_release_readiness_summary(self) -> None:
        self.assertIs(
            minigpt.build_model_capability_route_promotion_release_readiness_summary,
            build_model_capability_route_promotion_release_readiness_summary,
        )
        self.assertIs(
            minigpt.write_model_capability_route_promotion_release_readiness_summary_outputs,
            write_model_capability_route_promotion_release_readiness_summary_outputs,
        )

    def test_builds_ready_release_readiness_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, review, review_path, snapshot, snapshot_path = ready_release_readiness_inputs(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_summary(
                packet,
                review,
                snapshot,
                release_packet_path=packet_path,
                release_packet_review_path=review_path,
                governance_snapshot_path=snapshot_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_readiness_summary_ready")
        self.assertTrue(report["summary"]["release_readiness_summary_ready"])
        self.assertEqual(report["summary"]["active_routes"], ["objective_level_contrast"])
        self.assertEqual(report["summary"]["handoff_status"], "ready_for_bounded_governance_release")
        self.assertEqual(report["downstream_policy"]["allowed_scope"], "bounded_route_promotion_release_governance_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_blocks_when_route_alignment_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, review, review_path, snapshot, snapshot_path = ready_release_readiness_inputs(Path(tmp))
            snapshot["summary"]["route_ids"] = ["different_route"]
            report = build_model_capability_route_promotion_release_readiness_summary(
                packet,
                review,
                snapshot,
                release_packet_path=packet_path,
                release_packet_review_path=review_path,
                governance_snapshot_path=snapshot_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("active_routes_align", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path, review, review_path, snapshot, snapshot_path = ready_release_readiness_inputs(root)
            self.assertEqual(locate_route_promotion_release_packet(packet_path.parent), packet_path)
            self.assertEqual(locate_route_promotion_release_packet_review(review_path.parent), review_path)
            self.assertEqual(locate_route_promotion_governance_snapshot(snapshot_path.parent), snapshot_path)

            report = build_model_capability_route_promotion_release_readiness_summary(
                packet,
                review,
                snapshot,
                release_packet_path=packet_path,
                release_packet_review_path=review_path,
                governance_snapshot_path=snapshot_path,
            )
            outputs = write_model_capability_route_promotion_release_readiness_summary_outputs(report, root / "summary")
            cli_main(
                [
                    "--release-packet",
                    str(packet_path.parent),
                    "--release-packet-review",
                    str(review_path.parent),
                    "--governance-snapshot",
                    str(snapshot_path.parent),
                    "--out-dir",
                    str(root / "cli-summary"),
                    "--require-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("release_readiness_summary_ready=True", render_model_capability_route_promotion_release_readiness_summary_text(report))
        self.assertIn("Sources", render_model_capability_route_promotion_release_readiness_summary_markdown(report))
        self.assertIn("release readiness summary", render_model_capability_route_promotion_release_readiness_summary_html(report))


if __name__ == "__main__":
    unittest.main()
