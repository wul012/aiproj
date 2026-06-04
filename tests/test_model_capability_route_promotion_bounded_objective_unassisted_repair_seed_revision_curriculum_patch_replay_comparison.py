from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison,
    locate_curriculum_patch_training_run,
    locate_objective_contract,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_html,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_text,
    write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionCurriculumPatchReplayComparisonTests(unittest.TestCase):
    def test_partial_hit_replay_is_ready_but_not_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison(
                objective_contract(),
                curriculum_patch_training_run(run_dir),
                generator_runner=fake_runner(" fixed t"),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_partial_required_term_hit")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready"])
        self.assertFalse(report["summary"]["objective_contract_recovered"])
        self.assertEqual(report["summary"]["any_hit_case_count"], 3)
        self.assertEqual(report["summary"]["zero_hit_case_count"], 0)
        self.assertEqual(report["comparison"]["training_source"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run")
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 1)

    def test_all_cases_pass_marks_holdout_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison(
                objective_contract(),
                curriculum_patch_training_run(run_dir),
                generator_runner=fake_runner(" fixed loss"),
            )

        self.assertEqual(
            report["decision"],
            "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_contract_recovered_holdout_required",
        )
        self.assertTrue(report["summary"]["objective_contract_recovered"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 0)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            training_path = root / "training" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(curriculum_patch_training_run(run_dir), training_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_curriculum_patch_training_run(training_path.parent), training_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison(
                objective_contract(),
                curriculum_patch_training_run(run_dir),
                generator_runner=fake_runner(" fixed loss"),
            )
            outputs = write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_outputs(report, root / "out")
            cli_main(
                [
                    "--objective-contract",
                    str(contract_path.parent),
                    "--training-run",
                    str(training_path.parent),
                    "--checkpoint",
                    str(run_dir / "checkpoint.pt"),
                    "--tokenizer",
                    str(run_dir / "tokenizer.json"),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready=True", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_text(report))
        self.assertIn("Replay Rows", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_markdown(report))
        self.assertIn("Replay Rows", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_html(report))


def objective_contract() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_objective_contract_ready": True, "contract_case_count": 3, "unchanged_suite_check_required": True},
        "objective_contract": {"required_exact_completion": "fixed loss"},
        "contract_cases": [
            {"case_id": "canonical_direct_completion", "prompt": "answer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "minimal_direct_completion", "prompt": "answer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "completion_label_surface", "prompt": "completion:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
        ],
    }


def curriculum_patch_training_run(run_dir: Path) -> dict:
    return {
        "status": "pass",
        "run_dir": str(run_dir),
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready": True,
            "final_train_loss": 1.65,
            "final_val_loss": 1.76,
            "train_loss_delta": -1.9,
            "decoder_anchor_example_count": 0,
        },
    }


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    return run_dir


def fake_runner(continuation: str):
    def run(case: dict, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
        prompt = str(case.get("prompt") or "")
        return {
            "prompt": prompt,
            "continuation": continuation,
            "generated": prompt + continuation,
            "max_new_tokens": 8,
            "temperature": 0.2,
            "top_k": 20,
            "seed": 1857,
        }

    return run


if __name__ == "__main__":
    unittest.main()
