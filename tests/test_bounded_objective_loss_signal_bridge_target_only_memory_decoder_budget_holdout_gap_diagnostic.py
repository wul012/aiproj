from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME,
    build_decoder_budget_holdout_gap_diagnostic,
    locate_decoder_budget_holdout_replay,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_artifacts import (
    render_decoder_budget_holdout_gap_diagnostic_html,
    render_decoder_budget_holdout_gap_diagnostic_markdown,
    render_decoder_budget_holdout_gap_diagnostic_text,
    write_decoder_budget_holdout_gap_diagnostic_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.diagnose_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap import main as cli_main


class DecoderBudgetHoldoutGapDiagnosticTests(unittest.TestCase):
    def test_detects_tokenizer_prompt_coverage_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path, corpus_path = write_tokenizer_and_corpus(root, corpus="fixed loss answer only")
            report = build_decoder_budget_holdout_gap_diagnostic(
                holdout_report(),
                tokenizer_path=tokenizer_path,
                training_corpus_path=corpus_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_tokenizer_coverage_blocks_promotion")
        self.assertEqual(report["summary"]["dominant_gap"], "tokenizer_prompt_coverage_gap")
        self.assertEqual(report["summary"]["tokenizer_prompt_coverage_gap_count"], 1)
        self.assertEqual(report["summary"]["prompt_unknown_row_count"], 1)
        self.assertGreater(report["summary"]["prompt_unknown_token_count"], 0)
        self.assertEqual(report["summary"]["next_step"], "build_tokenizer_coverage_aware_holdout_suite_before_more_training")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_detects_unseen_prompt_surface_after_tokenizer_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path, corpus_path = write_tokenizer_and_corpus(root, corpus="fixed loss answer only", tokenizer_text="Prompt: fixed loss answer")
            source = holdout_report(prompt="Prompt: fixed loss answer", continuation=" fixed", case_pass=False)
            report = build_decoder_budget_holdout_gap_diagnostic(source, tokenizer_path=tokenizer_path, training_corpus_path=corpus_path)

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_unseen_prompt_surface_blocks_promotion")
        self.assertEqual(report["diagnostic_rows"][0]["failure_class"], "holdout_prompt_unseen_surface_gap")

    def test_failed_source_report_blocks_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path, corpus_path = write_tokenizer_and_corpus(root, corpus="fixed loss")
            source = holdout_report()
            source["status"] = "fail"
            report = build_decoder_budget_holdout_gap_diagnostic(source, tokenizer_path=tokenizer_path, training_corpus_path=corpus_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("holdout_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path, corpus_path = write_tokenizer_and_corpus(root, corpus="fixed loss answer only")
            source_path = root / "holdout" / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME
            write_json_payload(holdout_report(), source_path)
            self.assertEqual(locate_decoder_budget_holdout_replay(source_path.parent), source_path)
            report = build_decoder_budget_holdout_gap_diagnostic(
                holdout_report(),
                tokenizer_path=tokenizer_path,
                training_corpus_path=corpus_path,
            )
            outputs = write_decoder_budget_holdout_gap_diagnostic_outputs(report, root / "out")
            cli_main(
                [
                    "--holdout-replay",
                    str(source_path.parent),
                    "--tokenizer",
                    str(tokenizer_path),
                    "--training-corpus",
                    str(corpus_path),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-diagnostic-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("dominant_gap=tokenizer_prompt_coverage_gap", render_decoder_budget_holdout_gap_diagnostic_text(report))
        self.assertIn("Diagnostic Rows", render_decoder_budget_holdout_gap_diagnostic_markdown(report))
        self.assertIn("holdout gap diagnostic", render_decoder_budget_holdout_gap_diagnostic_html(report))


def write_tokenizer_and_corpus(root: Path, *, corpus: str, tokenizer_text: str = "fixed loss answer only") -> tuple[Path, Path]:
    tokenizer = CharTokenizer.train(tokenizer_text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    corpus_path = root / "prepared_corpus.txt"
    corpus_path.write_text(corpus, encoding="utf-8")
    return tokenizer_path, corpus_path


def holdout_report(*, prompt: str = "任务：输出 fixed loss", continuation: str = " fixed", case_pass: bool = False) -> dict[str, object]:
    hit_terms = ["fixed", "loss"] if case_pass else ["fixed"]
    missed_terms = [] if case_pass else ["loss"]
    return {
        "status": "pass",
        "summary": {"promotion_ready": case_pass, "pass_rate": 1.0 if case_pass else 0.0},
        "replay_rows": [
            {
                "case_id": "case-one",
                "prompt": prompt,
                "continuation": continuation,
                "expected_terms": ["fixed", "loss"],
                "hit_terms": hit_terms,
                "missed_terms": missed_terms,
                "case_pass": case_pass,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
