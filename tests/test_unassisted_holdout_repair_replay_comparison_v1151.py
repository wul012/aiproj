from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.unassisted_holdout_repair_replay_comparison_v1151 import (
    GENERATION_ROWS_NAME,
    UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM,
    build_unassisted_holdout_repair_replay_comparison_v1151,
    locate_v1150_training_handoff,
    resolve_exit_code,
    write_unassisted_holdout_repair_replay_comparison_v1151_outputs,
)
from minigpt.unassisted_holdout_repair_training_run_v1150 import TRAINING_HANDOFF_NAME
from scripts.run_unassisted_holdout_repair_replay_comparison_v1151 import main as cli_main


class UnassistedHoldoutRepairReplayComparisonV1151Tests(unittest.TestCase):
    def test_partial_signal_is_ready_but_not_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = write_handoff(root)
            report = build_unassisted_holdout_repair_replay_comparison_v1151(
                handoff,
                holdout_prompts=holdout_prompts(),
                generator_runner=fake_runner(["fixed", "", "fixed", ""]),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_holdout_repair_replay_partial_signal")
        self.assertTrue(report["summary"]["unassisted_holdout_repair_replay_ready"])
        self.assertEqual(report["summary"]["fixed_hit_case_count"], 2)
        self.assertEqual(report["summary"]["loss_hit_case_count"], 0)
        self.assertEqual(report["summary"]["full_pair_case_count"], 0)
        self.assertTrue(report["summary"]["partial_signal_visible"])
        self.assertEqual(report["summary"]["model_quality_claim"], "bounded_holdout_replay_partial_signal")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_full_pair=True), 1)

    def test_all_full_pair_hits_mark_recovery_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = write_handoff(root)
            report = build_unassisted_holdout_repair_replay_comparison_v1151(
                handoff,
                holdout_prompts=holdout_prompts(),
                generator_runner=fake_runner(["fixed loss", "fixed loss", "fixed loss", "fixed loss"]),
            )

        self.assertEqual(report["decision"], "unassisted_holdout_repair_replay_full_pair_recovered_candidate")
        self.assertEqual(report["summary"]["full_pair_case_count"], 4)
        self.assertTrue(report["summary"]["all_full_pair_hit"])
        self.assertEqual(report["summary"]["model_quality_claim"], "bounded_holdout_replay_recovered_candidate")
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_full_pair=True), 0)

    def test_target_contaminated_holdout_prompt_fails_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = write_handoff(root)
            prompts = holdout_prompts()
            prompts[0]["prompt"] = "answer fixed:"
            report = build_unassisted_holdout_repair_replay_comparison_v1151(
                handoff,
                holdout_prompts=prompts,
                generator_runner=fake_runner(["fixed loss"] * 4),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("holdout_prompts_target_free", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["rows"], [])

    def test_archived_handoff_falls_back_to_sibling_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archive"
            run = archive / "run"
            run.mkdir(parents=True)
            (run / "checkpoint.pt").write_bytes(b"checkpoint")
            (run / "tokenizer.json").write_text("{}", encoding="utf-8")
            holdout = archive / "holdout.json"
            write_json_payload(holdout_prompts(), holdout)
            handoff_path = archive / TRAINING_HANDOFF_NAME
            handoff = {
                "status": "pass",
                "checkpoint": str(root / "deleted-output" / "checkpoint.pt"),
                "tokenizer": str(root / "deleted-output" / "tokenizer.json"),
                "holdout_prompts": str(holdout),
                "promotion_ready": False,
                "next_step": "run_unassisted_holdout_repair_replay_comparison",
            }
            write_json_payload(handoff, handoff_path)
            report = build_unassisted_holdout_repair_replay_comparison_v1151(
                handoff,
                holdout_prompts=holdout_prompts(),
                handoff_path=handoff_path,
                precomputed_generations=generation_rows(["fixed loss", "fixed loss", "fixed loss", "fixed loss"]),
            )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["checkpoint"].endswith("run\\checkpoint.pt") or report["checkpoint"].endswith("run/checkpoint.pt"))

    def test_outputs_and_cli_accept_precomputed_generations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = write_handoff(root)
            handoff_path = root / "handoff" / TRAINING_HANDOFF_NAME
            prompts_path = root / "holdout.json"
            generations_path = root / "generations.json"
            write_json_payload(holdout_prompts(), prompts_path)
            write_json_payload(generation_rows(["fixed loss", "fixed loss", "fixed loss", "fixed loss"]), generations_path)
            report = build_unassisted_holdout_repair_replay_comparison_v1151(
                handoff,
                holdout_prompts=holdout_prompts(),
                precomputed_generations=generation_rows(["fixed loss", "fixed loss", "fixed loss", "fixed loss"]),
            )
            outputs = write_unassisted_holdout_repair_replay_comparison_v1151_outputs(report, root / "replay")
            cli_main(
                [
                    "--handoff",
                    str(handoff_path.parent),
                    "--holdout-prompts",
                    str(prompts_path),
                    "--precomputed-generations",
                    str(generations_path),
                    "--out-dir",
                    str(root / "cli-replay"),
                    "--require-comparison-ready",
                    "--require-full-pair",
                    "--force",
                ]
            )

            self.assertEqual(locate_v1150_training_handoff(handoff_path.parent), handoff_path)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html", "generation_rows"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM}.json"))
            self.assertTrue((root / "replay" / GENERATION_ROWS_NAME).is_file())
            self.assertTrue((root / "cli-replay" / GENERATION_ROWS_NAME).is_file())


