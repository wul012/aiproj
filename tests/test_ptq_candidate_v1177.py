from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.ptq_candidate_v1177 import (
    PtqCandidatePolicy,
    build_ptq_candidate_report,
    locate_ptq_report,
    resolve_exit_code,
    write_ptq_candidate_outputs,
)
from scripts.select_ptq_candidate_v1177 import main as cli_main


class PtqCandidateV1177Tests(unittest.TestCase):
    def test_selects_lowest_effective_bits_inside_quality_budget(self) -> None:
        report = build_ptq_candidate_report(_ptq_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "ptq_deployment_candidate_selected")
        self.assertTrue(report["summary"]["candidate_ready"])
        self.assertEqual(report["summary"]["selected_candidate_id"], "group32:3b")
        self.assertEqual(report["summary"]["selected_eff_bits"], 3.5)
        rejected = {row["candidate_id"]: row["reject_reasons"] for row in report["rejected_candidates"]}
        self.assertIn("per_channel_row:3b", rejected)
        self.assertIn("exact_match_drop_above_budget", rejected["per_channel_row:3b"])

    def test_tighter_policy_can_reject_all_low_bit_candidates(self) -> None:
        policy = PtqCandidatePolicy(max_dce_nats=0.011, max_exact_match_drop=0.02, max_kl_nats=0.02)
        report = build_ptq_candidate_report(_ptq_report(), policy=policy)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["selected_candidate_id"], "per_channel_row:4b")
        self.assertLessEqual(report["summary"]["selected_dce_mean"], 0.011)

    def test_source_failure_blocks_candidate(self) -> None:
        source = _ptq_report(status="review")
        report = build_ptq_candidate_report(source)

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["summary"]["candidate_ready"])
        self.assertEqual(report["decision"], "repair_source_ptq_report")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_path_directory_input_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source"
            source_dir.mkdir()
            (source_dir / "ptq_v1175.json").write_text(json.dumps(_ptq_report()), encoding="utf-8")
            self.assertEqual(locate_ptq_report(source_dir), source_dir / "ptq_v1175.json")

            outputs = write_ptq_candidate_outputs(build_ptq_candidate_report(source_dir), root / "out")
            exit_code = cli_main([str(source_dir), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})

    def test_cli_require_pass_returns_one_when_no_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "ptq_v1175.json"
            source.write_text(json.dumps(_ptq_report(status="review")), encoding="utf-8")
            exit_code = cli_main([str(source), "--out-dir", str(root / "out"), "--require-pass", "--force"])

        self.assertEqual(exit_code, 1)


def _ptq_report(*, status: str = "pass") -> dict[str, object]:
    return {
        "schema_version": 1,
        "title": "MiniGPT post-training weight quantization v1175",
        "status": status,
        "decision": "ptq_degradation_measured" if status == "pass" else "review_ptq",
        "summary": {
            "verdict": "per_channel_advantage_not_separable",
            "fp32_ce": 0.080853,
            "fp32_exact_match": 0.883333,
        },
        "rows": [
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
