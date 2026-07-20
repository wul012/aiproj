from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_curriculum_patch_profile_sweep import (
    CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME,
    build_bounded_objective_curriculum_patch_profile_sweep,
    locate_curriculum_patch_training_run,
    locate_objective_contract,
    locate_shape_migration_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_curriculum_patch_profile_sweep_artifacts import (
    render_curriculum_patch_profile_sweep_html,
    render_curriculum_patch_profile_sweep_markdown,
    render_curriculum_patch_profile_sweep_text,
    write_curriculum_patch_profile_sweep_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.curriculum_patch_shape_diag import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.run_bounded_objective_curriculum_patch_profile_sweep import main as cli_main


class BoundedObjectiveCurriculumPatchProfileSweepTests(unittest.TestCase):
    def test_profile_sweep_finds_loss_signal_without_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_bounded_objective_curriculum_patch_profile_sweep(
                objective_contract(),
                training_run(run_dir),
                shape_diagnostic(),
                profiles=profiles(),
                profile_runner=fake_runner({"loss-probe": " loss", "baseline": " fixed"}),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_curriculum_patch_profile_sweep_found_loss_signal_bridge_required")
        self.assertTrue(report["summary"]["bounded_objective_curriculum_patch_profile_sweep_ready"])
        self.assertFalse(report["summary"]["any_profile_recovered"])
        self.assertEqual(report["summary"]["profile_with_loss_hit_count"], 1)
        self.assertEqual(report["summary"]["max_loss_hit_case_count"], 2)
        self.assertEqual(report["summary"]["best_profile_id"], "loss-probe")
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True, require_any_profile_recovered=True), 1)

    def test_fails_when_shape_diagnostic_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            diagnostic = shape_diagnostic()
            diagnostic["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready"] = False
            report = build_bounded_objective_curriculum_patch_profile_sweep(
                objective_contract(),
                training_run(run_dir),
                diagnostic,
                profiles=profiles(),
                profile_runner=fake_runner({"baseline": " fixed"}),
            )

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "bounded_objective_curriculum_patch_profile_sweep_blocked")
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            training_path = root / "training" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME
            diagnostic_path = root / "diagnostic" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(training_run(run_dir), training_path)
            write_json_payload(shape_diagnostic(), diagnostic_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_curriculum_patch_training_run(training_path.parent), training_path)
            self.assertEqual(locate_shape_migration_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_bounded_objective_curriculum_patch_profile_sweep(
                objective_contract(),
                training_run(run_dir),
                shape_diagnostic(),
                profiles=profiles(),
                profile_runner=fake_runner({"baseline": " fixed"}),
            )
            outputs = write_curriculum_patch_profile_sweep_outputs(report, root / "out")
            cli_main(
                [
                    "--objective-contract",
                    str(contract_path.parent),
                    "--training-run",
                    str(training_path.parent),
                    "--shape-diagnostic",
                    str(diagnostic_path.parent),
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
        self.assertTrue(outputs["json"].endswith(CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME))
        self.assertIn("profile_count=2", render_curriculum_patch_profile_sweep_text(report))
        self.assertIn("Profile Summaries", render_curriculum_patch_profile_sweep_markdown(report))
        self.assertIn("Sweep Rows", render_curriculum_patch_profile_sweep_html(report))


def objective_contract() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_contract_ready": True},
        "contract_cases": [
            {"case_id": "canonical", "prompt": "answer:", "required_terms": ["fixed", "loss"]},
            {"case_id": "minimal", "prompt": "answer:", "required_terms": ["fixed", "loss"]},
        ],
    }


def training_run(run_dir: Path) -> dict[str, object]:
    return {
        "status": "pass",
        "run_dir": str(run_dir),
        "summary": {"bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready": True},
    }


def shape_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready": True},
    }


def profiles() -> list[dict[str, object]]:
    return [
        {"profile_id": "baseline", "max_new_tokens": 8, "temperature": 0.2, "top_k": 20, "seed": 1},
        {"profile_id": "loss-probe", "max_new_tokens": 8, "temperature": 0.1, "top_k": 1, "seed": 2},
    ]


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    return run_dir


def fake_runner(by_profile: dict[str, str]):
    def run(case: dict[str, object], profile: dict[str, object], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, object]:
        continuation = by_profile.get(str(profile.get("profile_id")), " fixed")
        prompt = str(case.get("prompt") or "")
        return {"prompt": prompt, "continuation": continuation, "generated": prompt + continuation}

    return run


if __name__ == "__main__":
    unittest.main()
