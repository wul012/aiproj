from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_patch import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_training_run import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_pair_binding_training_run,
    locate_pair_binding_patch,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_training_run_artifacts import (
    render_pair_binding_training_run_html,
    render_pair_binding_training_run_markdown,
    render_pair_binding_training_run_text,
    write_pair_binding_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_pair_binding_training_run import main as cli_main


class BoundedObjectiveLossSignalBridgePairBindingTrainingRunTests(unittest.TestCase):
    def test_training_run_ready_for_pair_binding_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_bounded_objective_loss_signal_bridge_pair_binding_training_run(pair_binding_patch(), write_fake_run(root))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_pair_binding_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_pair_binding_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 8)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "bounded_objective_loss_signal_bridge_pair_binding_replay_comparison")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_when_patch_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            patch = pair_binding_patch()
            patch["summary"]["bounded_objective_loss_signal_bridge_pair_binding_patch_ready"] = False
            report = build_bounded_objective_loss_signal_bridge_pair_binding_training_run(patch, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_bounded_objective_loss_signal_bridge_pair_binding_training_run")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            patch_path = root / "patch" / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME
            write_json_payload(pair_binding_patch(), patch_path)
            self.assertEqual(locate_pair_binding_patch(patch_path.parent), patch_path)
            report = build_bounded_objective_loss_signal_bridge_pair_binding_training_run(pair_binding_patch(), run_dir, pair_binding_patch_path=patch_path)
            outputs = write_pair_binding_training_run_outputs(report, root / "out")
            cli_main(["--pair-binding-patch", str(patch_path.parent), "--run-dir", str(run_dir), "--out-dir", str(root / "cli-out"), "--require-training-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_loss_signal_bridge_pair_binding_training_ready=True", render_pair_binding_training_run_text(report))
        self.assertIn("Artifacts", render_pair_binding_training_run_markdown(report))
        self.assertIn("Artifacts", render_pair_binding_training_run_html(report))


def pair_binding_patch() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_pair_binding_patch_ready": True,
            "patch_example_count": 18,
            "pair_binding_example_count": 6,
            "decoder_anchor_example_count": 0,
            "patched_corpus_char_count": 4771,
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
        {"step": 0, "train_loss": 3.4, "val_loss": 3.6},
        {"step": 8, "train_loss": 1.5, "val_loss": 1.9},
    ]
    (run_dir / "metrics.jsonl").write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json_payload({"max_iters": 8, "seed": 1865}, run_dir / "train_config.json")
    write_json_payload({"training": {"args": {"seed": 1865}}}, run_dir / "run_manifest.json")
    return run_dir


if __name__ == "__main__":
    unittest.main()
