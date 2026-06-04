from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_seed import (
    BOUNDED_OBJECTIVE_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_training_run import (
    BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_training_run,
    locate_objective_seed,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_training_run_artifacts import (
    render_bounded_objective_training_run_html,
    render_bounded_objective_training_run_markdown,
    render_bounded_objective_training_run_text,
    write_bounded_objective_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_training_run import main as cli_main


class BoundedObjectiveTrainingRunTests(unittest.TestCase):
    def test_builds_ready_bounded_objective_training_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_training_run(objective_seed(), run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 4)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["direct_example_count"], 18)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_replay_comparison")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            (run_dir / "checkpoint.pt").unlink()
            report = build_model_capability_route_promotion_bounded_objective_training_run(objective_seed(), run_dir)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_training_run_fails_with_carry_forward_seed(self) -> None:
        seed = objective_seed()
        seed["summary"]["carry_forward_example_count"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_route_promotion_bounded_objective_training_run(seed, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_carry_forward_examples", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            input_path = root / "seed" / BOUNDED_OBJECTIVE_SEED_JSON_FILENAME
            write_json_payload(objective_seed(), input_path)
            self.assertEqual(locate_objective_seed(input_path.parent), input_path)
            report = build_model_capability_route_promotion_bounded_objective_training_run(objective_seed(), run_dir)
            outputs = write_bounded_objective_training_run_outputs(report, root / "evidence")
            cli_main(
                [
                    "--objective-seed",
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
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_training_ready=True", render_bounded_objective_training_run_text(report))
        self.assertIn("Artifacts", render_bounded_objective_training_run_markdown(report))
        self.assertIn("Artifacts", render_bounded_objective_training_run_html(report))


def objective_seed() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_seed_ready": True,
            "example_count": 18,
            "direct_example_count": 18,
            "carry_forward_example_count": 0,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_training_run",
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
        {"step": 4, "train_loss": 1.2, "val_loss": 1.7},
    ]
    (run_dir / "metrics.jsonl").write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json_payload({"max_iters": 4, "seed": 1337}, run_dir / "train_config.json")
    write_json_payload({"training": {"args": {"seed": 1337}}}, run_dir / "run_manifest.json")
    return run_dir


if __name__ == "__main__":
    unittest.main()
