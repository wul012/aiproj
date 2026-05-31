from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_fixed_retention_route_decision import (
    build_model_capability_required_term_pair_fixed_retention_route_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_route_decision_artifacts import (
    render_fixed_retention_route_decision_html,
    render_fixed_retention_route_decision_markdown,
    render_fixed_retention_route_decision_text,
    write_fixed_retention_route_decision_outputs,
)
from minigpt.report_utils import write_json_payload


ROOT = Path(__file__).resolve().parents[1]


class FixedRetentionRouteDecisionTests(unittest.TestCase):
    def test_selects_fixed_recovery_route_for_loss_rebalance(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_route_decision(comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "select_fixed_recovery_route_for_loss_rebalance_not_promotion")
        self.assertEqual(report["summary"]["selected_route"], "v601-first-token")
        self.assertTrue(report["summary"]["loss_rebalance_objective_required"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_promotes_pair_full_route(self) -> None:
        comparison = comparison_fixture()
        comparison["branch_rows"][0]["pair_full_observed"] = True
        report = build_model_capability_required_term_pair_fixed_retention_route_decision(comparison)

        self.assertEqual(report["decision"], "promote_fixed_retention_pair_full_route")
        self.assertTrue(report["summary"]["promotion_ready"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_fixed_retention_route_decision(comparison_fixture())
            outputs = write_fixed_retention_route_decision_outputs(report, Path(tmp))
            text = render_fixed_retention_route_decision_text(report)
            markdown = render_fixed_retention_route_decision_markdown(report)
            html = render_fixed_retention_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("loss_rebalance_objective_required=True", text)
            self.assertIn("Fixed-Retention Route Decision", markdown)
            self.assertIn("MiniGPT fixed-retention route decision", html)

    def test_cli_runs_with_directory_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "comparison" / "model_capability_required_term_pair_fixed_retention_objective_comparison.json"
            write_json_payload(comparison_fixture(), source)

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_fixed_retention_route_decision.py"),
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

            self.assertEqual(result.returncode, 0)
            self.assertIn("selected_route=v601-first-token", result.stdout)


def comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "fixed_retention_objectives_confirm_branch_tradeoff",
        "summary": {
            "mixed_tradeoff_observed": True,
            "union_hit_terms": ["fixed", "loss"],
        },
        "branch_rows": [
            route("v600-balanced", "equals_surface_no_pair_id_fixed_retention_balanced_repair", ["loss"]),
            route("v601-first-token", "equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed"]),
            route("v602-prompt-guard", "equals_surface_no_pair_id_fixed_retention_prompt_guard_repair", ["loss"]),
        ],
    }


def route(label: str, corpus_mode: str, hit_terms: list[str]) -> dict[str, object]:
    return {
        "source_label": label,
        "corpus_mode": corpus_mode,
        "seed": 3535,
        "hit_terms": hit_terms,
        "missed_terms": [term for term in ("fixed", "loss") if term not in hit_terms],
        "fixed_only_tradeoff": hit_terms == ["fixed"],
        "loss_only_tradeoff": hit_terms == ["loss"],
        "pair_full_observed": set(hit_terms) == {"fixed", "loss"},
    }


if __name__ == "__main__":
    unittest.main()
