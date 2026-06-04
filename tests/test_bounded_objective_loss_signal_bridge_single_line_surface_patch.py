from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic import (
    PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_patch import (
    SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME,
    build_single_line_surface_patch,
    locate_replay_comparison,
    locate_zero_hit_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_patch_artifacts import (
    render_single_line_surface_patch_html,
    render_single_line_surface_patch_markdown,
    render_single_line_surface_patch_text,
    write_single_line_surface_patch_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_single_line_surface_patch import main as cli_main


class SingleLineSurfacePatchTests(unittest.TestCase):
    def test_builds_single_line_surface_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_single_line_surface_patch(zero_hit_diagnostic(), replay_comparison(), source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_single_line_surface_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_single_line_surface_patch_ready"])
        self.assertEqual(report["summary"]["single_line_case_example_count"], 6)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["completion_surface_example_count"], 2)
        self.assertIn("answer: fixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_without_label_echo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = zero_hit_diagnostic()
            diagnostic["summary"]["all_cases_label_echo"] = False
            report = build_single_line_surface_patch(diagnostic, replay_comparison(), source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("label_echo_confirmed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            diagnostic_path = root / "diagnostic" / PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
            replay_path = root / "replay" / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(zero_hit_diagnostic(), diagnostic_path)
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_zero_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_replay_comparison(replay_path.parent), replay_path)
            report = build_single_line_surface_patch(zero_hit_diagnostic(), replay_comparison(), source_corpus_path=corpus)
            outputs = write_single_line_surface_patch_outputs(report, root / "out")
            cli_main(["--zero-hit-diagnostic", str(diagnostic_path.parent), "--replay-comparison", str(replay_path.parent), "--source-corpus", str(corpus), "--out-dir", str(root / "cli-out"), "--require-patch-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME))
        self.assertIn("single_line_surface_patch_ready=True", render_single_line_surface_patch_text(report))
        self.assertIn("Patch Examples", render_single_line_surface_patch_markdown(report))
        self.assertIn("single_line_case_surface", render_single_line_surface_patch_html(report))


def zero_hit_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_ready": True,
            "all_cases_label_echo": True,
        },
    }


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready": True,
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
