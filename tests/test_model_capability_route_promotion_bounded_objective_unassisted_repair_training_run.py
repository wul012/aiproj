from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run,
    locate_unassisted_repair_seed,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_artifacts import (
    render_bounded_objective_unassisted_repair_training_run_html,
    render_bounded_objective_unassisted_repair_training_run_markdown,
    render_bounded_objective_unassisted_repair_training_run_text,
    write_bounded_objective_unassisted_repair_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run import main as cli_main


class BoundedObjectiveUnassistedRepairTrainingRunTests(unittest.TestCase):
    def test_builds_ready_unassisted_repair_training_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run(unassisted_repair_seed(), run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 6)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["neutral_prompt_example_count"], 12)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "training_artifact_only")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            (run_dir / "checkpoint.pt").unlink()
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run(unassisted_repair_seed(), run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_training_run_fails_when_seed_uses_decoder_anchor(self) -> None:
        seed = unassisted_repair_seed()
        seed["summary"]["decoder_anchor_example_count"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run(seed, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_decoder_anchor_examples", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            input_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME
            write_json_payload(unassisted_repair_seed(), input_path)
            self.assertEqual(locate_unassisted_repair_seed(input_path.parent), input_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run(unassisted_repair_seed(), run_dir)
            outputs = write_bounded_objective_unassisted_repair_training_run_outputs(report, root / "evidence")
            cli_main(
                [
                    "--unassisted-repair-seed",
                    str(input_path.parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-evidence"),
                    "--require-training-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_training_ready=True", render_bounded_objective_unassisted_repair_training_run_text(report))
        self.assertIn("Artifacts", render_bounded_objective_unassisted_repair_training_run_markdown(report))
        self.assertIn("Artifacts", render_bounded_objective_unassisted_repair_training_run_html(report))


def unassisted_repair_seed() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_ready": True,
            "example_count": 24,
            "neutral_prompt_example_count": 12,
            "decoder_anchor_example_count": 0,
            "direct_example_count": 24,
            "corpus_char_count": 1778,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_training_run",
        },
    }


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, content in {
        "checkpoint.pt": b"checkpoint",
        "tokenizer.json": b"{}",
        "sample.txt": b"prompt\nfixed loss",
        "prepared_corpus.txt": b"answer: fixed loss",
    }.items():
        (run_dir / name).write_bytes(content)
    records = [
        {"step": 0, "train_loss": 2.0, "val_loss": 2.2},
        {"step": 6, "train_loss": 1.1, "val_loss": 1.6},
    ]
    (run_dir / "metrics.jsonl").write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json_payload({"max_iters": 6, "seed": 1847}, run_dir / "train_config.json")
    write_json_payload({"training": {"args": {"seed": 1847}}}, run_dir / "run_manifest.json")
    return run_dir


if __name__ == "__main__":
    unittest.main()
