from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed import (  # noqa: E402
    build_promoted_training_scale_seed,
    load_promoted_training_scale_decision,
    render_promoted_training_scale_seed_html,
    render_promoted_training_scale_seed_markdown,
    write_promoted_training_scale_seed_outputs,
)


class PromotedTrainingScaleSeedTests(unittest.TestCase):
    def test_builds_ready_seed_from_accepted_decision_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_name="next-zh",
                dataset_version_prefix="v81-smoke",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["seed_status"], "ready")
            self.assertEqual(report["summary"]["selected_name"], "beta")
            self.assertTrue(report["summary"]["execution_ready"])
            self.assertEqual(report["summary"]["source_count"], 1)
            self.assertIn("scripts/plan_training_scale.py", report["next_plan"]["command"])
            self.assertIn("v81-smoke", report["next_plan"]["command"])

    def test_review_decision_keeps_command_but_marks_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="review")
            source = write_source(root)

            report = build_promoted_training_scale_seed(decision, [source], project_root=root)

            self.assertEqual(report["seed_status"], "review")
            self.assertTrue(report["next_plan"]["command_available"])
            self.assertFalse(report["next_plan"]["execution_ready"])
            self.assertTrue(any("Review" in item or "review" in item for item in report["recommendations"]))

    def test_blocks_when_decision_has_no_selected_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="blocked", selected=False)
            source = write_source(root)

            report = build_promoted_training_scale_seed(decision, [source], project_root=root)

            self.assertEqual(report["seed_status"], "blocked")
            self.assertFalse(report["next_plan"]["command_available"])
            self.assertGreaterEqual(report["summary"]["blocker_count"], 1)
            self.assertTrue(any("selected_baseline" in item for item in report["blockers"]))

    def test_blocks_missing_next_corpus_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            missing = root / "missing.txt"

            report = build_promoted_training_scale_seed(decision, [missing], project_root=root)

            self.assertEqual(report["seed_status"], "blocked")
            self.assertEqual(report["summary"]["missing_source_count"], 1)
            self.assertFalse(report["next_plan"]["command_available"])
            self.assertTrue(any("missing corpus sources" in item for item in report["blockers"]))

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            source = write_source(root)
            report = build_promoted_training_scale_seed(
                decision.parent,
                [source],
                project_root=root,
                title="<Seed>",
            )

            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            loaded = load_promoted_training_scale_decision(decision.parent)
            markdown = render_promoted_training_scale_seed_markdown(report)
            html = render_promoted_training_scale_seed_html(report)

            self.assertEqual(loaded["decision_status"], "accepted")
            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("## Next Plan Command", markdown)
            self.assertIn("&lt;Seed&gt;", html)
            self.assertNotIn("<Seed>", html)


def write_decision_tree(root: Path, *, decision_status: str, selected: bool = True) -> Path:
    run_path = root / "beta" / "scale-run" / "training_scale_run.json"
    write_json(
        run_path,
        {
            "name": "beta",
            "status": "completed",
            "allowed": True,
            "gate_profile": "review",
            "gate": {"overall_status": "pass"},
            "scale_plan_summary": {
                "dataset_name": "sample-zh",
                "version_prefix": "v80",
                "scale_tier": "tiny",
                "char_count": 2048,
                "variant_count": 1,
            },
            "batch_summary": {"status": "completed", "variant_count": 1},
        },
    )
    payload = {
        "schema_version": 1,
        "title": "decision",
        "decision_status": decision_status,
        "comparison_path": str(root / "comparison" / "promoted_training_scale_comparison.json"),
        "selected_baseline": {
            "name": "beta",
            "gate_status": "pass",
            "batch_status": "completed",
            "readiness_score": 107,
            "training_scale_run_path": str(run_path),
            "promotion_status": "promoted",
        }
        if selected
        else None,
        "summary": {"decision_status": decision_status, "selected_name": "beta" if selected else None},
    }
    decision_path = root / "promoted-decision" / "promoted_training_scale_decision.json"
    write_json(decision_path, payload)
    return decision_path


def write_source(root: Path) -> Path:
    source = root / "corpus.txt"
    source.write_text("MiniGPT next cycle corpus.\n" * 120, encoding="utf-8")
    return source


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
