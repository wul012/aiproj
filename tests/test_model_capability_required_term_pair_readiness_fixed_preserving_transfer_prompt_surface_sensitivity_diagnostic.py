from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic import (
    build_prompt_surface_sensitivity_diagnostic,
    locate_prompt_surface_sensitivity_replay_source,
    locate_prompt_surface_sensitivity_training_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic_artifacts import (
    render_prompt_surface_sensitivity_diagnostic_html,
    render_prompt_surface_sensitivity_diagnostic_markdown,
    render_prompt_surface_sensitivity_diagnostic_text,
    write_prompt_surface_sensitivity_diagnostic_outputs,
)


class PromptSurfaceSensitivityDiagnosticTests(unittest.TestCase):
    def test_diagnostic_finds_surface_sensitivity(self) -> None:
        report = build_prompt_surface_sensitivity_diagnostic(training_fixture(), partial_replay_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found")
        self.assertTrue(report["summary"]["surface_sensitivity_observed"])
        self.assertTrue(report["summary"]["promotion_blocked"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_ready_when_required_surface_passes(self) -> None:
        replay = partial_replay_fixture()
        replay["summary"]["required_all_pair_full"] = True
        replay["summary"]["exact_heldout_pair_full"] = True
        replay["replay_rows"][0]["replay_pair_full"] = True
        report = build_prompt_surface_sensitivity_diagnostic(training_fixture(), replay)

        self.assertEqual(report["decision"], "pair_readiness_fixed_preserving_transfer_prompt_surface_ready_for_promotion_guard")
        self.assertFalse(report["summary"]["promotion_blocked"])

    def test_diagnostic_fails_for_bad_training_source(self) -> None:
        training = training_fixture()
        training["status"] = "fail"
        report = build_prompt_surface_sensitivity_diagnostic(training, partial_replay_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_locators_accept_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            training_source = locate_prompt_surface_sensitivity_training_source(tmp)
            replay_source = locate_prompt_surface_sensitivity_replay_source(tmp)

        self.assertEqual(training_source.name, "model_capability_required_term_pair_readiness_training_run.json")
        self.assertEqual(replay_source.name, "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json")

    def test_outputs_render_all_formats(self) -> None:
        report = build_prompt_surface_sensitivity_diagnostic(training_fixture(), partial_replay_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_prompt_surface_sensitivity_diagnostic_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("surface_sensitivity_observed=True", render_prompt_surface_sensitivity_diagnostic_text(report))
        self.assertIn("Prompt-Surface Sensitivity Diagnostic", render_prompt_surface_sensitivity_diagnostic_markdown(report))
        self.assertIn("MiniGPT prompt-surface sensitivity diagnostic", render_prompt_surface_sensitivity_diagnostic_html(report))


def training_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_pair_full_observed",
        "summary": {"pair_full_observed": True, "default_continuation_hit_count": 2},
    }


def partial_replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial",
        "summary": {
            "exact_heldout_pair_full": False,
            "required_all_pair_full": False,
            "pair_full_count": 1,
        },
        "replay_rows": [
            {
                "spec_id": "exact-heldout-pair",
                "prompt": "fixed=|loss=",
                "required_for_ready": True,
                "replay_pair_full": False,
                "default_continuation_hit_count": 1,
                "suppression_continuation_hit_count": 1,
            },
            {
                "spec_id": "arrow-heldout-pair",
                "prompt": "fixed -> | loss ->",
                "required_for_ready": False,
                "replay_pair_full": True,
                "default_continuation_hit_count": 2,
                "suppression_continuation_hit_count": 2,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
