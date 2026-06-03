from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run,
    locate_rebalanced_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run import main as cli_main


class RebalancedTrainingRunTests(unittest.TestCase):
    def test_builds_ready_rebalanced_training_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run(ready_rebalanced_seed(), run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_ready")
        self.assertTrue(report["summary"]["decoder_anchor_rebalanced_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 4)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["direct_answer_count"], 15)
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_fails_when_rebalanced_direct_share_is_not_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = ready_rebalanced_seed()
            seed["summary"]["direct_answer_share"] = 0.1
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run(seed, write_fake_run(root))

        self.assertEqual(report["status"], "fail")
        self.assertIn("direct_answer_share_repaired", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs(ready_rebalanced_seed(), root / "seed")
            run_dir = write_fake_run(root)
            self.assertEqual(locate_rebalanced_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run(ready_rebalanced_seed(), run_dir)
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_outputs(report, root / "training")
            cli_main(
                [
                    "--rebalanced-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-training"),
                    "--require-training-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("rebalanced_training_ready=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_text(report))
        self.assertIn("Artifacts", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_markdown(report))
        self.assertIn("rebalanced decoder-anchor corpus", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_html(report))

    def test_cli_force_preserves_nested_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs(ready_rebalanced_seed(), root / "seed")
            out_dir = root / "evidence"
            out_dir.mkdir()
            run_dir = write_fake_run(out_dir)
            (out_dir / "stale.txt").write_text("stale", encoding="utf-8")
            cli_main(
                [
                    "--rebalanced-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(out_dir),
                    "--require-training-ready",
                    "--force",
                ]
            )
            self.assertTrue((run_dir / "checkpoint.pt").is_file())
            self.assertFalse((out_dir / "stale.txt").exists())


def ready_rebalanced_seed() -> dict:
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_rebalanced_seed_revision_ready": True,
            "example_count": 40,
            "carry_forward_count": 10,
            "direct_answer_count": 15,
            "decoder_bridge_count": 15,
            "carry_forward_share": 0.25,
            "direct_answer_share": 0.375,
            "decoder_bridge_share": 0.375,
        },
        "seed_examples": [],
    }


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text(json.dumps({"max_iters": 4, "seed": 1093}), encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps({"training": {"args": {"seed": 1093}}}), encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text(
        json.dumps({"step": 1, "train_loss": 4.0, "val_loss": 4.1}) + "\n" + json.dumps({"step": 4, "train_loss": 3.5, "val_loss": 3.6}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "sample.txt").write_text("fixed loss", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text("fixed loss", encoding="utf-8")
    return run_dir


if __name__ == "__main__":
    unittest.main()
