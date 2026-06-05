from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic import (
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_patch import (
    TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME,
    build_target_only_memory_patch,
    locate_replay_comparison,
    locate_zero_hit_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_patch_artifacts import (
    render_target_only_memory_patch_html,
    render_target_only_memory_patch_markdown,
    render_target_only_memory_patch_text,
    write_target_only_memory_patch_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_patch import main as cli_main


class TargetOnlyMemoryPatchTests(unittest.TestCase):
    def test_builds_target_only_memory_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_target_only_memory_patch(
                zero_hit_diagnostic(),
                replay_comparison(),
                source_corpus_path=write_corpus(Path(tmp)),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_patch_ready"])
        self.assertEqual(report["summary"]["patch_example_count"], 24)
        self.assertEqual(report["summary"]["target_only_example_count"], 14)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("fixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_without_loss_improved_zero_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = zero_hit_diagnostic()
            diagnostic["summary"]["loss_improved_without_required_term_uptake"] = False
            report = build_target_only_memory_patch(diagnostic, replay_comparison(), source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("loss_improved_without_uptake", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            diagnostic_path = root / "diagnostic" / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
            replay_path = root / "replay" / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(zero_hit_diagnostic(), diagnostic_path)
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_zero_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_replay_comparison(replay_path.parent), replay_path)
            report = build_target_only_memory_patch(zero_hit_diagnostic(), replay_comparison(), source_corpus_path=corpus)
            outputs = write_target_only_memory_patch_outputs(report, root / "out")
            cli_main(["--zero-hit-diagnostic", str(diagnostic_path.parent), "--replay-comparison", str(replay_path.parent), "--source-corpus", str(corpus), "--out-dir", str(root / "cli-out"), "--require-patch-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME))
        self.assertIn("target_only_memory_patch_ready=True", render_target_only_memory_patch_text(report))
        self.assertIn("Patch Examples", render_target_only_memory_patch_markdown(report))
        self.assertIn("target_only_completion_memory", render_target_only_memory_patch_html(report))


def zero_hit_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready": True,
            "all_cases_label_or_fragment": True,
            "loss_improved_without_required_term_uptake": True,
        },
        "case_diagnostics": [
            {"case_id": "canonical_direct_completion", "continuation_class": "exact_label_echo"},
            {"case_id": "minimal_direct_completion", "continuation_class": "exact_label_echo"},
            {"case_id": "completion_label_surface", "continuation_class": "label_prefix_fragment"},
        ],
    }


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready": True,
            "any_hit_case_count": 0,
        },
        "replay_rows": [
            {"case_id": "canonical_direct_completion", "prompt": "Answer with exactly two tokens: fixed loss\nanswer:"},
            {"case_id": "minimal_direct_completion", "prompt": "Answer with exactly two words: fixed loss\nanswer:"},
            {"case_id": "completion_label_surface", "prompt": "Complete with exactly two tokens: fixed loss\ncompletion:"},
        ],
    }


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("answer:\nfixed loss\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
