from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_repair_comparison import (
    build_pair_readiness_repair_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_repair_comparison_artifacts import (
    render_pair_readiness_repair_comparison_html,
    render_pair_readiness_repair_comparison_markdown,
    render_pair_readiness_repair_comparison_text,
    write_pair_readiness_repair_comparison_outputs,
)


class PairReadinessRepairComparisonTests(unittest.TestCase):
    def test_comparison_reports_regression(self) -> None:
        report = build_pair_readiness_repair_comparison(
            baseline_report=training_fixture(default_hits=1),
            candidate_report=training_fixture(default_hits=0),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_loss_retention_patch_regressed")
        self.assertEqual(report["summary"]["default_hit_delta"], -1)
        self.assertTrue(report["summary"]["candidate_regressed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_blocks_missing_checkpoint(self) -> None:
        candidate = training_fixture(default_hits=0)
        candidate["summary"]["checkpoint_exists"] = False
        report = build_pair_readiness_repair_comparison(
            baseline_report=training_fixture(default_hits=1),
            candidate_report=candidate,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_readiness_repair_comparison(
            baseline_report=training_fixture(default_hits=1),
            candidate_report=training_fixture(default_hits=0),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_readiness_repair_comparison_outputs(report, Path(tmp) / "comparison")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_loss_retention_patch_regressed", render_pair_readiness_repair_comparison_text(report))
        self.assertIn("Pair-Readiness Repair Comparison", render_pair_readiness_repair_comparison_markdown(report))
        self.assertIn("MiniGPT pair-readiness repair comparison", render_pair_readiness_repair_comparison_html(report))


def training_fixture(default_hits: int) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_no_pair_full",
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": False,
            "default_continuation_hit_count": default_hits,
            "suppression_continuation_hit_count": default_hits,
        },
        "interpretation": {"model_quality_claim": "not_claimed"},
    }


if __name__ == "__main__":
    unittest.main()
