from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.baseline_candidate_handoff import build_baseline_candidate_handoff, write_baseline_candidate_handoff_outputs
from minigpt.baseline_candidate_handoff_check import (
    build_baseline_candidate_handoff_check,
    render_baseline_candidate_handoff_check_text,
)
from scripts.build_baseline_candidate_handoff import main as build_main
from scripts.check_baseline_candidate_handoff import main as check_main, resolve_exit_code


class BaselineCandidateHandoffCheckTests(unittest.TestCase):
    def test_valid_handoff_check_passes_when_candidate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff_path = _write_handoff_bundle(Path(tmp), accepted=False)

            report = build_baseline_candidate_handoff_check(handoff_path, generated_at="2026-05-26T00:00:00Z")
            text = render_baseline_candidate_handoff_check_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "continue_with_valid_handoff")
            self.assertEqual(report["failed_count"], 0)
            self.assertEqual(report["handoff_decision"], "keep_current_baseline")
            self.assertIn("failed_count=0", text)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_tampered_next_baseline_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff_path = _write_handoff_bundle(Path(tmp), accepted=False)
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
            payload["next_baseline"]["source"] = "candidate"
            handoff_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_baseline_candidate_handoff_check(handoff_path, generated_at="2026-05-26T00:00:00Z")

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["failed_count"], 1)
            self.assertEqual(report["issues"][0]["field"], "next_baseline")

    def test_missing_source_loop_report_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff_path = _write_handoff_bundle(Path(tmp), accepted=False)
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
            payload["source_loop_report"] = "missing-loop.json"
            handoff_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_baseline_candidate_handoff_check(handoff_path, generated_at="2026-05-26T00:00:00Z")

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["issues"][0]["id"], "source_loop_report_not_found")

    def test_cli_require_pass_returns_one_on_failed_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = _write_handoff_bundle(root, accepted=False)
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
            payload["next_baseline"]["source"] = "candidate"
            handoff_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                check_main([str(handoff_path), "--out-dir", str(root / "check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "check" / "baseline_candidate_handoff_check.json").is_file())

    def test_builder_check_out_dir_writes_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_path = _write_loop_bundle(root, accepted=True)
            out_dir = root / "handoff"
            check_dir = root / "handoff-check"

            build_main([str(loop_path), "--out-dir", str(out_dir), "--check-out-dir", str(check_dir), "--force"])

            check_payload = json.loads((check_dir / "baseline_candidate_handoff_check.json").read_text(encoding="utf-8"))
            self.assertEqual(check_payload["status"], "pass")
            self.assertEqual(check_payload["failed_count"], 0)


def _write_handoff_bundle(root: Path, *, accepted: bool) -> Path:
    loop_path = _write_loop_bundle(root, accepted=accepted)
    handoff = build_baseline_candidate_handoff(loop_path, generated_at="2026-05-26T00:00:00Z")
    outputs = write_baseline_candidate_handoff_outputs(handoff, root / "handoff")
    return Path(outputs["json"])


def _write_loop_bundle(root: Path, *, accepted: bool) -> Path:
    smoke_dir = root / "smoke"
    baseline_dir = smoke_dir / "baseline"
    candidate_dir = smoke_dir / "candidate"
    (baseline_dir / "run").mkdir(parents=True)
    (candidate_dir / "run").mkdir(parents=True)
    (baseline_dir / "run" / "checkpoint.pt").write_text("baseline checkpoint", encoding="utf-8")
    (candidate_dir / "run" / "checkpoint.pt").write_text("candidate checkpoint", encoding="utf-8")
    source_summary = smoke_dir / "tiny_scorecard_comparison_smoke_summary.json"
    source_summary.write_text(
        json.dumps(
            {
                "baseline_dir": str(baseline_dir),
                "candidate_dir": str(candidate_dir),
                "artifacts": {
                    "candidate_scorecard_path": str(candidate_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json"),
                    "candidate_pair_batch_path": str(candidate_dir / "run" / "pair_batch" / "pair_generation_batch.json"),
                    "benchmark_history_json_path": str(smoke_dir / "benchmark-history" / "benchmark_history.json"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    loop_path = root / "baseline_candidate_eval_loop.json"
    loop_path.write_text(json.dumps(_loop_report(source_summary, accepted=accepted), ensure_ascii=False), encoding="utf-8")
    return loop_path


def _loop_report(source_summary: Path, *, accepted: bool) -> dict[str, object]:
    decision = "accept_candidate" if accepted else "reject_candidate"
    acceptance_status = "pass" if accepted else "fail"
    rejected_reasons = [] if accepted else ["min_overall_score_delta expected >= 1.0, got 0.0"]
    return {
        "status": "pass",
        "decision": decision,
        "source_smoke_summary": str(source_summary),
        "experiment": {
            "baseline_name": "tiny-baseline",
            "candidate_name": "tiny-candidate",
            "min_overall_score_delta": 1.0,
        },
        "baseline_metrics": {
            "status": "pass",
            "scorecard_status": "pass",
            "overall_score": 81.17,
        },
        "candidate_metrics": {
            "status": "pass",
            "scorecard_status": "pass",
            "overall_score": 81.17 if not accepted else 82.25,
        },
        "delta_report": {
            "overall_score_delta": 0.0 if not accepted else 1.08,
            "case_delta_count": 20,
            "case_regression_count": 0,
        },
        "control_summary": {
            "status": "pass",
            "failed_reasons": [],
        },
        "acceptance_criteria": {
            "status": acceptance_status,
            "failed_reasons": rejected_reasons,
        },
        "promotion_decision": {
            "status": "promote",
            "selected_name": "tiny-candidate",
            "accepted": accepted,
            "rejected_reasons": rejected_reasons,
        },
        "execution": {
            "source_mode": "rerun_smoke",
            "gate_mode": "strict",
            "expected_exit_code": 0 if accepted else 2,
        },
        "boundary": {
            "model_quality_claim": "not_claimed",
            "reason": "Tiny benchmark handoff evidence only.",
        },
    }


if __name__ == "__main__":
    unittest.main()
