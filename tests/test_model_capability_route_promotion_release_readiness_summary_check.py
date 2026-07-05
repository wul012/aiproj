from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import minigpt
from minigpt.model_capability_route_promotion_release_readiness_summary import (
    build_model_capability_route_promotion_release_readiness_summary,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_artifacts import (
    write_model_capability_route_promotion_release_readiness_summary_outputs,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_check import (
    build_model_capability_route_promotion_release_readiness_summary_check,
    locate_route_promotion_release_readiness_summary,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_check_artifacts import (
    render_model_capability_route_promotion_release_readiness_summary_check_html,
    render_model_capability_route_promotion_release_readiness_summary_check_markdown,
    render_model_capability_route_promotion_release_readiness_summary_check_text,
    write_model_capability_route_promotion_release_readiness_summary_check_outputs,
)
from scripts.check_model_capability_route_promotion_release_readiness_summary import main as cli_main
from tests.test_model_capability_route_promotion_release_readiness_summary import ready_release_readiness_inputs


def ready_summary(root: Path) -> tuple[dict, Path]:
    packet, packet_path, review, review_path, snapshot, snapshot_path = ready_release_readiness_inputs(root / "inputs")
    report = build_model_capability_route_promotion_release_readiness_summary(
        packet,
        review,
        snapshot,
        release_packet_path=packet_path,
        release_packet_review_path=review_path,
        governance_snapshot_path=snapshot_path,
    )
    outputs = write_model_capability_route_promotion_release_readiness_summary_outputs(report, root / "summary")
    return report, Path(outputs["json"])


class ModelCapabilityRoutePromotionReleaseReadinessSummaryCheckTests(unittest.TestCase):
    def test_root_facade_exports_release_readiness_summary_check(self) -> None:
        self.assertIs(
            minigpt.build_model_capability_route_promotion_release_readiness_summary_check,
            build_model_capability_route_promotion_release_readiness_summary_check,
        )
        self.assertIs(
            minigpt.write_model_capability_route_promotion_release_readiness_summary_check_outputs,
            write_model_capability_route_promotion_release_readiness_summary_check_outputs,
        )

    def test_contract_check_passes_for_ready_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, summary_path = ready_summary(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_summary_check(summary, release_readiness_summary_path=summary_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_readiness_summary_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["source_digest_count"], 3)
        self.assertEqual(report["summary"]["active_routes"], ["objective_level_contrast"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_source_path_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = ready_summary(Path(tmp))
            summary["source_rows"][0]["path"] = str(Path(tmp) / "missing-packet.json")
            summary["source_rows"][0]["exists"] = True
            report = build_model_capability_route_promotion_release_readiness_summary_check(summary)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_files_digestible", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_check_fails_when_claim_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = ready_summary(Path(tmp))
            summary["summary"]["model_quality_claim"] = "production_model_quality"
            summary["boundary_claim"]["model_quality_claim"] = "production_model_quality"
            summary["boundary_claim"]["claims"] = ["production_model_quality"] * 3
            summary["boundary_claim"]["claim_bounded"] = False
            report = build_model_capability_route_promotion_release_readiness_summary_check(summary)

        self.assertEqual(report["status"], "fail")
        self.assertIn("claim_bounded", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary, summary_path = ready_summary(root)
            self.assertEqual(locate_route_promotion_release_readiness_summary(summary_path.parent), summary_path)

            report = build_model_capability_route_promotion_release_readiness_summary_check(summary, release_readiness_summary_path=summary_path)
            outputs = write_model_capability_route_promotion_release_readiness_summary_check_outputs(report, root / "check")
            cli_main(
                [
                    "--release-readiness-summary",
                    str(summary_path.parent),
                    "--out-dir",
                    str(root / "cli-check"),
                    "--require-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("contract_check_ready=True", render_model_capability_route_promotion_release_readiness_summary_check_text(report))
        self.assertIn("Source Digests", render_model_capability_route_promotion_release_readiness_summary_check_markdown(report))
        self.assertIn("release readiness summary contract check", render_model_capability_route_promotion_release_readiness_summary_check_html(report))


if __name__ == "__main__":
    unittest.main()
