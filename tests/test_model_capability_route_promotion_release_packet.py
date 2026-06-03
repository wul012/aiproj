from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_gate import MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME, build_model_capability_route_promotion_gate
from minigpt.model_capability_route_promotion_portfolio import MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
from minigpt.model_capability_route_promotion_regression_monitor import MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME, build_model_capability_route_promotion_regression_monitor
from minigpt.model_capability_route_promotion_release_packet import (
    build_model_capability_route_promotion_release_packet,
    locate_route_promotion_gate,
    locate_route_promotion_portfolio,
    locate_route_promotion_regression_monitor,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_packet_artifacts import (
    render_model_capability_route_promotion_release_packet_html,
    render_model_capability_route_promotion_release_packet_markdown,
    render_model_capability_route_promotion_release_packet_text,
    write_model_capability_route_promotion_release_packet_outputs,
)
from scripts.build_model_capability_route_promotion_release_packet import main as cli_main
from tests.test_model_capability_route_promotion_regression_monitor import ready_portfolio


def ready_packet_inputs(root: Path) -> tuple[dict, dict, dict, Path, Path, Path]:
    portfolio = ready_portfolio(root / "source")
    monitor = build_model_capability_route_promotion_regression_monitor(portfolio, baseline_portfolio=portfolio)
    gate = build_model_capability_route_promotion_gate(portfolio, monitor)
    portfolio_path = _write(root / "portfolio", MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME, portfolio)
    monitor_path = _write(root / "monitor", MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME, monitor)
    gate_path = _write(root / "gate", MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME, gate)
    return portfolio, monitor, gate, portfolio_path, monitor_path, gate_path


class ModelCapabilityRoutePromotionReleasePacketTests(unittest.TestCase):
    def test_release_packet_passes_with_clean_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            portfolio, monitor, gate, portfolio_path, monitor_path, gate_path = ready_packet_inputs(Path(tmp))
            report = build_model_capability_route_promotion_release_packet(
                portfolio,
                monitor,
                gate,
                portfolio_path=portfolio_path,
                regression_monitor_path=monitor_path,
                gate_path=gate_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_packet_ready")
        self.assertTrue(report["summary"]["release_packet_ready"])
        self.assertEqual(report["summary"]["evidence_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_release_packet_fails_when_gate_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            portfolio, monitor, gate, portfolio_path, monitor_path, gate_path = ready_packet_inputs(Path(tmp))
            gate["status"] = "fail"

            report = build_model_capability_route_promotion_release_packet(
                portfolio,
                monitor,
                gate,
                portfolio_path=portfolio_path,
                regression_monitor_path=monitor_path,
                gate_path=gate_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("gate_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portfolio, monitor, gate, portfolio_path, monitor_path, gate_path = ready_packet_inputs(root)
            self.assertEqual(locate_route_promotion_portfolio(portfolio_path.parent), portfolio_path)
            self.assertEqual(locate_route_promotion_regression_monitor(monitor_path.parent), monitor_path)
            self.assertEqual(locate_route_promotion_gate(gate_path.parent), gate_path)

            report = build_model_capability_route_promotion_release_packet(
                portfolio,
                monitor,
                gate,
                portfolio_path=portfolio_path,
                regression_monitor_path=monitor_path,
                gate_path=gate_path,
            )
            outputs = write_model_capability_route_promotion_release_packet_outputs(report, root / "packet")
            cli_main(
                [
                    "--portfolio",
                    str(portfolio_path.parent),
                    "--regression-monitor",
                    str(monitor_path.parent),
                    "--gate",
                    str(gate_path.parent),
                    "--out-dir",
                    str(root / "cli-packet"),
                    "--require-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("release_packet_ready=True", render_model_capability_route_promotion_release_packet_text(report))
        self.assertIn("Evidence", render_model_capability_route_promotion_release_packet_markdown(report))
        self.assertIn("route promotion release packet", render_model_capability_route_promotion_release_packet_html(report))


def _write(root: Path, filename: str, payload: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
