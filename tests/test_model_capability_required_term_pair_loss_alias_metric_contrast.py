from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_metric_contrast import (
    build_model_capability_required_term_pair_loss_alias_metric_contrast,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_metric_contrast_artifacts import (
    render_model_capability_required_term_pair_loss_alias_metric_contrast_html,
    render_model_capability_required_term_pair_loss_alias_metric_contrast_markdown,
    render_model_capability_required_term_pair_loss_alias_metric_contrast_text,
    write_model_capability_required_term_pair_loss_alias_metric_contrast_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasMetricContrastTests(unittest.TestCase):
    def test_metric_contrast_reports_focus_normalized_delta(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_metric_contrast(
            stability_report(),
            focus_report(),
            out_dir="out",
            stability_source_path="stability.json",
            focus_source_path="focus.json",
            generated_at="2026-05-30T17:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_loss_alias_focus_normalized_delta_observed")
        self.assertEqual(report["summary"]["metric_contrast_decision"], "loss_alias_focus_introduced_normalized_full_signal")
        self.assertEqual(report["summary"]["normalization_gain_delta"], 4)
        self.assertFalse(report["summary"]["source_stable_normalized_full"])
        self.assertTrue(report["summary"]["focus_stable_normalized_full"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_metric_contrast_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_metric_contrast(
                stability_report(),
                focus_report(),
                out_dir=root / "contrast",
            )
            outputs = write_model_capability_required_term_pair_loss_alias_metric_contrast_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_metric_contrast_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_metric_contrast_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_metric_contrast_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("metric_contrast_decision=loss_alias_focus_introduced_normalized_full_signal", text)
            self.assertIn("Loss-Alias Metric Contrast", markdown)
            self.assertIn("MiniGPT loss-alias metric contrast", html)

    def test_metric_contrast_fails_when_source_report_fails(self) -> None:
        bad = stability_report()
        bad["status"] = "fail"
        report = build_model_capability_required_term_pair_loss_alias_metric_contrast(
            bad,
            focus_report(),
            out_dir="out",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias stability report is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def stability_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_loss_alias_stable_partial_hit",
        "summary": {
            "loss_alias_stability_decision": "loss_alias_stable_partial_hit",
            "loss_alias_stability_metric_decision": "loss_alias_stable_partial_hit",
            "seed_count": 2,
            "heldout_loss_alias_full_seed_count": 1,
            "heldout_loss_alias_normalized_full_seed_count": 1,
            "stable_loss_alias_full_coverage": False,
            "stable_loss_alias_normalized_full_coverage": False,
            "normalization_gain_count": 0,
        },
    }


def focus_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_loss_alias_focus_normalized_support_signal",
        "summary": {
            "loss_alias_focus_decision": "loss_alias_focus_no_repair",
            "loss_alias_focus_metric_decision": "loss_alias_focus_strict_miss_normalized_support_full_signal",
            "seed_count": 1,
            "support_full_seed_count": 0,
            "support_normalized_full_seed_count": 1,
            "stable_support_full_coverage": False,
            "stable_support_normalized_full_coverage": True,
            "normalization_gain_count": 4,
        },
    }
