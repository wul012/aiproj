from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff,
    render_promoted_training_scale_seed_handoff_html,
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_outputs,
)


class PromotedTrainingScaleSeedHandoffSuiteDesignTests(unittest.TestCase):
    def test_handoff_carries_suite_design_regression_context_to_outputs_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_suite_design_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(
                seed,
                require_clean_batch_review=True,
                generated_at="2026-05-24T00:00:00Z",
            )
            summary = report["summary"]
            clean_requirement = report["clean_batch_review_requirement"]

            self.assertEqual(summary["selected_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(summary["selected_handoff_selected_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(summary["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(summary["handoff_selected_batch_maturity_suite_design_regression_total"], 1)
            self.assertEqual(summary["handoff_batch_maturity_suite_design_regression_names"], ["beta-suite", "standard"])
            self.assertEqual(summary["handoff_selected_batch_maturity_suite_design_regression_names"], ["beta-suite"])
            self.assertEqual(summary["comparison_ready_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(clean_requirement["status"], "pass")
            self.assertEqual(clean_requirement["selected_suite_design_regression_count"], 0)
            self.assertTrue(clean_requirement["clean"])
            self.assertTrue(
                any("handoff batch suite-design regressions" in item for item in report["recommendations"])
            )

            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = render_promoted_training_scale_seed_handoff_markdown(report)
            html = render_promoted_training_scale_seed_handoff_html(report)

            self.assertIn("handoff_batch_maturity_suite_design_regression_count", csv_text)
            self.assertIn("clean_batch_review_requirement_selected_suite_design_regression_count", csv_text)
            self.assertIn("Handoff batch suite-design regressions", markdown)
            self.assertIn("Comparison-ready handoff batch suite-design regressions", markdown)
            self.assertIn("Handoff suite-design regressions", html)
            self.assertIn("Ready suite-design regressions", html)

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/execute_promoted_training_scale_seed.py",
                    str(seed),
                    "--out-dir",
                    str(root / "script-handoff"),
                    "--require-clean-batch-review",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("handoff_batch_maturity_suite_design_regression_count=2", completed.stdout)
            self.assertIn('handoff_batch_maturity_suite_design_regression_names=["beta-suite", "standard"]', completed.stdout)
            self.assertIn("comparison_ready_handoff_batch_maturity_suite_design_regression_count=0", completed.stdout)
            self.assertIn("clean_batch_review_required_selected_suite_design_regression_count=0", completed.stdout)
            self.assertIn("clean_batch_review_required=pass", completed.stdout)


def write_suite_design_seed_tree(root: Path) -> Path:
    source = root / "corpus.txt"
    source.write_text("MiniGPT v425 suite-design handoff corpus.\n" * 32, encoding="utf-8")
    plan_out = root / "next-plan"
    suite = {"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh", "source": "inherited"}
    seed = {
        "schema_version": 1,
        "title": "suite design seed",
        "generated_at": "2026-05-24T00:00:00Z",
        "seed_status": "ready",
        "baseline_seed": {
            "selected_name": "beta",
            "decision_status": "accepted",
            "gate_status": "pass",
            "batch_status": "completed",
            "readiness_score": 112,
            "suite": suite,
            "suite_path": suite["path"],
            "handoff_suite_guard": {
                "selected_handoff_require_suite_consistency": True,
                "selected_handoff_suite_consistency": "consistent",
                "selected_handoff_suite_mismatch_count": 0,
                "selected_handoff_selected_suite_path": suite["path"],
                "handoff_suite_consistent_count": 2,
                "handoff_suite_mismatch_total": 0,
                "comparison_ready_handoff_suite_mismatch_total": 0,
            },
            "handoff_clean_batch_review": {
                "selected_handoff_require_clean_batch_review": True,
                "selected_handoff_clean_batch_review_status": "clean",
                "selected_handoff_batch_maturity_ci_regression_count": 0,
                "selected_handoff_batch_maturity_ci_regression_names": [],
                "selected_handoff_batch_maturity_ci_regression_reason_counts": {},
                "selected_handoff_batch_maturity_suite_design_regression_count": 0,
                "selected_handoff_batch_maturity_suite_design_regression_names": [],
                "selected_handoff_selected_batch_maturity_ci_regression_count": 0,
                "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": {},
                "selected_handoff_selected_batch_maturity_suite_design_regression_count": 0,
                "selected_handoff_selected_batch_maturity_suite_design_regression_names": [],
                "selected_comparison_exclusion_reasons": [],
                "handoff_require_clean_batch_review_count": 3,
                "handoff_clean_batch_review_count": 2,
                "handoff_unclean_batch_review_count": 1,
                "handoff_batch_maturity_ci_regression_count": 0,
                "handoff_selected_batch_maturity_ci_regression_total": 0,
                "handoff_batch_maturity_ci_regression_names": [],
                "handoff_batch_maturity_ci_regression_reason_counts": {},
                "handoff_selected_batch_maturity_ci_regression_reason_counts": {},
                "handoff_batch_maturity_suite_design_regression_count": 2,
                "handoff_selected_batch_maturity_suite_design_regression_total": 1,
                "handoff_batch_maturity_suite_design_regression_names": ["beta-suite", "standard"],
                "handoff_selected_batch_maturity_suite_design_regression_names": ["beta-suite"],
                "comparison_exclusion_reasons": ["handoff batch suite-design regression count is 2"],
                "comparison_ready_handoff_require_clean_batch_review_count": 1,
                "comparison_ready_handoff_clean_batch_review_count": 1,
                "comparison_ready_handoff_unclean_batch_review_count": 0,
                "comparison_ready_handoff_batch_maturity_ci_regression_count": 0,
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": 0,
                "comparison_ready_handoff_batch_maturity_ci_regression_names": [],
                "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {},
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": {},
                "comparison_ready_handoff_batch_maturity_suite_design_regression_count": 0,
                "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": 0,
                "comparison_ready_handoff_batch_maturity_suite_design_regression_names": [],
                "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": [],
            },
        },
        "next_plan": {
            "project_root": str(ROOT),
            "dataset_name": "next-zh",
            "dataset_version_prefix": "v425-test",
            "suite": suite,
            "suite_path": suite["path"],
            "suite_source": suite["source"],
            "plan_out_dir": str(plan_out),
            "batch_out_root": str(root / "batch"),
            "sources": [
                {"path": str(source), "resolved_path": str(source.resolve()), "exists": True, "kind": "file"}
            ],
            "command": [sys.executable, "-c", "print('planned v425 seed handoff')"],
            "command_text": f"{sys.executable} -c print('planned v425 seed handoff')",
            "command_available": True,
            "execution_ready": True,
        },
        "summary": {"seed_status": "ready", "selected_name": "beta", "command_available": True},
    }
    seed_path = root / "promoted-seed" / "promoted_training_scale_seed.json"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    return seed_path


if __name__ == "__main__":
    unittest.main()
