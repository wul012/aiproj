from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_promotion_index import (  # noqa: E402
    build_training_scale_promotion_index,
    render_training_scale_promotion_index_html,
    render_training_scale_promotion_index_markdown,
    write_training_scale_promotion_index_outputs,
)
from minigpt import training_scale_promotion_index_helpers as promotion_helpers  # noqa: E402


class TrainingScalePromotionIndexTests(unittest.TestCase):
    def test_indexes_promoted_reports_and_builds_compare_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted")
            beta = make_promotion(root, "beta", "promoted")

            report = build_training_scale_promotion_index(
                [alpha, beta],
                names=["alpha-run", "beta-run"],
                baseline="beta-run",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 2)
            self.assertTrue(report["summary"]["compare_command_ready"])
            self.assertEqual(report["comparison_inputs"]["baseline_name"], "beta-run")
            self.assertEqual(report["comparison_inputs"]["names"], ["alpha-run", "beta-run"])
            self.assertIn("scripts/compare_training_scale_runs.py", report["comparison_inputs"]["compare_command"])

    def test_excludes_review_and_blocked_reports_from_compare_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = make_promotion(root, "promoted", "promoted")
            review = make_promotion(root, "review", "review")
            blocked = make_promotion(root, "blocked", "blocked")

            report = build_training_scale_promotion_index([promoted, review, blocked])

            self.assertEqual(report["summary"]["promoted_count"], 1)
            self.assertEqual(report["summary"]["review_count"], 1)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertFalse(report["summary"]["compare_command_ready"])
            self.assertEqual(report["comparison_inputs"]["names"], ["promoted"])
            self.assertTrue(any("single promoted run" in item for item in report["recommendations"]))

    def test_baseline_must_be_promoted_for_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = make_promotion(root, "promoted", "promoted")
            review = make_promotion(root, "review", "review")

            with self.assertRaises(ValueError):
                build_training_scale_promotion_index([promoted, review], baseline="review")

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promotion = make_promotion(root, "alpha", "promoted", title="<Index>")
            report = build_training_scale_promotion_index([promotion], names=["<alpha>"], title="<Index>")

            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            markdown = render_training_scale_promotion_index_markdown(report)
            html = render_training_scale_promotion_index_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["promoted_count"], 1)
            self.assertIn("## Compare Inputs", markdown)
            self.assertIn("&lt;Index&gt;", html)
            self.assertIn("&lt;alpha&gt;", html)
            self.assertNotIn("<Index>", html)
            self.assertNotIn("<alpha>", html)

    def test_carries_suite_guard_into_index_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted", include_suite_guard=True)
            beta = make_promotion(root, "beta", "promoted", include_suite_guard=True)

            report = build_training_scale_promotion_index([alpha, beta], names=["alpha-run", "beta-run"])
            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertTrue(row["handoff_require_suite_consistency"])
            self.assertEqual(row["handoff_suite_consistency"], "consistent")
            self.assertEqual(row["handoff_suite_mismatch_count"], 0)
            self.assertEqual(row["handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_require_suite_consistency_count"], 2)
            self.assertEqual(summary["handoff_suite_consistent_count"], 2)
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertEqual(summary["handoff_selected_suite_path_count"], 2)
            self.assertIn("handoff_require_suite_consistency", csv_text)
            self.assertIn("Handoff Suite", markdown)
            self.assertIn("Selected Suite", markdown)
            self.assertIn("Handoff strict suite", html)
            self.assertIn("Suite mismatches", html)

    def test_carries_handoff_batch_review_context_into_index_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted", selected_batch_review_status="blocker")
            beta = make_promotion(root, "beta", "promoted", selected_batch_review_status="review")

            report = build_training_scale_promotion_index([alpha, beta], names=["alpha-run", "beta-run"])
            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertTrue(row["promoted_for_comparison"])
            self.assertEqual(row["handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(row["handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["comparison_ready_count"], 2)
            self.assertEqual(summary["handoff_selected_batch_review_count"], 1)
            self.assertEqual(summary["handoff_selected_batch_blocker_count"], 1)
            self.assertEqual(summary["handoff_selected_batch_comparison_review_action_total"], 4)
            self.assertEqual(summary["handoff_selected_batch_comparison_blocker_action_total"], 1)
            self.assertEqual(summary["handoff_batch_comparison_review_action_total"], 4)
            self.assertEqual(summary["handoff_batch_comparison_blocker_action_total"], 1)
            self.assertEqual(summary["handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertIn("Resolve selected handoff batch blocker actions", " ".join(report["recommendations"]))
            self.assertIn("handoff_selected_batch_review_status", csv_text)
            self.assertIn("Batch Review", markdown)
            self.assertIn("Selected batch blockers", markdown)
            self.assertIn("Batch Blockers", markdown)
            self.assertIn("Batch Review", html)
            self.assertIn("Batch blocker actions", html)

    def test_carries_handoff_clean_batch_review_guard_into_index_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted", require_clean_batch_review=True, clean_batch_review_status="clean")
            beta = make_promotion(root, "beta", "promoted", require_clean_batch_review=True, clean_batch_review_status="clean")

            report = build_training_scale_promotion_index([alpha, beta], names=["alpha-run", "beta-run"])
            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertTrue(row["promoted_for_comparison"])
            self.assertTrue(row["handoff_require_clean_batch_review"])
            self.assertEqual(row["handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["comparison_ready_count"], 2)
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 0)
            self.assertEqual(summary["handoff_batch_maturity_ci_regression_count"], 0)
            self.assertIn("handoff_require_clean_batch_review", csv_text)
            self.assertIn("handoff_clean_batch_review_status", csv_text)
            self.assertIn("Handoff require clean batch review", markdown)
            self.assertIn("Handoff clean batch review", markdown)
            self.assertIn("Handoff clean required", html)
            self.assertIn("Clean Status", html)

    def test_unclean_handoff_clean_batch_requirement_is_excluded_from_compare_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = make_promotion(root, "clean", "promoted", require_clean_batch_review=True, clean_batch_review_status="clean")
            dirty = make_promotion(
                root,
                "dirty",
                "promoted",
                require_clean_batch_review=True,
                clean_batch_review_status="review",
                selected_batch_review_status="review",
            )

            report = build_training_scale_promotion_index([clean, dirty], names=["clean-run", "dirty-run"])

            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertEqual(report["summary"]["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(report["summary"]["handoff_clean_batch_review_count"], 1)
            self.assertEqual(report["summary"]["handoff_unclean_batch_review_count"], 1)
            self.assertTrue(report["promotions"][0]["promoted_for_comparison"])
            self.assertFalse(report["promotions"][1]["promoted_for_comparison"])
            self.assertEqual(report["comparison_inputs"]["names"], ["clean-run"])
            self.assertIn("Resolve handoff clean batch-review requirements", " ".join(report["recommendations"]))

    def test_handoff_batch_ci_regression_is_carried_and_excluded_when_clean_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = make_promotion(root, "clean", "promoted", require_clean_batch_review=True, clean_batch_review_status="clean")
            ci_regressed = make_promotion(
                root,
                "ci-regressed",
                "promoted",
                require_clean_batch_review=True,
                clean_batch_review_status="clean",
                batch_ci_regression_count=2,
                batch_ci_regression_names=["review", "standard"],
                batch_ci_regression_reason_counts={"missing-ci-step": 1, "workflow-order-regressed": 1},
                selected_batch_ci_regression_reason_counts={"workflow-order-regressed": 1},
            )

            report = build_training_scale_promotion_index([clean, ci_regressed], names=["clean-run", "ci-run"])
            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")

            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertEqual(report["summary"]["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(report["summary"]["handoff_clean_batch_review_count"], 1)
            self.assertEqual(report["summary"]["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(report["summary"]["handoff_selected_batch_maturity_ci_regression_total"], 2)
            self.assertEqual(
                report["summary"]["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(
                report["summary"]["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertEqual(report["summary"]["handoff_batch_maturity_ci_regression_names"], ["review", "standard"])
            self.assertTrue(report["promotions"][0]["promoted_for_comparison"])
            self.assertFalse(report["promotions"][1]["promoted_for_comparison"])
            self.assertEqual(report["promotions"][1]["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(
                report["promotions"][1]["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(
                report["promotions"][1]["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertEqual(report["comparison_inputs"]["names"], ["clean-run"])
            self.assertIn("handoff_batch_maturity_ci_regression_count", csv_text)
            self.assertIn("handoff_batch_maturity_ci_regression_reason_counts", csv_text)
            self.assertIn("missing-ci-step:1, workflow-order-regressed:1", csv_text)
            self.assertIn("review;standard", csv_text)
            self.assertIn("Handoff batch CI regressions", markdown)
            self.assertIn("Handoff batch CI regression reasons", markdown)
            self.assertIn("Handoff selected batch CI regression reasons", markdown)
            self.assertIn("workflow-order-regressed:1", markdown)
            self.assertIn("CI Regressions", markdown)
            self.assertIn("Handoff CI regressions", html)
            self.assertIn("Handoff CI reasons", html)
            self.assertIn("Selected CI reasons", html)
            self.assertIn("missing-ci-step:1, workflow-order-regressed:1", " ".join(report["recommendations"]))

    def test_handoff_batch_suite_design_regression_is_carried_and_excluded_when_clean_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = make_promotion(root, "clean", "promoted", require_clean_batch_review=True, clean_batch_review_status="clean")
            suite_regressed = make_promotion(
                root,
                "suite-regressed",
                "promoted",
                require_clean_batch_review=True,
                clean_batch_review_status="clean",
                batch_suite_design_regression_count=2,
                batch_suite_design_regression_names=["review", "standard"],
                selected_batch_suite_design_regression_count=1,
                selected_batch_suite_design_regression_names=["review"],
            )

            report = build_training_scale_promotion_index([clean, suite_regressed], names=["clean-run", "suite-run"])
            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            completed = __import__("subprocess").run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "index_training_scale_promotions.py"),
                    "--out-dir",
                    str(root / "script-index"),
                    str(clean),
                    str(suite_regressed),
                    "--name",
                    "clean-run",
                    "--name",
                    "suite-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertEqual(report["summary"]["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(report["summary"]["handoff_clean_batch_review_count"], 1)
            self.assertEqual(report["summary"]["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(report["summary"]["handoff_selected_batch_maturity_suite_design_regression_total"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_suite_design_regression_names"], ["review", "standard"])
            self.assertEqual(report["summary"]["handoff_selected_batch_maturity_suite_design_regression_names"], ["review"])
            self.assertTrue(report["promotions"][0]["promoted_for_comparison"])
            self.assertFalse(report["promotions"][1]["promoted_for_comparison"])
            self.assertEqual(report["promotions"][1]["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(report["promotions"][1]["handoff_batch_maturity_suite_design_regression_names"], ["review", "standard"])
            self.assertEqual(report["comparison_inputs"]["names"], ["clean-run"])
            self.assertIn("handoff_batch_maturity_suite_design_regression_count", csv_text)
            self.assertIn("review;standard", csv_text)
            self.assertIn("Handoff batch suite-design regressions", markdown)
            self.assertIn("Handoff selected batch suite-design names", markdown)
            self.assertIn("Suite-Design Regressions", markdown)
            self.assertIn("Handoff suite-design regressions", html)
            self.assertIn("Selected suite-design names", html)
            self.assertIn("suite-design regression evidence", " ".join(report["recommendations"]))
            self.assertIn("handoff_batch_maturity_suite_design_regression_count=2", completed.stdout)
            self.assertIn("handoff_selected_batch_maturity_suite_design_regression_total=1", completed.stdout)
            self.assertIn('handoff_batch_maturity_suite_design_regression_names=["review", "standard"]', completed.stdout)
            self.assertIn('handoff_selected_batch_maturity_suite_design_regression_names=["review"]', completed.stdout)

    def test_index_script_reports_suite_guard_counts_and_reason_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted", include_suite_guard=True)
            beta = make_promotion(
                root,
                "beta",
                "promoted",
                include_suite_guard=True,
                require_clean_batch_review=True,
                batch_ci_regression_count=1,
                batch_ci_regression_reason_counts={"workflow-status-regressed": 1},
            )

            out_dir = root / "index"
            command = [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "index_training_scale_promotions.py"),
                "--out-dir",
                str(out_dir),
                "--title",
                "MiniGPT v207 training scale promotion index",
                str(alpha),
                str(beta),
                "--name",
                "alpha-run",
                "--name",
                "beta-run",
            ]
            completed = __import__("subprocess").run(command, check=True, capture_output=True, text=True)

            self.assertIn("handoff_require_suite_consistency_count=2", completed.stdout)
            self.assertIn("handoff_suite_consistent_count=2", completed.stdout)
            self.assertIn("handoff_suite_mismatch_total=0", completed.stdout)
            self.assertIn("handoff_selected_suite_path_count=2", completed.stdout)
            self.assertIn("handoff_require_clean_batch_review_count=1", completed.stdout)
            self.assertIn("handoff_unclean_batch_review_count=1", completed.stdout)
            self.assertIn("handoff_batch_maturity_ci_regression_count=1", completed.stdout)
            self.assertIn('handoff_batch_maturity_ci_regression_reason_counts={"workflow-status-regressed": 1}', completed.stdout)
            self.assertIn('handoff_selected_batch_maturity_ci_regression_reason_counts={"workflow-status-regressed": 1}', completed.stdout)
            self.assertIn("handoff_selected_batch_review_count=0", completed.stdout)
            self.assertIn("handoff_batch_comparison_blocker_action_total=0", completed.stdout)
            self.assertTrue((out_dir / "training_scale_promotion_index.json").exists())
            self.assertTrue((out_dir / "training_scale_promotion_index.html").exists())

    def test_helper_module_still_drives_comparison_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = make_promotion(root, "alpha", "promoted")
            report = build_training_scale_promotion_index([promoted], names=["alpha-run"])

            comparison = promotion_helpers._comparison_inputs(report["promotions"], None)

            self.assertEqual(comparison["names"], ["alpha-run"])
            self.assertFalse(comparison["compare_command_ready"])
            self.assertEqual(promotion_helpers._summary(report["promotions"], report["comparison_inputs"])["promoted_count"], 1)


def make_promotion(
    root: Path,
    name: str,
    status: str,
    title: str | None = None,
    *,
    include_suite_guard: bool = False,
    require_clean_batch_review: bool = False,
    clean_batch_review_status: str | None = None,
    selected_batch_review_status: str = "clean",
    batch_suite_design_regression_count: int = 0,
    batch_suite_design_regression_names: list[str] | None = None,
    selected_batch_suite_design_regression_count: int | None = None,
    selected_batch_suite_design_regression_names: list[str] | None = None,
    batch_ci_regression_count: int = 0,
    batch_ci_regression_names: list[str] | None = None,
    batch_ci_regression_reason_counts: dict[str, int] | None = None,
    selected_batch_ci_regression_reason_counts: dict[str, int] | None = None,
) -> Path:
    promotion_root = root / name / "promotion"
    run_root = root / name / "scale-run"
    run_json = run_root / "training_scale_run.json"
    batch_json = run_root / "batch" / "training_portfolio_batch.json"
    portfolio_json = run_root / "batch" / "variants" / name / "training_portfolio.json"
    checkpoint = run_root / "batch" / "variants" / name / "runs" / name / "checkpoint.pt"
    registry = run_root / "batch" / "variants" / name / "registry" / "registry.json"
    narrative = run_root / "batch" / "variants" / name / "maturity-narrative" / "maturity_narrative.json"
    selected_suite_design_count = (
        batch_suite_design_regression_count
        if selected_batch_suite_design_regression_count is None
        else selected_batch_suite_design_regression_count
    )
    selected_suite_design_names = (
        batch_suite_design_regression_names
        if selected_batch_suite_design_regression_names is None
        else selected_batch_suite_design_regression_names
    )
    for path in [run_json, batch_json, portfolio_json, checkpoint, registry, narrative]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if path.suffix == ".json" else "checkpoint", encoding="utf-8")
    variant_status = "ready" if status == "promoted" else "review"
    suite_guard = {}
    summary_suite_fields = {}
    if include_suite_guard:
        suite_guard = {
            "handoff_require_suite_consistency": True,
            "handoff_suite_consistency": "consistent",
            "handoff_suite_mismatch_count": 0,
            "handoff_selected_suite_path": "builtin:standard-zh",
        }
        summary_suite_fields = {
            "handoff_require_suite_consistency": True,
            "handoff_suite_consistency": "consistent",
            "handoff_suite_mismatch_count": 0,
            "handoff_selected_suite_path": "builtin:standard-zh",
        }
    report = {
        "title": title or f"{name} promotion",
        "generated_at": "2026-05-14T00:00:00Z",
        "handoff_path": str(root / name / "handoff" / "training_scale_handoff.json"),
        "project_root": str(root),
        "out_root": str(run_root),
        "training_scale_run_path": str(run_json),
        "batch_path": str(batch_json),
        "summary": {
            "promotion_status": status,
            "handoff_status": "completed" if status != "blocked" else "failed",
            "scale_run_status": "completed" if status != "blocked" else "blocked",
            "batch_status": "completed" if status != "blocked" else "skipped",
            "variant_count": 1,
            "ready_variant_count": 1 if status == "promoted" else 0,
            "checkpoint_count": 1,
            "registry_count": 1,
            "maturity_narrative_count": 1,
            "required_artifact_count": 9,
            "available_required_artifact_count": 9 if status == "promoted" else 7,
            "blocker_count": 1 if status == "blocked" else 0,
            "review_item_count": 1 if status == "review" else 0,
            "handoff_selected_batch_review_status": selected_batch_review_status,
            "handoff_require_clean_batch_review": require_clean_batch_review,
            "handoff_clean_batch_review_status": clean_batch_review_status or selected_batch_review_status,
            "handoff_selected_batch_comparison_review_action_count": (
                2 if selected_batch_review_status in {"review", "blocker"} else 0
            ),
            "handoff_selected_batch_comparison_blocker_action_count": 1 if selected_batch_review_status == "blocker" else 0,
            "handoff_selected_batch_maturity_coverage_regression_count": (
                1 if selected_batch_review_status in {"review", "blocker"} else 0
            ),
            "handoff_selected_batch_maturity_suite_design_regression_count": selected_suite_design_count,
            "handoff_selected_batch_maturity_suite_design_regression_names": selected_suite_design_names or [],
            "handoff_selected_batch_maturity_ci_regression_count": batch_ci_regression_count,
            "handoff_selected_batch_maturity_ci_regression_reason_counts": selected_batch_ci_regression_reason_counts
            or batch_ci_regression_reason_counts
            or {},
            "handoff_batch_comparison_review_action_count": 2 if selected_batch_review_status in {"review", "blocker"} else 0,
            "handoff_batch_comparison_blocker_action_count": 1 if selected_batch_review_status == "blocker" else 0,
            "handoff_batch_comparison_blocker_reasons": (
                ["coverage-regressed"] if selected_batch_review_status == "blocker" else []
            ),
            "handoff_batch_maturity_ci_regression_count": batch_ci_regression_count,
            "handoff_batch_maturity_ci_regression_reason_counts": batch_ci_regression_reason_counts or {},
            "handoff_batch_maturity_ci_regression_names": batch_ci_regression_names or [],
            "handoff_batch_maturity_suite_design_regression_count": batch_suite_design_regression_count,
            "handoff_batch_maturity_suite_design_regression_names": batch_suite_design_regression_names or [],
            **summary_suite_fields,
        },
        "suite_guard": suite_guard,
        "clean_batch_review_guard": {
            "handoff_require_clean_batch_review": require_clean_batch_review,
            "handoff_clean_batch_review_status": clean_batch_review_status or selected_batch_review_status,
            "handoff_batch_maturity_ci_regression_count": batch_ci_regression_count,
            "handoff_batch_maturity_ci_regression_reason_counts": batch_ci_regression_reason_counts or {},
            "handoff_batch_maturity_ci_regression_names": batch_ci_regression_names or [],
            "handoff_batch_maturity_suite_design_regression_count": batch_suite_design_regression_count,
            "handoff_batch_maturity_suite_design_regression_names": batch_suite_design_regression_names or [],
        }
        if require_clean_batch_review
        else {},
        "variants": [
            {
                "name": f"{name}-variant",
                "promotion_status": variant_status,
                "portfolio_json": str(portfolio_json),
                "missing_required": [] if status == "promoted" else ["registry", "maturity_narrative"],
                "artifact_rows": [
                    {"key": "checkpoint", "path": str(checkpoint), "exists": True},
                    {"key": "registry", "path": str(registry), "exists": status == "promoted"},
                    {"key": "maturity_narrative", "path": str(narrative), "exists": status == "promoted"},
                ],
            }
        ],
        "blockers": ["handoff status is failed"] if status == "blocked" else [],
        "review_items": ["variant missing registry, maturity_narrative"] if status == "review" else [],
    }
    write_json(promotion_root / "training_scale_promotion.json", report)
    return promotion_root


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
