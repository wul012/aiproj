from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import torch

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME,
    build_decoder_budget_replay_comparison,
    locate_decoder_budget_audit,
    locate_objective_contract,
    locate_stagnation_aware_suffix_training_run,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_artifacts import (
    render_decoder_budget_replay_comparison_html,
    render_decoder_budget_replay_comparison_markdown,
    render_decoder_budget_replay_comparison_text,
    write_decoder_budget_replay_comparison_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.run_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison import main as cli_main


class DecoderBudgetReplayComparisonTests(unittest.TestCase):
    def test_budget_replay_recovers_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_decoder_budget_replay_comparison(
                objective_contract(),
                training_run(),
                decoder_budget_audit(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner({"canonical_direct_completion": "\nfixed loss", "minimal_direct_completion": "\nfixed loss", "completion_label_surface": "\nfixed loss"}),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_contract_recovered_holdout_required")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_ready"])
        self.assertTrue(report["summary"]["objective_contract_recovered"])
        self.assertEqual(report["summary"]["passed_case_count"], 3)
        self.assertEqual(report["summary"]["decoder_budget_max_new_tokens"], 11)
        self.assertEqual(report["interpretation"]["next_action"], "run_unchanged_bounded_suite_holdout_replay")
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 0)

    def test_fails_when_budget_audit_is_not_ready(self) -> None:
        audit = decoder_budget_audit()
        audit["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready"] = False
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_decoder_budget_replay_comparison(
                objective_contract(),
                training_run(),
                audit,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner({"canonical_direct_completion": "\nfixed loss"}),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("decoder_budget_audit_ready", [issue["id"] for issue in report["issues"]])

    def test_partial_budget_replay_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_decoder_budget_replay_comparison(
                objective_contract(),
                training_run(),
                decoder_budget_audit(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner({"canonical_direct_completion": "\nfixed loss"}),
            )

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_partial_required_term_hit")
        self.assertFalse(report["summary"]["objective_contract_recovered"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_objective_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = fake_checkpoint(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            training_path = root / "training" / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME
            audit_path = root / "audit" / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(training_run(), training_path)
            write_json_payload(decoder_budget_audit(), audit_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_stagnation_aware_suffix_training_run(training_path.parent), training_path)
            self.assertEqual(locate_decoder_budget_audit(audit_path.parent), audit_path)
            report = build_decoder_budget_replay_comparison(
                objective_contract(),
                training_run(),
                decoder_budget_audit(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner({"canonical_direct_completion": "\nfixed loss"}),
            )
            outputs = write_decoder_budget_replay_comparison_outputs(report, root / "out")
            cli_main([
                "--objective-contract",
                str(contract_path.parent),
                "--training-run",
                str(training_path.parent),
                "--decoder-budget-audit",
                str(audit_path.parent),
                "--checkpoint",
                str(checkpoint),
                "--tokenizer",
                str(tokenizer),
                "--device",
                "cpu",
                "--out-dir",
                str(root / "cli-out"),
                "--require-comparison-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME))
        self.assertIn("decoder_budget_replay_comparison_ready=True", render_decoder_budget_replay_comparison_text(report))
        self.assertIn("Replay Rows", render_decoder_budget_replay_comparison_markdown(report))
        self.assertIn("Replay Rows", render_decoder_budget_replay_comparison_html(report))


def objective_contract() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_contract_ready": True, "contract_case_count": 3, "unchanged_suite_check_required": True},
        "objective_contract": {"required_exact_completion": True},
        "contract_cases": [
            case("canonical_direct_completion", "Answer with exactly two tokens: fixed loss\nanswer:"),
            case("minimal_direct_completion", "Answer with exactly two words: fixed loss\nanswer:"),
            case("completion_label_surface", "Complete with: fixed loss\ncompletion:"),
        ],
    }


def training_run() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_ready": True,
            "final_train_loss": 0.5,
            "final_val_loss": 0.6,
            "train_loss_delta": -1.0,
        },
        "run_dir": "",
    }


def decoder_budget_audit() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready": True,
            "recommended_max_new_tokens": 11,
        },
    }


def case(case_id: str, prompt: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "prompt": prompt,
        "expected_completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
    }


def fake_runner(outputs: dict[str, str]):
    def run(case: dict[str, object], _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict[str, object]:
        prompt = str(case.get("prompt") or "")
        continuation = outputs.get(str(case.get("case_id")), "\nunrelated")
        return {
            "prompt": prompt,
            "generated": prompt + continuation,
            "continuation": continuation,
            "max_new_tokens": 11,
            "temperature": 0.2,
            "top_k": 20,
            "seed": 1839,
        }

    return run


def fake_checkpoint(root: Path) -> tuple[Path, Path]:
    tokenizer = CharTokenizer.train("Answer with exactly two tokens: fixed loss\nanswer: Complete with completion:")
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=64, n_layer=1, n_head=1, n_embd=16, dropout=0.0)
    model = MiniGPT(config)
    checkpoint_path = root / "checkpoint.pt"
    torch.save({"config": config.__dict__, "model": model.state_dict(), "step": 0}, checkpoint_path)
    return checkpoint_path, tokenizer_path


if __name__ == "__main__":
    unittest.main()
