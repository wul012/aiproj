from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import minigpt
from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import (
    build_model_capability_route_promotion_release_readiness_downstream_receipt,
)
from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt_artifacts import (
    write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs,
)
from minigpt.model_capability_route_promotion_release_readiness_receipt_index import (
    build_model_capability_route_promotion_release_readiness_receipt_index,
    locate_route_promotion_release_readiness_downstream_receipt,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_receipt_index_artifacts import (
    render_model_capability_route_promotion_release_readiness_receipt_index_html,
    render_model_capability_route_promotion_release_readiness_receipt_index_markdown,
    render_model_capability_route_promotion_release_readiness_receipt_index_text,
    write_model_capability_route_promotion_release_readiness_receipt_index_outputs,
)
from scripts.build_model_capability_route_promotion_release_readiness_receipt_index import main as cli_main
from tests.test_model_capability_route_promotion_release_readiness_downstream_receipt import ready_checked_summary


def ready_downstream_receipt(root: Path) -> tuple[dict, Path]:
    check, check_path = ready_checked_summary(root / "check-source")
    receipt = build_model_capability_route_promotion_release_readiness_downstream_receipt(
        check,
        consumer_name="release-readiness-index-builder",
        route_id="objective_level_contrast",
        release_readiness_summary_check_path=check_path,
    )
    outputs = write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs(receipt, root / "receipt")
    return receipt, Path(outputs["json"])


class ModelCapabilityRoutePromotionReleaseReadinessReceiptIndexTests(unittest.TestCase):
    def test_root_facade_exports_receipt_index(self) -> None:
        self.assertIs(
            minigpt.build_model_capability_route_promotion_release_readiness_receipt_index,
            build_model_capability_route_promotion_release_readiness_receipt_index,
        )
        self.assertIs(
            minigpt.write_model_capability_route_promotion_release_readiness_receipt_index_outputs,
            write_model_capability_route_promotion_release_readiness_receipt_index_outputs,
        )

    def test_receipt_index_is_ready_for_granted_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_downstream_receipt(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_receipt_index(
                receipt,
                downstream_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_readiness_receipt_index_ready")
        self.assertTrue(report["summary"]["receipt_index_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["route_id"], "objective_level_contrast")
        self.assertEqual(report["summary"]["source_digest_count"], 3)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(len(report["receipt_index"]["downstream_receipt_digest"]), 64)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)

    def test_receipt_index_blocks_ungranted_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            check, check_path = ready_checked_summary(root / "check-source")
            receipt = build_model_capability_route_promotion_release_readiness_downstream_receipt(
                check,
                consumer_name="release-readiness-index-builder",
                route_id="objective_level_contrast",
                requested_scope="production_model_release",
                release_readiness_summary_check_path=check_path,
            )
            outputs = write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs(receipt, root / "receipt")
            report = build_model_capability_route_promotion_release_readiness_receipt_index(
                receipt,
                downstream_receipt_path=outputs["json"],
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("downstream_receipt_passed", [issue["id"] for issue in report["issues"]])
        self.assertIn("receipt_status_granted", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True), 1)

    def test_receipt_index_blocks_missing_receipt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, _ = ready_downstream_receipt(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_receipt_index(
                receipt,
                downstream_receipt_path=Path(tmp) / "missing.json",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("downstream_receipt_file_exists", [issue["id"] for issue in report["issues"]])
        self.assertIn("downstream_receipt_digest_present", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_downstream_receipt(root)
            self.assertEqual(locate_route_promotion_release_readiness_downstream_receipt(receipt_path.parent), receipt_path)

            report = build_model_capability_route_promotion_release_readiness_receipt_index(
                receipt,
                downstream_receipt_path=receipt_path,
            )
            outputs = write_model_capability_route_promotion_release_readiness_receipt_index_outputs(report, root / "index")
            cli_main(
                [
                    "--downstream-receipt",
                    str(receipt_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("receipt_index_ready=True", render_model_capability_route_promotion_release_readiness_receipt_index_text(report))
        self.assertIn("Lookup Rows", render_model_capability_route_promotion_release_readiness_receipt_index_markdown(report))
        self.assertIn("receipt index", render_model_capability_route_promotion_release_readiness_receipt_index_html(report))


if __name__ == "__main__":
    unittest.main()
