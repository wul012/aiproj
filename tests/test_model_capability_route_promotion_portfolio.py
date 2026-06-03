from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_history import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME,
    build_model_capability_route_promotion_history,
)
from minigpt.model_capability_route_promotion_portfolio import (
    build_model_capability_route_promotion_portfolio,
    locate_route_promotion_history,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_portfolio_artifacts import (
    render_model_capability_route_promotion_portfolio_html,
    render_model_capability_route_promotion_portfolio_markdown,
    render_model_capability_route_promotion_portfolio_text,
    write_model_capability_route_promotion_portfolio_outputs,
)
from scripts.build_model_capability_route_promotion_portfolio import main as cli_main
from tests.test_model_capability_route_promotion_history import _write_manifest, ready_promotion_manifest


def ready_history(root: Path) -> tuple[dict, Path]:
    manifest_path = _write_manifest(root, ready_promotion_manifest())
    history = build_model_capability_route_promotion_history([manifest_path])
    history_dir = root / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME
    history_path.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")
    return history, history_path


class ModelCapabilityRoutePromotionPortfolioTests(unittest.TestCase):
    def test_builds_ready_portfolio_from_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history, history_path = ready_history(Path(tmp))
            report = build_model_capability_route_promotion_portfolio(history, source_history_path=history_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_portfolio_ready")
        self.assertTrue(report["summary"]["route_promotion_portfolio_ready"])
        self.assertEqual(report["summary"]["active_route_count"], 1)
        self.assertEqual(report["portfolio"]["active_routes"], ["objective_level_contrast"])
        self.assertEqual(resolve_exit_code(report, require_ready_portfolio=True), 0)

    def test_rejects_history_with_boundary_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history, _ = ready_history(root)
            history["entries"][0]["boundary"] = "production_model_quality"
            report = build_model_capability_route_promotion_portfolio(history)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_boundary_mismatches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_ready_portfolio=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history, history_path = ready_history(root)
            history_dir = history_path.parent
            self.assertEqual(locate_route_promotion_history(history_dir), history_path)

            report = build_model_capability_route_promotion_portfolio(history, source_history_path=history_path)
            outputs = write_model_capability_route_promotion_portfolio_outputs(report, root / "portfolio")
            cli_main(["--history", str(history_dir), "--out-dir", str(root / "cli-portfolio"), "--require-ready-portfolio", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("route_promotion_portfolio_ready=True", render_model_capability_route_promotion_portfolio_text(report))
        self.assertIn("Route Cards", render_model_capability_route_promotion_portfolio_markdown(report))
        self.assertIn("model capability route promotion portfolio", render_model_capability_route_promotion_portfolio_html(report))


if __name__ == "__main__":
    unittest.main()
