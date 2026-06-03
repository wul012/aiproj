from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_portfolio import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME,
    build_model_capability_route_promotion_portfolio,
)
from minigpt.model_capability_route_promotion_regression_monitor import (
    build_model_capability_route_promotion_regression_monitor,
    locate_route_promotion_portfolio,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_regression_monitor_artifacts import (
    render_model_capability_route_promotion_regression_monitor_html,
    render_model_capability_route_promotion_regression_monitor_markdown,
    render_model_capability_route_promotion_regression_monitor_text,
    write_model_capability_route_promotion_regression_monitor_outputs,
)
from scripts.check_model_capability_route_promotion_regression import main as cli_main
from tests.test_model_capability_route_promotion_portfolio import ready_history


def ready_portfolio(root: Path) -> dict:
    history, history_path = ready_history(root)
    return build_model_capability_route_promotion_portfolio(history, source_history_path=history_path)


class ModelCapabilityRoutePromotionRegressionMonitorTests(unittest.TestCase):
    def test_monitor_passes_when_current_matches_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            portfolio = ready_portfolio(Path(tmp))

            report = build_model_capability_route_promotion_regression_monitor(portfolio, baseline_portfolio=portfolio)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_regression_monitor_passed")
        self.assertEqual(report["summary"]["lost_active_route_count"], 0)
        self.assertFalse(report["summary"]["boundary_changed"])
        self.assertEqual(report["route_deltas"][0]["relation"], "stable_active")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_monitor_fails_when_active_route_is_lost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline = ready_portfolio(Path(tmp) / "baseline")
            current = json.loads(json.dumps(baseline))
            current["route_cards"][0]["portfolio_status"] = "blocked"
            current["summary"]["active_route_count"] = 0
            current["portfolio"]["active_routes"] = []

            report = build_model_capability_route_promotion_regression_monitor(current, baseline_portfolio=baseline)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_active_route_loss", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["lost_active_route_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portfolio = ready_portfolio(root)
            portfolio_dir = root / "portfolio"
            portfolio_dir.mkdir(parents=True, exist_ok=True)
            portfolio_path = portfolio_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
            portfolio_path.write_text(json.dumps(portfolio, ensure_ascii=False), encoding="utf-8")

            self.assertEqual(locate_route_promotion_portfolio(portfolio_dir), portfolio_path)
            report = build_model_capability_route_promotion_regression_monitor(portfolio, baseline_portfolio=portfolio)
            outputs = write_model_capability_route_promotion_regression_monitor_outputs(report, root / "monitor")
            cli_main(["--current", str(portfolio_dir), "--baseline", str(portfolio_dir), "--out-dir", str(root / "cli-monitor"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("lost_active_route_count=0", render_model_capability_route_promotion_regression_monitor_text(report))
        self.assertIn("Route Deltas", render_model_capability_route_promotion_regression_monitor_markdown(report))
        self.assertIn("route promotion regression monitor", render_model_capability_route_promotion_regression_monitor_html(report))


if __name__ == "__main__":
    unittest.main()
