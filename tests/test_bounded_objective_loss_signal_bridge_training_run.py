from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge import LOSS_SIGNAL_BRIDGE_JSON_FILENAME
from minigpt.bounded_objective_loss_signal_bridge_training_run import (
    LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_training_run,
    locate_loss_signal_bridge,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_training_run_artifacts import (
    render_loss_signal_bridge_training_run_html,
    render_loss_signal_bridge_training_run_markdown,
    render_loss_signal_bridge_training_run_text,
    write_loss_signal_bridge_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_training_run import main as cli_main


class BoundedObjectiveLossSignalBridgeTrainingRunTests(unittest.TestCase):
    def test_training_run_ready_for_loss_signal_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            report = build_bounded_objective_loss_signal_bridge_training_run(loss_signal_bridge(), run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 6)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "bounded_objective_loss_signal_bridge_replay_comparison")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "training_artifact_only")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_when_bridge_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = loss_signal_bridge()
            bridge["summary"]["bounded_objective_loss_signal_bridge_ready"] = False
            report = build_bounded_objective_loss_signal_bridge_training_run(bridge, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_bounded_objective_loss_signal_bridge_training_run")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            bridge_path = root / "bridge" / LOSS_SIGNAL_BRIDGE_JSON_FILENAME
            write_json_payload(loss_signal_bridge(), bridge_path)
            self.assertEqual(locate_loss_signal_bridge(bridge_path.parent), bridge_path)
            report = build_bounded_objective_loss_signal_bridge_training_run(loss_signal_bridge(), run_dir, bridge_path=bridge_path)
            outputs = write_loss_signal_bridge_training_run_outputs(report, root / "out")
            cli_main(["--loss-signal-bridge", str(bridge_path.parent), "--run-dir", str(run_dir), "--out-dir", str(root / "cli-out"), "--require-training-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_loss_signal_bridge_training_ready=True", render_loss_signal_bridge_training_run_text(report))
        self.assertIn("Artifacts", render_loss_signal_bridge_training_run_markdown(report))
        self.assertIn("Artifacts", render_loss_signal_bridge_training_run_html(report))


def loss_signal_bridge() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_ready": True,
            "bridge_example_count": 16,
            "loss_signal_bridge_example_count": 6,
            "decoder_anchor_example_count": 0,
            "bridged_corpus_char_count": 3908,
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
        {"step": 0, "train_loss": 3.0, "val_loss": 3.2},
        {"step": 6, "train_loss": 1.8, "val_loss": 2.0},
    ]
    (run_dir / "metrics.jsonl").write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json_payload({"max_iters": 6, "seed": 1861}, run_dir / "train_config.json")
    write_json_payload({"training": {"args": {"seed": 1861}}}, run_dir / "run_manifest.json")
    return run_dir


if __name__ == "__main__":
    unittest.main()
