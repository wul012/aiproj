from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_seed_config_selection import (
    build_model_capability_required_term_pair_seed_config_selection,
    locate_pair_seed_coverage_tradeoff,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_selection_artifacts import (
    render_model_capability_required_term_pair_seed_config_selection_html,
    render_model_capability_required_term_pair_seed_config_selection_markdown,
    render_model_capability_required_term_pair_seed_config_selection_text,
    write_model_capability_required_term_pair_seed_config_selection_outputs,
)


class ModelCapabilityRequiredTermPairSeedConfigSelectionTests(unittest.TestCase):
    def test_selection_reports_multi_config_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_selection(
                tradeoff_report(),
                out_dir=Path(tmp) / "selection",
                generated_at="2026-05-31T01:20:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_seed_config_selection_multi_config_ready")
            self.assertEqual(report["summary"]["selection_ready_seed_count"], 3)
            self.assertTrue(report["summary"]["requires_multi_config_policy"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_selection_fails_when_winning_config_is_not_pair_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = tradeoff_report()
            payload["seed_rows"][0]["per_config_pair_full"]["v544"] = False
            report = build_model_capability_required_term_pair_seed_config_selection(
                payload,
                out_dir=Path(tmp) / "selection",
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("seed 535 has no pair-full selected config", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_config_selection(
                tradeoff_report(),
                out_dir=root / "selection",
            )
            outputs = write_model_capability_required_term_pair_seed_config_selection_outputs(report, root / "selection")
            text = render_model_capability_required_term_pair_seed_config_selection_text(report)
            markdown = render_model_capability_required_term_pair_seed_config_selection_markdown(report)
            html = render_model_capability_required_term_pair_seed_config_selection_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("requires_multi_config_policy=True", text)
            self.assertIn("Seed Config Selection", markdown)
            self.assertIn("MiniGPT pair seed config selection", html)

    def test_locate_accepts_output_directory(self) -> None:
        self.assertEqual(
            locate_pair_seed_coverage_tradeoff(Path("out-dir")),
            Path("out-dir"),
        )


def tradeoff_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_seed_coverage_tradeoff_complementary_full_union",
        "config_rows": [
            {"config_id": "v544", "source_path": "v544.json", "pair_full_seed_count": 2},
            {"config_id": "v546", "source_path": "v546.json", "pair_full_seed_count": 1},
        ],
        "seed_rows": [
            {
                "seed": 535,
                "winning_config_id": "v544",
                "covering_config_ids": ["v544"],
                "per_config_pair_full": {"v544": True, "v546": False},
            },
            {
                "seed": 1535,
                "winning_config_id": "v546",
                "covering_config_ids": ["v546"],
                "per_config_pair_full": {"v544": False, "v546": True},
            },
            {
                "seed": 2535,
                "winning_config_id": "v544",
                "covering_config_ids": ["v544"],
                "per_config_pair_full": {"v544": True, "v546": False},
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
