from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import torch

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe import (
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME,
    build_loss_token_probability_probe,
    locate_objective_contract,
    locate_replay_delta_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_artifacts import (
    render_loss_token_probability_probe_html,
    render_loss_token_probability_probe_markdown,
    render_loss_token_probability_probe_text,
    write_loss_token_probability_probe_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.probe_bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability import main as cli_main


class LossTokenProbabilityProbeTests(unittest.TestCase):
    def test_detects_low_probability_loss_suffix_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_loss_token_probability_probe(
                objective_contract(),
                replay_delta(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                token_scorer=fake_scorer(),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_low_probability")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready"])
        self.assertEqual(report["summary"]["probe_step_count"], 9)
        self.assertEqual(report["summary"]["target_top1_step_count"], 0)
        self.assertEqual(report["summary"]["low_probability_step_count"], 9)
        self.assertEqual(report["summary"]["next_step"], "add_targeted_oss_suffix_probability_repair_before_more_training")
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True), 0)

    def test_detects_topk_visible_loss_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_loss_token_probability_probe(
                objective_contract(),
                replay_delta(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                token_scorer=fake_scorer(rank=2, probability=0.2),
            )

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_visible_not_top1")
        self.assertTrue(report["summary"]["all_cases_loss_suffix_topk"])
        self.assertEqual(report["summary"]["next_step"], "test_greedy_or_low_temperature_loss_suffix_replay")

    def test_fails_when_replay_delta_is_not_ready(self) -> None:
        bad_delta = replay_delta()
        bad_delta["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready"] = False
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_loss_token_probability_probe(
                objective_contract(),
                bad_delta,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                token_scorer=fake_scorer(),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_delta_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = fake_checkpoint(root)
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            delta_path = root / "delta" / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            write_json_payload(replay_delta(), delta_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            self.assertEqual(locate_replay_delta_diagnostic(delta_path.parent), delta_path)
            report = build_loss_token_probability_probe(
                objective_contract(),
                replay_delta(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                token_scorer=fake_scorer(),
            )
            outputs = write_loss_token_probability_probe_outputs(report, root / "out")
            cli_main([
                "--objective-contract",
                str(contract_path.parent),
                "--replay-delta-diagnostic",
                str(delta_path.parent),
                "--checkpoint",
                str(checkpoint),
                "--tokenizer",
                str(tokenizer),
                "--device",
                "cpu",
                "--out-dir",
                str(root / "cli-out"),
                "--require-probe-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME))
        self.assertIn("loss_token_probability_probe_ready=True", render_loss_token_probability_probe_text(report))
        self.assertIn("Probe Steps", render_loss_token_probability_probe_markdown(report))
        self.assertIn("Probe Steps", render_loss_token_probability_probe_html(report))


def objective_contract() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_contract_ready": True, "contract_case_count": 3},
        "contract_cases": [
            case("canonical_direct_completion", "Answer with exactly two tokens: fixed loss\nanswer:"),
            case("minimal_direct_completion", "Answer with exactly two words: fixed loss\nanswer:"),
            case("completion_label_surface", "Complete with: fixed loss\ncompletion:"),
        ],
    }


def replay_delta() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready": True,
            "no_contract_gain_confirmed": True,
        },
    }


def case(case_id: str, prompt: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "prompt": prompt,
        "expected_completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
    }


def fake_scorer(*, rank: int = 8, probability: float = 0.04):
    def score(_context: str, target_token: str) -> dict[str, object]:
        return {
            "target_token_id": {"o": 37, "s": 41}.get(target_token, 0),
            "target_probability": probability,
            "target_rank": rank,
            "target_in_top_k": rank <= 5,
            "top_token": "\n",
            "top_token_probability": 0.5,
            "top_candidates": [
                {"rank": 1, "token_id": 1, "token_text": "\n", "probability": 0.5},
                {"rank": rank, "token_id": {"o": 37, "s": 41}.get(target_token, 0), "token_text": target_token, "probability": probability},
            ],
        }

    return score


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
