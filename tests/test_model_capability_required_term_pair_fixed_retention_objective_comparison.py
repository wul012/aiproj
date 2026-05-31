from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (
    build_model_capability_required_term_pair_fixed_retention_objective_comparison,
    locate_fixed_retention_objective_refresh_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison_artifacts import (
    render_fixed_retention_objective_comparison_html,
    render_fixed_retention_objective_comparison_markdown,
    render_fixed_retention_objective_comparison_text,
    write_fixed_retention_objective_comparison_outputs,
)
from minigpt.report_utils import write_json_payload


ROOT = Path(__file__).resolve().parents[1]


class FixedRetentionObjectiveComparisonTests(unittest.TestCase):
    def test_comparison_reports_mixed_fixed_and_loss_tradeoffs(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_objective_comparison(
            [
                refresh_report("equals_surface_no_pair_id_fixed_retention_balanced_repair", ["loss"]),
                refresh_report("equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed"]),
                refresh_report("equals_surface_no_pair_id_fixed_retention_prompt_guard_repair", ["loss"]),
            ],
            source_labels=["balanced", "first-token", "prompt-guard"],
            generated_at="2026-06-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "fixed_retention_objectives_confirm_branch_tradeoff")
        self.assertEqual(report["summary"]["fixed_only_tradeoff_report_count"], 1)
        self.assertEqual(report["summary"]["loss_only_tradeoff_report_count"], 2)
        self.assertEqual(report["summary"]["fixed_recovery_route"], "first-token")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_promotes_pair_full_candidate(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_objective_comparison(
            [refresh_report("equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed", "loss"]), refresh_report("equals_surface_no_pair_id_fixed_retention_prompt_guard_repair", ["loss"])],
        )

        self.assertEqual(report["decision"], "promote_fixed_retention_pair_full_candidate")
        self.assertEqual(report["summary"]["pair_full_report_count"], 1)

    def test_comparison_fails_for_non_fixed_retention_mode(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_objective_comparison(
            [
                refresh_report("equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed"]),
                refresh_report("equals_surface_no_pair_id_loss_branch_targeted_repair", ["loss"]),
            ],
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("is not a fixed-retention objective corpus mode", " ".join(report["issues"]))

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_fixed_retention_objective_comparison(
                [
                    refresh_report("equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed"]),
                    refresh_report("equals_surface_no_pair_id_fixed_retention_prompt_guard_repair", ["loss"]),
                ]
            )
            outputs = write_fixed_retention_objective_comparison_outputs(report, Path(tmp))
            text = render_fixed_retention_objective_comparison_text(report)
            markdown = render_fixed_retention_objective_comparison_markdown(report)
            html = render_fixed_retention_objective_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("fixed_recovery_route=", text)
            self.assertIn("Fixed-Retention Objective Comparison", markdown)
            self.assertIn("MiniGPT fixed-retention objective comparison", html)

    def test_cli_runs_with_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first" / "model_capability_required_term_pair_coexistence_refresh.json"
            loss = root / "loss" / "model_capability_required_term_pair_coexistence_refresh.json"
            write_json_payload(refresh_report("equals_surface_no_pair_id_fixed_retention_first_token_repair", ["fixed"]), first)
            write_json_payload(refresh_report("equals_surface_no_pair_id_fixed_retention_prompt_guard_repair", ["loss"]), loss)

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_fixed_retention_objective_comparison.py"),
                    str(first.parent),
                    str(loss.parent),
                    "--labels",
                    "first",
                    "loss",
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
            self.assertIn("status=pass", result.stdout)
            self.assertEqual(locate_fixed_retention_objective_refresh_report(first.parent), first)


def refresh_report(corpus_mode: str, hit_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": corpus_mode, "seed": 3535},
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": set(hit_terms) == {"fixed", "loss"},
        },
        "replay_report": {
            "case_rows": [
                case_row("default", "fixed", "fixed" in hit_terms),
                case_row("default", "loss", "loss" in hit_terms),
            ]
        },
    }


def case_row(profile: str, term: str, hit: bool) -> dict[str, object]:
    return {
        "profile_id": profile,
        "term": term,
        "prompt": f"{term}=",
        "continuation_hit": hit,
        "newline_cleanup_hit": hit,
        "generated_preview": f"{term}={term if hit else 'miss'}",
        "continuation_preview": term if hit else "miss",
    }


if __name__ == "__main__":
    unittest.main()
