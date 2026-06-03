from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_gate import (
    build_model_capability_route_promotion_gate,
    locate_route_promotion_portfolio,
    locate_route_promotion_regression_monitor,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_gate_artifacts import (
    render_model_capability_route_promotion_gate_html,
    render_model_capability_route_promotion_gate_markdown,
    render_model_capability_route_promotion_gate_text,
    write_model_capability_route_promotion_gate_outputs,
)
from minigpt.model_capability_route_promotion_portfolio import MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
from minigpt.model_capability_route_promotion_regression_monitor import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME,
    build_model_capability_route_promotion_regression_monitor,
)
from scripts.check_model_capability_route_promotion_gate import main as cli_main
from tests.test_model_capability_route_promotion_regression_monitor import ready_portfolio


def ready_gate_inputs(root: Path) -> tuple[dict, dict, Path, Path]:
    portfolio = ready_portfolio(root / "portfolio-source")
    monitor = build_model_capability_route_promotion_regression_monitor(portfolio, baseline_portfolio=portfolio)
    portfolio_dir = root / "portfolio"
    monitor_dir = root / "monitor"
    portfolio_dir.mkdir(parents=True, exist_ok=True)
    monitor_dir.mkdir(parents=True, exist_ok=True)
    portfolio_path = portfolio_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
    monitor_path = monitor_dir / MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME
    portfolio_path.write_text(json.dumps(portfolio, ensure_ascii=False), encoding="utf-8")
    monitor_path.write_text(json.dumps(monitor, ensure_ascii=False), encoding="utf-8")
    return portfolio, monitor, portfolio_path, monitor_path


class ModelCapabilityRoutePromotionGateTests(unittest.TestCase):
    def test_gate_passes_clean_portfolio_and_regression_monitor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            portfolio, monitor, portfolio_path, monitor_path = ready_gate_inputs(Path(tmp))
            report = build_model_capability_route_promotion_gate(
                portfolio,
                monitor,
                portfolio_path=portfolio_path,
                regression_monitor_path=monitor_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_gate_passed")
        self.assertTrue(report["summary"]["route_promotion_gate_ready"])
        self.assertEqual(report["summary"]["active_route_count"], 1)
        self.assertIn("route_promotion_release_packet", report["gate"]["allowed_next_steps"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_gate_fails_when_regression_monitor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            portfolio, monitor, _, _ = ready_gate_inputs(Path(tmp))
            monitor["status"] = "fail"
            monitor["decision"] = "fix_model_capability_route_promotion_regressions"

            report = build_model_capability_route_promotion_gate(portfolio, monitor)

        self.assertEqual(report["status"], "fail")
        self.assertIn("regression_monitor_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portfolio, monitor, portfolio_path, monitor_path = ready_gate_inputs(root)
            self.assertEqual(locate_route_promotion_portfolio(portfolio_path.parent), portfolio_path)
            self.assertEqual(locate_route_promotion_regression_monitor(monitor_path.parent), monitor_path)

            report = build_model_capability_route_promotion_gate(portfolio, monitor)
            outputs = write_model_capability_route_promotion_gate_outputs(report, root / "gate")
            cli_main(
                [
                    "--portfolio",
                    str(portfolio_path.parent),
                    "--regression-monitor",
                    str(monitor_path.parent),
                    "--out-dir",
                    str(root / "cli-gate"),
                    "--require-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("route_promotion_gate_ready=True", render_model_capability_route_promotion_gate_text(report))
        self.assertIn("route promotion gate", render_model_capability_route_promotion_gate_markdown(report))
        self.assertIn("MiniGPT model capability route promotion gate", render_model_capability_route_promotion_gate_html(report))


if __name__ == "__main__":
    unittest.main()
