from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_surface_mismatch_diagnostic import (
    build_surface_mismatch_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_surface_mismatch_diagnostic_artifacts import (
    render_surface_mismatch_diagnostic_html,
    render_surface_mismatch_diagnostic_markdown,
    render_surface_mismatch_diagnostic_text,
    write_surface_mismatch_diagnostic_outputs,
)


class SurfaceMismatchDiagnosticTests(unittest.TestCase):
    def test_diagnostic_detects_direct_surface_mismatch(self) -> None:
        report = build_surface_mismatch_diagnostic(contract_report=contract_fixture(), training_report=training_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_direct_surface_mismatch_detected")
        self.assertTrue(report["summary"]["surface_mismatch_detected"])
        self.assertEqual(report["summary"]["default_missed_terms"], ["fixed", "loss"])
        self.assertEqual(report["summary"]["recommended_next_artifact"], "pair_readiness_direct_prompt_bridge_contract_patch")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_fails_when_training_already_hits_a_direct_term(self) -> None:
        training = training_fixture()
        training["replay_report"]["case_rows"][0]["continuation_hit"] = True
        training["replay_report"]["case_rows"][0]["continuation"] = "fixed"
        report = build_surface_mismatch_diagnostic(contract_report=contract_fixture(), training_report=training)

        self.assertEqual(report["status"], "fail")
        self.assertIn("both_direct_terms_missed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_surface_mismatch_diagnostic(contract_report=contract_fixture(), training_report=training_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_surface_mismatch_diagnostic_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("surface_mismatch_detected=True", render_surface_mismatch_diagnostic_text(report))
        self.assertIn("Surface Mismatch Diagnostic", render_surface_mismatch_diagnostic_markdown(report))
        self.assertIn("MiniGPT surface mismatch diagnostic", render_surface_mismatch_diagnostic_html(report))


def contract_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_structure_contract_ready",
        "contract": {
            "template_family": "objective_structure_task_id_and_paired_blocks",
            "training_rows": [
                "objective=direct_term | term=fixed | prompt_surface=fixed_equals | answer=fixed",
                "objective=direct_term | term=loss | prompt_surface=loss_equals | answer=loss",
            ],
        },
        "summary": {"contract_ready": True},
    }


def training_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_no_pair_full",
        "summary": {"training_status": "pass", "pair_full_observed": False},
        "replay_report": {
            "status": "pass",
            "case_rows": [
                {
                    "profile_id": "default",
                    "term": "fixed",
                    "prompt": "fixed=",
                    "continuation": "d | | |",
                    "continuation_hit": False,
                },
                {
                    "profile_id": "default",
                    "term": "loss",
                    "prompt": "loss=",
                    "continuation": "d | | |",
                    "continuation_hit": False,
                },
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
