from __future__ import annotations

import json
import os
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


def make_compared_comparison_tree(root: Path, second_promoted: bool = True, title: str = "MiniGPT promoted training scale comparison") -> Path:
    index_dir = root / "promotion-index"
    alpha_run = root / "alpha" / "scale-run" / "training_scale_run.json"
    beta_run = root / "beta" / "scale-run" / "training_scale_run.json"
    write_json(alpha_run, run_payload("alpha", "warn", 88))
    write_json(beta_run, run_payload("beta", "pass", 91))
    promotions = [
        {
            "name": "alpha",
            "promotion_status": "promoted",
            "promoted_for_comparison": True,
            "training_scale_run_path": os_rel(alpha_run, index_dir),
            "training_scale_run_exists": True,
            "gate_status": "warn",
            "batch_status": "completed",
            "readiness_score": 88,
        }
    ]
    compare_names = ["alpha"]
    compare_paths = [os_rel(alpha_run, index_dir)]
    if second_promoted:
        promotions.append(
            {
                "name": "beta",
                "promotion_status": "promoted",
                "promoted_for_comparison": True,
                "training_scale_run_path": os_rel(beta_run, index_dir),
                "training_scale_run_exists": True,
                "gate_status": "pass",
                "batch_status": "completed",
                "readiness_score": 91,
            }
        )
        compare_names.append("beta")
        compare_paths.append(os_rel(beta_run, index_dir))
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


def run_payload(name: str, gate_status: str, readiness: int) -> dict:
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