def write_handoff(root: Path) -> dict[str, object]:
    checkpoint = root / "run" / "checkpoint.pt"
    tokenizer = root / "run" / "tokenizer.json"
    holdout = root / "holdout.json"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    tokenizer.write_text("{}", encoding="utf-8")
    write_json_payload(holdout_prompts(), holdout)
    handoff = {
        "status": "pass",
        "decision": "unassisted_holdout_repair_training_run_ready",
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "holdout_prompts": str(holdout),
        "promotion_ready": False,
        "next_step": "run_unassisted_holdout_repair_replay_comparison",
    }
    handoff_path = root / "handoff" / TRAINING_HANDOFF_NAME
    write_json_payload(handoff, handoff_path)
    return handoff


def holdout_prompts() -> list[dict[str, object]]:
    return [
        {"case_id": "holdout-01", "prompt": "answer:", "expected_terms": ["fixed", "loss"], "max_new_tokens": 8, "temperature": 0.2, "top_k": 5},
        {"case_id": "holdout-02", "prompt": "completion:", "expected_terms": ["fixed", "loss"], "max_new_tokens": 8, "temperature": 0.2, "top_k": 5},
        {"case_id": "holdout-03", "prompt": "finish:", "expected_terms": ["fixed", "loss"], "max_new_tokens": 8, "temperature": 0.2, "top_k": 5},
        {"case_id": "holdout-04", "prompt": "signal:", "expected_terms": ["fixed", "loss"], "max_new_tokens": 8, "temperature": 0.2, "top_k": 5},
    ]


def fake_runner(outputs: list[str]):
    def run(row: dict[str, object], _checkpoint: Path, _tokenizer: Path, _device: str, index: int) -> dict[str, object]:
        continuation = outputs[index - 1]
        prompt = str(row["prompt"])
        return {
            "case_id": row["case_id"],
            "prompt": prompt,
            "generated": prompt + continuation,
            "continuation": continuation,
            "expected_terms": row["expected_terms"],
        }

    return run


def generation_rows(outputs: list[str]) -> list[dict[str, object]]:
    rows = []
    for index, continuation in enumerate(outputs, start=1):
        prompt = str(holdout_prompts()[index - 1]["prompt"])
        rows.append(
            {
                "case_id": f"holdout-{index:02d}",
                "prompt": prompt,
                "generated": prompt + continuation,
                "continuation": continuation,
                "expected_terms": ["fixed", "loss"],
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
