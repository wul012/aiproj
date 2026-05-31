from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff import (
    build_model_capability_required_term_pair_seed_coverage_tradeoff,
    locate_pair_colon_immediate_stability,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff_artifacts import (
    render_model_capability_required_term_pair_seed_coverage_tradeoff_html,
    render_model_capability_required_term_pair_seed_coverage_tradeoff_markdown,
    render_model_capability_required_term_pair_seed_coverage_tradeoff_text,
    write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs,
)


class ModelCapabilityRequiredTermPairSeedCoverageTradeoffTests(unittest.TestCase):
    def test_tradeoff_reports_complementary_full_union(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_coverage_tradeoff(
                [
                    stability_report("topk2", [535, 2535]),
                    stability_report("loss-calibrated", [1535]),
                ],
                out_dir=root / "tradeoff",
                labels=["v544-topk2", "v546-loss-calibrated"],
                generated_at="2026-05-31T01:00:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_seed_coverage_tradeoff_complementary_full_union")
            self.assertEqual(report["summary"]["union_pair_full_seed_count"], 3)
            self.assertEqual(report["summary"]["best_single_pair_full_seed_count"], 2)
            self.assertTrue(report["summary"]["tradeoff_detected"])
            self.assertEqual(report["summary"]["contributing_config_ids"], ["v544-topk2", "v546-loss-calibrated"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_tradeoff_reports_partial_without_union_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_coverage_tradeoff(
                [stability_report("topk2", [535]), stability_report("loss-calibrated", [535])],
                out_dir=Path(tmp) / "tradeoff",
                labels=["a", "b"],
            )

            self.assertEqual(report["decision"], "required_term_pair_seed_coverage_tradeoff_partial_coverage_observed")
            self.assertFalse(report["summary"]["tradeoff_detected"])
            self.assertEqual(report["summary"]["uncovered_seeds"], [1535, 2535])

    def test_tradeoff_fails_for_invalid_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_coverage_tradeoff(
                [{"status": "fail", "seed_rows": []}],
                out_dir=Path(tmp) / "tradeoff",
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_coverage_tradeoff(
                [stability_report("topk2", [535, 2535]), stability_report("loss-calibrated", [1535])],
                out_dir=root / "tradeoff",
                labels=["v544", "v546"],
            )
            outputs = write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs(report, root / "tradeoff")
            text = render_model_capability_required_term_pair_seed_coverage_tradeoff_text(report)
            markdown = render_model_capability_required_term_pair_seed_coverage_tradeoff_markdown(report)
            html = render_model_capability_required_term_pair_seed_coverage_tradeoff_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("tradeoff_detected=True", text)
            self.assertIn("Seed Coverage Tradeoff", markdown)
            self.assertIn("MiniGPT pair seed coverage tradeoff", html)
            self.assertTrue(Path(outputs["json"]).is_file())

    def test_locate_accepts_output_directory(self) -> None:
        self.assertEqual(
            locate_pair_colon_immediate_stability(Path("some-output")),
            Path("some-output"),
        )


def stability_report(config_id: str, pair_full_seeds: list[int]) -> dict[str, object]:
    seed_rows = [
        {"seed": 535, "pair_full_observed": 535 in pair_full_seeds, "decision": "seed-535"},
        {"seed": 1535, "pair_full_observed": 1535 in pair_full_seeds, "decision": "seed-1535"},
        {"seed": 2535, "pair_full_observed": 2535 in pair_full_seeds, "decision": "seed-2535"},
    ]
    return {
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_partial_stability",
        "settings": {
            "corpus_mode": config_id,
            "top_k": 2,
            "temperature": 0.8,
            "max_iters": 2200,
        },
        "summary": {
            "seed_count": len(seed_rows),
            "pair_full_seed_count": len(pair_full_seeds),
        },
        "seed_rows": seed_rows,
    }


if __name__ == "__main__":
    unittest.main()
