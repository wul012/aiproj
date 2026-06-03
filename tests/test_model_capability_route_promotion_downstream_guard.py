from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_downstream_guard import (
    build_model_capability_route_promotion_downstream_guard,
    locate_route_promotion_governance_snapshot,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_downstream_guard_artifacts import (
    render_model_capability_route_promotion_downstream_guard_html,
    render_model_capability_route_promotion_downstream_guard_markdown,
    render_model_capability_route_promotion_downstream_guard_text,
    write_model_capability_route_promotion_downstream_guard_outputs,
)
from minigpt.model_capability_route_promotion_governance_snapshot import build_model_capability_route_promotion_governance_snapshot
from minigpt.model_capability_route_promotion_governance_snapshot_artifacts import write_model_capability_route_promotion_governance_snapshot_outputs
from scripts.check_model_capability_route_promotion_downstream_guard import main as cli_main
from tests.test_model_capability_route_promotion_governance_snapshot import ready_snapshot_inputs


def ready_governance_snapshot(root: Path) -> tuple[dict, Path]:
    index, index_path, check, check_path = ready_snapshot_inputs(root)
    snapshot = build_model_capability_route_promotion_governance_snapshot(index, check, decision_index_path=index_path, index_contract_check_path=check_path)
    outputs = write_model_capability_route_promotion_governance_snapshot_outputs(snapshot, root / "snapshot")
    return snapshot, Path(outputs["json"])


class ModelCapabilityRoutePromotionDownstreamGuardTests(unittest.TestCase):
    def test_allows_bounded_consumer_for_verified_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, snapshot_path = ready_governance_snapshot(Path(tmp))
            report = build_model_capability_route_promotion_downstream_guard(
                snapshot,
                route_id="objective_level_contrast",
                consumer_name="bounded-benchmark-planner",
                governance_snapshot_path=snapshot_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_downstream_guard_allowed")
        self.assertTrue(report["summary"]["access_allowed"])
        self.assertEqual(report["summary"]["route_id"], "objective_level_contrast")
        self.assertEqual(resolve_exit_code(report, require_allowed=True), 0)

    def test_rejects_wider_requested_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, _ = ready_governance_snapshot(Path(tmp))
            report = build_model_capability_route_promotion_downstream_guard(
                snapshot,
                route_id="objective_level_contrast",
                consumer_name="production-release-planner",
                requested_scope="production_model_release",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_scope_allowed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_allowed=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot, snapshot_path = ready_governance_snapshot(root)
            self.assertEqual(locate_route_promotion_governance_snapshot(snapshot_path.parent), snapshot_path)
            report = build_model_capability_route_promotion_downstream_guard(snapshot, route_id="objective_level_contrast", consumer_name="bounded-benchmark-planner")
            outputs = write_model_capability_route_promotion_downstream_guard_outputs(report, root / "guard")
            cli_main([
                "--governance-snapshot",
                str(snapshot_path.parent),
                "--route-id",
                "objective_level_contrast",
                "--consumer-name",
                "bounded-benchmark-planner",
                "--out-dir",
                str(root / "cli-guard"),
                "--require-allowed",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("access_allowed=True", render_model_capability_route_promotion_downstream_guard_text(report))
        self.assertIn("bounded-benchmark-planner", render_model_capability_route_promotion_downstream_guard_markdown(report))
        self.assertIn("downstream guard", render_model_capability_route_promotion_downstream_guard_html(report))


if __name__ == "__main__":
    unittest.main()
