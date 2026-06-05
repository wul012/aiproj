from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME,
    build_stabilized_loss_suffix_uptake_replay_comparison,
    locate_objective_contract,
    locate_stabilized_loss_suffix_uptake_training_run,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_artifacts import (
    render_stabilized_loss_suffix_uptake_replay_comparison_html,
    render_stabilized_loss_suffix_uptake_replay_comparison_markdown,
    render_stabilized_loss_suffix_uptake_replay_comparison_text,
    write_stabilized_loss_suffix_uptake_replay_comparison_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_training_run import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.run_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison import (
    main as cli_main,
)
from tests.test_bounded_objective_loss_signal_bridge_replay_comparison import fake_runner, objective_contract, write_fake_run


class StabilizedLossSuffixUptakeReplayComparisonTests(unittest.TestCase):
    def test_partial_replay_is_ready_but_not_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_stabilized_loss_suffix_uptake_replay_comparison(
                objective_contract(),
                training_run(write_fake_run(Path(tmp))),
                generator_runner=fake_runner({"canonical_direct_completion": " fixed loss"}),
            )

        self.assertEqual(report["status"], "pass")
        self.assertIn("stabilized_loss_suffix_uptake", report["decision"])
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_ready"])
        self.assertEqual(report["summary"]["route"], "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake")
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)

    def test_contract_recovered_still_requires_holdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_stabilized_loss_suffix_uptake_replay_comparison(
                objective_contract(),
                training_run(write_fake_run(Path(tmp))),
                generator_runner=fake_runner({}),
            )

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_contract_recovered_holdout_required")
        self.assertTrue(report["summary"]["objective_contract_recovered"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 0)

    def test_training_run_must_be_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            training = training_run(write_fake_run(Path(tmp)))
            training["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_training_ready"] = False
            report = build_stabilized_loss_suffix_uptake_replay_comparison(objective_contract(), training, generator_runner=fake_runner({}))

        self.assertEqual(report["status"], "fail")
        self.assertIn("training_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            training_path = root / "training" / TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_TRAINING_RUN_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(training_run(run_dir), training_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_stabilized_loss_suffix_uptake_training_run(training_path.parent), training_path)
            report = build_stabilized_loss_suffix_uptake_replay_comparison(objective_contract(), training_run(run_dir), generator_runner=fake_runner({}))
            outputs = write_stabilized_loss_suffix_uptake_replay_comparison_outputs(report, root / "out")
            cli_main([
                "--objective-contract",
                str(contract_path.parent),
                "--training-run",
                str(training_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME))
        self.assertIn("stabilized_loss_suffix_uptake_replay_comparison_ready=True", render_stabilized_loss_suffix_uptake_replay_comparison_text(report))
        self.assertIn("Replay Rows", render_stabilized_loss_suffix_uptake_replay_comparison_markdown(report))
        self.assertIn("Replay Rows", render_stabilized_loss_suffix_uptake_replay_comparison_html(report))


def training_run(run_dir: Path) -> dict[str, object]:
    return {
        "status": "pass",
        "run_dir": str(run_dir),
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_training_ready": True,
            "final_train_loss": 0.48,
            "final_val_loss": 0.53,
            "train_loss_delta": -3.17,
        },
    }


if __name__ == "__main__":
    unittest.main()
