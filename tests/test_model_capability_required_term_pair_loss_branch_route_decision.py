from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_branch_route_decision import (
    build_model_capability_required_term_pair_loss_branch_route_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_branch_route_decision_artifacts import (
    render_loss_branch_route_decision_html,
    render_loss_branch_route_decision_markdown,
    render_loss_branch_route_decision_text,
    write_loss_branch_route_decision_outputs,
)
from minigpt.report_utils import write_json_payload


ROOT = Path(__file__).resolve().parents[1]


class LossBranchRouteDecisionTests(unittest.TestCase):
    def test_selects_targeted_route_as_stability_baseline_not_promotion(self) -> None:
        report = build_model_capability_required_term_pair_loss_branch_route_decision(fake_comparison())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "select_targeted_loss_branch_for_seed_stability_not_promotion")
        self.assertEqual(report["summary"]["selected_stability_route"], "v590-targeted")
        self.assertTrue(report["summary"]["fixed_retention_objective_required"])
        self.assertFalse(report["summary"]["promotion_ready"])

    def test_promotes_pair_full_route_when_present(self) -> None:
        comparison = fake_comparison(pair_full_route=True)
        report = build_model_capability_required_term_pair_loss_branch_route_decision(comparison)

        self.assertEqual(report["decision"], "promote_loss_branch_pair_full_route")
        self.assertTrue(report["summary"]["promotion_ready"])

    def test_failed_comparison_fails_decision(self) -> None:
        comparison = fake_comparison()
        comparison["status"] = "fail"
        report = build_model_capability_required_term_pair_loss_branch_route_decision(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_branch_route_decision(fake_comparison())
            outputs = write_loss_branch_route_decision_outputs(report, Path(tmp))
            text = render_loss_branch_route_decision_text(report)
            markdown = render_loss_branch_route_decision_markdown(report)
            html = render_loss_branch_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("selected_stability_route=v590-targeted", text)
            self.assertIn("Loss-Branch Route Decision", markdown)
            self.assertIn("MiniGPT loss-branch route decision", html)

    def test_cli_require_pass_returns_nonzero_on_bad_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "comparison" / "model_capability_required_term_pair_loss_branch_objective_comparison.json"
            bad = fake_comparison()
            bad["status"] = "fail"
            write_json_payload(bad, source)

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_loss_branch_route_decision.py"),
                    str(source.parent),
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


def fake_comparison(*, pair_full_route: bool = False) -> dict[str, object]:
    rows = [
        branch_row("v590-targeted", "equals_surface_no_pair_id_loss_branch_targeted_repair", ["loss"], ["fixed"]),
        branch_row("v591-dual-anchor", "equals_surface_no_pair_id_loss_branch_dual_anchor_repair", ["loss"], ["fixed"]),
        branch_row("v592-micro-span", "equals_surface_no_pair_id_loss_branch_micro_span_repair", ["loss"], ["fixed"]),
    ]
    if pair_full_route:
        rows.append(branch_row("candidate", "equals_surface_no_pair_id_loss_branch_targeted_repair", ["fixed", "loss"], []))
    return {
        "status": "pass",
        "decision": "loss_branch_objectives_confirm_loss_only_tradeoff",
        "summary": {"union_hit_terms": ["loss"]},
        "branch_rows": rows,
    }


def branch_row(label: str, corpus_mode: str, hit_terms: list[str], missed_terms: list[str]) -> dict[str, object]:
    return {
        "source_label": label,
        "corpus_mode": corpus_mode,
        "seed": 3535,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "pair_full_observed": not missed_terms,
    }


if __name__ == "__main__":
    unittest.main()
