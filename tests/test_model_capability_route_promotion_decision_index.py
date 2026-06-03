from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_decision_index import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME,
    build_model_capability_route_promotion_decision_index,
    load_route_promotion_review_decision,
    locate_route_promotion_review_decision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_decision_index_artifacts import (
    render_model_capability_route_promotion_decision_index_html,
    render_model_capability_route_promotion_decision_index_markdown,
    render_model_capability_route_promotion_decision_index_text,
    write_model_capability_route_promotion_decision_index_outputs,
)
from minigpt.model_capability_route_promotion_review_decision import MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME
from scripts.build_model_capability_route_promotion_decision_index import main as cli_main
from tests.test_model_capability_route_promotion_review_decision import ready_packet_review
from minigpt.model_capability_route_promotion_review_decision import build_model_capability_route_promotion_review_decision


def ready_review_decision(root: Path) -> tuple[dict, Path]:
    review, review_path = ready_packet_review(root)
    decision = build_model_capability_route_promotion_review_decision(review, release_packet_review_path=review_path)
    out_dir = root / "decision"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME
    path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
    return decision, path


class ModelCapabilityRoutePromotionDecisionIndexTests(unittest.TestCase):
    def test_builds_ready_index_from_accepted_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, decision_path = ready_review_decision(Path(tmp))
            report = build_model_capability_route_promotion_decision_index([decision], source_decision_paths=[decision_path])

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_decision_index_ready")
        self.assertTrue(report["summary"]["decision_index_ready"])
        self.assertEqual(report["summary"]["accepted_route_count"], 1)
        self.assertEqual(report["entries"][0]["entry_status"], "accepted")
        self.assertEqual(report["entries"][0]["route_id"], "objective_level_contrast")
        self.assertEqual(resolve_exit_code(report, require_ready_index=True), 0)

    def test_rejects_non_accepted_final_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision, _ = ready_review_decision(Path(tmp))
            decision["final_decision"]["decision"] = "reject_or_repair_bounded_route_promotion"
            report = build_model_capability_route_promotion_decision_index([decision])

        self.assertEqual(report["status"], "fail")
        self.assertIn("blocked_sources_absent", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_index=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, decision_path = ready_review_decision(root)
            self.assertEqual(locate_route_promotion_review_decision(decision_path.parent), decision_path)
            report = build_model_capability_route_promotion_decision_index([load_route_promotion_review_decision(decision_path)])
            outputs = write_model_capability_route_promotion_decision_index_outputs(report, root / "index")
            cli_main([str(decision_path.parent), "--out-dir", str(root / "cli-index"), "--require-ready-index", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue((Path(outputs["json"]).name == MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME))
        self.assertIn("decision_index_ready=True", render_model_capability_route_promotion_decision_index_text(report))
        self.assertIn("Route Entries", render_model_capability_route_promotion_decision_index_markdown(report))
        self.assertIn("route promotion decision index", render_model_capability_route_promotion_decision_index_html(report))


if __name__ == "__main__":
    unittest.main()
