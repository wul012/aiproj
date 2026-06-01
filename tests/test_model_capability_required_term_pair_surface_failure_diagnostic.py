from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_failure_diagnostic import (
    build_model_capability_required_term_pair_surface_failure_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_failure_diagnostic_artifacts import (
    render_surface_failure_diagnostic_html,
    render_surface_failure_diagnostic_markdown,
    render_surface_failure_diagnostic_text,
    write_surface_failure_diagnostic_outputs,
)


class SurfaceFailureDiagnosticTests(unittest.TestCase):
    def test_diagnostic_isolates_single_surface_failure_term(self) -> None:
        report = build_model_capability_required_term_pair_surface_failure_diagnostic(
            stability_report_fixture(),
            forced_choice_report_fixture(),
            generated_at="2026-06-02T00:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_single_term_surface_failure_isolated")
        self.assertEqual(report["summary"]["surface_failure_seeds"], [2535])
        self.assertEqual(report["summary"]["surface_failure_terms"], ["loss"])
        self.assertEqual(report["seed_rows"][1]["dominant_failure_term"], "loss")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_no_surface_failure_when_generation_and_internal_align(self) -> None:
        stability = stability_report_fixture()
        stability["seed_rows"][1]["pair_full_observed"] = True
        stability["seed_reports"][1]["replay_report"]["variant_rows"][0]["missed_terms"] = []
        stability["seed_reports"][1]["replay_report"]["variant_rows"][0]["hit_terms"] = ["fixed", "loss"]
        report = build_model_capability_required_term_pair_surface_failure_diagnostic(stability, forced_choice_report_fixture())

        self.assertEqual(report["decision"], "required_term_pair_surface_failure_not_observed")
        self.assertEqual(report["summary"]["surface_failure_seed_count"], 0)

    def test_bad_source_status_fails(self) -> None:
        stability = stability_report_fixture()
        stability["status"] = "fail"
        report = build_model_capability_required_term_pair_surface_failure_diagnostic(stability, forced_choice_report_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("source seed stability report is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_failure_diagnostic(
                stability_report_fixture(),
                forced_choice_report_fixture(),
            )
            outputs = write_surface_failure_diagnostic_outputs(report, root / "surface-failure")
            text = render_surface_failure_diagnostic_text(report)
            markdown = render_surface_failure_diagnostic_markdown(report)
            html = render_surface_failure_diagnostic_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("surface_failure_terms=['loss']", text)
            self.assertIn("Surface Failure Diagnostic", markdown)
            self.assertIn("MiniGPT surface failure diagnostic", html)


def stability_report_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_aligned_candidate_partial_stability",
        "seed_rows": [
            {"seed": 1535, "pair_full_observed": True},
            {"seed": 2535, "pair_full_observed": False},
        ],
        "seed_reports": [
            seed_report(1535, hit_terms=["fixed", "loss"], missed_terms=[], preview="loss"),
            seed_report(2535, hit_terms=["fixed"], missed_terms=["loss"], preview=" candidate l"),
        ],
    }


def forced_choice_report_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "refresh_forced_choice_internal_pair_match",
        "source_summaries": [
            {"source_label": "dual-boundary-seed-1535", "expected_best_terms": ["fixed", "loss"], "forced_choice_full_match": True},
            {"source_label": "dual-boundary-seed-2535", "expected_best_terms": ["fixed", "loss"], "forced_choice_full_match": True},
        ],
    }


def seed_report(seed: int, *, hit_terms: list[str], missed_terms: list[str], preview: str) -> dict[str, object]:
    return {
        "settings": {"seed": seed},
        "replay_report": {
            "variant_rows": [
                {
                    "variant_id": "coexistence-refresh",
                    "profile_id": "default",
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                }
            ],
            "case_rows": [
                {"term": "loss", "continuation_preview": preview, "generated_preview": "loss=" + preview},
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
