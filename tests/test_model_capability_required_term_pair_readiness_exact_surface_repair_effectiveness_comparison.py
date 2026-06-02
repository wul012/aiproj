from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison import (
    build_exact_surface_repair_effectiveness_comparison,
    locate_exact_surface_repair_effectiveness_replay_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison_artifacts import (
    render_exact_surface_repair_effectiveness_comparison_html,
    render_exact_surface_repair_effectiveness_comparison_markdown,
    render_exact_surface_repair_effectiveness_comparison_text,
    write_exact_surface_repair_effectiveness_comparison_outputs,
)


class ExactSurfaceRepairEffectivenessComparisonTests(unittest.TestCase):
    def test_comparison_stops_ineffective_route(self) -> None:
        report = build_exact_surface_repair_effectiveness_comparison(replay_fixture(), replay_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_ineffective_stop_route")
        self.assertTrue(report["summary"]["repair_ineffective"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_detects_exact_surface_improvement(self) -> None:
        repaired = replay_fixture()
        repaired["replay_rows"][0]["default_continuation_hit_count"] = 2
        report = build_exact_surface_repair_effectiveness_comparison(replay_fixture(), repaired)

        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_partial_improvement")
        self.assertTrue(report["summary"]["exact_surface_improved"])

    def test_comparison_ready_when_repaired_exact_pair_full(self) -> None:
        repaired = replay_fixture()
        repaired["summary"]["exact_heldout_pair_full"] = True
        repaired["replay_rows"][0]["replay_pair_full"] = True
        report = build_exact_surface_repair_effectiveness_comparison(replay_fixture(), repaired)

        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_effective_ready_for_promotion_guard")

    def test_locator_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = locate_exact_surface_repair_effectiveness_replay_source(tmp)
        self.assertEqual(source.name, "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json")

    def test_outputs_render_all_formats(self) -> None:
        report = build_exact_surface_repair_effectiveness_comparison(replay_fixture(), replay_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_exact_surface_repair_effectiveness_comparison_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("repair_ineffective=True", render_exact_surface_repair_effectiveness_comparison_text(report))
        self.assertIn("Exact-Surface Repair Effectiveness Comparison", render_exact_surface_repair_effectiveness_comparison_markdown(report))
        self.assertIn("MiniGPT exact-surface repair effectiveness comparison", render_exact_surface_repair_effectiveness_comparison_html(report))


def replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial",
        "summary": {
            "exact_heldout_pair_full": False,
            "pair_full_count": 1,
        },
        "replay_rows": [
            {
                "spec_id": "exact-heldout-pair",
                "prompt": "fixed=|loss=",
                "required_for_ready": True,
                "replay_pair_full": False,
                "default_continuation_hit_count": 1,
            },
            {
                "spec_id": "arrow-heldout-pair",
                "prompt": "fixed -> | loss ->",
                "required_for_ready": False,
                "replay_pair_full": True,
                "default_continuation_hit_count": 2,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
