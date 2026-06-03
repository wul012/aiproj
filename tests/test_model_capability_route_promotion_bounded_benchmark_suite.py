from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    build_model_capability_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_consumer_plan,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_artifacts import (
    render_model_capability_route_promotion_bounded_benchmark_suite_html,
    render_model_capability_route_promotion_bounded_benchmark_suite_markdown,
    render_model_capability_route_promotion_bounded_benchmark_suite_text,
    write_model_capability_route_promotion_bounded_benchmark_suite_outputs,
)
from minigpt.model_capability_route_promotion_consumer_plan import build_model_capability_route_promotion_consumer_plan
from minigpt.model_capability_route_promotion_consumer_plan_artifacts import write_model_capability_route_promotion_consumer_plan_outputs
from scripts.build_model_capability_route_promotion_bounded_benchmark_suite import main as cli_main
from tests.test_model_capability_route_promotion_consumer_plan import ready_downstream_guard


def ready_consumer_plan(root: Path) -> tuple[dict, Path]:
    guard, guard_path = ready_downstream_guard(root)
    plan = build_model_capability_route_promotion_consumer_plan(guard, downstream_guard_path=guard_path)
    outputs = write_model_capability_route_promotion_consumer_plan_outputs(plan, root / "plan")
    return plan, Path(outputs["json"])


class ModelCapabilityRoutePromotionBoundedBenchmarkSuiteTests(unittest.TestCase):
    def test_builds_ready_bounded_benchmark_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan, plan_path = ready_consumer_plan(Path(tmp))
            report = build_model_capability_route_promotion_bounded_benchmark_suite(plan, consumer_plan_path=plan_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_benchmark_suite_ready")
        self.assertTrue(report["summary"]["bounded_benchmark_suite_ready"])
        self.assertEqual(report["summary"]["case_count"], 5)
        self.assertEqual(report["summary"]["expected_terms"], ["fixed", "loss"])
        self.assertEqual(resolve_exit_code(report, require_ready_suite=True), 0)

    def test_blocks_when_next_artifact_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan, _ = ready_consumer_plan(Path(tmp))
            plan["summary"]["proposed_next_artifact"] = "production_release_suite"
            report = build_model_capability_route_promotion_bounded_benchmark_suite(plan)

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_suite=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan, plan_path = ready_consumer_plan(root)
            self.assertEqual(locate_route_promotion_consumer_plan(plan_path.parent), plan_path)
            report = build_model_capability_route_promotion_bounded_benchmark_suite(plan, consumer_plan_path=plan_path)
            outputs = write_model_capability_route_promotion_bounded_benchmark_suite_outputs(report, root / "suite")
            cli_main(["--consumer-plan", str(plan_path.parent), "--out-dir", str(root / "cli-suite"), "--require-ready-suite", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bounded_benchmark_suite_ready=True", render_model_capability_route_promotion_bounded_benchmark_suite_text(report))
        self.assertIn("Expected terms", render_model_capability_route_promotion_bounded_benchmark_suite_markdown(report))
        self.assertIn("bounded benchmark suite", render_model_capability_route_promotion_bounded_benchmark_suite_html(report))


if __name__ == "__main__":
    unittest.main()
