from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed import build_model_capability_route_promotion_bounded_real_replay_repair_seed
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts import write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run import (
    build_model_capability_route_promotion_bounded_real_replay_repair_training_run,
    locate_route_promotion_bounded_real_replay_repair_seed,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_training_run import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_seed import ready_seed_inputs


def ready_seed(root: Path) -> tuple[dict, Path]:
    plan, _, replay, _ = ready_seed_inputs(root)
    seed = build_model_capability_route_promotion_bounded_real_replay_repair_seed(plan, replay)
    outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs(seed, root / "seed")
    return seed, Path(outputs["json"])


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text(json.dumps({"max_iters": 2, "seed": 991}), encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps({"training": {"args": {"seed": 991}}}), encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text(
        json.dumps({"step": 1, "train_loss": 4.0, "val_loss": 4.2}) + "\n" + json.dumps({"step": 2, "train_loss": 3.8, "val_loss": 4.0}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "sample.txt").write_text("fixed loss", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text("fixed loss", encoding="utf-8")
    return run_dir


class ModelCapabilityRoutePromotionBoundedRealReplayRepairTrainingRunTests(unittest.TestCase):
    def test_builds_ready_training_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed, seed_path = ready_seed(root)
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run(seed, run_dir, repair_seed_path=seed_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_training_run_ready")
        self.assertTrue(report["summary"]["bounded_real_replay_repair_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 2)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed, _ = ready_seed(root)
            run_dir = write_fake_run(root)
            (run_dir / "checkpoint.pt").unlink()
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run(seed, run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed, seed_path = ready_seed(root)
            run_dir = write_fake_run(root)
            self.assertEqual(locate_route_promotion_bounded_real_replay_repair_seed(seed_path.parent), seed_path)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run(seed, run_dir, repair_seed_path=seed_path)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs(report, root / "training-evidence")
            cli_main(["--repair-seed", str(seed_path.parent), "--run-dir", str(run_dir), "--out-dir", str(root / "cli-training"), "--require-training-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bounded_real_replay_repair_training_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_text(report))
        self.assertIn("Artifacts", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_markdown(report))
        self.assertIn("repair training", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_html(report))


if __name__ == "__main__":
    unittest.main()
