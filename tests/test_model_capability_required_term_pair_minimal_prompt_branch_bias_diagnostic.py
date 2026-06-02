from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic import (
    build_minimal_prompt_branch_bias_diagnostic,
    locate_minimal_prompt_branch_bias_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic_artifacts import (
    render_minimal_prompt_branch_bias_diagnostic_html,
    render_minimal_prompt_branch_bias_diagnostic_markdown,
    render_minimal_prompt_branch_bias_diagnostic_text,
    write_minimal_prompt_branch_bias_diagnostic_outputs,
)


class MinimalPromptBranchBiasDiagnosticTests(unittest.TestCase):
    def test_diagnostic_detects_fixed_absorbing_loss(self) -> None:
        report = build_minimal_prompt_branch_bias_diagnostic(refresh_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_branch_bias_fixed_absorbs_loss")
        self.assertEqual(report["summary"]["loss_prompt_fixed_start_count"], 2)
        self.assertEqual(report["summary"]["dominant_bias"], "fixed")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_reports_pair_full_candidate(self) -> None:
        source = refresh_fixture(pair_full=True)
        for row in source["replay_report"]["case_rows"]:
            if row["term"] == "loss":
                row["continuation"] = "loss=loss"
                row["continuation_hit"] = True
        report = build_minimal_prompt_branch_bias_diagnostic(source)

        self.assertEqual(report["decision"], "minimal_prompt_branch_bias_pair_full_observed")

    def test_diagnostic_fails_when_checkpoint_missing(self) -> None:
        source = refresh_fixture()
        source["summary"]["checkpoint_exists"] = False
        report = build_minimal_prompt_branch_bias_diagnostic(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source refresh checkpoint is missing", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_minimal_prompt_branch_bias_diagnostic(refresh_fixture())
            outputs = write_minimal_prompt_branch_bias_diagnostic_outputs(report, Path(tmp) / "diagnostic")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("dominant_bias=fixed", render_minimal_prompt_branch_bias_diagnostic_text(report))
        self.assertIn("Branch-Bias Diagnostic", render_minimal_prompt_branch_bias_diagnostic_markdown(report))
        self.assertIn("MiniGPT minimal prompt branch-bias diagnostic", render_minimal_prompt_branch_bias_diagnostic_html(report))

    def test_locator_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_minimal_prompt_branch_bias_source(root),
                root / "model_capability_required_term_pair_coexistence_refresh.json",
            )


def refresh_fixture(*, pair_full: bool = False) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": "minimal_prompt_equals_surface_objective", "seed": 3535},
        "summary": {"training_status": "pass", "checkpoint_exists": True, "pair_full_observed": pair_full},
        "replay_report": {
            "case_rows": [
                row("default", "fixed", "fixed=fixed=", True),
                row("suppress_newline_tokens", "fixed", "fixed=fixed=", True),
                row("default", "loss", "fixed=fixed=", False),
                row("suppress_newline_tokens", "loss", "fixed=fixed=", False),
            ]
        },
    }


def row(profile: str, term: str, continuation: str, hit: bool) -> dict[str, object]:
    return {
        "profile_id": profile,
        "term": term,
        "prompt": f"{term}=",
        "generated": f"{term}={continuation}",
        "continuation": continuation,
        "continuation_hit": hit,
        "newline_cleanup_hit": hit,
    }


if __name__ == "__main__":
    unittest.main()
