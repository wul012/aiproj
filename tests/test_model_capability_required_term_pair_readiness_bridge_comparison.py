from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_bridge_comparison import (
    build_bridge_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_bridge_comparison_artifacts import (
    render_bridge_comparison_html,
    render_bridge_comparison_markdown,
    render_bridge_comparison_text,
    write_bridge_comparison_outputs,
)


class BridgeComparisonTests(unittest.TestCase):
    def test_comparison_closes_bridge_when_pollution_is_introduced(self) -> None:
        report = build_bridge_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_bridge_no_improvement_introduced_fixed_pollution")
        self.assertEqual(report["summary"]["default_hit_delta"], 0)
        self.assertTrue(report["summary"]["bridge_pollution_introduced"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_reports_improvement_when_bridge_hits(self) -> None:
        bridge = training_fixture("bridge")
        bridge["summary"]["pair_full_observed"] = False
        bridge["replay_report"]["case_rows"][0]["continuation_hit"] = True
        bridge["replay_report"]["case_rows"][0]["continuation"] = "fixed"
        report = build_bridge_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=bridge,
        )

        self.assertEqual(report["decision"], "pair_readiness_bridge_improved_direct_hits")
        self.assertTrue(report["summary"]["bridge_improved"])

    def test_outputs_render_all_formats(self) -> None:
        report = build_bridge_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_bridge_comparison_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bridge_pollution_introduced=True", render_bridge_comparison_text(report))
        self.assertIn("Bridge Comparison", render_bridge_comparison_markdown(report))
        self.assertIn("MiniGPT bridge comparison", render_bridge_comparison_html(report))


def training_fixture(kind: str) -> dict[str, object]:
    if kind == "objective":
        continuations = [("fixed", "d | | |", False), ("loss", "d | | |", False)]
    else:
        continuations = [("fixed", " | | | ted |", False), ("loss", "fixed | | |", False)]
    return {
        "status": "pass",
        "decision": "pair_readiness_training_no_pair_full",
        "summary": {"training_status": "pass", "checkpoint_exists": True, "pair_full_observed": False},
        "replay_report": {
            "case_rows": [
                {"profile_id": "default", "term": term, "continuation": continuation, "continuation_hit": hit}
                for term, continuation, hit in continuations
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
