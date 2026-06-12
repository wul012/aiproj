from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.unassisted_holdout_repair_partial_signal_diagnostic_v1152 import (
    UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM,
    build_unassisted_holdout_repair_partial_signal_diagnostic_v1152,
    locate_v1149_seed_corpus,
    locate_v1151_replay_comparison,
    resolve_exit_code,
    write_unassisted_holdout_repair_partial_signal_diagnostic_v1152_outputs,
)
from minigpt.unassisted_holdout_repair_replay_comparison_v1151 import (
    UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM,
)
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (
    UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
)
from scripts.diagnose_unassisted_holdout_repair_partial_signal_v1152 import main as cli_main


class UnassistedHoldoutRepairPartialSignalDiagnosticV1152Tests(unittest.TestCase):
    def test_fixed_only_partial_signal_is_diagnostic_ready(self) -> None:
        report = build_unassisted_holdout_repair_partial_signal_diagnostic_v1152(replay_report(), seed_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_holdout_repair_partial_signal_diagnostic_ready")
        self.assertTrue(report["summary"]["unassisted_holdout_repair_partial_signal_diagnostic_ready"])
        self.assertEqual(report["summary"]["fixed_hit_case_count"], 4)
        self.assertEqual(report["summary"]["loss_hit_case_count"], 0)
        self.assertEqual(report["summary"]["full_pair_case_count"], 0)
        self.assertEqual(report["summary"]["loss_after_fixed_training_context_count"], 1)
        self.assertEqual(report["summary"]["root_cause_hypothesis"], "loss_suffix_context_tied_and_underlearned_after_fixed")
        self.assertEqual(report["summary"]["next_step"], "build_unassisted_loss_suffix_repair_seed")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_source_replay_failure_blocks_diagnostic(self) -> None:
        replay = replay_report()
        replay["status"] = "fail"
        report = build_unassisted_holdout_repair_partial_signal_diagnostic_v1152(replay, seed_report())

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_unassisted_holdout_repair_partial_signal_diagnostic_inputs")
        self.assertIn("v1151_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_loss_suffix_without_training_context_changes_hypothesis(self) -> None:
        seed = seed_report()
        seed["rows"] = [row for row in seed["rows"] if row["kind"] != "loss_after_model_fixed"]
        report = build_unassisted_holdout_repair_partial_signal_diagnostic_v1152(replay_report(), seed)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["loss_after_fixed_training_context_count"], 0)
        self.assertEqual(report["summary"]["root_cause_hypothesis"], "loss_suffix_underlearned_after_fixed")

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / f"{UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM}.json"
            seed_path = root / "seed" / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
            write_json_payload(replay_report(), replay_path)
            write_json_payload(seed_report(), seed_path)
            report = build_unassisted_holdout_repair_partial_signal_diagnostic_v1152(
                replay_report(),
                seed_report(),
                replay_path=replay_path,
                seed_path=seed_path,
            )
            outputs = write_unassisted_holdout_repair_partial_signal_diagnostic_v1152_outputs(report, root / "diagnostic")
            cli_main(
                [
                    "--replay",
                    str(replay_path.parent),
                    "--seed-corpus",
                    str(seed_path.parent),
                    "--out-dir",
                    str(root / "cli-diagnostic"),
                    "--require-diagnostic-ready",
                    "--force",
                ]
            )

            self.assertEqual(locate_v1151_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_v1149_seed_corpus(seed_path.parent), seed_path)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM}.json"))
            self.assertTrue((root / "cli-diagnostic" / f"{UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM}.html").is_file())


def replay_report() -> dict[str, object]:
    rows = [
        generation("unassisted-holdout-01", "answer:", " fixed\n\n", True, False),
        generation("unassisted-holdout-02", "completion:", " fios\n\n\n", False, False),
        generation("unassisted-holdout-03", "finish:", " fixed\n\n", True, False),
        generation("unassisted-holdout-04", "state compact signal\nanswer:", "e compact signal\nanswer: fixed\n\n", True, False, generated_prefix=False),
        generation("unassisted-holdout-05", "signal:", " fixed\n\n", True, False),
    ]
    return {
        "status": "pass",
        "decision": "unassisted_holdout_repair_replay_partial_signal",
        "rows": rows,
        "summary": {
            "unassisted_holdout_repair_replay_ready": True,
            "case_count": 5,
            "fixed_hit_case_count": 4,
            "loss_hit_case_count": 0,
            "full_pair_case_count": 0,
            "partial_signal_visible": True,
            "promotion_ready": False,
            "next_step": "diagnose_unassisted_holdout_repair_partial_signal",
        },
    }


def generation(case_id: str, prompt: str, continuation: str, fixed: bool, loss: bool, *, generated_prefix: bool = True) -> dict[str, object]:
    return {
        "case_id": case_id,
        "prompt": prompt,
        "generated": prompt + continuation if generated_prefix else continuation,
        "continuation": continuation,
        "expected_terms": ["fixed", "loss"],
        "fixed_hit": fixed,
        "loss_hit": loss,
        "full_pair_hit": fixed and loss,
        "status": "pass" if fixed and loss else "partial" if fixed or loss else "fail",
    }


def seed_report() -> dict[str, object]:
    return {
        "status": "pass",
        "rows": [
            seed("pair-01", "full_pair", "answer:", " fixed loss", ["fixed", "loss"]),
            seed("pair-02", "full_pair", "completion:", " fixed loss", ["fixed", "loss"]),
            seed("pair-03", "full_pair", "finish:", " fixed loss", ["fixed", "loss"]),
            seed("fixed-01", "fixed_first", "answer:", " fixed", ["fixed"]),
            seed("fixed-02", "fixed_first", "completion:", " fixed", ["fixed"]),
            seed("loss-after-fixed-01", "loss_after_model_fixed", "answer: fixed", " loss", ["fixed", "loss"], training_only=True),
        ],
        "summary": {
            "unassisted_holdout_repair_seed_corpus_ready": True,
            "promotion_ready": False,
        },
    }


def seed(
    example_id: str,
    kind: str,
    prompt: str,
    completion: str,
    target_terms: list[str],
    *,
    training_only: bool = False,
) -> dict[str, object]:
    return {
        "example_id": example_id,
        "kind": kind,
        "prompt": prompt,
        "completion": completion,
        "target_terms": target_terms,
        "training_only_context": training_only,
    }


if __name__ == "__main__":
    unittest.main()
