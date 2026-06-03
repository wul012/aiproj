from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_decision_index_check import build_model_capability_route_promotion_decision_index_check
from minigpt.model_capability_route_promotion_decision_index_check_artifacts import write_model_capability_route_promotion_decision_index_check_outputs
from minigpt.model_capability_route_promotion_governance_snapshot import (
    build_model_capability_route_promotion_governance_snapshot,
    locate_route_promotion_decision_index,
    locate_route_promotion_decision_index_check,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_governance_snapshot_artifacts import (
    render_model_capability_route_promotion_governance_snapshot_html,
    render_model_capability_route_promotion_governance_snapshot_markdown,
    render_model_capability_route_promotion_governance_snapshot_text,
    write_model_capability_route_promotion_governance_snapshot_outputs,
)
from scripts.build_model_capability_route_promotion_governance_snapshot import main as cli_main
from tests.test_model_capability_route_promotion_decision_index_check import ready_decision_index


def ready_snapshot_inputs(root: Path) -> tuple[dict, Path, dict, Path]:
    index, index_path = ready_decision_index(root)
    check = build_model_capability_route_promotion_decision_index_check(index, decision_index_path=index_path)
    check_outputs = write_model_capability_route_promotion_decision_index_check_outputs(check, root / "index-check")
    return index, index_path, check, Path(check_outputs["json"])


class ModelCapabilityRoutePromotionGovernanceSnapshotTests(unittest.TestCase):
    def test_builds_ready_governance_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path, check, check_path = ready_snapshot_inputs(Path(tmp))
            report = build_model_capability_route_promotion_governance_snapshot(index, check, decision_index_path=index_path, index_contract_check_path=check_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_governance_snapshot_ready")
        self.assertTrue(report["summary"]["governance_snapshot_ready"])
        self.assertEqual(report["summary"]["verified_route_count"], 1)
        self.assertEqual(report["route_cards"][0]["verification_status"], "contract_verified")
        self.assertEqual(report["downstream_policy"]["allowed"], True)
        self.assertEqual(resolve_exit_code(report, require_ready_snapshot=True), 0)

    def test_blocks_when_contract_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path, check, check_path = ready_snapshot_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_model_capability_route_promotion_governance_snapshot(index, check, decision_index_path=index_path, index_contract_check_path=check_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_snapshot=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path, check, check_path = ready_snapshot_inputs(root)
            self.assertEqual(locate_route_promotion_decision_index(index_path.parent), index_path)
            self.assertEqual(locate_route_promotion_decision_index_check(check_path.parent), check_path)
            report = build_model_capability_route_promotion_governance_snapshot(index, check, decision_index_path=index_path, index_contract_check_path=check_path)
            outputs = write_model_capability_route_promotion_governance_snapshot_outputs(report, root / "snapshot")
            cli_main(["--decision-index", str(index_path.parent), "--index-check", str(check_path.parent), "--out-dir", str(root / "cli-snapshot"), "--require-ready-snapshot", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("governance_snapshot_ready=True", render_model_capability_route_promotion_governance_snapshot_text(report))
        self.assertIn("Route Cards", render_model_capability_route_promotion_governance_snapshot_markdown(report))
        self.assertIn("governance snapshot", render_model_capability_route_promotion_governance_snapshot_html(report))


if __name__ == "__main__":
    unittest.main()
