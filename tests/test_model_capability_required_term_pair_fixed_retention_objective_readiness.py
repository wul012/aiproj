from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness import (
    build_model_capability_required_term_pair_fixed_retention_objective_readiness,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness_artifacts import (
    render_fixed_retention_objective_readiness_html,
    render_fixed_retention_objective_readiness_markdown,
    render_fixed_retention_objective_readiness_text,
    write_fixed_retention_objective_readiness_outputs,
)
from minigpt.report_utils import write_json_payload


from tests._bootstrap import ROOT


class FixedRetentionObjectiveReadinessTests(unittest.TestCase):
    def test_readiness_passes_when_route_and_diagnostic_align(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_objective_readiness(
            route_decision=fake_route_decision(),
            diagnostic=fake_diagnostic(),
            generated_at="2026-05-31T14:50:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "design_fixed_retention_objective_before_more_loss_branch_training")
        self.assertTrue(report["summary"]["first_token_gap_confirmed"])
        self.assertTrue(report["summary"]["ready_for_fixed_retention_objective_design"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_readiness_fails_without_first_token_gap(self) -> None:
        diagnostic = fake_diagnostic()
        diagnostic["summary"]["missed_first_token_gap_count"] = 0
        report = build_model_capability_required_term_pair_fixed_retention_objective_readiness(
            route_decision=fake_route_decision(),
            diagnostic=diagnostic,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic does not confirm first-token gap", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_fixed_retention_objective_readiness(
                route_decision=fake_route_decision(),
                diagnostic=fake_diagnostic(),
            )
            outputs = write_fixed_retention_objective_readiness_outputs(report, Path(tmp))
            text = render_fixed_retention_objective_readiness_text(report)
            markdown = render_fixed_retention_objective_readiness_markdown(report)
            html = render_fixed_retention_objective_readiness_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("first_token_gap_confirmed=True", text)
            self.assertIn("Fixed-Retention Objective Readiness", markdown)
            self.assertIn("MiniGPT fixed-retention objective readiness", html)

    def test_cli_require_pass_returns_nonzero_on_bad_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route = root / "route" / "model_capability_required_term_pair_loss_branch_route_decision.json"
            diag = root / "diag" / "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.json"
            bad_route = fake_route_decision()
            bad_route["status"] = "fail"
            write_json_payload(bad_route, route)
            write_json_payload(fake_diagnostic(), diag)

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_fixed_retention_objective_readiness.py"),
                    "--route-decision",
                    str(route.parent),
                    "--diagnostic",
                    str(diag.parent),
                    "--out-dir",
                    str(root / "out"),
                    "--require-pass",
                    "--force",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("status=fail", result.stdout)


def fake_route_decision() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "select_targeted_loss_branch_for_seed_stability_not_promotion",
        "summary": {
            "selected_stability_route": "v590-targeted",
            "pair_full_route_count": 0,
            "fixed_retention_objective_required": True,
        },
    }


def fake_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_first_token_gap",
        "summary": {
            "missed_seed_count": 3,
            "missed_first_token_gap_count": 3,
        },
        "seed_rows": [],
    }


if __name__ == "__main__":
    unittest.main()
