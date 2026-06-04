from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_curriculum_patch_profile_sweep import CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME
from minigpt.bounded_objective_loss_signal_bridge import (
    LOSS_SIGNAL_BRIDGE_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge,
    locate_profile_sweep,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_artifacts import (
    render_loss_signal_bridge_html,
    render_loss_signal_bridge_markdown,
    render_loss_signal_bridge_text,
    write_loss_signal_bridge_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge import main as cli_main


class BoundedObjectiveLossSignalBridgeTests(unittest.TestCase):
    def test_builds_bridge_from_loss_and_fixed_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = write_corpus(Path(tmp))
            report = build_bounded_objective_loss_signal_bridge(profile_sweep(), source_corpus_path=corpus)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_ready"])
        self.assertGreaterEqual(report["summary"]["bridge_example_count"], 8)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("loss_signal_pair_bridge", report["summary"]["bridge_kinds"])
        self.assertIn("fixed_signal_pair_bridge", report["summary"]["bridge_kinds"])
        self.assertIn("fixed loss", report["bridged_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_bridge_ready=True), 0)

    def test_fails_without_loss_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = write_corpus(Path(tmp))
            sweep = profile_sweep()
            sweep["summary"]["max_loss_hit_case_count"] = 0
            report = build_bounded_objective_loss_signal_bridge(sweep, source_corpus_path=corpus)

        self.assertEqual(report["status"], "fail")
        self.assertIn("loss_signal_present", [row["id"] for row in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_bridge_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            sweep_path = root / "sweep" / CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME
            write_json_payload(profile_sweep(), sweep_path)
            self.assertEqual(locate_profile_sweep(sweep_path.parent), sweep_path)
            report = build_bounded_objective_loss_signal_bridge(profile_sweep(), source_corpus_path=corpus, profile_sweep_path=sweep_path)
            outputs = write_loss_signal_bridge_outputs(report, root / "out")
            cli_main(["--profile-sweep", str(sweep_path.parent), "--source-corpus", str(corpus), "--out-dir", str(root / "cli-out"), "--require-bridge-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_JSON_FILENAME))
        self.assertIn("bounded_objective_loss_signal_bridge_ready=True", render_loss_signal_bridge_text(report))
        self.assertIn("Bridge Examples", render_loss_signal_bridge_markdown(report))
        self.assertIn("loss_signal_pair_bridge", render_loss_signal_bridge_html(report))


def profile_sweep() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_curriculum_patch_profile_sweep_ready": True,
            "max_loss_hit_case_count": 2,
            "any_profile_recovered": False,
        },
        "sweep_rows": [
            row("longer-open", "canonical", ["loss"], ["fixed"], "fixer: loss"),
            row("longer-open", "completion", ["loss"], ["fixed"], "fixet lossw"),
            row("top1-low-temp", "canonical", ["fixed"], ["loss"], " fixed l"),
            row("top1-low-temp", "completion", ["fixed"], ["loss"], " fixed l"),
        ],
    }


def row(profile_id: str, case_id: str, hit_terms: list[str], missed_terms: list[str], continuation: str) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "prompt": "answer:",
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "loss_hit": "loss" in hit_terms,
        "fixed_hit": "fixed" in hit_terms,
        "continuation": continuation,
    }


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("answer:\nfixed loss\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
