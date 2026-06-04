from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_patch import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_pair_binding_patch,
    locate_partial_hit_diagnostic,
    locate_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_patch_artifacts import (
    render_pair_binding_patch_html,
    render_pair_binding_patch_markdown,
    render_pair_binding_patch_text,
    write_pair_binding_patch_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_partial_hit_diagnostic import (
    LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_pair_binding_patch import main as cli_main


class BoundedObjectiveLossSignalBridgePairBindingPatchTests(unittest.TestCase):
    def test_builds_pair_binding_patch_from_split_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = write_corpus(Path(tmp))
            report = build_bounded_objective_loss_signal_bridge_pair_binding_patch(
                partial_hit_diagnostic(),
                replay_comparison(),
                source_corpus_path=source,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_pair_binding_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_pair_binding_patch_ready"])
        self.assertGreaterEqual(report["summary"]["patch_example_count"], 12)
        self.assertGreater(report["summary"]["pair_binding_example_count"], 0)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("fixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_without_pair_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = partial_hit_diagnostic()
            diagnostic["summary"]["paired_signal_split"] = False
            report = build_bounded_objective_loss_signal_bridge_pair_binding_patch(
                diagnostic,
                replay_comparison(),
                source_corpus_path=write_corpus(Path(tmp)),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("pair_split_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_corpus(root)
            diagnostic_path = root / "diagnostic" / LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
            replay_path = root / "replay" / LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(partial_hit_diagnostic(), diagnostic_path)
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_partial_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_replay_comparison(replay_path.parent), replay_path)
            report = build_bounded_objective_loss_signal_bridge_pair_binding_patch(
                partial_hit_diagnostic(),
                replay_comparison(),
                source_corpus_path=source,
            )
            outputs = write_pair_binding_patch_outputs(report, root / "out")
            cli_main(
                [
                    "--partial-hit-diagnostic",
                    str(diagnostic_path.parent),
                    "--replay-comparison",
                    str(replay_path.parent),
                    "--source-corpus",
                    str(source),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-patch-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME))
        self.assertIn("pair_binding_patch_ready=True", render_pair_binding_patch_text(report))
        self.assertIn("Patch Examples", render_pair_binding_patch_markdown(report))
        self.assertIn("case_pair_repeat", render_pair_binding_patch_html(report))


def partial_hit_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready": True,
            "paired_signal_split": True,
        },
        "case_diagnostics": [
            {"case_id": "canonical_direct_completion", "label": "loss_only"},
            {"case_id": "minimal_direct_completion", "label": "fixed_only"},
            {"case_id": "completion_label_surface", "label": "zero_hit"},
        ],
    }


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_replay_comparison_ready": True,
            "objective_contract_recovered": False,
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
