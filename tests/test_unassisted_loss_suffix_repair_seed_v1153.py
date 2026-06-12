from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.unassisted_holdout_repair_partial_signal_diagnostic_v1152 import (
    UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM,
)
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (
    UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
)
from minigpt.unassisted_loss_suffix_repair_seed_v1153 import (
    LOSS_SUFFIX_REPAIR_CORPUS_NAME,
    UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM,
    build_unassisted_loss_suffix_repair_seed_v1153,
    locate_v1149_seed_corpus,
    locate_v1152_diagnostic,
    resolve_exit_code,
    write_unassisted_loss_suffix_repair_seed_v1153_outputs,
)
from scripts.build_unassisted_loss_suffix_repair_seed_v1153 import main as cli_main


class UnassistedLossSuffixRepairSeedV1153Tests(unittest.TestCase):
    def test_materializes_loss_suffix_repair_seed(self) -> None:
        report = build_unassisted_loss_suffix_repair_seed_v1153(diagnostic_report(), seed_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_loss_suffix_repair_seed_ready")
        self.assertTrue(report["summary"]["unassisted_loss_suffix_repair_seed_ready"])
        self.assertEqual(report["summary"]["base_example_count"], 6)
        self.assertEqual(report["summary"]["repair_example_count"], 6)
        self.assertEqual(report["summary"]["loss_suffix_repair_example_count"], 5)
        self.assertEqual(report["summary"]["zero_hit_full_pair_repair_example_count"], 1)
        self.assertEqual(report["summary"]["target_free_holdout_prompt_count"], 5)
        self.assertEqual(report["summary"]["model_quality_claim"], "seed_revision_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "run_unassisted_loss_suffix_repair_training")
        suffix_rows = [row for row in report["repair_rows"] if row["kind"] == "loss_suffix_after_fixed"]
        self.assertTrue(all(row["training_only_context"] for row in suffix_rows))
        self.assertTrue(all("fixed" in str(row["prompt"]) for row in suffix_rows))
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_diagnostic_failure_blocks_seed_revision(self) -> None:
        diagnostic = diagnostic_report()
        diagnostic["status"] = "fail"
        report = build_unassisted_loss_suffix_repair_seed_v1153(diagnostic, seed_report())

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix_unassisted_loss_suffix_repair_seed_inputs")
        self.assertIn("v1152_diagnostic_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["rows"], [])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_holdout_prompts_remain_target_free(self) -> None:
        report = build_unassisted_loss_suffix_repair_seed_v1153(diagnostic_report(), seed_report())
        prompts = report["holdout_prompt_rows"]

        self.assertEqual(len(prompts), 5)
        self.assertFalse(any("fixed" in str(row["prompt"]).lower() or "loss" in str(row["prompt"]).lower() for row in prompts))

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostic_path = root / "diagnostic" / f"{UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM}.json"
            seed_path = root / "seed" / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
            write_json_payload(diagnostic_report(), diagnostic_path)
            write_json_payload(seed_report(), seed_path)
            report = build_unassisted_loss_suffix_repair_seed_v1153(
                diagnostic_report(),
                seed_report(),
                diagnostic_path=diagnostic_path,
                seed_path=seed_path,
            )
            outputs = write_unassisted_loss_suffix_repair_seed_v1153_outputs(report, root / "repair-seed")
            cli_main(
                [
                    "--diagnostic",
                    str(diagnostic_path.parent),
                    "--seed-corpus",
                    str(seed_path.parent),
                    "--out-dir",
                    str(root / "cli-repair-seed"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

            self.assertEqual(locate_v1152_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_v1149_seed_corpus(seed_path.parent), seed_path)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html", "corpus", "jsonl", "holdout_prompts", "train_command_hint"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM}.json"))
            self.assertTrue((root / "cli-repair-seed" / LOSS_SUFFIX_REPAIR_CORPUS_NAME).is_file())


def diagnostic_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "unassisted_holdout_repair_partial_signal_diagnostic_ready": True,
            "fixed_hit_case_count": 4,
            "loss_hit_case_count": 0,
            "full_pair_case_count": 0,
            "fixed_only_case_count": 4,
            "zero_hit_case_count": 1,
            "promotion_ready": False,
            "next_step": "build_unassisted_loss_suffix_repair_seed",
        },
        "replay_profile": {
            "fixed_only_case_ids": [
                "unassisted-holdout-01",
                "unassisted-holdout-03",
                "unassisted-holdout-04",
                "unassisted-holdout-05",
            ],
            "zero_hit_case_ids": ["unassisted-holdout-02"],
        },
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
        "holdout_prompt_rows": [
            holdout("unassisted-holdout-01", "answer:"),
            holdout("unassisted-holdout-02", "completion:"),
            holdout("unassisted-holdout-03", "finish:"),
            holdout("unassisted-holdout-04", "state compact signal\nanswer:"),
            holdout("unassisted-holdout-05", "signal:"),
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
        "text": f"{prompt}{completion}",
        "target_terms": target_terms,
        "training_only_context": training_only,
        "prompt_contains_target_terms": training_only,
    }


def holdout(case_id: str, prompt: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "prompt": prompt,
        "expected_terms": ["fixed", "loss"],
        "max_new_tokens": 8,
        "temperature": 0.2,
        "top_k": 5,
    }


if __name__ == "__main__":
    unittest.main()
