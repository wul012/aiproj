from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_consumer_plan import (
    build_model_capability_route_promotion_consumer_plan,
    locate_route_promotion_downstream_guard,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_consumer_plan_artifacts import (
    render_model_capability_route_promotion_consumer_plan_html,
    render_model_capability_route_promotion_consumer_plan_markdown,
    render_model_capability_route_promotion_consumer_plan_text,
    write_model_capability_route_promotion_consumer_plan_outputs,
)
from minigpt.model_capability_route_promotion_downstream_guard import build_model_capability_route_promotion_downstream_guard
from minigpt.model_capability_route_promotion_downstream_guard_artifacts import write_model_capability_route_promotion_downstream_guard_outputs
from scripts.build_model_capability_route_promotion_consumer_plan import main as cli_main
from tests.test_model_capability_route_promotion_downstream_guard import ready_governance_snapshot


def ready_downstream_guard(root: Path) -> tuple[dict, Path]:
    snapshot, snapshot_path = ready_governance_snapshot(root)
    guard = build_model_capability_route_promotion_downstream_guard(
        snapshot,
        route_id="objective_level_contrast",
        consumer_name="bounded-benchmark-planner",
        governance_snapshot_path=snapshot_path,
    )
    outputs = write_model_capability_route_promotion_downstream_guard_outputs(guard, root / "guard")
    return guard, Path(outputs["json"])


class ModelCapabilityRoutePromotionConsumerPlanTests(unittest.TestCase):
    def test_builds_ready_consumer_plan_from_allowed_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard, guard_path = ready_downstream_guard(Path(tmp))
            report = build_model_capability_route_promotion_consumer_plan(guard, downstream_guard_path=guard_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_consumer_plan_ready")
        self.assertTrue(report["summary"]["consumer_plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_benchmark_suite")
        self.assertEqual(report["summary"]["plan_step_count"], 5)
        self.assertEqual(resolve_exit_code(report, require_ready_plan=True), 0)

    def test_blocks_when_guard_is_not_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard, _ = ready_downstream_guard(Path(tmp))
            guard["summary"]["access_allowed"] = False
            guard["access_decision"]["allowed"] = False
            report = build_model_capability_route_promotion_consumer_plan(guard)

        self.assertEqual(report["status"], "fail")
        self.assertIn("access_allowed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_plan=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guard, guard_path = ready_downstream_guard(root)
            self.assertEqual(locate_route_promotion_downstream_guard(guard_path.parent), guard_path)
            report = build_model_capability_route_promotion_consumer_plan(guard, downstream_guard_path=guard_path)
            outputs = write_model_capability_route_promotion_consumer_plan_outputs(report, root / "plan")
            cli_main(["--downstream-guard", str(guard_path.parent), "--out-dir", str(root / "cli-plan"), "--require-ready-plan", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("consumer_plan_ready=True", render_model_capability_route_promotion_consumer_plan_text(report))
        self.assertIn("Plan Steps", render_model_capability_route_promotion_consumer_plan_markdown(report))
        self.assertIn("consumer plan", render_model_capability_route_promotion_consumer_plan_html(report))


if __name__ == "__main__":
    unittest.main()
