from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import minigpt
from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import (
    build_model_capability_route_promotion_release_readiness_downstream_receipt,
    locate_route_promotion_release_readiness_summary_check,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt_artifacts import (
    render_model_capability_route_promotion_release_readiness_downstream_receipt_html,
    render_model_capability_route_promotion_release_readiness_downstream_receipt_markdown,
    render_model_capability_route_promotion_release_readiness_downstream_receipt_text,
    write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_check import (
    build_model_capability_route_promotion_release_readiness_summary_check,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_check_artifacts import (
    write_model_capability_route_promotion_release_readiness_summary_check_outputs,
)
from scripts.build_model_capability_route_promotion_release_readiness_downstream_receipt import main as cli_main
from tests.test_model_capability_route_promotion_release_readiness_summary_check import ready_summary


def ready_checked_summary(root: Path) -> tuple[dict, Path]:
    summary, summary_path = ready_summary(root / "summary-source")
    check = build_model_capability_route_promotion_release_readiness_summary_check(summary, release_readiness_summary_path=summary_path)
    outputs = write_model_capability_route_promotion_release_readiness_summary_check_outputs(check, root / "check")
    return check, Path(outputs["json"])


class ModelCapabilityRoutePromotionReleaseReadinessDownstreamReceiptTests(unittest.TestCase):
    def test_root_facade_exports_downstream_receipt(self) -> None:
        self.assertIs(
            minigpt.build_model_capability_route_promotion_release_readiness_downstream_receipt,
            build_model_capability_route_promotion_release_readiness_downstream_receipt,
        )
        self.assertIs(
            minigpt.write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs,
            write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs,
        )

    def test_receipt_grants_checked_release_readiness_summary_to_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check, check_path = ready_checked_summary(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_downstream_receipt(
                check,
                consumer_name="release-readiness-index-builder",
                route_id="objective_level_contrast",
                release_readiness_summary_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_readiness_downstream_receipt_granted")
        self.assertTrue(report["summary"]["downstream_receipt_ready"])
        self.assertEqual(report["summary"]["granted_scope"], "bounded_route_promotion_release_governance_only")
        self.assertEqual(report["receipt"]["source_digest_count"], 3)
        self.assertIn("production_model_quality_claim", report["receipt"]["blocked_uses"])
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 0)

    def test_receipt_blocks_unknown_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check, _ = ready_checked_summary(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_downstream_receipt(
                check,
                consumer_name="release-readiness-index-builder",
                route_id="missing_route",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("route_id_in_checked_summary", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 1)

    def test_receipt_blocks_unbounded_requested_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check, _ = ready_checked_summary(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_downstream_receipt(
                check,
                consumer_name="release-readiness-index-builder",
                route_id="objective_level_contrast",
                requested_scope="production_model_release",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_scope_allowed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            check, check_path = ready_checked_summary(root)
            self.assertEqual(locate_route_promotion_release_readiness_summary_check(check_path.parent), check_path)

            report = build_model_capability_route_promotion_release_readiness_downstream_receipt(
                check,
                consumer_name="release-readiness-index-builder",
                route_id="objective_level_contrast",
                release_readiness_summary_check_path=check_path,
            )
            outputs = write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs(report, root / "receipt")
            cli_main(
                [
                    "--release-readiness-summary-check",
                    str(check_path.parent),
                    "--consumer-name",
                    "release-readiness-index-builder",
                    "--route-id",
                    "objective_level_contrast",
                    "--out-dir",
                    str(root / "cli-receipt"),
                    "--require-receipt-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("downstream_receipt_ready=True", render_model_capability_route_promotion_release_readiness_downstream_receipt_text(report))
        self.assertIn("Source Digests", render_model_capability_route_promotion_release_readiness_downstream_receipt_markdown(report))
        self.assertIn("downstream receipt", render_model_capability_route_promotion_release_readiness_downstream_receipt_html(report))


if __name__ == "__main__":
    unittest.main()
