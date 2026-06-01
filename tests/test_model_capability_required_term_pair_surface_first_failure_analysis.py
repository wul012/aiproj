from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_first_failure_analysis import (
    build_model_capability_required_term_pair_surface_first_failure_analysis,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_first_failure_analysis_artifacts import (
    render_surface_first_failure_analysis_html,
    render_surface_first_failure_analysis_markdown,
    render_surface_first_failure_analysis_text,
    write_surface_first_failure_analysis_outputs,
)


class SurfaceFirstFailureAnalysisTests(unittest.TestCase):
    def test_analysis_confirms_fixed_collapse(self) -> None:
        report = build_model_capability_required_term_pair_surface_first_failure_analysis(
            refresh_report=refresh_report(["fixed"]),
            forced_choice_report=forced_choice_report(["fixed"]),
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "surface_first_schedule_fixed_collapse_confirmed")
        self.assertTrue(report["summary"]["fixed_collapse_confirmed"])
        self.assertEqual(report["summary"]["next_objective"], "loss_guarded_surface_schedule_repair")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_analysis_fails_on_bad_input_status(self) -> None:
        bad_refresh = refresh_report(["fixed"])
        bad_refresh["status"] = "fail"
        report = build_model_capability_required_term_pair_surface_first_failure_analysis(
            refresh_report=bad_refresh,
            forced_choice_report=forced_choice_report(["fixed"]),
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("surface-first refresh status is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_surface_first_failure_analysis(
                refresh_report=refresh_report(["fixed"]),
                forced_choice_report=forced_choice_report(["fixed"]),
                comparison_report=comparison_report(),
                route_decision_report=route_decision_report(),
            )
            outputs = write_surface_first_failure_analysis_outputs(report, Path(tmp) / "analysis")
            text = render_surface_first_failure_analysis_text(report)
            markdown = render_surface_first_failure_analysis_markdown(report)
            html = render_surface_first_failure_analysis_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("fixed_collapse_confirmed=True", text)
            self.assertIn("Surface-First Failure Analysis", markdown)
            self.assertIn("MiniGPT surface-first failure analysis", html)


def refresh_report(hit_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "replay_report": {
            "case_rows": [
                {"term": "fixed", "continuation_hit": "fixed" in hit_terms},
                {"term": "loss", "continuation_hit": "loss" in hit_terms},
            ]
        },
    }


def forced_choice_report(expected_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "prompt_summaries": [
            {"source_label": "surface-first-schedule", "prompt_term": "fixed", "expected_best": "fixed" in expected_terms},
            {"source_label": "surface-first-schedule", "prompt_term": "loss", "expected_best": "loss" in expected_terms},
        ],
    }


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "source_rows": [
            {
                "source_label": "surface-first-schedule",
                "alignment_class": "fixed_only_aligned_partial",
            }
        ],
    }


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "selected_generation_route_label": "loss-internal-joint-cycle",
            "internal_anchor_route_label": "joint-cycle-internal-repair",
        },
    }


if __name__ == "__main__":
    unittest.main()
