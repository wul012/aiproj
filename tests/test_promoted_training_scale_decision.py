from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_comparison import build_promoted_training_scale_comparison  # noqa: E402
from minigpt.promoted_training_scale_decision import (  # noqa: E402
    build_promoted_training_scale_decision,
    render_promoted_training_scale_decision_html,
    render_promoted_training_scale_decision_markdown,
    write_promoted_training_scale_decision_outputs,
)


class PromotedTrainingScaleDecisionTests(unittest.TestCase):
    def test_selects_baseline_from_compared_promoted_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(root)

            report = build_promoted_training_scale_decision(comparison_dir, min_readiness=60)

            self.assertEqual(report["decision_status"], "accepted")
            self.assertEqual(report["summary"]["candidate_count"], 2)
            self.assertEqual(report["summary"]["selected_name"], "beta")
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertEqual(report["summary"]["selected_suite_path"], "builtin:standard-zh")
            self.assertFalse(report["rejected_runs"])
            self.assertEqual(report["selected_baseline"]["name"], "beta")

    def test_blocks_when_only_one_candidate_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(root, second_promoted=False)

            report = build_promoted_training_scale_decision(comparison_dir)

            self.assertEqual(report["decision_status"], "blocked")
            self.assertEqual(report["summary"]["candidate_count"], 0)
            self.assertEqual(report["summary"]["comparison_status"], "blocked")
            self.assertTrue(any("Need at least two promoted runs" in item or "comparison" in item.lower() for item in report["recommendations"]))

    def test_blocks_when_comparison_is_not_compared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_blocked_comparison_tree(root)

            report = build_promoted_training_scale_decision(comparison_dir)

            self.assertEqual(report["decision_status"], "blocked")
            self.assertEqual(report["summary"]["comparison_status"], "blocked")
            self.assertEqual(report["summary"]["candidate_count"], 0)

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(root, title="<Comparison>")
            report = build_promoted_training_scale_decision(comparison_dir, title="<Decision>")

            outputs = write_promoted_training_scale_decision_outputs(report, root / "out")
            markdown = render_promoted_training_scale_decision_markdown(report)
            html = render_promoted_training_scale_decision_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["decision_status"], "accepted")
            self.assertIn("## Rejected Runs", markdown)
            self.assertIn("&lt;Decision&gt;", html)
            self.assertNotIn("<Decision>", html)

    def test_require_suite_consistency_blocks_mixed_promoted_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(root, mixed_suite=True)

            default_report = build_promoted_training_scale_decision(comparison_dir, min_readiness=60)
            strict_report = build_promoted_training_scale_decision(
                comparison_dir,
                min_readiness=60,
                require_suite_consistency=True,
            )

            self.assertEqual(default_report["decision_status"], "accepted")
            self.assertEqual(default_report["summary"]["suite_consistency"], "mixed")
            self.assertFalse(default_report["summary"]["require_suite_consistency"])
            self.assertTrue(any("different benchmark suites" in item for item in default_report["recommendations"]))
            self.assertEqual(strict_report["decision_status"], "blocked")
            self.assertTrue(strict_report["summary"]["require_suite_consistency"])
            reasons = [reason for row in strict_report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("benchmark suite consistency is mixed", reasons)
            self.assertTrue(any("Fix benchmark suite consistency" in item for item in strict_report["recommendations"]))

    def test_carries_promoted_comparison_handoff_suite_guard_into_decision_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(root, include_handoff_suite_guard=True)

            report = build_promoted_training_scale_decision(comparison_dir, min_readiness=60)
            outputs = write_promoted_training_scale_decision_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "decide_promoted_training_scale_baseline.py"),
                    str(comparison_dir),
                    "--min-readiness",
                    "60",
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            selected = report["selected_baseline"]
            summary = report["summary"]
            self.assertEqual(report["decision_status"], "accepted")
            self.assertTrue(selected["handoff_require_suite_consistency"])
            self.assertEqual(selected["handoff_suite_consistency"], "consistent")
            self.assertEqual(selected["handoff_suite_mismatch_count"], 0)
            self.assertEqual(selected["handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["selected_handoff_suite_consistency"], "consistent")
            self.assertEqual(summary["selected_handoff_suite_mismatch_count"], 0)
            self.assertEqual(summary["selected_handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_suite_consistent_count"], 2)
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertIn("selected_handoff_suite_consistency", csv_text)
            self.assertIn("Selected handoff suite", markdown)
            self.assertIn("Handoff suite mismatches", markdown)
            self.assertIn("Selected handoff suite", html)
            self.assertIn("selected_handoff_suite_consistency=consistent", completed.stdout)
            self.assertIn("handoff_suite_mismatch_total=0", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_decision.json").exists())

    def test_carries_promoted_comparison_handoff_batch_review_into_decision_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(
                root,
                include_handoff_suite_guard=True,
                include_handoff_batch_review=True,
            )

            report = build_promoted_training_scale_decision(comparison_dir, min_readiness=60)
            outputs = write_promoted_training_scale_decision_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "decide_promoted_training_scale_baseline.py"),
                    str(comparison_dir),
                    "--min-readiness",
                    "60",
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            selected = report["selected_baseline"]
            summary = report["summary"]
            self.assertEqual(report["decision_status"], "accepted")
            self.assertEqual(selected["name"], "beta")
            self.assertEqual(selected["handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(selected["handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_review_action_count"], 2)
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["selected_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_review_action_total"], 4)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_blocker_action_total"], 1)
            self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertIn("selected_handoff_selected_batch_review_status", csv_text)
            self.assertIn("Selected handoff batch review", markdown)
            self.assertIn("Selected handoff batch", html)
            self.assertIn("selected_handoff_selected_batch_review_status=blocker", completed.stdout)
            self.assertIn("comparison_ready_handoff_selected_batch_blocker_count=1", completed.stdout)
            self.assertTrue(any("selected handoff batch blocker" in item for item in report["recommendations"]))

    def test_carries_promoted_comparison_clean_batch_review_into_decision_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_dir = make_compared_comparison_tree(
                root,
                include_handoff_suite_guard=True,
                include_clean_batch_review=True,
                include_unclean_promoted_review=True,
            )

            report = build_promoted_training_scale_decision(comparison_dir, min_readiness=60)
            outputs = write_promoted_training_scale_decision_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "decide_promoted_training_scale_baseline.py"),
                    str(comparison_dir),
                    "--min-readiness",
                    "60",
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            selected = report["selected_baseline"]
            summary = report["summary"]
            rejected = {row["name"]: row for row in report["rejected_runs"]}
            self.assertEqual(report["decision_status"], "review")
            self.assertEqual(selected["name"], "beta")
            self.assertTrue(selected["handoff_require_clean_batch_review"])
            self.assertEqual(selected["handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["selected_handoff_require_clean_batch_review"], True)
            self.assertEqual(summary["selected_handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 3)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_unclean_batch_review_count"], 0)
            self.assertIn("dirty", rejected)
            self.assertIn("run was not promoted for comparison", rejected["dirty"]["reasons"])
            self.assertIn("clean batch-review requirement is not clean", rejected["dirty"]["reasons"])
            self.assertIn("selected_handoff_require_clean_batch_review", csv_text)
            self.assertIn("Selected handoff clean batch review", markdown)
            self.assertIn("Ready clean batch", html)
            self.assertIn("selected_handoff_clean_batch_review_status=clean", completed.stdout)
            self.assertIn("handoff_unclean_batch_review_count=1", completed.stdout)
            self.assertIn("comparison_ready_handoff_unclean_batch_review_count=0", completed.stdout)
            self.assertTrue(any("Rejected promoted inputs include unclean clean-required handoffs" in item for item in report["recommendations"]))


def make_compared_comparison_tree(
    root: Path,
    second_promoted: bool = True,
    title: str = "MiniGPT promoted training scale comparison",
    mixed_suite: bool = False,
    include_handoff_suite_guard: bool = False,
    include_handoff_batch_review: bool = False,
    include_clean_batch_review: bool = False,
    include_unclean_promoted_review: bool = False,
) -> Path:
    index_dir = root / "promotion-index"
    alpha_run = root / "alpha" / "scale-run" / "training_scale_run.json"
    beta_run = root / "beta" / "scale-run" / "training_scale_run.json"
    write_json(alpha_run, run_payload("alpha", "warn", 88, suite_name=None if mixed_suite else "standard-zh"))
    write_json(beta_run, run_payload("beta", "pass", 91))
    promotions = [
        promotion_row(
            "alpha",
            os_rel(alpha_run, index_dir),
            "warn",
            88,
            include_handoff_suite_guard=include_handoff_suite_guard,
            include_handoff_batch_review=include_handoff_batch_review,
            include_clean_batch_review=include_clean_batch_review,
        )
    ]
    compare_names = ["alpha"]
    compare_paths = [os_rel(alpha_run, index_dir)]
    if second_promoted:
        promotions.append(
            promotion_row(
                "beta",
                os_rel(beta_run, index_dir),
                "pass",
                91,
                include_handoff_suite_guard=include_handoff_suite_guard,
                include_handoff_batch_review=include_handoff_batch_review,
                include_clean_batch_review=include_clean_batch_review,
            )
        )
        compare_names.append("beta")
        compare_paths.append(os_rel(beta_run, index_dir))
    if include_unclean_promoted_review:
        dirty_run = root / "dirty" / "scale-run" / "training_scale_run.json"
        write_json(dirty_run, run_payload("dirty", "pass", 93))
        promotions.append(
            promotion_row(
                "dirty",
                os_rel(dirty_run, index_dir),
                "pass",
                93,
                include_handoff_suite_guard=include_handoff_suite_guard,
                include_handoff_batch_review=include_handoff_batch_review,
                include_clean_batch_review=True,
                clean_batch_review_status="review",
            )
        )
    write_json(
        index_dir / "training_scale_promotion_index.json",
        {
            "title": "index",
            "generated_at": "2026-05-14T00:00:00Z",
            "summary": {
                "promotion_count": len(promotions),
                "promoted_count": len(compare_names),
                "review_count": 0,
                "blocked_count": 0,
                "comparison_ready_count": len(compare_names),
                "compare_command_ready": len(compare_names) >= 2,
            },
            "promotions": promotions,
            "comparison_inputs": {
                "run_count": len(compare_names),
                "names": compare_names,
                "training_scale_run_paths": compare_paths,
                "baseline_name": "beta",
                "compare_command_ready": len(compare_names) >= 2,
            },
        },
    )
    index_report = build_promoted_training_scale_comparison(index_dir, title=title)
    comparison_dir = root / "comparison"
    write_json(comparison_dir / "promoted_training_scale_comparison.json", index_report)
    return comparison_dir


def promotion_row(
    name: str,
    run_path: str,
    gate_status: str,
    readiness_score: int,
    *,
    include_handoff_suite_guard: bool,
    include_handoff_batch_review: bool,
    include_clean_batch_review: bool = False,
    clean_batch_review_status: str = "clean",
) -> dict:
    row = {
        "name": name,
        "promotion_status": "promoted",
        "promoted_for_comparison": True,
        "training_scale_run_path": run_path,
        "training_scale_run_exists": True,
        "gate_status": gate_status,
        "batch_status": "completed",
        "readiness_score": readiness_score,
    }
    if include_handoff_suite_guard:
        row.update(
            {
                "handoff_require_suite_consistency": True,
                "handoff_suite_consistency": "consistent",
                "handoff_suite_mismatch_count": 0,
                "handoff_selected_suite_path": "builtin:standard-zh",
            }
        )
    if include_handoff_batch_review:
        row.update(
            {
                "handoff_selected_batch_review_status": "blocker" if name == "beta" else "review",
                "handoff_selected_batch_comparison_review_action_count": 2,
                "handoff_selected_batch_comparison_blocker_action_count": 1 if name == "beta" else 0,
                "handoff_selected_batch_maturity_coverage_regression_count": 1,
                "handoff_batch_comparison_review_action_count": 2,
                "handoff_batch_comparison_blocker_action_count": 1 if name == "beta" else 0,
                "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"] if name == "beta" else [],
            }
        )
    if include_clean_batch_review:
        row.update(
            {
                "clean_batch_review_guard": {
                    "handoff_require_clean_batch_review": True,
                    "handoff_clean_batch_review_status": clean_batch_review_status,
                },
                "handoff_require_clean_batch_review": True,
                "handoff_clean_batch_review_status": clean_batch_review_status,
            }
        )
    return row


def make_blocked_comparison_tree(root: Path) -> Path:
    comparison_dir = root / "comparison"
    write_json(
        comparison_dir / "promoted_training_scale_comparison.json",
        {
            "title": "blocked comparison",
            "generated_at": "2026-05-14T00:00:00Z",
            "comparison_status": "blocked",
            "comparison_path": "blocked",
            "promotions": [],
            "summary": {
                "comparison_status": "blocked",
                "comparison_ready_count": 0,
                "candidate_count": 0,
                "rejected_count": 0,
                "blocked_reason": "no promoted runs",
            },
            "blockers": ["no promoted runs"],
            "recommendations": ["promote more runs"],
        },
    )
    return comparison_dir


def run_payload(name: str, gate_status: str, readiness: int, suite_name: str | None = "standard-zh") -> dict:
    suite = (
        {"suite_mode": "builtin", "suite_name": suite_name, "suite_path": f"builtin:{suite_name}"}
        if suite_name
        else {"suite_mode": "file", "suite_name": None, "suite_path": str(ROOT / "data" / "eval_prompts.json")}
    )
    return {
        "name": name,
        "status": "completed",
        "allowed": True,
        "execute": True,
        "gate_profile": "review",
        "gate": {
            "overall_status": gate_status,
            "pass_count": 2 if gate_status == "pass" else 1,
            "warn_count": 0 if gate_status == "pass" else 1,
            "fail_count": 0,
        },
        "scale_plan_summary": {
            "dataset_name": "sample-zh",
            "version_prefix": "v80-test",
            "scale_tier": "tiny",
            "char_count": 1024,
            "warning_count": 0 if gate_status == "pass" else 1,
            "variant_count": 1,
            "baseline": name,
            **suite,
        },
        "batch_summary": {
            "status": "completed",
            "comparison_status": "written",
            "variant_count": 1,
            "completed_variant_count": 1,
        },
        "readiness_score": readiness,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def os_rel(path: Path, base: Path) -> str:
    return os.path.relpath(path, base)


if __name__ == "__main__":
    unittest.main()
