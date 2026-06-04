from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_patch import (
    SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_training_run import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_single_line_surface_training_run,
    locate_single_line_surface_patch,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_training_run_artifacts import (
    render_single_line_surface_training_run_html,
    render_single_line_surface_training_run_markdown,
    render_single_line_surface_training_run_text,
    write_single_line_surface_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_single_line_surface_training_run import main as cli_main


class BoundedObjectiveLossSignalBridgeSingleLineSurfaceTrainingRunTests(unittest.TestCase):
    def test_training_run_ready_for_single_line_surface_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_bounded_objective_loss_signal_bridge_single_line_surface_training_run(
                single_line_surface_patch(),
                write_fake_run(root),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_single_line_surface_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_single_line_surface_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 10)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(
            report["summary"]["proposed_next_artifact"],
            "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison",
        )
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_when_patch_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            patch = single_line_surface_patch()
            patch["summary"]["bounded_objective_loss_signal_bridge_single_line_surface_patch_ready"] = False
            report = build_bounded_objective_loss_signal_bridge_single_line_surface_training_run(patch, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_bounded_objective_loss_signal_bridge_single_line_surface_training_run")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "patch" / SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME
            run_dir = write_fake_run(root)
            write_json_payload(single_line_surface_patch(), patch_path)
            self.assertEqual(locate_single_line_surface_patch(patch_path.parent), patch_path)
            report = build_bounded_objective_loss_signal_bridge_single_line_surface_training_run(
                single_line_surface_patch(),
                run_dir,
                single_line_surface_patch_path=patch_path,
            )
            outputs = write_single_line_surface_training_run_outputs(report, root / "out")
            cli_main(
                [
                    "--single-line-surface-patch",
                    str(patch_path.parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-training-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("single_line_surface_training_ready=True", render_single_line_surface_training_run_text(report))
        self.assertIn("single-line surface training run", render_single_line_surface_training_run_markdown(report))
        self.assertIn("single-line surface training run", render_single_line_surface_training_run_html(report))


def single_line_surface_patch() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_single_line_surface_patch_ready": True,
            "patch_example_count": 14,
            "single_line_case_example_count": 6,
            "decoder_anchor_example_count": 0,
            "patched_corpus_char_count": 2048,
        },
    }


def write_fake_run(root: Path) -> Path:
    run = root / "run"
    run.mkdir(parents=True, exist_ok=True)
    files = {
        "checkpoint.pt": b"fake",
        "tokenizer.json": b"{}",
        "metrics.jsonl": b'{"step": 0, "train_loss": 2.4, "val_loss": 2.6}\n{"step": 10, "train_loss": 1.1, "val_loss": 1.2}\n',
        "train_config.json": json.dumps({"max_iters": 10, "sample_prompt": "answer:"}).encode(),
        "run_manifest.json": b"{}",
        "run_manifest.svg": b"<svg/>",
        "loss_curve.svg": b"<svg/>",
        "sample.txt": b"answer: fixed loss",
        "prepared_corpus.txt": b"answer: fixed loss",
    }
    for name, content in files.items():
        (run / name).write_bytes(content)
    return run


if __name__ == "__main__":
    unittest.main()
