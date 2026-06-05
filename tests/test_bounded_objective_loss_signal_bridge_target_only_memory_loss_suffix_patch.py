from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSON_FILENAME,
    build_loss_suffix_patch,
    locate_partial_hit_diagnostic,
    locate_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_artifacts import (
    render_loss_suffix_patch_html,
    render_loss_suffix_patch_markdown,
    render_loss_suffix_patch_text,
    write_loss_suffix_patch_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch import main as cli_main


class TargetOnlyMemoryLossSuffixPatchTests(unittest.TestCase):
    def test_builds_loss_suffix_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_loss_suffix_patch(
                partial_hit_diagnostic(),
                replay_comparison(),
                source_corpus_path=write_corpus(Path(tmp)),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready"])
        self.assertEqual(report["summary"]["patch_example_count"], 27)
        self.assertEqual(report["summary"]["target_pair_example_count"], 12)
        self.assertEqual(report["summary"]["loss_suffix_example_count"], 9)
        self.assertEqual(report["summary"]["loss_prefix_bridge_example_count"], 3)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("fixed l\nloss\nfixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_without_all_loss_prefix_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = partial_hit_diagnostic()
            diagnostic["summary"]["all_cases_loss_prefix"] = False
            report = build_loss_suffix_patch(diagnostic, replay_comparison(), source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_cases_loss_prefix", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            diagnostic_path = root / "diagnostic" / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
            replay_path = root / "replay" / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(partial_hit_diagnostic(), diagnostic_path)
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_partial_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_replay_comparison(replay_path.parent), replay_path)
            report = build_loss_suffix_patch(partial_hit_diagnostic(), replay_comparison(), source_corpus_path=corpus)
            outputs = write_loss_suffix_patch_outputs(report, root / "out")
            cli_main([
                "--partial-hit-diagnostic",
                str(diagnostic_path.parent),
                "--replay-comparison",
                str(replay_path.parent),
                "--source-corpus",
                str(corpus),
                "--out-dir",
                str(root / "cli-out"),
                "--require-patch-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSON_FILENAME))
        self.assertIn("loss_suffix_patch_ready=True", render_loss_suffix_patch_text(report))
        self.assertIn("loss_prefix_bridge", render_loss_suffix_patch_markdown(report))
        self.assertIn("Patch Examples", render_loss_suffix_patch_html(report))


def partial_hit_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready": True,
            "loss_prefix_case_count": 3,
            "loss_hit_case_count": 0,
            "all_cases_loss_prefix": True,
        },
    }


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "any_hit_case_count": 3,
        },
        "replay_rows": [
            row("canonical_direct_completion", "\nfixed l"),
            row("minimal_direct_completion", "\nfixed l"),
            row("completion_label_surface", "fixed l"),
        ],
    }


def row(case_id: str, continuation: str) -> dict[str, object]:
    return {"case_id": case_id, "continuation": continuation}


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("fixed loss\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
