from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_decision_index import build_model_capability_route_promotion_decision_index, load_route_promotion_review_decision
from minigpt.model_capability_route_promotion_decision_index_artifacts import write_model_capability_route_promotion_decision_index_outputs
from minigpt.model_capability_route_promotion_decision_index_check import (
    build_model_capability_route_promotion_decision_index_check,
    locate_route_promotion_decision_index,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_decision_index_check_artifacts import (
    render_model_capability_route_promotion_decision_index_check_html,
    render_model_capability_route_promotion_decision_index_check_markdown,
    render_model_capability_route_promotion_decision_index_check_text,
    write_model_capability_route_promotion_decision_index_check_outputs,
)
from scripts.check_model_capability_route_promotion_decision_index import main as cli_main
from tests.test_model_capability_route_promotion_decision_index import ready_review_decision


def ready_decision_index(root: Path) -> tuple[dict, Path]:
    _, decision_path = ready_review_decision(root)
    index = build_model_capability_route_promotion_decision_index([load_route_promotion_review_decision(decision_path)])
    outputs = write_model_capability_route_promotion_decision_index_outputs(index, root / "index")
    return index, Path(outputs["json"])


class ModelCapabilityRoutePromotionDecisionIndexCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_decision_index(Path(tmp))
            report = build_model_capability_route_promotion_decision_index_check(index, decision_index_path=index_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_decision_index_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_route_entry_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, _ = ready_decision_index(Path(tmp))
            index["entries"][0]["route_id"] = "tampered_route"
            report = build_model_capability_route_promotion_decision_index_check(index)

        self.assertEqual(report["status"], "fail")
        self.assertIn("entries", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_check_fails_without_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, _ = ready_decision_index(Path(tmp))
            index["summary"]["source_decision_paths"] = []
            index["sources"][0]["source_decision_path"] = ""
            report = build_model_capability_route_promotion_decision_index_check(index)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_paths_present", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_decision_index(root)
            self.assertEqual(locate_route_promotion_decision_index(index_path.parent), index_path)
            report = build_model_capability_route_promotion_decision_index_check(index, decision_index_path=index_path)
            outputs = write_model_capability_route_promotion_decision_index_check_outputs(report, root / "check")
            cli_main(["--decision-index", str(index_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("contract_check_ready=True", render_model_capability_route_promotion_decision_index_check_text(report))
        self.assertIn("Checks", render_model_capability_route_promotion_decision_index_check_markdown(report))
        self.assertIn("contract check", render_model_capability_route_promotion_decision_index_check_html(report))


if __name__ == "__main__":
    unittest.main()
