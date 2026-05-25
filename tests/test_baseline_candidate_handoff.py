from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.baseline_candidate_handoff import (
    build_baseline_candidate_handoff,
    render_baseline_candidate_handoff_text,
    write_baseline_candidate_handoff_outputs,
)
from scripts.build_baseline_candidate_handoff import main, resolve_exit_code


class BaselineCandidateHandoffTests(unittest.TestCase):
    def test_handoff_promotes_accepted_candidate_to_next_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_path = _write_loop_bundle(root, accepted=True)

            handoff = build_baseline_candidate_handoff(loop_path, generated_at="2026-05-26T00:00:00Z")
            text = render_baseline_candidate_handoff_text(handoff)

            self.assertEqual(handoff["status"], "pass")
            self.assertEqual(handoff["decision"], "promote_candidate_to_next_baseline")
            self.assertTrue(handoff["handoff_ready"])
            self.assertEqual(handoff["next_baseline"]["name"], "tiny-candidate")
            self.assertEqual(handoff["next_baseline"]["source"], "candidate")
            self.assertTrue(handoff["next_baseline"]["checkpoint_exists"])
            self.assertEqual(handoff["candidate"]["accepted"], True)
            self.assertIn("handoff_ready=True", text)
            self.assertIn("next_baseline_source=candidate", text)

    def test_handoff_keeps_current_baseline_when_candidate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_path = _write_loop_bundle(root, accepted=False)

            handoff = build_baseline_candidate_handoff(loop_path, generated_at="2026-05-26T00:00:00Z")

            self.assertEqual(handoff["status"], "pass")
            self.assertEqual(handoff["decision"], "keep_current_baseline")
            self.assertFalse(handoff["handoff_ready"])
            self.assertEqual(handoff["next_baseline"]["name"], "tiny-baseline")
            self.assertEqual(handoff["next_baseline"]["source"], "current_baseline")
            self.assertIn("min_overall_score_delta expected >= 1.0, got 0.0", handoff["guardrails"]["rejected_reasons"])
            self.assertEqual(resolve_exit_code(handoff, require_accepted=True), 2)
            self.assertEqual(resolve_exit_code(handoff, require_accepted=False), 0)

    def test_write_outputs_persists_handoff_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_path = _write_loop_bundle(root, accepted=True)
            handoff = build_baseline_candidate_handoff(loop_path, generated_at="2026-05-26T00:00:00Z")

            outputs = write_baseline_candidate_handoff_outputs(handoff, root / "handoff")

            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["text"]).is_file())
            self.assertTrue(Path(outputs["markdown"]).is_file())
            self.assertTrue(Path(outputs["html"]).is_file())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["decision"], "promote_candidate_to_next_baseline")
            self.assertIn("Handoff ready: `True`", Path(outputs["markdown"]).read_text(encoding="utf-8"))

    def test_cli_reuses_loop_report_and_can_require_accepted_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_path = _write_loop_bundle(root, accepted=False)
            out_dir = root / "handoff"

            with self.assertRaises(SystemExit) as raised:
                main([str(loop_path), "--out-dir", str(out_dir), "--require-accepted", "--force"])

            self.assertEqual(raised.exception.code, 2)
            payload = json.loads((out_dir / "baseline_candidate_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "keep_current_baseline")
            self.assertFalse(payload["handoff_ready"])


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
