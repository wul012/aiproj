from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_revision import (
    build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision,
    locate_route_promotion_bounded_real_replay_repair_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_seed_revision import ready_strategy_revision
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_seed_revision import repair_seed_report
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision,
)


def ready_seed_revision() -> dict:
    return build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision(ready_strategy_revision(), repair_seed_report())


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text(json.dumps({"max_iters": 3, "seed": 992}), encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps({"training": {"args": {"seed": 992}}}), encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text(
        json.dumps({"step": 1, "train_loss": 4.0, "val_loss": 4.1}) + "\n" + json.dumps({"step": 3, "train_loss": 3.7, "val_loss": 3.8}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "sample.txt").write_text("fixed loss", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text("fixed loss", encoding="utf-8")
    return run_dir


class ModelCapabilityRoutePromotionBoundedRealReplayRepairTrainingRunRevisionTests(unittest.TestCase):
    def test_builds_ready_training_revision_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_seed_revision()
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision(seed, run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_ready")
        self.assertTrue(report["summary"]["bounded_real_replay_repair_training_revision_ready"])
        self.assertEqual(report["summary"]["final_step"], 3)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["baseline_preservation_example_count"], 2)
        self.assertEqual(resolve_exit_code(report, require_training_revision_ready=True), 0)

    def test_training_revision_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_seed_revision()
            run_dir = write_fake_run(root)
            (run_dir / "checkpoint.pt").unlink()
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision(seed, run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_revision_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_seed_revision()
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs(seed, root / "seed-revision")
            run_dir = write_fake_run(root)
            self.assertEqual(locate_route_promotion_bounded_real_replay_repair_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision(seed, run_dir)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_outputs(report, root / "training-revision")
            cli_main(
                [
                    "--seed-revision",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-training-revision"),
                    "--require-training-revision-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("training_revision_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_text(report))
        self.assertIn("Artifacts", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_markdown(report))
        self.assertIn("repair training run revision", render_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_html(report))

    def test_cli_force_preserves_nested_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_seed_revision()
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs(seed, root / "seed-revision")
            out_dir = root / "evidence"
            run_dir = out_dir / "run"
            out_dir.mkdir()
            write_fake_run(out_dir)
            (out_dir / "stale.txt").write_text("stale", encoding="utf-8")
            cli_main(
                [
                    "--seed-revision",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(out_dir),
                    "--require-training-revision-ready",
                    "--force",
                ]
            )
            self.assertTrue((run_dir / "checkpoint.pt").is_file())
            self.assertFalse((out_dir / "stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
