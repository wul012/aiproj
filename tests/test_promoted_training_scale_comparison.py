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

from minigpt import promoted_training_scale_comparison  # noqa: E402
from minigpt import promoted_training_scale_comparison_artifacts  # noqa: E402
from minigpt.promoted_training_scale_comparison import (  # noqa: E402
    build_promoted_training_scale_comparison,
    render_promoted_training_scale_comparison_html,
    render_promoted_training_scale_comparison_markdown,
    write_promoted_training_scale_comparison_outputs,
)


class PromotedTrainingScaleComparisonTests(unittest.TestCase):
    def test_comparison_module_reexports_artifact_writers(self) -> None:
        self.assertIs(
            promoted_training_scale_comparison.write_promoted_training_scale_comparison_outputs,
            promoted_training_scale_comparison_artifacts.write_promoted_training_scale_comparison_outputs,
        )
        self.assertIs(
            promoted_training_scale_comparison.render_promoted_training_scale_comparison_html,
            promoted_training_scale_comparison_artifacts.render_promoted_training_scale_comparison_html,
        )
        self.assertIs(
            promoted_training_scale_comparison.render_promoted_training_scale_comparison_markdown,
            promoted_training_scale_comparison_artifacts.render_promoted_training_scale_comparison_markdown,
        )

    def test_compares_only_promoted_runs_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("beta", "beta", "promoted", "pass"),
                    entry("review", "review", "review", "warn"),
                ],
                baseline_name="beta",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["comparison_status"], "compared")
            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 2)
            self.assertEqual(report["summary"]["compared_run_count"], 2)
            self.assertEqual(report["summary"]["baseline_name"], "beta")
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertEqual([row["name"] for row in report["comparison"]["runs"]], ["alpha", "beta"])
            self.assertNotIn("review", [row["name"] for row in report["comparison"]["runs"]])
            self.assertFalse(report["blockers"])

    def test_mixed_promoted_run_suites_are_carried_to_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn", suite_name=None),
                    entry("beta", "beta", "promoted", "pass", suite_name="standard-zh"),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["comparison_status"], "compared")
            self.assertEqual(report["summary"]["suite_consistency"], "mixed")
            self.assertEqual(report["summary"]["suite_mismatch_count"], 1)
            self.assertTrue(any("different benchmark suites" in item for item in report["recommendations"]))
            beta = next(row for row in report["promotions"] if row["name"] == "beta")
            self.assertEqual(beta["suite_path"], "builtin:standard-zh")

    def test_carries_index_handoff_suite_guard_into_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn", include_handoff_suite_guard=True),
                    entry("beta", "beta", "promoted", "pass", include_handoff_suite_guard=True),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertTrue(row["handoff_require_suite_consistency"])
            self.assertEqual(row["handoff_suite_consistency"], "consistent")
            self.assertEqual(row["handoff_suite_mismatch_count"], 0)
            self.assertEqual(row["handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_require_suite_consistency_count"], 2)
            self.assertEqual(summary["handoff_suite_consistent_count"], 2)
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertEqual(summary["comparison_ready_handoff_suite_mismatch_total"], 0)
            self.assertIn("handoff_suite_consistency", csv_text)
            self.assertIn("Handoff Suite", markdown)
            self.assertIn("Comparison-ready handoff suite mismatches", markdown)
            self.assertIn("Handoff suite consistent", html)
            self.assertIn("Ready suite mismatches", html)
            self.assertIn("handoff_require_suite_consistency_count=2", completed.stdout)
            self.assertIn("handoff_suite_consistent_count=2", completed.stdout)
            self.assertIn("comparison_ready_handoff_suite_mismatch_total=0", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_blocks_when_promoted_input_is_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("review", "review", "review", "warn"),
                ],
            )

            report = build_promoted_training_scale_comparison(index_dir)

            self.assertEqual(report["comparison_status"], "blocked")
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertIn("at least two promoted runs", report["summary"]["blocked_reason"])
            self.assertTrue(any("two promoted runs" in item for item in report["blockers"]))

    def test_invalid_baseline_is_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("beta", "beta", "promoted", "pass"),
                ],
            )

            report = build_promoted_training_scale_comparison(index_dir, baseline="missing")

            self.assertEqual(report["comparison_status"], "blocked")
            self.assertIn("baseline not found", report["summary"]["blocked_reason"])

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "<alpha>", "promoted", "warn"),
                    entry("beta", "<beta>", "promoted", "pass"),
                ],
                baseline_name="<beta>",
            )
            report = build_promoted_training_scale_comparison(index_dir, title="<Promoted Compare>")

            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = render_promoted_training_scale_comparison_markdown(report)
            html = render_promoted_training_scale_comparison_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["comparison_status"], "compared")
            self.assertIn("## Comparison", markdown)
            self.assertIn("&lt;Promoted Compare&gt;", html)
            self.assertIn("&lt;alpha&gt;", html)
            self.assertNotIn("<Promoted Compare>", html)
            self.assertNotIn("<alpha>", html)


def entry(
    safe_id: str,
    name: str,
    status: str,
    gate_status: str,
    suite_name: str | None = "standard-zh",
    *,
    include_handoff_suite_guard: bool = False,
) -> dict:
    return {
        "safe_id": safe_id,
        "name": name,
        "status": status,
        "gate_status": gate_status,
        "suite_name": suite_name,
        "include_handoff_suite_guard": include_handoff_suite_guard,
    }


def make_index_tree(root: Path, entries: list[dict], baseline_name: str | None = None) -> Path:
    index_dir = root / "promotion-index"
    promotions = []
    compare_names = []
    compare_paths = []
    for item in entries:
        run_path = root / "runs" / item["safe_id"] / "training_scale_run.json"
        write_json(run_path, scale_run(item["name"], item["gate_status"], item.get("suite_name")))
        rel_run_path = os.path.relpath(run_path, index_dir)
        promoted = item["status"] == "promoted"
        promotion = {
            "name": item["name"],
            "promotion_status": item["status"],
            "promoted_for_comparison": promoted,
            "training_scale_run_path": rel_run_path,
            "training_scale_run_exists": True,
        }
        if item.get("include_handoff_suite_guard"):
            promotion.update(
                {
                    "handoff_require_suite_consistency": True,
                    "handoff_suite_consistency": "consistent",
                    "handoff_suite_mismatch_count": 0,
                    "handoff_selected_suite_path": "builtin:standard-zh",
                }
            )
        promotions.append(promotion)
        if promoted:
            compare_names.append(item["name"])
            compare_paths.append(rel_run_path)
    write_json(
        index_dir / "training_scale_promotion_index.json",
        {
            "title": "test promotion index",
            "generated_at": "2026-05-14T00:00:00Z",
            "summary": {
                "promotion_count": len(entries),
                "promoted_count": len(compare_names),
                "review_count": sum(1 for item in entries if item["status"] == "review"),
                "blocked_count": sum(1 for item in entries if item["status"] == "blocked"),
                "comparison_ready_count": len(compare_names),
                "compare_command_ready": len(compare_names) >= 2,
            },
            "promotions": promotions,
            "comparison_inputs": {
                "run_count": len(compare_names),
                "names": compare_names,
                "training_scale_run_paths": compare_paths,
                "baseline_name": baseline_name or (compare_names[0] if compare_names else None),
                "compare_command_ready": len(compare_names) >= 2,
            },
        },
    )
    return index_dir


def scale_run(name: str, gate_status: str, suite_name: str | None = "standard-zh") -> dict:
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
            "version_prefix": "v79-test",
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
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
