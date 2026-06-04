from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run,
    locate_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_training_run_html,
    render_bounded_objective_unassisted_repair_seed_revision_training_run_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_training_run_text,
    write_bounded_objective_unassisted_repair_seed_revision_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionTrainingRunTests(unittest.TestCase):
    def test_builds_seed_revision_training_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run(seed_revision(), run_dir)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_training_ready"])
        self.assertEqual(report["summary"]["final_step"], 8)
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_fails_when_seed_revision_not_ready(self) -> None:
        seed = seed_revision()
        seed["summary"]["bounded_objective_unassisted_repair_seed_revision_ready"] = False
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run(seed, write_fake_run(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("unassisted_repair_seed_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME
            write_json_payload(seed_revision(), seed_path)
            self.assertEqual(locate_seed_revision(seed_path.parent), seed_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run(seed_revision(), run_dir)
            outputs = write_bounded_objective_unassisted_repair_seed_revision_training_run_outputs(report, root / "out")
            cli_main(
                [
                    "--seed-revision",
                    str(seed_path.parent),
                    "--run-dir",
                    str(run_dir),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-training-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_seed_revision_training_ready=True", render_bounded_objective_unassisted_repair_seed_revision_training_run_text(report))
        self.assertIn("Artifacts", render_bounded_objective_unassisted_repair_seed_revision_training_run_markdown(report))
        self.assertIn("Artifacts", render_bounded_objective_unassisted_repair_seed_revision_training_run_html(report))


def seed_revision() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_ready": True,
            "example_count": 24,
            "neutral_prompt_example_count": 18,
            "decoder_anchor_example_count": 0,
            "corpus_char_count": 2028,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run",
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
        {"step": 8, "train_loss": 1.0, "val_loss": 1.5},
    ]
    (run_dir / "metrics.jsonl").write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    write_json_payload({"max_iters": 8, "seed": 1852}, run_dir / "train_config.json")
    write_json_payload({"training": {"args": {"seed": 1852}}}, run_dir / "run_manifest.json")
    return run_dir


if __name__ == "__main__":
    unittest.main()
