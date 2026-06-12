from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import write_unassisted_holdout_repair_seed_corpus_v1149_outputs
from minigpt.unassisted_holdout_repair_training_run_v1150 import (
    TRAINING_HANDOFF_NAME,
    UNASSISTED_HOLDOUT_REPAIR_TRAINING_RUN_V1150_STEM,
    build_unassisted_holdout_repair_training_run_v1150,
    locate_v1149_seed_corpus,
    resolve_exit_code,
    write_unassisted_holdout_repair_training_run_v1150_outputs,
)
from scripts.run_unassisted_holdout_repair_training_v1150 import main as cli_main


class UnassistedHoldoutRepairTrainingRunV1150Tests(unittest.TestCase):
    def test_builds_training_run_evidence_from_v1149_seed_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_report, seed_path = write_seed_corpus(root)
            run_dir = write_fake_run(root, seed_report["corpus_text"])
            report = build_unassisted_holdout_repair_training_run_v1150(seed_report, run_dir, seed_corpus_path=seed_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_holdout_repair_training_run_ready")
        self.assertTrue(report["summary"]["unassisted_holdout_repair_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 50)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertLess(report["summary"]["val_loss_delta"], 0)
        self.assertTrue(report["summary"]["sample_fixed_hit"])
        self.assertFalse(report["summary"]["sample_loss_hit"])
        self.assertEqual(report["summary"]["model_quality_claim"], "training_artifact_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "run_unassisted_holdout_repair_replay_comparison")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_fails_when_checkpoint_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_report, _ = write_seed_corpus(root)
            run_dir = write_fake_run(root, seed_report["corpus_text"])
            (run_dir / "checkpoint.pt").unlink()
            report = build_unassisted_holdout_repair_training_run_v1150(seed_report, run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_fails_when_training_used_different_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_report, _ = write_seed_corpus(root)
            run_dir = write_fake_run(root, "different corpus text\n")
            report = build_unassisted_holdout_repair_training_run_v1150(seed_report, run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("prepared_corpus_matches_seed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_report, seed_path = write_seed_corpus(root)
            run_dir = write_fake_run(root, seed_report["corpus_text"])
            self.assertEqual(locate_v1149_seed_corpus(seed_path.parent), seed_path)
            report = build_unassisted_holdout_repair_training_run_v1150(seed_report, run_dir, seed_corpus_path=seed_path)
            outputs = write_unassisted_holdout_repair_training_run_v1150_outputs(report, root / "training-evidence")
            cli_main(
                [
                    "--seed-corpus",
                    str(seed_path.parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-training-evidence"),
                    "--require-training-ready",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html", "training_handoff"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_HOLDOUT_REPAIR_TRAINING_RUN_V1150_STEM}.json"))
            self.assertTrue((root / "training-evidence" / TRAINING_HANDOFF_NAME).is_file())
            self.assertTrue((root / "cli-training-evidence" / TRAINING_HANDOFF_NAME).is_file())


def write_seed_corpus(root: Path) -> tuple[dict[str, object], Path]:
    report: dict[str, object] = {
        "status": "pass",
        "summary": {
            "unassisted_holdout_repair_seed_corpus_ready": True,
            "next_step": "run_unassisted_holdout_repair_training",
            "promotion_ready": False,
            "corpus_char_count": len(corpus_text()),
            "target_free_holdout_prompt_count": 2,
        },
        "corpus_text": corpus_text(),
        "rows": [
            {"example_id": "pair-01", "prompt": "answer:", "completion": " fixed loss", "text": "answer: fixed loss"},
            {"example_id": "pair-02", "prompt": "completion:", "completion": " fixed loss", "text": "completion: fixed loss"},
        ],
        "holdout_prompt_rows": [{"case_id": "holdout-01", "prompt": "answer:", "expected_terms": ["fixed", "loss"]}],
    }
    outputs = write_unassisted_holdout_repair_seed_corpus_v1149_outputs(report, root / "seed-corpus")
    return report, Path(outputs["json"])


def write_fake_run(root: Path, prepared_text: str) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text(json.dumps({"max_iters": 50, "seed": 1150, "prepared_data": "seed.txt"}), encoding="utf-8")
    write_json_payload({"training": {"args": {"seed": 1150, "max_iters": 50}}}, run_dir / "run_manifest.json")
    (run_dir / "metrics.jsonl").write_text(
        json.dumps({"step": 1, "train_loss": 3.0, "val_loss": 3.2}) + "\n" + json.dumps({"step": 50, "train_loss": 1.2, "val_loss": 1.5}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "history_summary.json").write_text(json.dumps({"last_step": 50}), encoding="utf-8")
    (run_dir / "loss_curve.svg").write_text("<svg></svg>", encoding="utf-8")
    (run_dir / "sample.txt").write_text("prompt: answer:\n\nanswer: fixed\n", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text(prepared_text, encoding="utf-8")
    return run_dir


def corpus_text() -> str:
    return "answer: fixed loss\n\ncompletion: fixed loss\n"


if __name__ == "__main__":
    unittest.main()
