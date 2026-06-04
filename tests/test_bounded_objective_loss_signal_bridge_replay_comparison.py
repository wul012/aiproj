from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_replay_comparison,
    locate_loss_signal_bridge_training_run,
    locate_objective_contract,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_replay_comparison_artifacts import (
    render_loss_signal_bridge_replay_comparison_html,
    render_loss_signal_bridge_replay_comparison_markdown,
    render_loss_signal_bridge_replay_comparison_text,
    write_loss_signal_bridge_replay_comparison_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_training_run import LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.run_bounded_objective_loss_signal_bridge_replay_comparison import main as cli_main


class BoundedObjectiveLossSignalBridgeReplayComparisonTests(unittest.TestCase):
    def test_partial_replay_is_ready_but_not_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_bounded_objective_loss_signal_bridge_replay_comparison(
                objective_contract(),
                training_run(run_dir),
                generator_runner=fake_runner(
                    {
                        "canonical_direct_completion": " fixed",
                        "minimal_direct_completion": " unrelated",
                        "completion_label_surface": " unrelated",
                    }
                ),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_replay_partial_required_term_hit")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_replay_comparison_ready"])
        self.assertFalse(report["summary"]["objective_contract_recovered"])
        self.assertEqual(report["summary"]["passed_case_count"], 0)
        self.assertEqual(report["summary"]["any_hit_case_count"], 1)
        self.assertEqual(report["summary"]["route"], "bounded_objective_loss_signal_bridge")
        self.assertFalse(report["summary"]["decoder_anchor_used"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 1)

    def test_contract_recovered_still_requires_holdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_fake_run(Path(tmp))
            report = build_bounded_objective_loss_signal_bridge_replay_comparison(
                objective_contract(),
                training_run(run_dir),
                generator_runner=fake_runner({}),
            )

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_replay_contract_recovered_holdout_required")
        self.assertTrue(report["summary"]["objective_contract_recovered"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["interpretation"]["next_action"], "run_unchanged_bounded_suite_holdout_replay")
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 0)

    def test_training_run_must_be_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            training = training_run(write_fake_run(Path(tmp)))
            training["summary"]["bounded_objective_loss_signal_bridge_training_ready"] = False
            report = build_bounded_objective_loss_signal_bridge_replay_comparison(
                objective_contract(),
                training,
                generator_runner=fake_runner({}),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("training_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = write_fake_run(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            training_path = root / "training" / LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(training_run(run_dir), training_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_loss_signal_bridge_training_run(training_path.parent), training_path)
            report = build_bounded_objective_loss_signal_bridge_replay_comparison(
                objective_contract(),
                training_run(run_dir),
                generator_runner=fake_runner({}),
            )
            outputs = write_loss_signal_bridge_replay_comparison_outputs(report, root / "out")
            cli_main(
                [
                    "--objective-contract",
                    str(contract_path.parent),
                    "--training-run",
                    str(training_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME))
        self.assertIn("bounded_objective_loss_signal_bridge_replay_comparison_ready=True", render_loss_signal_bridge_replay_comparison_text(report))
        self.assertIn("Replay Rows", render_loss_signal_bridge_replay_comparison_markdown(report))
        self.assertIn("Replay Rows", render_loss_signal_bridge_replay_comparison_html(report))


def objective_contract() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_contract_ready": True,
            "contract_case_count": 3,
            "unchanged_suite_check_required": True,
        },
        "objective_contract": {"required_exact_completion": "fixed loss"},
        "contract_cases": [
            {"case_id": "canonical_direct_completion", "prompt": "answer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "minimal_direct_completion", "prompt": "answer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "completion_label_surface", "prompt": "completion:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
        ],
    }


def training_run(run_dir: Path) -> dict[str, object]:
    return {
        "status": "pass",
        "run_dir": str(run_dir),
        "summary": {
            "bounded_objective_loss_signal_bridge_training_ready": True,
            "final_train_loss": 1.47,
            "final_val_loss": 1.12,
            "train_loss_delta": -2.12,
            "decoder_anchor_example_count": 0,
        },
    }


def write_fake_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    return run_dir


def fake_runner(overrides: dict[str, str]):
    def run(case: dict[str, object], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, object]:
        prompt = str(case.get("prompt") or "")
        continuation = overrides.get(str(case.get("case_id") or ""), " fixed loss")
        return {
            "prompt": prompt,
            "continuation": continuation,
            "generated": prompt + continuation,
            "max_new_tokens": 8,
            "temperature": 0.2,
            "top_k": 20,
            "seed": 1862,
        }

    return run


if __name__ == "__main__":
    unittest.main()
