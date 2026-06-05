from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME,
    build_decoder_budget_audit,
    locate_loss_token_probability_probe,
    locate_stagnation_aware_suffix_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_artifacts import (
    render_decoder_budget_audit_html,
    render_decoder_budget_audit_markdown,
    render_decoder_budget_audit_text,
    write_decoder_budget_audit_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe import (
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.audit_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget import main as cli_main


class DecoderBudgetAuditTests(unittest.TestCase):
    def test_detects_budget_exhaustion_before_top1_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer = write_tokenizer(Path(tmp))
            report = build_decoder_budget_audit(replay_comparison(), probability_probe(), tokenizer_path=tokenizer)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_exhausted_before_loss_suffix")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready"])
        self.assertEqual(report["summary"]["budget_exhausted_case_count"], 3)
        self.assertEqual(report["summary"]["loss_suffix_top1_case_count"], 3)
        self.assertEqual(report["summary"]["recommended_max_new_tokens"], 11)
        self.assertEqual(report["summary"]["max_additional_tokens_needed"], 3)
        self.assertEqual(resolve_exit_code(report, require_audit_ready=True), 0)

    def test_fails_when_budget_is_already_sufficient(self) -> None:
        replay = replay_comparison(max_new_tokens=11)
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer = write_tokenizer(Path(tmp))
            report = build_decoder_budget_audit(replay, probability_probe(), tokenizer_path=tokenizer)

        self.assertEqual(report["status"], "fail")
        self.assertIn("budget_exhaustion_confirmed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["recommended_max_new_tokens"], 11)

    def test_fails_when_probability_probe_is_not_top1(self) -> None:
        probe = probability_probe(top1=False)
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer = write_tokenizer(Path(tmp))
            report = build_decoder_budget_audit(replay_comparison(), probe, tokenizer_path=tokenizer)

        self.assertEqual(report["status"], "fail")
        self.assertIn("probability_probe_top1", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer = write_tokenizer(root)
            replay_path = root / "replay" / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME
            probe_path = root / "probe" / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            write_json_payload(probability_probe(), probe_path)
            self.assertEqual(locate_stagnation_aware_suffix_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_loss_token_probability_probe(probe_path.parent), probe_path)
            report = build_decoder_budget_audit(replay_comparison(), probability_probe(), tokenizer_path=tokenizer)
            outputs = write_decoder_budget_audit_outputs(report, root / "out")
            cli_main([
                "--replay-comparison",
                str(replay_path.parent),
                "--loss-token-probability-probe",
                str(probe_path.parent),
                "--tokenizer",
                str(tokenizer),
                "--out-dir",
                str(root / "cli-out"),
                "--require-audit-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME))
        self.assertIn("decoder_budget_audit_ready=True", render_decoder_budget_audit_text(report))
        self.assertIn("Case Budget Rows", render_decoder_budget_audit_markdown(report))
        self.assertIn("Case Budget Rows", render_decoder_budget_audit_html(report))


def replay_comparison(*, max_new_tokens: int = 8) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready": True,
            "passed_case_count": 0,
            "any_hit_case_count": 3,
        },
        "replay_rows": [
            replay_row("canonical_direct_completion", max_new_tokens),
            replay_row("completion_label_surface", max_new_tokens),
            replay_row("minimal_direct_completion", max_new_tokens),
        ],
    }


def replay_row(case_id: str, max_new_tokens: int) -> dict[str, object]:
    return {
        "case_id": case_id,
        "continuation": "\nfixed l",
        "expected_completion": "fixed loss",
        "max_new_tokens": max_new_tokens,
    }


def probability_probe(*, top1: bool = True) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready": True,
            "all_cases_loss_suffix_top1": top1,
            "target_top1_rate": 1.0 if top1 else 0.0,
        },
        "case_rows": [
            probe_case("canonical_direct_completion", top1),
            probe_case("completion_label_surface", top1),
            probe_case("minimal_direct_completion", top1),
        ],
    }


def probe_case(case_id: str, top1: bool) -> dict[str, object]:
    return {
        "case_id": case_id,
        "target_suffix": "oss",
        "target_suffix_probability_product": 0.8,
        "loss_suffix_top1": top1,
        "loss_suffix_topk": top1,
    }


def write_tokenizer(root: Path) -> Path:
    tokenizer = CharTokenizer.train("Answer with exactly two tokens: fixed loss\nanswer: Complete with completion:")
    path = root / "tokenizer.json"
    tokenizer.save(path)
    return path


if __name__ == "__main__":
    unittest.main()
