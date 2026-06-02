from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic import (
    build_pair_prompt_transfer_regression_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic_artifacts import (
    render_pair_prompt_transfer_regression_diagnostic_html,
    render_pair_prompt_transfer_regression_diagnostic_markdown,
    render_pair_prompt_transfer_regression_diagnostic_text,
    write_pair_prompt_transfer_regression_diagnostic_outputs,
)


class PairPromptTransferRegressionDiagnosticTests(unittest.TestCase):
    def test_diagnostic_closes_regressed_transfer_route(self) -> None:
        report = build_pair_prompt_transfer_regression_diagnostic(
            direct_completion_training_report=training_fixture(["fixed", "loss"], [], 2, pair_full=True),
            pair_probe_replay_report=pair_probe_fixture(exact_pair_full=False),
            transfer_training_report=training_fixture(["loss"], ["fixed"], 1, pair_full=False),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_pair_prompt_transfer_regressed_stop_route")
        self.assertEqual(report["summary"]["transfer_hit_delta_from_direct"], -1)
        self.assertTrue(report["summary"]["fixed_regressed"])
        self.assertTrue(report["summary"]["transfer_route_closed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_reports_candidate_when_transfer_is_pair_full(self) -> None:
        report = build_pair_prompt_transfer_regression_diagnostic(
            direct_completion_training_report=training_fixture(["fixed", "loss"], [], 2, pair_full=True),
            pair_probe_replay_report=pair_probe_fixture(exact_pair_full=False),
            transfer_training_report=training_fixture(["fixed", "loss"], [], 2, pair_full=True),
        )

        self.assertEqual(report["decision"], "pair_readiness_pair_prompt_transfer_candidate_found")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "comparison_pair_full_candidate")

    def test_diagnostic_fails_for_missing_transfer_checkpoint(self) -> None:
        transfer = training_fixture(["loss"], ["fixed"], 1, pair_full=False)
        transfer["summary"]["checkpoint_exists"] = False
        report = build_pair_prompt_transfer_regression_diagnostic(
            direct_completion_training_report=training_fixture(["fixed", "loss"], [], 2, pair_full=True),
            pair_probe_replay_report=pair_probe_fixture(exact_pair_full=False),
            transfer_training_report=transfer,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("pair-prompt-transfer_checkpoint_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_prompt_transfer_regression_diagnostic(
            direct_completion_training_report=training_fixture(["fixed", "loss"], [], 2, pair_full=True),
            pair_probe_replay_report=pair_probe_fixture(exact_pair_full=False),
            transfer_training_report=training_fixture(["loss"], ["fixed"], 1, pair_full=False),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_prompt_transfer_regression_diagnostic_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("transfer_route_closed=True", render_pair_prompt_transfer_regression_diagnostic_text(report))
        self.assertIn("Pair Prompt Transfer Regression Diagnostic", render_pair_prompt_transfer_regression_diagnostic_markdown(report))
        self.assertIn("MiniGPT pair prompt transfer regression diagnostic", render_pair_prompt_transfer_regression_diagnostic_html(report))


def training_fixture(hit_terms: list[str], missed_terms: list[str], hit_count: int, *, pair_full: bool) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_pair_full_observed" if pair_full else "pair_readiness_training_no_pair_full",
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": pair_full,
            "default_continuation_hit_count": hit_count,
        },
        "replay_report": {
            "variant_rows": [
                {
                    "profile_id": "default",
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "hit_count": hit_count,
                    "pair_full_hit": pair_full,
                }
            ]
        },
    }


def pair_probe_fixture(*, exact_pair_full: bool) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_completion_pair_probe_replay_ready"
        if exact_pair_full
        else "pair_readiness_direct_completion_pair_probe_replay_not_ready",
        "summary": {
            "required_pair_full_count": 1 if exact_pair_full else 0,
            "required_all_pair_full": exact_pair_full,
            "exact_heldout_pair_full": exact_pair_full,
        },
    }


if __name__ == "__main__":
    unittest.main()
