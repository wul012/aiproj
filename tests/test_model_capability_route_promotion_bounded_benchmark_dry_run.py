from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run import (
    build_model_capability_route_promotion_bounded_benchmark_dry_run,
    locate_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_bounded_benchmark_suite_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run_artifacts import (
    render_model_capability_route_promotion_bounded_benchmark_dry_run_html,
    render_model_capability_route_promotion_bounded_benchmark_dry_run_markdown,
    render_model_capability_route_promotion_bounded_benchmark_dry_run_text,
    write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import build_model_capability_route_promotion_bounded_benchmark_suite_review
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review_artifacts import write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs
from scripts.run_model_capability_route_promotion_bounded_benchmark_dry_run import main as cli_main
from tests.test_model_capability_route_promotion_bounded_benchmark_suite_review import ready_bounded_suite


def ready_suite_and_review(root: Path) -> tuple[dict, Path, dict, Path]:
    suite, suite_path = ready_bounded_suite(root)
    review = build_model_capability_route_promotion_bounded_benchmark_suite_review(suite, benchmark_suite_path=suite_path)
    review_outputs = write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs(review, root / "review")
    return suite, suite_path, review, Path(review_outputs["json"])


class ModelCapabilityRoutePromotionBoundedBenchmarkDryRunTests(unittest.TestCase):
    def test_dry_run_validates_scoring_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, suite_path, review, review_path = ready_suite_and_review(Path(tmp))
            report = build_model_capability_route_promotion_bounded_benchmark_dry_run(review, suite, suite_review_path=review_path, benchmark_suite_path=suite_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_benchmark_dry_run_passed")
        self.assertEqual(report["summary"]["passed_case_count"], 5)
        self.assertFalse(report["summary"]["negative_control_passed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_dry_run_fails_when_positive_continuation_misses_term(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, _, review, _ = ready_suite_and_review(Path(tmp))
            report = build_model_capability_route_promotion_bounded_benchmark_dry_run(review, suite, positive_continuation="fixed only")

        self.assertEqual(report["status"], "fail")
        self.assertIn("positive_rows_pass", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path = ready_suite_and_review(root)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite_review(review_path.parent), review_path)
            report = build_model_capability_route_promotion_bounded_benchmark_dry_run(review, suite, suite_review_path=review_path, benchmark_suite_path=suite_path)
            outputs = write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs(report, root / "dry-run")
            cli_main(["--benchmark-suite", str(suite_path.parent), "--suite-review", str(review_path.parent), "--out-dir", str(root / "cli-dry-run"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bounded_benchmark_dry_run_ready=True", render_model_capability_route_promotion_bounded_benchmark_dry_run_text(report))
        self.assertIn("Dry Run Rows", render_model_capability_route_promotion_bounded_benchmark_dry_run_markdown(report))
        self.assertIn("dry run", render_model_capability_route_promotion_bounded_benchmark_dry_run_html(report))


if __name__ == "__main__":
    unittest.main()
