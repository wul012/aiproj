from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run,
    locate_curriculum_patch,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_html,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_text,
    write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionCurriculumPatchTrainingRunTests(unittest.TestCase):
    def test_training_run_ready_for_curriculum_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run(
                curriculum_patch(),
                run_dir,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready"])
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "training_artifact_only")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 0)

    def test_training_run_fails_when_patch_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch = curriculum_patch()
            patch["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready"] = False
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run(
                patch,
                write_fake_run(root),
            )

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run")
        self.assertEqual(resolve_exit_code(report, require_training_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            patch_path = root / "patch" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME
            write_json_payload(curriculum_patch(), patch_path)
            self.assertEqual(locate_curriculum_patch(patch_path.parent), patch_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run(
                curriculum_patch(),
                run_dir,
            )
            outputs = write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_outputs(report, root / "out")
            cli_main(
                [
                    "--curriculum-patch",
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
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready=True", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_text(report))
        self.assertIn("training run", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_markdown(report))
        self.assertIn("Artifacts", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_html(report))


def curriculum_patch() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready": True,
            "patch_example_count": 18,
            "loss_focus_example_count": 18,
            "completion_surface_example_count": 2,
            "decoder_anchor_example_count": 0,
            "patched_corpus_char_count": 2996,
        },
    }


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (run_dir / "train_config.json").write_text('{"max_iters": 20, "seed": 1856}', encoding="utf-8")
    (run_dir / "run_manifest.json").write_text('{"training": {"args": {"seed": 1856}}}', encoding="utf-8")
    (run_dir / "sample.txt").write_text("fixed loss", encoding="utf-8")
    (run_dir / "prepared_corpus.txt").write_text("answer: fixed loss", encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text(
        '{"step": 1, "train_loss": 3.0, "val_loss": 3.2, "last_loss": 3.0}\n'
        '{"step": 20, "train_loss": 1.5, "val_loss": 1.8, "last_loss": 1.5}\n',
        encoding="utf-8",
    )
    return run_dir


if __name__ == "__main__":
    unittest.main()
