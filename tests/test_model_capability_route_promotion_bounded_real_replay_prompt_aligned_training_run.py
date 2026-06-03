from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run import (
    build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run,
    locate_prompt_aligned_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_html,
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_markdown,
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_text,
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import diagnostic_report
from tests.test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import seed_revision_report
from tests.test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import suite_report


def ready_prompt_aligned_seed_revision() -> dict:
    return build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision(
        suite_report(),
        diagnostic_report(),
        seed_revision_report(),
    )


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text(json.dumps({"max_iters": 4, "seed": 993}), encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps({"training": {"args": {"seed": 993}}}), encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text(
        json.dumps({"step": 1, "train_loss": 4.0, "val_loss": 4.1}) + "\n" + json.dumps({"step": 4, "train_loss": 3.6, "val_loss": 3.7}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "sample.txt").write_text("fixed loss", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text("fixed loss", encoding="utf-8")
    return run_dir


class ModelCapabilityRoutePromotionBoundedRealReplayPromptAlignedTrainingRunTests(unittest.TestCase):
    def test_builds_ready_prompt_aligned_training_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_prompt_aligned_seed_revision()
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run(seed, run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_ready")
        self.assertTrue(report["summary"]["prompt_aligned_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 4)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["exact_prompt_answer_count"], 2)
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_prompt_aligned_training_run_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_prompt_aligned_seed_revision()
            run_dir = write_fake_run(root)
            (run_dir / "checkpoint.pt").unlink()
            report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run(seed, run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_prompt_aligned_seed_revision()
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs(seed, root / "prompt-seed")
            run_dir = write_fake_run(root)
            self.assertEqual(locate_prompt_aligned_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run(seed, run_dir)
            outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_outputs(report, root / "training")
            cli_main(
                [
                    "--prompt-aligned-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-training"),
                    "--require-prompt-aligned-training-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("prompt_aligned_training_ready=True", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_text(report))
        self.assertIn("Artifacts", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_markdown(report))
        self.assertIn("prompt-aligned training run", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_html(report))

    def test_cli_force_preserves_nested_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_prompt_aligned_seed_revision()
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs(seed, root / "prompt-seed")
            out_dir = root / "evidence"
            run_dir = out_dir / "run"
            out_dir.mkdir()
            write_fake_run(out_dir)
            (out_dir / "stale.txt").write_text("stale", encoding="utf-8")
            cli_main(
                [
                    "--prompt-aligned-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(out_dir),
                    "--require-prompt-aligned-training-ready",
                    "--force",
                ]
            )
            self.assertTrue((run_dir / "checkpoint.pt").is_file())
            self.assertFalse((out_dir / "stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
