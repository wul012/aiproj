from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.ptq_policy_sensitivity_v1178 import (
    build_ptq_policy_sensitivity_report,
    resolve_exit_code,
    write_ptq_policy_sensitivity_outputs,
)
from scripts.run_ptq_policy_sensitivity_v1178 import main as cli_main


class PtqPolicySensitivityV1178Tests(unittest.TestCase):
    def test_profiles_show_candidate_choice_is_budget_sensitive(self) -> None:
        report = build_ptq_policy_sensitivity_report(_ptq_report(), generated_at="2026-06-17T02:30:00Z")
        by_profile = {row["profile_id"]: row for row in report["rows"]}

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "ptq_policy_sensitivity_measured")
        self.assertFalse(report["summary"]["selection_stable_across_profiles"])
        self.assertEqual(by_profile["strict_quality"]["selected_candidate_id"], "per_tensor:4b")
        self.assertEqual(by_profile["balanced_default"]["selected_candidate_id"], "group32:3b")
        self.assertEqual(by_profile["aggressive_compression"]["selected_candidate_id"], "per_channel_row:3b")
        self.assertEqual(report["summary"]["unique_selected_candidate_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_source_failure_blocks_all_profiles(self) -> None:
        report = build_ptq_policy_sensitivity_report(_ptq_report(status="review"))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "repair_ptq_policy_sensitivity_inputs")
        self.assertEqual(report["summary"]["passing_profile_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source"
            source_dir.mkdir()
            (source_dir / "ptq_v1175.json").write_text(json.dumps(_ptq_report()), encoding="utf-8")

            outputs = write_ptq_policy_sensitivity_outputs(build_ptq_policy_sensitivity_report(source_dir), root / "out")
            exit_code = cli_main([str(source_dir), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _ptq_report(*, status: str = "pass") -> dict[str, object]:
    return {
        "schema_version": 1,
        "title": "MiniGPT post-training weight quantization v1175",
        "status": status,
        "decision": "ptq_measured" if status == "pass" else "review_ptq",
        "summary": {
            "verdict": "per_channel_advantage_not_separable",
            "fp32_ce": 0.080853,
            "fp32_exact_match": 0.883333,
        },
        "rows": [
            _row("per_tensor", 8, 8.0014, 0.080932, 0.000079, 0.000094, 0.881111),
            _row("per_tensor", 6, 6.0014, 0.083875, 0.003022, 0.001815, 0.878333),
            _row("per_tensor", 4, 4.0014, 0.097258, 0.016405, 0.030221, 0.852778),
            _row("per_tensor", 3, 3.0014, 0.539784, 0.458931, 0.489815, 0.465),
            _row("per_channel_row", 4, 4.1878, 0.091388, 0.010535, 0.011153, 0.864444),
            _row("per_channel_row", 3, 3.1878, 0.167595, 0.086742, 0.089207, 0.760),
            _row("group32", 4, 4.5, 0.090183, 0.00933, 0.009255, 0.865),
            _row("group32", 3, 3.5, 0.145139, 0.064286, 0.07137, 0.792778),
            _row("group32", 2, 2.5, 2.095955, 2.015102, 2.025453, 0.058333),
        ],
    }


def _row(granularity: str, bits: int, eff_bits: float, ce: float, dce: float, kl: float, em: float) -> dict[str, object]:
    return {
        "sweep": "S1",
        "component": "all",
        "granularity": granularity,
        "bits": bits,
        "eff_bits": eff_bits,
        "ce_mean": ce,
        "dce_mean": dce,
        "kl_mean": kl,
        "em_mean": em,
    }


if __name__ == "__main__":
    unittest.main()
