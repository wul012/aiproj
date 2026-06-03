from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import build_model_capability_route_promotion_bounded_benchmark_suite
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_artifacts import write_model_capability_route_promotion_bounded_benchmark_suite_outputs
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import (
    build_model_capability_route_promotion_bounded_benchmark_suite_review,
    locate_route_promotion_bounded_benchmark_suite,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review_artifacts import (
    render_model_capability_route_promotion_bounded_benchmark_suite_review_html,
    render_model_capability_route_promotion_bounded_benchmark_suite_review_markdown,
    render_model_capability_route_promotion_bounded_benchmark_suite_review_text,
    write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs,
)
from scripts.review_model_capability_route_promotion_bounded_benchmark_suite import main as cli_main
from tests.test_model_capability_route_promotion_bounded_benchmark_suite import ready_consumer_plan


def ready_bounded_suite(root: Path) -> tuple[dict, Path]:
    plan, plan_path = ready_consumer_plan(root)
    suite = build_model_capability_route_promotion_bounded_benchmark_suite(plan, consumer_plan_path=plan_path)
    outputs = write_model_capability_route_promotion_bounded_benchmark_suite_outputs(suite, root / "suite")
    return suite, Path(outputs["json"])


class ModelCapabilityRoutePromotionBoundedBenchmarkSuiteReviewTests(unittest.TestCase):
    def test_reviews_ready_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, suite_path = ready_bounded_suite(Path(tmp))
            report = build_model_capability_route_promotion_bounded_benchmark_suite_review(suite, benchmark_suite_path=suite_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_benchmark_suite_review_ready")
        self.assertTrue(report["summary"]["approved_for_execution"])
        self.assertEqual(report["summary"]["passed_case_review_count"], 5)
        self.assertEqual(resolve_exit_code(report, require_ready_review=True), 0)

    def test_fails_when_expected_terms_are_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, _ = ready_bounded_suite(Path(tmp))
            suite["benchmark_suite"]["cases"][0]["expected_terms"] = ["fixed"]
            report = build_model_capability_route_promotion_bounded_benchmark_suite_review(suite)

        self.assertEqual(report["status"], "fail")
        self.assertIn("case_reviews_clean", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_review=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path = ready_bounded_suite(root)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite(suite_path.parent), suite_path)
            report = build_model_capability_route_promotion_bounded_benchmark_suite_review(suite, benchmark_suite_path=suite_path)
            outputs = write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs(report, root / "review")
            cli_main(["--benchmark-suite", str(suite_path.parent), "--out-dir", str(root / "cli-review"), "--require-ready-review", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("approved_for_execution=True", render_model_capability_route_promotion_bounded_benchmark_suite_review_text(report))
        self.assertIn("Case Reviews", render_model_capability_route_promotion_bounded_benchmark_suite_review_markdown(report))
        self.assertIn("suite review", render_model_capability_route_promotion_bounded_benchmark_suite_review_html(report))


if __name__ == "__main__":
    unittest.main()
