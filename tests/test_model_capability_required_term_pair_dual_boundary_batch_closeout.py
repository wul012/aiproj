from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_dual_boundary_batch_closeout import (
    build_model_capability_required_term_pair_dual_boundary_batch_closeout,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_dual_boundary_batch_closeout_artifacts import (
    render_dual_boundary_batch_closeout_html,
    render_dual_boundary_batch_closeout_markdown,
    render_dual_boundary_batch_closeout_text,
    write_dual_boundary_batch_closeout_outputs,
)


class ModelCapabilityRequiredTermPairDualBoundaryBatchCloseoutTests(unittest.TestCase):
    def test_closeout_reports_internal_stable_generation_surface_unstable(self) -> None:
        report = build_model_capability_required_term_pair_dual_boundary_batch_closeout(
            stability_report_fixture(),
            forced_choice_report_fixture(),
            generated_at="2026-06-01T14:40:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_dual_boundary_internal_stable_generation_surface_unstable")
        self.assertEqual(report["summary"]["generation_pair_full_seed_count"], 2)
        self.assertEqual(report["summary"]["internal_pair_full_seed_count"], 3)
        self.assertEqual(report["summary"]["internal_only_seed_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_reports_promotion_ready_when_both_layers_stable(self) -> None:
        stability = stability_report_fixture()
        for row in stability["seed_rows"]:
            row["pair_full_observed"] = True
        report = build_model_capability_required_term_pair_dual_boundary_batch_closeout(stability, forced_choice_report_fixture())

        self.assertEqual(report["decision"], "required_term_pair_dual_boundary_ready_for_candidate_promotion")
        self.assertTrue(report["summary"]["promotion_ready"])

    def test_closeout_fails_on_bad_source_status(self) -> None:
        stability = stability_report_fixture()
        stability["status"] = "fail"
        report = build_model_capability_required_term_pair_dual_boundary_batch_closeout(stability, forced_choice_report_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("source seed stability report is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_dual_boundary_batch_closeout(
                stability_report_fixture(),
                forced_choice_report_fixture(),
            )
            outputs = write_dual_boundary_batch_closeout_outputs(report, root / "closeout")
            text = render_dual_boundary_batch_closeout_text(report)
            markdown = render_dual_boundary_batch_closeout_markdown(report)
            html = render_dual_boundary_batch_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("promotion_ready=False", text)
            self.assertIn("Dual-Boundary Batch Closeout", markdown)
            self.assertIn("MiniGPT dual-boundary batch closeout", html)


def stability_report_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_aligned_candidate_partial_stability",
        "summary": {"seed_count": 3, "pair_full_seed_count": 2},
        "seed_rows": [
            {
                "seed": 1535,
                "decision": "required_term_pair_coexistence_refresh_pair_full_observed",
                "pair_full_observed": True,
            },
            {
                "seed": 2535,
                "decision": "required_term_pair_coexistence_refresh_no_pair_full",
                "pair_full_observed": False,
            },
            {
                "seed": 3535,
                "decision": "required_term_pair_coexistence_refresh_pair_full_observed",
                "pair_full_observed": True,
            },
        ],
    }


def forced_choice_report_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "refresh_forced_choice_internal_pair_match",
        "summary": {"forced_choice_full_match_source_count": 3},
        "source_summaries": [
            {
                "source_label": "dual-boundary-seed-1535",
                "expected_best_terms": ["fixed", "loss"],
                "forced_choice_full_match": True,
            },
            {
                "source_label": "dual-boundary-seed-2535",
                "expected_best_terms": ["fixed", "loss"],
                "forced_choice_full_match": True,
            },
            {
                "source_label": "dual-boundary-seed-3535",
                "expected_best_terms": ["fixed", "loss"],
                "forced_choice_full_match": True,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
