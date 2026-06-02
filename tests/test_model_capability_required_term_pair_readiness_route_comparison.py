from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_route_comparison import (
    build_pair_readiness_route_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_route_comparison_artifacts import (
    render_pair_readiness_route_comparison_html,
    render_pair_readiness_route_comparison_markdown,
    render_pair_readiness_route_comparison_text,
    write_pair_readiness_route_comparison_outputs,
)


class PairReadinessRouteComparisonTests(unittest.TestCase):
    def test_comparison_reports_failure_shape_change_without_promotion(self) -> None:
        report = build_pair_readiness_route_comparison(
            baseline_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
            loss_retention_report=training_fixture(hit_terms=[], missed_terms=["fixed", "loss"], hit_count=0),
            structured_template_report=training_fixture(hit_terms=["loss"], missed_terms=["fixed"], hit_count=1),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_structured_template_changes_failure_shape_without_pair_full")
        self.assertEqual(report["summary"]["structured_vs_baseline_default_hit_delta"], 0)
        self.assertEqual(report["summary"]["structured_vs_loss_retention_default_hit_delta"], 1)
        self.assertTrue(report["summary"]["failure_shape_changed"])
        self.assertEqual(report["interpretation"]["model_quality_claim"], "comparison_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_blocks_missing_checkpoint(self) -> None:
        structured = training_fixture(hit_terms=["loss"], missed_terms=["fixed"], hit_count=1)
        structured["summary"]["checkpoint_exists"] = False
        report = build_pair_readiness_route_comparison(
            baseline_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
            loss_retention_report=training_fixture(hit_terms=[], missed_terms=["fixed", "loss"], hit_count=0),
            structured_template_report=structured,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_comparison_reports_pair_full_candidate(self) -> None:
        structured = training_fixture(hit_terms=["fixed", "loss"], missed_terms=[], hit_count=2, pair_full=True)
        report = build_pair_readiness_route_comparison(
            baseline_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
            loss_retention_report=training_fixture(hit_terms=[], missed_terms=["fixed", "loss"], hit_count=0),
            structured_template_report=structured,
        )

        self.assertEqual(report["decision"], "pair_readiness_route_pair_full_candidate_found")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "comparison_pair_full_candidate")

    def test_comparison_reports_fixed_recovery_returning_to_baseline(self) -> None:
        report = build_pair_readiness_route_comparison(
            baseline_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
            loss_retention_report=training_fixture(hit_terms=[], missed_terms=["fixed", "loss"], hit_count=0),
            structured_template_report=training_fixture(hit_terms=["loss"], missed_terms=["fixed"], hit_count=1),
            fixed_recovery_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full")
        self.assertEqual(report["summary"]["route_count"], 4)
        self.assertEqual(report["summary"]["fixed_recovery_vs_structured_default_hit_delta"], 0)
        self.assertTrue(report["summary"]["fixed_recovery_returns_to_baseline"])
        self.assertEqual(report["interpretation"]["next_action"], "close single-sided fixed/loss row patching and test capacity or objective structure instead")

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_readiness_route_comparison(
            baseline_report=training_fixture(hit_terms=["fixed"], missed_terms=["loss"], hit_count=1),
            loss_retention_report=training_fixture(hit_terms=[], missed_terms=["fixed", "loss"], hit_count=0),
            structured_template_report=training_fixture(hit_terms=["loss"], missed_terms=["fixed"], hit_count=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_readiness_route_comparison_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_structured_template_changes_failure_shape_without_pair_full", render_pair_readiness_route_comparison_text(report))
        self.assertIn("Pair-Readiness Route Comparison", render_pair_readiness_route_comparison_markdown(report))
        self.assertIn("MiniGPT pair-readiness route comparison", render_pair_readiness_route_comparison_html(report))


def training_fixture(*, hit_terms: list[str], missed_terms: list[str], hit_count: int, pair_full: bool = False) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_pair_full_observed" if pair_full else "pair_readiness_training_no_pair_full",
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": pair_full,
            "default_continuation_hit_count": hit_count,
            "suppression_continuation_hit_count": hit_count,
        },
        "interpretation": {"model_quality_claim": "direct_pair_probe_hit" if pair_full else "not_claimed"},
        "replay_report": {
            "variant_rows": [
                {
                    "profile_id": "default",
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "hit_count": hit_count,
                    "pair_full_hit": pair_full,
                },
                {
                    "profile_id": "suppress_newline_tokens",
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "hit_count": hit_count,
                    "pair_full_hit": pair_full,
                },
            ]
        },
    }


if __name__ == "__main__":
    unittest.main()
